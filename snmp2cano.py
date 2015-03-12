#!/usr/bin/env python
"""
SNMP Connector for Canopsis
===========================

.. author:: Mathieu Virbel <mat@meltingrocks.com>
"""

__version__ = "0.1"


import time
import json
import logbook
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
from threading import Thread, Semaphore
from collections import deque
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from kombu import Connection
from kombu.pools import producers


# Logging
logsnmp = logbook.Logger("snmp")
logamqp = logbook.Logger("amqp")


# Configuration
config = ConfigParser()


# Queue management
q = deque()
sem = Semaphore(0)


def read_snmp_queue(producer):
    # consume the snmp event in the queue.
    exchange = config.get("amqp", "exchange")
    while sem.acquire(True):
        if not q:
            return True
        event = q[0]
        try:
            routing_key = "{}.{}.{}.{}.{}".format(
                event["connector"], event["connector_name"],
                event["event_type"], event["source_type"],
                event["component"])

            producer.publish(
                event,
                serializer="json",
                exchange=exchange,
                routing_key=routing_key)
        except:
            logamqp.exception("Error while publishing an event")
            sem.release()
            return
        else:
            q.popleft()


def thread_producer():
    logamqp.debug("Thread started")
    options = {
        "hostname": config.get("amqp", "host"),
        "userid": config.get("amqp", "user"),
        "port": config.getint("amqp", "port"),
        "virtual_host": config.get("amqp", "host"),
        "password": config.get("amqp", "password")}

    while True:
        logamqp.info("Connecting to {userid}@{hostname}, on {virtual_host}",
                     **options)
        try:
            with Connection(**options) as conn:
                with producers[conn].acquire(block=True) as producer:
                    logamqp.debug("Read the snmp queue"),
                    if read_snmp_queue(producer):
                        logamqp.debug("Leaving the thread")
                        return

                    time.sleep(2)
                    continue
        except Exception as e:
            logamqp.exception("Error during the connection, restarting")
            time.sleep(1)

    logamqp.debug("Thread leaved.")


def val_to_json(val):
    val = val.getComponent().getComponent()
    return val.prettyPrint()


def snmp_callback(dispatcher, domain, address, msg):
    while msg:
        msg_version = int(api.decodeMessageVersion(msg))
        if msg_version in api.protoModules:
            mod = api.protoModules[msg_version]
        else:
            logsnmp.error("Unsupported SNMP version {}".format(msg_version))
            return
        reqmsg, msg = decoder.decode(msg, asn1Spec=mod.Message())
        reqpdu = mod.apiMessage.getPDU(reqmsg)
        if reqpdu.isSameTypeWith(mod.TrapPDU()):
            event = {
                "connector": "snmp",
                "connector_name": "snmp2cano",
                "event_type": "trap",
                "source_type": "component",
                "state": 3,
                "state_type": 1,
                "timestamp": time.time()}
            message = {}
            if msg_version == api.protoVersion1:
                atp = mod.apiTrapPDU
                event["component"] = atp.getAgentAddr(reqpdu).prettyPrint()
                message["enterprise"] = atp.getEnterprise(reqpdu).prettyPrint()
                message["timeticks"] = atp.getTimeStamp(reqpdu).prettyPrint()
                var_binds = atp.getVarBindList(reqpdu)
                message["vars"] = {}
                for oid, val in var_binds:
                    message["vars"][oid.prettyPrint()] = val_to_json(val)
            else:
                raise NotImplementedError()

            event["output"] = json.dumps(message)
            q.append(event)
            sem.release()

    return msg


def run():
    # start the thread to amqp
    amqp_thread = Thread(target=thread_producer)
    amqp_thread.daemon = True
    amqp_thread.start()

    # start the snmp daemon
    dispatcher = AsynsockDispatcher()
    dispatcher.registerRecvCbFun(snmp_callback)
    snmp_ip = config.get("snmp", "ip")
    snmp_port = config.getint("snmp", "port")
    dispatcher.registerTransport(
        udp.domainName,
        udp.UdpSocketTransport().openServerMode((snmp_ip, snmp_port)))
    dispatcher.jobStarted(1)
    try:
        logsnmp.info("Start SNMP listener on {}:{}".format(
            snmp_ip, snmp_port))
        dispatcher.runDispatcher()
    except KeyboardInterrupt:
        logsnmp.info("Stop SNMP listener")
        dispatcher.closeDispatcher()

        logsnmp.debug("Stop AMQP thread")
        sem.release()
        try:
            while amqp_thread.isAlive():
                amqp_thread.join(.5)
        except KeyboardInterrupt:
            logsnmp.warning("Unable to stop AMQP thread, leaving")
            logsnmp.warning("{} messages lost".format(len(q)))


def main():
    # entry point
    import argparse

    parser = argparse.ArgumentParser(description="Send SNMP trap to amqp")
    parser.add_argument("-p", "--port", type=int, nargs="?",
                        default=162,
                        help="SNMP port to listen")
    parser.add_argument("-l", "--ip", nargs="?",
                        default="127.0.0.1",
                        help="SNMP ip to listen (0.0.0.0 for all)")
    parser.add_argument("-H", "--amqp-host", nargs="?",
                        default="127.0.0.1",
                        help="AMQP hostname")
    parser.add_argument("-P", "--amqp-port", type=int, nargs="?",
                        default=5672,
                        help="AMQP port")
    parser.add_argument("-U", "--amqp-user", nargs="?",
                        default="guest",
                        help="AMQP user")
    parser.add_argument("-W", "--amqp-password", nargs="?",
                        default="guest",
                        help="AMQP password")
    parser.add_argument("-V", "--amqp-vhost", nargs="?",
                        default="canopsis",
                        help="AMQP vhost")
    parser.add_argument("-E", "--amqp-exchange", nargs="?",
                        default="canopsis.events",
                        help="AMQP exchange")
    parser.add_argument("-c", "--config", nargs="?",
                        help="Configuration file")

    args = parser.parse_args()

    if args.config:
        config.read(args.config)

    if not config.has_section("snmp"):
        config.add_section("snmp")
    if not config.has_option("snmp", "ip"):
        config.set("snmp", "ip", args.ip)
    if not config.has_option("snmp", "port"):
        config.set("snmp", "port", str(args.port))
    if not config.has_section("amqp"):
        config.add_section("amqp")
    if not config.has_option("amqp", "host"):
        config.set("amqp", "host", args.amqp_host)
    if not config.has_option("amqp", "port"):
        config.set("amqp", "port", str(args.amqp_port))
    if not config.has_option("amqp", "user"):
        config.set("amqp", "user", args.amqp_user)
    if not config.has_option("amqp", "password"):
        config.set("amqp", "password", args.amqp_password)
    if not config.has_option("amqp", "vhost"):
        config.set("amqp", "vhost", args.amqp_vhost)
    if not config.has_option("amqp", "exchange"):
        config.set("amqp", "exchange", args.amqp_exchange)

    run()

if __name__ == "__main__":
    main()