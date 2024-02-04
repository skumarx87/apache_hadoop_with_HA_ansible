#!/bin/bash

# Load hadoop variables

. $(dirname $0)/bigdata-user-profile.sh

fqdn_hostname=$(hostname -f)
hdfs_port=9000
hivesrv_port=10000
hivems_port=9083
sparkms_port=7077
yarn_port=8032
zookeeper_port=2181
kafka_broker_port=9092

bigdata_pids_dir=/usr/bigdata/pids
bigdata_log_dir=/usr/bigdata/logs
bigdata_log_file=$bigdata_log_dir/bigdata.log
hive_max_heap="-Xmx4g"

ant_file=apache-ant-1.9.16
ant_url="https://archive.apache.org/dist/ant/binaries/$ant_file-bin.tar.gz"

function check_command_status {
	return_code=$1
	message=$2
	if [ $return_code != 0 ]
	then
		log "ERROR $message "
		exit -1
	fi
}
function log {

    echo -e "$1"

}

function start_kafka_broker {

    log "START KAFKA BROKER"
    LOG_DIR=$bigdata_log_dir nohup $KAFKA_HOME/bin/kafka-server-start.sh  \
                $KAFKA_HOME/config/server.properties \
                > $bigdata_log_dir/kafkar_broker_nohup.log 2>&1 &

        for i in `seq 1 10`;
                do
                sleep 3
                pid=$(discover_process_by_port $kafka_broker_port)
                if [ "$pid" != '' ]; then
                        pid_file=$bigdata_pids_dir/kafka_broker_port.pid
                        echo "$pid" > $pid_file
                        log "Kafka Broker started, pid $pid written to $pid_file"
			status_line 'Kafka Broker' $kafka_broker_port
                        break
                fi
        done


}

function stop_kafka_broker {
	LOG_DIR=$bigdata_log_dir $KAFKA_HOME/bin/kafka-server-stop.sh
	sleep 3
	status_line 'Kafka Broker' $kafka_broker_port
}

function start_zookeeper {
	$ZOOKEEPER_HOME/bin/zkServer.sh start
}
function stop_zookeeper {
        $ZOOKEEPER_HOME/bin/zkServer.sh stop
}


function discover_process_by_port {

    port=$1
    pid=$(lsof  -i :$port |grep LISTEN|awk '{print $2}')
    echo "$pid"

}



function check_user_profile {
	if [ "$HADOOP_HOME" == '' ] || [ "$SPARK_HOME" == '' ]; then
		log "Please set environment variable [$1]"
		exit -1
	fi

} 

function start_hdfs {
    if [ "$BIGDATA_FILE_SYSTEM" == 'hdfs' ]; then
        log "START HDFS"
        $HADOOP_HOME/sbin/start-dfs.sh
    fi

}

function stop_hdfs {

    if [ "$BIGDATA_FILE_SYSTEM" == 'hdfs' ]; then
        log "STOP HDFS"
        $HADOOP_HOME/sbin/stop-dfs.sh
    fi

}

function stop_spark {

    log "STOP SPARK CLUSTER"
    $SPARK_HOME/sbin/stop-slaves.sh
    $SPARK_HOME/sbin/stop-master.sh

}


function start_hive_server {

    log "START HIVE SERVER"
    nohup $HIVE_HOME/bin/hive --service hiveserver2 \
                --hiveconf hive.metastore.uris="thrift://$fqdn_hostname:$hivems_port" \
                --hiveconf hive.server2.thrift.port=$hivesrv_port \
                --hiveconf hive.log.dir=$bigdata_log_dir \
                > $bigdata_log_dir/hiveserver_nohup.log 2>&1 &
	
	for i in `seq 1 10`;
		do
		sleep 3
		pid=$(discover_process_by_port $hivesrv_port)
		if [ "$pid" != '' ]; then
		 	pid_file=$bigdata_pids_dir/hive_server.pid
			echo "$pid" > $pid_file
			log "Hive Server started, pid $pid written to $pid_file"
			break
		fi
	done	


}

