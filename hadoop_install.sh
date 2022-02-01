#!/bin/bash

#ansible-playbook  downloads_binaries.yml
ansible-playbook  install_hadoop.yml 
ansible-playbook  install_hive.yml 
ansible-playbook  install_scripts.yml 
