# apache_hadoop_with_HA

## Root privilege setup
```
useradd hadoop
password hadoop

yum install epel-release
yum --enablerepo=epel -y install sshpass
yum -y install git-core net-tools sshpass wget
mkdir -p  /usr/bigdata /usr/bigdata/softwares
chown -R hadoop:hadoop /usr/bigdata
```
## Install and configure Ansible for managing all nodes from Master
```
su - hadoop
cd /usr/bigdata/softwares
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /usr/bigdata/Miniconda3
export PATH=/usr/bigdata/Miniconda3/bin:$PATH
/usr/bigdata/Miniconda3/bin/conda create -n ansible -y
source activate ansible
pip install ansible

```
## Setup the SSH Key authentication for non-root account within server
* ssh-keygen -t rsa -q -f "$HOME/.ssh/id_rsa" -N ""
* chmod 0700 $HOME/.ssh
* ssh-copy-id -i $HOME/.ssh/id_rsa.pub localhost
## Install OpenJDK Java  and git using below command
* su - root
* yum install -y java-1.8.0-openjdk.x86_64 java-1.8.0-openjdk-devel
### Create ansbile project to run ad-hoc commands all the hosts
```
mkdir -p /usr/bigdata/ansibleProjects /usr/bigdata/ansibleProjects/{files,playbooks}
cd /usr/bigdata/ansibleProjects/files

## create hosts file and update the entries like below hostnames
(ansible) [hadoop@hmn1 files]$ cat hosts
###################
[default]
laksha.home.com

[buildserver]
laksha.home.com

[nameNode]
laksha.home.com

[dataNode]
laksha.home.com
tanush.home.com

[hiveNode]
laksha.home.com
########################
create ansible.cfg and add below lines

(ansible) [hadoop@hmn1 files]$ cat ansible.cfg
[defaults]
inventory         = hosts
host_key_checking = False
###############################
```
## Update Bash_profile variable
```
vi ~/.bash_profile
######## set the variable 
export ANSIBLE_CONFIG=/usr/bigdata/ansibleProjects/files
##command to test the connection
ansible all -u root --ask-pass -m ping
## command to install yum packages
ansible all -u root --ask-pass -a "yum -y install git-core net-tools sshpass wget"
```
# Apache Hadoop Installation
## git code checkout
```
* git clone https://github.com/skumarx87/apache_hadoop_with_HA_ansible.git
* cd apache_hadoop_with_HA_ansible
* update the vars/bigdata_site_xml_properties.yml
   BIGDATA_DIR: "/usr/bigdata"
   NAMENODE_HOSTNAME: "laksha.tanu.com"
   DFS_REPLICATION_LEVEL: "3"
   FS_DEFAULT_NAME: "hdfs://laksha.tanu.com:9000"
   SPARK_LOCAL_DIR: "/tmp/"
   SPARK_SECRET: "test123"
* ./hadoop_install.sh
```


