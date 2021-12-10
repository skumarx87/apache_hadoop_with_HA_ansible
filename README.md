# apache_hadoop_with_HA
## Install and configure Ansible for managing all nodes from Master
```
mkdir -p  /user/bigdata
mkdir softwares
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
Miniconda3-latest-Linux-x86_64.sh
export PATH=$PATH:/user/bigdata/miniconda3/bin
conda create -n ansible
source activate ansible
pip install ansible
yum -y install git-core net-tools sshpass wget
```
### Create ansbile project to run ad-hoc commands all the hosts
```
mkdir -p /user/bigdata/ansibleProjects /user/bigdata/ansibleProjects/{files,playbooks}
cd /user/bigdata/ansibleProjects/sshpass/files

## create hosts file and include all the hostnames
(ansible) [hadoop@hmn1 files]$ cat hosts
hmn1.tanu.com
hmn2.tanu.com

create ansible.cfg and add below lines

(ansible) [hadoop@hmn1 files]$ cat ansible.cfg
[defaults]
inventory         = hosts
host_key_checking = False
###############################
##command to test the connection
ansible all -u root --ask-pass -m ping
## command to install yum packages
ansible all -u root --ask-pass -a "yum -y install git-core net-tools sshpass wget"
```