function start_hive_metastore {

    log "START HIVE METASERVER"
    nohup $HIVE_HOME/bin/hive --service metastore \
                --hiveconf hive.metastore.uris="thrift://$fqdn_hostname:$hivems_port" \
                --hiveconf hive.log.dir=$bigdata_log_dir \
                 > $bigdata_log_dir/hivemeta_nohup.log 2>&1 &


        for i in `seq 1 10`;
                do
		sleep 3
                pid=$(discover_process_by_port $hivems_port)
                if [ "$pid" != '' ]; then
                        pid_file=$bigdata_pids_dir/hive_metastore.pid
                        echo "$pid" > $pid_file
                        log "Hive Meta Server started, pid $pid written to $pid_file"
                        break
                fi
        done


}
function stop_hive_server {
	hive2_pid=$(pgrep -f org.apache.hive.service.server.HiveServer2)
	if [[ -n "$hive2_pid" ]]
	then
		kill $hive2_pid
		if ps -p $hive2_pid > /dev/null ; then
			echo "Initial kill failed, killing with -9 "
			kill -9 $hive2_pid
		fi
	else
		echo "Hiveserver2 process not found , HIveserver2 is not running !!!"
	fi
}

function stop_hive_meta_server {
	meta_pid=$(pgrep -f org.apache.hadoop.hive.metastore.HiveMetaStore)
        if [[ -n "$meta_pid" ]]
        then
                kill $meta_pid
                if ps -p $meta_pid > /dev/null ; then
                        echo "Initial kill failed, killing with -9 "
                        kill -9 $meta_pid
                fi
        else
                echo "Hive metastore process not found , Hive metastore is not running !!!"
        fi

}


function stop_hive {
	stop_hive_server
	stop_hive_meta_server
}


function start_hive {

    start_hive_metastore
    log ''
    start_hive_server

}

function format_namenode {

	log "Formating Name Node"
	hdfs namenode -format
	check_command_status $? "format_namenode"
	}


function hivems_initSchema {
	log "Hive MetaServer initSchema"
	$HIVE_HOME/bin/schematool -initSchema -dbType derby
	check_command_status $? "hivems_initSchema"
	
}
function setup_ant {
	log "setting up Ant"
	wget $ant_url -P /tmp/
	tar -xvf /tmp/$ant_file-bin.tar.gz -C $BIGDATA_ROOT 
	check_command_status $? "setup_ant"
}
function install_java {
	log "setting up Java"
	yum install java-1.8.0-openjdk.x86_64
	check_command_status $? "install_java"
}
function download_github_code {
	github_url=https://github.com/skumarx87/apache_hadoop_ant_install.git
	git clone $github_url
	cd apache_hadoop_ant_install
	$BIGDATA_ROOT/$ant_file/bin/ant -f hadoop_install.xml
}
function status_line {
	service=$1
	port=$2
	pid=$(discover_process_by_port $port)
	if [ "$pid" != '' ]; then
		status="Active [$port]"
		pid_status=$pid
	else
		status="Not Detected"
		pid_status='-'
	fi
	printf "%-20s%-10s%-30s\n" "$service" "$pid_status" "$status"

}

function hadoop_all_status {
	printf '%-20s%-10s%-30s\n' Service Pid Status
	log '..............................................................................'
	status_line 'Hadoop HDFS' $hdfs_port
	status_line 'Hive Metastore' $hivems_port
	status_line 'Hive Server' $hivesrv_port
	status_line 'Spark Master' $sparkms_port
	status_line 'Zookeeper' $zookeeper_port
	status_line 'Kafka Broker' $kafka_broker_port
}

function start_spark_master {

    log "Starting Spark master"
    $SPARK_HOME/sbin/start-master.sh

}

function start_spark_workers {

    log "Starting Spark workers"
    $SPARK_HOME/sbin/start-slaves.sh spark://${HOSTNAME}:$sparkms_port

}

function start_spark {

    log 'START SPARK CLUSTER'
    start_spark_master
    start_spark_workers

}


check_user_profile
	

case "$1" in 
	start)
		start_hdfs
		log ''
		start_hive
		log ''
		start_spark
		log ''
		start_zookeeper
		log ''
	        hadoop_all_status	
	;;
	status)
		hadoop_all_status
	;;
	fresh_install)
		format_namenode
		log ''
		hivems_initSchema
		log ''
	;;	
	stop)
		stop_hdfs
		stop_hive
		stop_spark
		stop_zookeeper
		hadoop_all_status
	;;
	stop_hive)
		stop_hive
	  	hadoop_all_status	
	;;

	stop_hdfs)
		stop_hdfs
	;;
	start_hdfs)
		start_hdfs
	;;
	start_spark)
		start_spark
	;;
	stop_spark)
		stop_spark
	;;
	start_zookeeper)
		start_zookeeper
	;;
	stop_zookeeper)
		stop_zookeeper
	;;
	start_kafka_broker)
		start_kafka_broker
	;;
	stop_kafka_broker)
		stop_kafka_broker
	;;
	esac
