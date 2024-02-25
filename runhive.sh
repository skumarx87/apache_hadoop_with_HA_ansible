ssh dev-kmaster0.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/apache-hive-2.3.5-bin
ssh dev-kmaster1.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/apache-hive-2.3.5-bin
ssh dev-kworker0.tanu.com rm -rf /usr/bigdata/releases/bigdata-3.0.0/apache-hive-2.3.5-bin
ansible-playbook ha_install_hivemeta.yml
