#!/bin/bash

echo $1

POXDIR=~/pox/

if [ $1 = 'cli' ]
then
	echo "Aha"
elif [ $1 = 'act' ]
then
	$POXDIR/./pox.py openflow.of_01 --port=9001 actuator --proactive_install=True  #misc.arp_responder --10.0.0.255=11:00:00:00:00:01
elif [ $1 = 'sch' ]
then
	$POXDIR/./pox.py openflow.of_01 --port=9010 sch_controller #misc.arp_responder --no_learn=True
elif [ $1 = 'arp' ]
then
	$POXDIR/./pox.py openflow.of_01 --port=9111 arp_responder --no_learn=True
elif [ $1 = 'den' ]
then
	$POXDIR/./pox.py openflow.of_01 --port=7000 deneme_controller
elif [ $1 = 'span' ]
then
	$POXDIR/./pox.py openflow.of_01 --port=9011 openflow.discovery openflow.spanning_tree --no-flood --hold-down
else
	echo "Argument did not match !"
fi
