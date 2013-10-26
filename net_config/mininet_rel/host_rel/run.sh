#!/bin/bash
# Port conventions and mappings:
# for transit P t{?} -> l_port:90{?}
# TCPServer running at controller1 -> port: 9999
# TCPServer running at scheduler   -> port: 9998
echo $1

if [ $1  = 'p' ]
then
  #python producer.py 127.0.0.1 7000 short_data.dat
  python producer.py 10.0.0.1 7000 short_data.dat
elif [ $1  = 'c' ]
then
  python consumer.py 127.0.0.1 7000 7001 7002
  #python producer.py 10.0.0.1 7000 short_data.dat
elif [ $1  = 't' ]
then
	python transit.py 7000 wlan0
else
	echo "Argument did not match !"
fi