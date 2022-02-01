mkdir -p  /usr/bigdata/softwares
mkdir -p /usr/bigdata/ansibleProjects/files
cd /usr/bigdata/softwares 
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /usr/bigdata/Miniconda3
export PATH=/usr/bigdata/Miniconda3/bin:$PATH
/usr/bigdata/Miniconda3/bin/conda create -n ansible -y
source activate ansible
pip install ansible

ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
ssh-copy-id -i ~/.ssh/id_rsa.pub localhost 
