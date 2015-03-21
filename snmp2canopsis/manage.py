# File that act like cat-nagios
import sys
import subprocess
import json
from ConfigParser import ConfigParser

INIT_SCRIPT = "/etc/init.d/snmp2canopsis"
CONFIG_FN = "/etc/snmp2canopsis.conf"
LOGFILE_FN = "/var/log/snmp2canopsis.log"


def cmd_start():
    p = subprocess.Popen(["snmp2canopsis", "--daemon", "--logfile", LOGFILE_FN],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p.returncode


def cmd_stop():
    p = subprocess.Popen(["snmp2canopsis", "--kill"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p.returncode


def cmd_restart():
    cmd_stop()
    return cmd_start()


def cmd_get_state():
    p = subprocess.Popen(["snmp2canopsis", "--status"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    status = 1 if p.returncode == 0 else 0
    ret = {"connector": status}
    print(json.dumps(ret))
    return p.returncode


def cmd_get_conf():
    # read version
    p = subprocess.Popen(["snmp2canopsis", "--version"],
                         stdout=subprocess.PIPE)
    version = p.communicate()[0].splitlines()[0]
    # read configuration file
    config = ConfigParser()
    with open(CONFIG_FN, "r") as fd:
        config.readfp(fd)
    ret = {
        "version": version,
        "virtual_host": config.get("amqp", "vhost"),
        "userid": config.get("amqp", "user"),
        "exchange_name": config.get("amqp", "exchange"),
        "host": config.get("amqp", "host"),
        "password": config.get("amqp", "password"),
        "port": config.get("amqp", "port"),
        "snmp_port": config.get("snmp", "port"),
        "snmp_ip": config.get("snmp", "ip")
    }
    print(json.dumps(ret))
    return 0


def cmd_set_conf():
    mapping = {
        "virtual_host": ("amqp", "vhost"),
        "userid": ("amqp", "user"),
        "exchange_name": ("amqp", "exchange"),
        "host": ("amqp", "host"),
        "password": ("amqp", "password"),
        "port": ("amqp", "port"),
        "snmp_port": ("snmp", "port"),
        "snmp_ip": ("snmp", "ip")
    }
    conf = json.loads(sys.stdin.read())

    config = ConfigParser()
    with open(CONFIG_FN, "r") as fd:
        config.readfp(fd)

    for key, value in conf.iteritems():
        if key not in mapping:
            continue
        section, name = mapping[key]
        config.set(section, name, value)

    with open(CONFIG_FN, "w") as fd:
        config.write(fd)
    return 0


def main():
    commands = ("start", "stop", "restart", "getState", "getConf", "setConf")
    if len(sys.argv) < 2:
        print("Error: missing command")
        sys.exit(1)

    command = sys.argv[1]
    if command not in commands:
        print("Error: invalid command '{}'".format(command))
        sys.exit(1)

    if command == "getState":
        ret = cmd_get_state()
    elif command == "getConf":
        ret = cmd_get_conf()
    elif command == "setConf":
        ret = cmd_set_conf()
    elif command == "start":
        cmd_start()
        ret = cmd_get_state()
    elif command == "stop":
        cmd_stop()
        ret = cmd_get_state()
    elif command == "restart":
        ret = cmd_restart()
    sys.exit(ret)

if __name__ == "__main__":
    main()
