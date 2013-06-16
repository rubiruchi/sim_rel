#!/bin/bash
echo $1
if [ $1 = 'cli' ]
then
	make cli
	./cli_deneme
elif [ $1 = 'sch' ]
then
	run-parts --regex '^r.*sh$' --arg 'cli' ~/git_repo/pox
	#./pox.py openflow.of_01 --port=8001 my_controller 
else
	echo "Argument did not match !"
fi
