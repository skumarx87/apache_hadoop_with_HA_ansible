import argparse
import logging
import os
import sys
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
import subprocess
import re
import time

class bigadm:
    def __init__(self):
        self.logger = logging.getLogger("bigadm")
        self.hive_metastore_port = 9083 
        self.hiveserver2_port = 10000
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        self.env_bigdata_root_name = 'BIGDATA_ROOT'
        #self.parse_ansible_inventory()
        if not self.env_bigdata_root_name in os.environ:
            self.logger.error("BIGDATA_ROOT environment variable not defined or loaded")
            sys.exit(-1)
        self.env_bigdata_root_value = os.environ.get(self.env_bigdata_root_name)
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')


        # Configure logging
        self.allowed_service = [
                'hdfs',
                'hive',
                'zookeeper',
                'kafka',
                'spark'
                ]
    def run_command_over_ssh(self,cmd):
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            stdout, stderr = process.communicate(timeout=5)
            #self.logger.info(stdout.strip())
            #self.logger.info(stderr.strip())
            if process.returncode == 0:
                return stdout.decode()
            else:
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("The subprocess timed out.")
            return None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with return code {e.returncode}: {e.output}")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            return None
            
    def parse_ansible_inventory(self,host_group):
        path = "/usr/bigdata/ansibleProjects/files/hosts"
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=path)
        try:
            hosts = inventory.get_groups_dict()[host_group]
            return hosts
        except:
            return None


    def read_pid_from_file(self,file_path):
        try:
            with open(file_path,'r') as file:
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
        parser = argparse.ArgumentParser(description="adoop cluster managment script")
        parser.add_argument('--start',help='for starting service')
        parser.add_argument('--stop',help='for starting service')
        parser.add_argument('--stopAll',help='for starting service')
        parser.add_argument('--startAll',help='for starting service')
        parser.add_argument('--statusAll',help='for starting service')
        parser.add_argument('--status',help='for starting service')
        return parser.parse_args()

    def check_string_pattern(self,string,keyword):
        if string is None:
            return False
        else:
            match=re.search(keyword,string)
            if match:
                return True
            else:
                return False
    
    def check_process_of_pid_over_ssh(self,host,pid_file,process_name,PidFile=True):
        if PidFile:
            cmd = ['ssh',host,' ','cat',pid_file]
            pid=self.run_command_over_ssh(cmd)
        else:
            pid = pid_file

        if pid is not None:
            cmd = ['ssh',host,'ps','-p',pid]
            res=self.run_command_over_ssh(cmd)
            if res is not None:
                is_running = self.check_string_pattern(res,process_name)
                return is_running
            else:
                return None
        else:
            return None

    def get_pid_from_port_overssh(self,host,port):
        cmd = ['ssh',host,'lsof','-t','-i:{}'.format(port),'-sTCP:LISTEN']
        pid=self.run_command_over_ssh(cmd)
        if isinstance(pid, str) :
            return pid.strip()
        else:
            return None

    def hive_process_pid_writting(self,host,port,pid_file,process_name):
        is_pid_launched = False
        start_time = time.time()
        while time.time() - start_time < 20:
            time.sleep(1)
            self.logger.info("waiting for {} Process to launch ({})s".format(process_name,int(time.time() - start_time)))
            pid=self.get_pid_from_port_overssh(host,port)
            if pid is not None:
                is_pid_launched=self.check_process_of_pid_over_ssh(host,pid,'java',PidFile=False)
                if is_pid_launched:
                    break
            '''
            cmd = ['ssh',host,'lsof','-t','-i:{}'.format(port)]
            out=self.run_command_over_ssh(cmd)
            if isinstance(out, str) :
                is_pid_launched=self.check_process_of_pid_over_ssh(host,out.strip(),'java',PidFile=False)
                if is_pid_launched:
                    break
            '''
        if is_pid_launched:
            cmd = ['ssh',host,'echo',pid,'>',pid_file]
            self.run_command_over_ssh(cmd)
            self.logger.info("{} server running...".format(process_name))
        else:
            self.logger.warning("{} is not started or taking long time to start".format(process_name))

    def hdfs_service(self,action):
        env_hadoop_home = os.environ.get('HADOOP_HOME')
        hadoop_daemon = "{}/sbin/hadoop-daemon.sh".format(env_hadoop_home)
        #hdfs --daemon start namenode

        nm_hosts = self.parse_ansible_inventory('nameNode')
        dn_hosts = self.parse_ansible_inventory('dataNode')
        jn_hosts = self.parse_ansible_inventory('journalNode')
        if action == 'status':
            nm_pid_file = "{}/pids/hadoop-hadoop-namenode.pid".format(self.env_bigdata_root_value)
            dn_pid_file = "{}/pids/hadoop-hadoop-datanode.pid".format(self.env_bigdata_root_value)
            jn_pid_file = "{}/pids/hadoop-hadoop-journalnode.pid".format(self.env_bigdata_root_value)
            for host in jn_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,jn_pid_file,'java')
                if is_running:
                    self.logger.info("Journal Node {} Running...".format(host))
                else:
                    self.logger.info("Journal Node {} is not Running...".format(host))

            for host in dn_hosts:
                is_running=self.check_process_of_pid_over_ssh(host,dn_pid_file,'java')
                if is_running:
                    self.logger.info("Data Node {} Running...".format(host))
                else:
                    self.logger.info("Data Node {} is not Running...".format(host))
            for host in nm_hosts:
                is_running=self.check_process_of_pid_over_ssh(host,nm_pid_file,'java')
                if is_running:
                    self.logger.info("Name Node {} Running...".format(host))
                else:
                    self.logger.info("Name Node {} is not Running...".format(host))
        elif action == 'start':
            for host in nm_hosts:
                cmd = ['ssh',host,hadoop_daemon,'start','namenode']
                self.logger.info("Starting Namenode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            for host in dn_hosts:
                cmd = ['ssh',host,hadoop_daemon,'start','datanode']
                self.logger.info("Starting datanode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            for host in jn_hosts:
                cmd = ['ssh',host,hadoop_daemon,'start','journalnode']
                self.logger.info("Starting journalnode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            self.hdfs_service('status')
        elif action == 'stop':
            for host in nm_hosts:
                cmd = ['ssh',host,hadoop_daemon,'stop','namenode']
                self.logger.info("Stopping Namenode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            for host in dn_hosts:
                cmd = ['ssh',host,hadoop_daemon,'stop','datanode']
                self.logger.info("Stopping datanode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            for host in jn_hosts:
                cmd = ['ssh',host,hadoop_daemon,'stop','journalnode']
                self.logger.info("Stopping journalnode on node: {}".format(host))
                out=self.run_command_over_ssh(cmd)
            self.hdfs_service('status')
                
                    
    def zookeeper_service(self,action):
        if action == 'status':
            zk_pid_file = "{}/Envs/zookeeper/dataDir/zookeeper_server.pid".format(self.env_bigdata_root_value)
            zk_hosts = self.parse_ansible_inventory('zookeeperNode')
            for host in zk_hosts:
                is_running = self.check_process_of_pid_over_ssh(host,zk_pid_file,'java')
                if is_running:
                    self.logger.info("zookeeper Node {} Running...".format(host))
                else:
                    self.logger.info("zookeeper Node {} is not Running...".format(host))

    def hive_service(self,action):
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





    def spark_service(self,action):
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

    '''
    def start_service(self,args,all_service=False):
        self.logger.info('Starting service')
        if all_service:
            self.logger.info("Staring all services")
        else:
            if args.start.lower() in self.allowed_service:
                if args.start.lower() == 'hdfs':
                    self.logger.info("Staring hdfs services")
                    self.hdfs_service('start')
                elif args.start.lower() == 'hive':
                    self.logger.info("Staring hive services")
                    self.hive_service('start')
                elif args.start.lower() == 'spark':
                    self.spark_service('start')
            else:
                self.logger.error("{} service doesn't exist".format(args.start))
    '''
    def start_service(self,args,all_service=False):
        if all_service:
            self.logger.info("Checking all service start")
            self.hdfs_service('start')
            self.zookeeper_service('start')
            self.hive_service('start')
            self.spark_service('start')
        else:
            if args.start.lower() in self.allowed_service:
                self.logger.info("Checking {} service start".format(args.start))
                if args.start.lower() == 'hdfs':
                    self.hdfs_service('start')
                elif args.start.lower() == 'zookeeper':
                    self.zookeeper_service('start')
                elif args.start.lower() == 'hive':
                    self.hive_service('start')
                elif args.start.lower() == 'spark':
                    self.spark_service('start')

            else:
                self.logger.error("{} service doesn't exist".format(args.start))


    def stop_service(self,args,all_service=False):
        if all_service:
            self.logger.info("Checking all service stop")
            self.hdfs_service('stop')
            self.zookeeper_service('stop')
            self.hive_service('stop')
            self.spark_service('stop')
        else:
            if args.stop.lower() in self.allowed_service:
                self.logger.info("Checking {} service stop".format(args.stop))
                if args.stop.lower() == 'hdfs':
                    self.hdfs_service('stop')
                elif args.stop.lower() == 'zookeeper':
                    self.zookeeper_service('stop')
                elif args.stop.lower() == 'hive':
                    self.hive_service('stop')
                elif args.stop.lower() == 'spark':
                    self.spark_service('stop')

            else:
                self.logger.error("{} service doesn't exist".format(args.stop))
    
    def status_service(self,args,all_service=False):
        if all_service:
            self.logger.info("Checking all service status")
            self.hdfs_service('status')
            self.zookeeper_service('status')
            self.hive_service('status')
            self.spark_service('status')
        else:
            if args.status.lower() in self.allowed_service:
                self.logger.info("Checking {} service status".format(args.status))
                if args.status.lower() == 'hdfs':
                    self.hdfs_service('status')
                elif args.status.lower() == 'zookeeper':
                    self.zookeeper_service('status')
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

