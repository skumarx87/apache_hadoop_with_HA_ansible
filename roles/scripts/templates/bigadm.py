import argparse
import logging
import os
import sys
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
import subprocess
import re

class bigadm:
    def __init__(self):
        self.logger = logging.getLogger("bigadm")
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
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=5)
            #self.logger.info(stdout.strip())
            if process.returncode == 0:
                return stdout
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

    def is_check_pid_running(self,pid):
        try:
            os.kill(pid,0)
        except OSError:
            return False
        else:
            return True

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
    
    def check_process_of_pid_over_ssh(self,host,pid_file,process_name):
        cmd = ['ssh',host,' ','cat',pid_file]
        pid=self.run_command_over_ssh(cmd)
        if pid is not None:
            cmd = ['ssh',host,'ps','-p',pid]
            res=self.run_command_over_ssh(cmd)
            is_running = self.check_string_pattern(res,process_name)
            return is_running




    def hdfs_service(self,action):
        if action == 'status':
            nm_pid_file = "{}/pids/hadoop-hadoop-namenode.pid".format(self.env_bigdata_root_value)
            dn_pid_file = "{}/pids/hadoop-hadoop-datanode.pid".format(self.env_bigdata_root_value)
            jn_pid_file = "{}/pids/hadoop-hadoop-journalnode.pid".format(self.env_bigdata_root_value)
            nm_hosts = self.parse_ansible_inventory('nameNode')
            dn_hosts = self.parse_ansible_inventory('dataNode')
            jn_hosts = self.parse_ansible_inventory('journalNode')
            #print(nm_hosts)
            #print(dn_hosts)
            #print(jn_hosts)

            #nn_pid = self.read_pid_from_file(nn_pid_file)
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
                    
                
            '''
                cmd = ['ssh',host,' ','cat',jn_pid_file]
                pid=self.run_command_over_ssh(cmd)
                if pid is not None:
                    cmd = ['ssh',host,'ps','-p',pid]
                    self.run_command_over_ssh(cmd)
            '''



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
        self.logger.info('Starting service')
        if all_service:
            self.logger.info("Staring all services")
        else:
            if args.start.lower() in self.allowed_service:
                self.logger.info("Staring hdfs services")
                self.hdfs_service('start')
            else:
                self.logger.error("{} service doesn't exist".format(args.start))

    def stop_service(self,args,all_service=False):
        self.logger.info('Stoping service')
        if all_service:
            self.logger.info("Stoping all services")
        else:
            if args.stop.lower() in self.allowed_service:
                self.logger.info("Stoping hdfs services")
                self.hdfs_service('stop')
            else:
                self.logger.error("{} service doesn't exist".format(args.start))
    

    def status_service(self,args,all_service=False):
        self.logger.info('Starting service')
        if all_service:
            self.logger.info("Staring all services")
        else:
            if args.status.lower() in self.allowed_service:
                self.logger.info("Staring hdfs services")
                self.hdfs_service('status')
            else:
                self.logger.error("{} service doesn't exist".format(args.start))
    


if __name__ == '__main__':
    obj = bigadm()
    args = obj.parse_arguments()
    obj.main(args)

