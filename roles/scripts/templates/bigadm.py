#!/usr/bigdata/Miniconda3/bin/python

import argparse
import logging
import os
import sys
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
import subprocess
import re
import time
import socket


class bigadm:
    def __init__(self):
        self.logger = logging.getLogger("bigadm")
        self.hive_metastore_port = 9083
        self.hiveserver2_port = 10000
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        self.env_bigdata_root_name = 'BIGDATA_ROOT'
        # self.parse_ansible_inventory()
        if not self.env_bigdata_root_name in os.environ:
            self.logger.error(
                "BIGDATA_ROOT environment variable not defined or loaded")
            sys.exit(-1)
        self.env_bigdata_root_value = os.environ.get(
            self.env_bigdata_root_name)
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        # Configure logging
        self.allowed_service = [
                'hdfs',
                'namenode',
                'datanode',
                'zkfc',
                'journalnode',
                'hive',
                'zookeeper',
                'kafka',
                'spark'
                ]

    def run_command_over_ssh(self, cmd):
        #print(cmd)
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            stdout, stderr = process.communicate(timeout=5)
            #self.logger.info(stdout.strip())
            #self.logger.info(stderr.strip())
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("The subprocess timed out.")
            return None
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"Command failed with return code {e.returncode}: {e.output}")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            return None

    def parse_ansible_inventory(self, host_group):
        path = "/usr/bigdata/ansibleProjects/files/hosts"
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=path)
        try:
            hosts = inventory.get_groups_dict()[host_group]
            return hosts
        except:
            return None

    def read_pid_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                pid = int(file.read().strip())
                return pid
        except:
            self.logger.error("pid file not found")
            return None
    '''
    def is_check_pid_running(self,pid):
        try:
            os.kill(pid,0)
        except OSError:
            return False
        else:
            return True
    '''

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="adoop cluster managment script")
        parser.add_argument('--start', help='for starting service')
        parser.add_argument('--stop', help='for starting service')
        parser.add_argument('--stopAll', help='for starting service')
        parser.add_argument('--startAll', help='for starting service')
        parser.add_argument('--statusAll', help='for starting service')
        parser.add_argument('--status', help='for starting service')
        parser.add_argument('--type', help='if type=service specified it will only start on same server')
        return parser.parse_args()

    def check_string_pattern(self, string, keyword):
        if string is None:
            return False
        else:
            match = re.search(keyword, string)
            if match:
                return True
            else:
                return False
            
    def check_process_of_pid_over_ssh(self,pid_file, process_name,host=None, PidFile=True):
        if PidFile:
            if host is None:
                cmd = ['cat', pid_file]
            else:
                cmd = ['ssh', host, ' ', 'cat', pid_file]
            pid = self.run_command_over_ssh(cmd)
        else:
            pid = pid_file

        if pid is not None:
            if host is None:
                cmd = ['ps', '-p', pid]
            else:
                cmd = ['ssh', host, 'ps', '-p', pid]
            res = self.run_command_over_ssh(cmd)
            if res is not None:
                is_running = self.check_string_pattern(res, process_name)
                return is_running
            else:
                return None
        else:
            return None

    def get_pid_from_port_overssh(self, host, port):
        cmd = ['ssh', host, '/usr/sbin/lsof', '-t',
            '-i:{}'.format(port), '-sTCP:LISTEN']
        pid = self.run_command_over_ssh(cmd)
        if isinstance(pid, str):
            return pid.strip()
        else:
            return None

    def hive_process_pid_writting(self, host, port, pid_file, process_name):
        is_pid_launched = False
        start_time = time.time()
        while time.time() - start_time < 40:
            time.sleep(1)
            self.logger.info("waiting for {} Process to launch ({})s".format(
                process_name, int(time.time() - start_time)))
            pid = self.get_pid_from_port_overssh(host, port)
            if pid is not None:
                is_pid_launched = self.check_process_of_pid_over_ssh(
                    host, pid, 'java', PidFile=False)
                if is_pid_launched:
                    break
            '''
            cmd = ['ssh',host,'/usr/sbin/lsof','-t','-i:{}'.format(port)]
            out=self.run_command_over_ssh(cmd)
            if isinstance(out, str) :
                is_pid_launched=self.check_process_of_pid_over_ssh(host,out.strip(),'java',PidFile=False)
                if is_pid_launched:
                    break
            '''
        if is_pid_launched:
            cmd = ['ssh', host, 'echo', pid, '>', pid_file]
            self.run_command_over_ssh(cmd)
            self.logger.info("{} server running...".format(process_name))
        else:
            self.logger.warning(
                "{} is not started or taking long time to start".format(process_name))

    def hdfs_service(self, action, service=None,script_type=None):
        nm_pid_file = "{}/pids/hadoop-hadoop-namenode.pid".format(
            self.env_bigdata_root_value)
        dn_pid_file = "{}/pids/hadoop-hadoop-datanode.pid".format(
            self.env_bigdata_root_value)
        jn_pid_file = "{}/pids/hadoop-hadoop-journalnode.pid".format(
            self.env_bigdata_root_value)
        zkfc_pid_file = "{}/pids/hadoop-hadoop-zkfc.pid".format(
            self.env_bigdata_root_value)
        env_hadoop_home = os.environ.get('HADOOP_HOME')
        hostname = socket.getfqdn()

        hadoop_daemon = "{}/sbin/hadoop-daemon.sh".format(env_hadoop_home)
        # hdfs --daemon start namenode

        nm_hosts = self.parse_ansible_inventory('nameNode')
        dn_hosts = self.parse_ansible_inventory('dataNode')
        jn_hosts = self.parse_ansible_inventory('journalNode')

        if action == 'status':
            #print("reached start")
            #print(script_type)
            if service == 'journalnode':
                for host in jn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            is_running = self.check_process_of_pid_over_ssh(jn_pid_file, 'java')
                            if is_running:
                                self.logger.info("JournalNode on {} Running...".format(host))
                            else:
                                self.logger.info("JournalNode on {} is not Running...".format(host))                            
                            break
                    if script_type is None:
                        is_running = self.check_process_of_pid_over_ssh(jn_pid_file, 'java',host=host)
                        if is_running:
                            self.logger.info("JournalNode on {} Running...".format(host))
                        else:
                            self.logger.info("JournalNode {} is not Running...".format(host))
                            
            elif service == 'namenode':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            is_running = self.check_process_of_pid_over_ssh(nm_pid_file, 'java')
                            if is_running:
                                self.logger.info("NameNode on {} Running...".format(host))
                            else:
                                self.logger.info("NameNode on {} is not Running...".format(host))                            
                            break
                    if script_type is None:
                        is_running = self.check_process_of_pid_over_ssh(nm_pid_file, 'java',host=host)
                        if is_running:
                            self.logger.info("NameNode on {} Running...".format(host))
                        else:
                            self.logger.info("NameNode on: {} is not Running...".format(host))                      
            elif service == 'datanode':
                for host in dn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            is_running = self.check_process_of_pid_over_ssh(dn_pid_file, 'java')
                            if is_running:
                                self.logger.info("DataNode on {} Running...".format(host))
                            else:
                                self.logger.info("DataNode on {} is not Running...".format(host))                            
                            break
                    if script_type is None:
                        is_running = self.check_process_of_pid_over_ssh(dn_pid_file, 'java',host=host)
                        if is_running:
                            self.logger.info("DataNode on {} Running...".format(host))
                        else:
                            self.logger.info("DataNode on: {} is not Running...".format(host))  
            elif service == 'zkfc':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            is_running = self.check_process_of_pid_over_ssh(zkfc_pid_file, 'java')
                            if is_running:
                                self.logger.info("ZKFailoverController on {} Running...".format(host))
                            else:
                                self.logger.info("ZKFailoverController on {} is not Running...".format(host))                            
                            break
                    if script_type is None:
                        is_running = self.check_process_of_pid_over_ssh(zkfc_pid_file, 'java',host=host)
                        if is_running:
                            self.logger.info("ZKFailoverController on {} Running...".format(host))
                        else:
                            self.logger.info("ZKFailoverController on: {} is not Running...".format(host))  
                                                 
        elif action == 'start':
            #print("reached start")
            #print(script_type)
            if service == 'namenode':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Starting Namenode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','namenode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Starting Namenode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','namenode'] 
                        out=self.run_command_over_ssh(cmd)    
            elif service == 'zkfc':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname:                        
                            self.logger.info("Starting ZKFailoverController on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','zkfc']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Starting ZKFailoverController on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','zkfc'] 
                        out=self.run_command_over_ssh(cmd)                        
            elif service == 'datanode':
                for host in dn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Starting Datanode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','datanode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Starting Datanode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','datanode'] 
                        out=self.run_command_over_ssh(cmd)   
            elif service == 'journalnode':
                for host in jn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Starting journalnode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','journalnode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Starting journalnode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','journalnode'] 
                        out=self.run_command_over_ssh(cmd) 
            else:
                self.logger.error("Invalid Servie: {} selected...".format(service))
        elif action == 'stop':
            #print("reached stop")
            #print(script_type)
            if service == 'namenode':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Stopping Namenode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','namenode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Stopping Namenode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','namenode'] 
                        out=self.run_command_over_ssh(cmd)    
            elif service == 'zkfc':
                for host in nm_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname:                        
                            self.logger.info("Stopping ZKFailoverController on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','zkfc']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Stopping ZKFailoverController on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','zkfc'] 
                        out=self.run_command_over_ssh(cmd)                        
            elif service == 'datanode':
                for host in dn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Stopping Datanode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','datanode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Stopping Datanode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','datanode'] 
                        out=self.run_command_over_ssh(cmd)   
            elif service == 'journalnode':
                for host in jn_hosts:
                    if script_type is not None and script_type.lower() == 'service':
                        if host == hostname: 
                            self.logger.info("Stopping journalnode on node: {}".format(host))
                            cmd = [hadoop_daemon,'start','journalnode']
                            out=self.run_command_over_ssh(cmd)
                            break
                    if script_type is None:
                        self.logger.info("Stopping journalnode on node: {}".format(host))
                        cmd = ['ssh',host,hadoop_daemon,'start','journalnode'] 
                        out=self.run_command_over_ssh(cmd)  
            else:
                self.logger.error("Invalid Servie: {} selected...".format(service))



    def zookeeper_service(self,action,script_type=None):
        hostname = socket.getfqdn()
        env_zk_home = os.environ.get('ZOOKEEPER_HOME')
        zk_bin_exe = "{env_zk_home}/bin/zkServer.sh".format(env_zk_home=env_zk_home)
        zk_pid_file = "{}/Envs/zookeeper/dataDir/zookeeper_server.pid".format(self.env_bigdata_root_value)
        zk_hosts = self.parse_ansible_inventory('zookeeperNode')
        if action == 'status':
            for host in zk_hosts:
                if script_type is not None and script_type.lower() == 'service':
                    if host == hostname:
                        is_running = self.check_process_of_pid_over_ssh(zk_pid_file,'java')                    
                        if is_running:
                            self.logger.info("zookeeper Node {} Running...".format(host))
                        else:
                            self.logger.info("zookeeper Node {} is not Running...".format(host))
                        break
                        
                if script_type is None:
                    is_running = self.check_process_of_pid_over_ssh(zk_pid_file,'java',host=host)
                    if is_running:
                        self.logger.info("zookeeper Node {} Running...".format(host))
                    else:
                        self.logger.info("zookeeper Node {} is not Running...".format(host))
                        
        elif action == 'start':
            zk_hosts = self.parse_ansible_inventory('zookeeperNode')
            for host in zk_hosts:
                if script_type is not None and script_type.lower() == 'service':
                    if host == hostname:                        
                        self.logger.info("Starting zookeeper on Node: {}".format(host))
                        cmd = [zk_bin_exe,'start'] 
                        out=self.run_command_over_ssh(cmd)
                        break
                if script_type is None:
                    self.logger.info("Starting zookeeper on Node: {}".format(host))
                    cmd = ['ssh',host,zk_bin_exe,'start'] 
                    out=self.run_command_over_ssh(cmd)
                    

        elif action == 'stop':
            zk_hosts = self.parse_ansible_inventory('zookeeperNode')
            for host in zk_hosts:
                if script_type is not None and script_type.lower() == 'service':
                    if host == hostname:                        
                        self.logger.info("Stopping zookeeper on Node: {}".format(host))
                        cmd = [zk_bin_exe,'stop'] 
                        out=self.run_command_over_ssh(cmd)
                        break
                if script_type is None:
                    self.logger.info("Stopping zookeeper on Node: {}".format(host))
                    cmd = ['ssh',host,zk_bin_exe,'stop'] 
                    out=self.run_command_over_ssh(cmd)


    def hive_service(self,action,script_type=None):
        hostname = socket.getfqdn()
        env_hive_home = os.environ.get('HIVE_HOME')
        hm_log_file = "{}/logs/hivemeta_nohup.log".format(self.env_bigdata_root_value)
        hs2_log_file = "{}/logs/hiveserver_nohup.log".format(self.env_bigdata_root_value)
        hive_log_path = "{}/logs".format(self.env_bigdata_root_value)
        hive_cmd="{}/bin/hive".format(env_hive_home)
        hs2_pid_file = "{}/pids/hive_server.pid".format(self.env_bigdata_root_value)
        hm_pid_file = "{}/pids/hive_metastore.pid".format(self.env_bigdata_root_value)
        hs2_hosts = self.parse_ansible_inventory('hiveserver2Node')
        hm_hosts = self.parse_ansible_inventory('hivemetastoreNode')
        if action == 'status':
            for host in hs2_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,hs2_pid_file,'java')
                if is_running:
                    self.logger.info("hiveserver2 Node {} Running...".format(host))
                else:
                    self.logger.info("hiveserver2 Node {} is not Running...".format(host))
            for host in hm_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,hm_pid_file,'java')
                if is_running:
                    self.logger.info("hivemetastore Node {} Running...".format(host))
                else:
                    self.logger.info("hivemetastore Node {} is not Running...".format(host))
        elif action == 'start':
            for host in hm_hosts:
                #cmd = ['ssh',host,'nohup',hive_cmd,'--service','metastore','&']
                cmd = """ssh hadoop@{} "source ~/.bash_profile;nohup {} --service metastore \
                --hiveconf hive.log.dir={} >{} 2>&1 &"
                """.format(host,hive_cmd,hive_log_path,hm_log_file)
                self.logger.info("Starting hivemetastore on node: {}".format(host))
                self.logger.info(cmd)
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                self.hive_process_pid_writting(host,self.hive_metastore_port,hm_pid_file,"hivemetastore")

            hivems_ha_hosts ="thrift://"+",".join(str(item)+":"+str(self.hive_metastore_port) for item in hm_hosts)

            for host in hs2_hosts:
                #cmd = ['ssh',host,'nohup',hive_cmd,'--service','metastore','&']
                cmd = """ssh hadoop@{} "source ~/.bash_profile;nohup {} --service hiveserver2 \
                --hiveconf hive.log.dir={} --hiveconf hive.metastore.uris={} >{} 2>&1 &"
                """.format(host,hive_cmd,hive_log_path,hivems_ha_hosts,hs2_log_file)
                self.logger.info("Starting hiveserver2 on node: {}".format(host))
                self.logger.info(cmd)
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                self.hive_process_pid_writting(host,self.hiveserver2_port,hs2_pid_file,"hiveserver2")

        elif action == 'stop':
            for host in hm_hosts:
                pid=self.get_pid_from_port_overssh(host,self.hive_metastore_port)
                #print(pid)
                is_running = self.check_process_of_pid_over_ssh(host,pid,'java',PidFile=False)
                #print(is_running)
                if is_running:
                    cmd = ['ssh',host,'kill','-9',pid]
                    out=self.run_command_over_ssh(cmd)
                    pid=self.get_pid_from_port_overssh(host,self.hive_metastore_port)
                    is_running = self.check_process_of_pid_over_ssh(host,pid,'java',PidFile=False)
                    if is_running:
                        self.logger.warning("some issue with stopping hivemeastore on Node {} !!!".format(host))
                    else:
                        self.logger.info("hivemeastore on Node {} stopped".format(host))
                else:
                    self.logger.info("hivemeastore on Node {} already stopped".format(host))

            for host in hs2_hosts:
                pid=self.get_pid_from_port_overssh(host,self.hiveserver2_port)
                is_running = self.check_process_of_pid_over_ssh(host,pid,'java',PidFile=False)
                #print(pid)
                #print(is_running)
                if is_running:
                    cmd = ['ssh',host,'kill','-9',pid]
                    out=self.run_command_over_ssh(cmd)
                    pid=self.get_pid_from_port_overssh(host,self.hiveserver2_port)
                    is_running = self.check_process_of_pid_over_ssh(host,pid,'java',PidFile=False)
                    if is_running:
                        self.logger.warning("some issue with stopping hiveserver2 on Node {} !!!".format(host))
                    else:
                        self.logger.info("hiveserver2 on Node {} stopped".format(host))
                else:
                    self.logger.info("hiveserver2 on Node {} already stopped".format(host))





    def spark_service(self,action,script_type=None):
        hostname = socket.getfqdn()
        env_spark_home = os.environ.get('SPARK_HOME')
        sparkmaster_start_cmd = "{}/sbin/start-master.sh".format(env_spark_home)
        sparkmaster_stop_cmd = "{}/sbin/stop-master.sh".format(env_spark_home)
        sparkworker_start_cmd = "{}/sbin/start-slaves.sh".format(env_spark_home)
        sparkworker_stop_cmd = "{}/sbin/stop-slaves.sh".format(env_spark_home)
        sm_hosts = self.parse_ansible_inventory('sparkMaster')
        sw_hosts = self.parse_ansible_inventory('sparkWorker')
        if action == 'status':
            sm_pid_file = "{}/pids/spark-hadoop-org.apache.spark.deploy.master.Master-1.pid".format(self.env_bigdata_root_value)
            sw_pid_file = "{}/pids/spark-hadoop-org.apache.spark.deploy.worker.Worker-1.pid".format(self.env_bigdata_root_value)

            for host in sm_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,sm_pid_file,'java')
                if is_running:
                    self.logger.info("Spark master Node {} Running...".format(host))
                else:
                    self.logger.info("Spark master Node {} is not Running...".format(host))
            for host in sw_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,sw_pid_file,'java')
                if is_running:
                    self.logger.info("Spark worker Node {} Running...".format(host))
                else:
                    self.logger.info("Spark worker Node {} is not Running...".format(host))
        if action == 'start':
            spark_master_ha_hosts ="spark://"+",".join(str(item)+":7077" for item in sm_hosts)
            for host in sm_hosts:
                self.logger.info("Starting Spark master node on {}".format(host))
                cmd = ['ssh',host,sparkmaster_start_cmd]
                out=self.run_command_over_ssh(cmd)
                self.logger.info("Starting Spark worker node on {}".format(host))
                cmd = ['ssh',host,sparkworker_start_cmd,spark_master_ha_hosts]
                out=self.run_command_over_ssh(cmd)

        if action == 'stop':
            spark_master_ha_hosts ="spark://"+",".join(str(item)+":7077" for item in sm_hosts)
            for host in sm_hosts:
                #self.logger.info("Stopping Spark workers node on {}".format(host))
                #cmd = ['ssh',host,sparkworker_stop_cmd,spark_master_ha_hosts]
                self.logger.info("Stopping Spark master node on {}".format(host))
                cmd = ['ssh',host,sparkmaster_stop_cmd]
                out=self.run_command_over_ssh(cmd)

            spark_master_ha_hosts ="spark://"+",".join(str(item)+":7077" for item in sm_hosts)
            for host in sw_hosts:
                self.logger.info("Stopping Spark worker node on {}".format(host))
                cmd = ['ssh',host,sparkworker_stop_cmd,spark_master_ha_hosts]
                out=self.run_command_over_ssh(cmd)


    def main(self,args):
        if args.start:
            if args.start.lower() == 'all':
                self.start_service(args,all_service=True)
            else:
                self.start_service(args)

        elif args.stop:
            if args.stop.lower() == 'all':
                self.stop_service(args,all_service=True)
            else:
                self.stop_service(args)
        elif args.status:
            if args.status.lower() == 'all':
                self.status_service(args,all_service=True)
            else:
                self.status_service(args)

    def start_service(self,args,all_service=False):
        if all_service:
            self.logger.info("Starting all service")
            self.zookeeper_service('start')
            self.hdfs_service('start','journalnode',script_type=args.type)
            self.hdfs_service('start','namenode',script_type=args.type)
            self.hdfs_service('start','zkfc',script_type=args.type)
            self.hdfs_service('start','datanode',script_type=args.type)
            self.hive_service('start')
            self.spark_service('start')
        else:
            if args.start.lower() in self.allowed_service:
                self.logger.info("Checking {} service start".format(args.start))
                if args.start.lower() == 'hdfs':
                    self.hdfs_service('start','journalnode',script_type=args.type)
                    self.hdfs_service('start','namenode',script_type=args.type)
                    self.hdfs_service('start','zkfc',script_type=args.type)
                    self.hdfs_service('start','datanode',script_type=args.type)
                if args.start.lower() == 'namenode':
                    self.hdfs_service('start','namenode',script_type=args.type)
                if args.start.lower() == 'zkfc':
                    self.hdfs_service('start','zkfc',script_type=args.type)
                if args.start.lower() == 'datanode':
                    self.hdfs_service('start','datanode',script_type=args.type)
                if args.start.lower() == 'journalnode':
                    self.hdfs_service('start','journalnode',script_type=args.type)
                elif args.start.lower() == 'zookeeper':
                    self.zookeeper_service('start',script_type=args.type)
                elif args.start.lower() == 'hive':
                    self.hive_service('start')
                elif args.start.lower() == 'spark':
                    self.spark_service('start')

            else:
                self.logger.error("{} service doesn't exist".format(args.start))


    def stop_service(self,args,all_service=False):
        if all_service:
            self.logger.info("Stopping all service")
            self.hdfs_service('stop','datanode',script_type=args.type)
            self.hdfs_service('stop','namenode',script_type=args.type)
            self.hdfs_service('stop','zkfc',script_type=args.type)
            self.hdfs_service('stop','journalnode',script_type=args.type)
            self.zookeeper_service('stop')
            self.hive_service('stop')
            self.spark_service('stop')
        else:
            if args.stop.lower() in self.allowed_service:
                self.logger.info("Checking {} service stop".format(args.stop))
                if args.stop.lower() == 'hdfs':
                    self.hdfs_service('stop','datanode',script_type=args.type)
                    self.hdfs_service('stop','namenode',script_type=args.type)
                    self.hdfs_service('stop','zkfc',script_type=args.type)
                    self.hdfs_service('stop','journalnode',script_type=args.type)
                if args.stop.lower() == 'namenode':
                    self.hdfs_service('stop','namenode',script_type=args.type)
                if args.stop.lower() == 'zkfc':
                    self.hdfs_service('stop','zkfc',script_type=args.type)
                if args.stop.lower() == 'datanode':
                    self.hdfs_service('stop','datanode',script_type=args.type)
                if args.stop.lower() == 'journalnode':
                    self.hdfs_service('stop','journalnode',script_type=args.type)
                elif args.stop.lower() == 'zookeeper':
                    self.zookeeper_service('stop',script_type=args.type)
                elif args.stop.lower() == 'hive':
                    self.hive_service('stop')
                elif args.stop.lower() == 'spark':
                    self.spark_service('stop')

            else:
                self.logger.error("{} service doesn't exist".format(args.stop))

    def status_service(self,args,all_service=False):

        #print(args)
        if all_service:
            self.logger.info("Checking all service status")
            self.hdfs_service('status',script_type=args.type)
            self.zookeeper_service('status')
            self.hive_service('status')
            self.spark_service('status')
        else:
            if args.status.lower() in self.allowed_service:
                self.logger.info("Checking {} service status".format(args.status))
                if args.status.lower() == 'hdfs':
                    self.hdfs_service('status','hdfs',script_type=args.type)
                if args.status.lower() == 'namenode':
                    self.hdfs_service('status','namenode',script_type=args.type)
                if args.status.lower() == 'zkfc':
                    self.hdfs_service('status','zkfc',script_type=args.type)
                if args.status.lower() == 'datanode':
                    self.hdfs_service('status','datanode',script_type=args.type)
                if args.status.lower() == 'journalnode':
                    self.hdfs_service('status','journalnode',script_type=args.type)                    
                elif args.status.lower() == 'zookeeper':
                    self.zookeeper_service('status',script_type=args.type)
                elif args.status.lower() == 'hive':
                    self.hive_service('status')
                elif args.status.lower() == 'spark':
                    self.spark_service('status')

            else:
                self.logger.error("{} service doesn't exist".format(args.status))



if __name__ == '__main__':
    obj = bigadm()
    args = obj.parse_arguments()
    obj.main(args)
