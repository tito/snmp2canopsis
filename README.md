# SNMP trap daemon for Canopsis / AMQP

`snmp2canopsis` is a daemon that listen to SNMP trap and send them into
the Canopsis/AMQP.


## Installation

Stable version (not published yet):

    pip install snmp2canopsis

Development version:

    pip install https://github.com/tito/snmp2canopsis


## Usage

Since the tool need to listen the SNMP trap port, you'll need to execute it
with root permission:

    $ sudo snmp2canopsis

Create a configuration file named "/etc/snmp2canopsis.conf":

    [snmp]
    ip = 127.0.0.1
    port = 162

    [amqp]
    host = localhost
    port = 5672
    user = guest
    password = guest
    vhost = amqp
    exchange = amqp.events

Then you can start with a predefined configuration:

    $ sudo snmp2canopsis -c snmp2canopsis.conf

Otherwise, you can go manually:

    $ snmp2canopsis --help
    usage: snmp2canopsis [-h] [-p [PORT]] [-l [IP]] [-H [AMQP_HOST]] [-P [AMQP_PORT]]
                     [-U [AMQP_USER]] [-W [AMQP_PASSWORD]] [-V [AMQP_VHOST]]
                     [-E [AMQP_EXCHANGE]] [-c [CONFIG]]

    Send SNMP trap to amqp

    optional arguments:
      -h, --help            show this help message and exit
      -p [PORT], --port [PORT]
                            SNMP port to listen
      -l [IP], --ip [IP]    SNMP ip to listen (0.0.0.0 for all)
      -H [AMQP_HOST], --amqp-host [AMQP_HOST]
                            AMQP hostname
      -P [AMQP_PORT], --amqp-port [AMQP_PORT]
                            AMQP port
      -U [AMQP_USER], --amqp-user [AMQP_USER]
                            AMQP user
      -W [AMQP_PASSWORD], --amqp-password [AMQP_PASSWORD]
                            AMQP password
      -V [AMQP_VHOST], --amqp-vhost [AMQP_VHOST]
                            AMQP vhost
      -E [AMQP_EXCHANGE], --amqp-exchange [AMQP_EXCHANGE]
                            AMQP exchange
      -c [CONFIG], --config [CONFIG]
                            Configuration file

A daemon management is also included, you can start it with:

    $ snmp2canopsis --daemon
    [2015-03-21 10:01:30.654804] INFO: snmp2canopsis: Read configuration from /etc/snmp2canopsis.conf
    Starting...

    $ snmp2canopsis --status
    [2015-03-21 10:01:57.394623] INFO: snmp2canopsis: Read configuration from /etc/snmp2canopsis.conf
    Process (pid 22688) is running...

    $ snmp2canopsis --kill
    [2015-03-21 10:02:00.773632] INFO: snmp2canopsis: Read configuration from /etc/snmp2canopsis.conf
    Stopping...
    Stopped


## Process management (ala nagios)

A script is included to allow to start/stop the process, and manage
configuration (start, stop, getState, getConf, setConf).

    # cat-snmp2canopsis status
    {"connector": "0"}
    # cat-snmp2canopsis start
    {"connector": "1"}
    # cat-snmp2canopsis getState
    {"connector": "1"}
    # cat-snmp2canopsis getConf
    {"host": "localhost", "version": "0.2", "virtual_host": "canopsis",
     "snmp_port": "162", "snmp_ip": "0.0.0.0",
     "exchange_name": "canopsis.snmp", "password": "guest",
     "userid": "guest", "port": "5672"}
    # cat-snmp2canopsis stop
    {"connector": "0"}


## Test trap (incomplete)

    $ snmptrap -v 1 -c public localhost IF-MIB:linkDown localhost 2 0 '' \
      ifIndex i 1 ifAdminStatus i 2 ifOperStatus i 2

    $ snmptrap -v 2c -c public localhost '' IF-MIB:linkDown \
      ifIndex i 1 ifAdminStatus i 2 ifOperStatus i 2
