#!/bin/bash
# Port conventions and mappings:
# for transit P t{?} -> l_port:90{?}
# TCPServer running at controller1 -> port: 9999
# TCPServer running at scheduler   -> port: 9998
echo $1

if [ $1  = 'p' ]
then
  python producer.py --c_addr=127.0.0.1 --cl_port=7000 --datasize=1 --logto=console
  #python producer.py --c_addr=10.0.0.1 --cl_port=7000 --datasize=10 --logto=console
elif [ $1  = 'c' ]
then
  python consumer.py --laddr=127.0.0.1 --logto=console --lports=7000,7001,7002
  #python producer.py 10.0.0.1 7000 short_data.dat
elif [ $1  = 't' ]
then
	python transit.py --nodename=mfa --lsching_port=7000 --bind_intf=wlan0 --logto=file
elif [ $1  = 't11' ]
then
	python transit.py --nodename=t11 --lsching_port=7000 --bind_intf=eth0 --logto=file
elif [ $1  = 't21' ]
then
	python transit.py --nodename=t21 --lsching_port=7000 --bind_intf=eth0 --logto=file
elif [ $1  = 't31' ]
then
  python transit.py --nodename=t31 --lsching_port=7000 --bind_intf=eth0 --logto=file
elif [ $1  = 'ds' ]
then
  python dummy_sender.py --dst_ip=127.0.0.1 --dst_lport=7998 --proto=tcp
elif [ $1  = 'dsp' ]
then
	python dummy_sender.py --dst_ip=10.0.0.1 --dst_lport=6000 --proto=udp
elif [ $1  = 'dr' ]
then
	python dummy_receiver.py --lintf=lo --lport=7999 --proto=tcp
else
	echo "Argument did not match !"
fi
