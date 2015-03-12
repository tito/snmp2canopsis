# SNMP trap daemon for Canopsis / AMQP

`snmp2cano` is a daemon that listen to SNMP trap and send them into
the Canopsis/AMQP.


## Installation

Stable version:

    pip install snmp2cano

Development version:

    pip install https://github.com/tito/snmp2cano


## Usage

Since the tool need to listen the SNMP trap port, you'll need to execute it
with root permission:

    $ sudo snmp2cano

Create a configuration file named "snmp2cano.conf":

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

    $ sudo snmp2cano -c snmp2cano.conf


## Test trap (incomplete)

$ snmptrap -v 1 -c public localhost IF-MIB:linkDown localhost 2 0 '' \
  ifIndex i 1 ifAdminStatus i 2 ifOperStatus i 2

$ snmptrap -v 2c -c public localhost '' IF-MIB:linkDown \
  ifIndex i 1 ifAdminStatus i 2 ifOperStatus i 2
