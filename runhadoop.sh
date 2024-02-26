ssh dev-kmaster0.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/hadoop-3.2.0 
ssh dev-kmaster1.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/hadoop-3.2.0
ssh dev-kworker0.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/hadoop-3.2.0
ansible-playbook  ha_install_hadoop.yml
