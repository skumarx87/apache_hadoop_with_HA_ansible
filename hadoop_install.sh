#!/bin/bash


function banner {
	msg=$1
	echo "---------------------------------------------" 
	echo "$msg				   	   " 
	echo "---------------------------------------------" 
}

function Error_msg {
	echo "Error: $1 !!!"
	exit -1
}

function check_Prequesties {

	banner "Checking wokers file"
	if [ ! -f "roles/hadoop/templates/workers" ]
	then
	   Error_msg "Workers file Not exits"
	fi 

	banner "Checking ansible host file"
	if [ ! -f "/usr/bigdata/ansibleProjects/files/hosts" ]
	then
	   Error_msg "ansible hosts (inventry) file missing"
	fi

        banner "Checking ansible host file"
        if [ ! -f "/usr/bigdata/ansibleProjects/files/ansible.cfg" ]
        then
           Error_msg "ansible ansible.cfg file missing"
        fi

	
}

function Install_Hadoop {
	export ANSIBLE_CONFIG=/usr/bigdata/ansibleProjects/files

	banner "Installing Hadoop cluster"
	export PATH=/usr/bigdata/Miniconda3/bin:$PATH
	source activate ansible


	echo "Downloading binaries"
	ansible-playbook  downloads_binaries.yml

	echo "Installing Hadoop"
	ansible-playbook  install_hadoop.yml 

	echo "Installing Hive"
	ansible-playbook  install_hive.yml 

	echo "Installing Scripts"
	ansible-playbook  install_scripts.yml 

	echo "Installing Tez"
	ansible-playbook  install_tez.yml 

	echo "Installing Derby"
	ansible-playbook  install_derby.yml 

}
check_Prequesties
Install_Hadoop
