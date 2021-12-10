# apache_hadoop_with_HA
## Install and configure Ansible for managing all nodes from Master
```
* mkdir -p  /user/bigdata
* mkdir softwares
* wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
* sh Miniconda3-latest-Linux-x86_64.sh
* export PATH=$PATH:/user/bigdata/miniconda3/bin
* conda create -n ansible
* source activate ansible
* pip install ansible
* yum -y install git-core net-tools sshpass wget
```
