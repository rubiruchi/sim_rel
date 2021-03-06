#!/bin/bash
#following tutorial:http://manual.futuregrid.org/os-virtualbox.html
echo $1

MINVMIDIR="/home/mehmet/Desktop/mininet-ovf"
MINVMINAME="mininet-vm-disk1.vmdk"

OPSVMIDIR="/home/mehmet/Dropbox/sim_rel/fg_rel"
OPSVMINAME="mininet-ops-vm.img"

#Convert your virtual box image to raw format
if [ $1  = 'trf' ]; then
  VBoxManage clonehd $MINVMIDIR/$MINVMINAME $OPSVMIDIR/$OPSVMINAME --format raw
elif [ $1  = 'scptlm' ]; then
  scp $OPSVMINAME mfa51@spring.rutgers.edu:~/Desktop
elif [ $1  = 'scptr' ]; then
  scp $OPSVMINAME mfa51@india.futuregrid.org:~/
elif [ $1  = 'bri' ]; then
  kvm -hda $OPSVMINAME -m 1024
else
	echo "Argument did not match !"
fi


