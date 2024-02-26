export BIGDATA_ROOT={{ bigdata_dir }}
export BIGDATA_FILE_SYSTEM=hdfs

export JAVA_HOME={{ java_home }}

export HADOOP_HOME=$BIGDATA_ROOT/Envs/hadoop
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS=-Djava.library.path=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin

export HIVE_HOME=$BIGDATA_ROOT/Envs/hive
export HIVE_CONF_DIR=$HIVE_HOME/conf
export PATH=$HIVE_HOME/bin:$PATH

export TEZ_HOME=$BIGDATA_ROOT/Envs/tez
export TEZ_CONF_DIR=$TEZ_HOME/conf
export HADOOP_CLASSPATH=$TEZ_CONF_DIR:$TEZ_HOME/*:$TEZ_HOME/lib/*

export SPARK_HOME=$BIGDATA_ROOT/Envs/spark
export SPARK_MASTER_WEBUI_PORT=8080
export SPARK_WORKER_WEBUI_PORT=8081
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

export KAFKA_HOME=$BIGDATA_ROOT/Envs/kafka
export PATH=$PATH:$KAFKA_HOME/bin

export ZOOKEEPER_HOME=$BIGDATA_ROOT/Envs/zookeeper
export PATH=$PATH:$ZOOKEEPER_HOME/bin
export ZOO_LOG_DIR=$BIGDATA_ROOT/logs

export PATH=$PATH:$BIGDATA_ROOT/thirdparts/Miniconda3/bin
export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9-src.zip:$PYTHONPATH

alias beeline="beeline -u jdbc:hive2://localhost:10000/default"
alias bigdata=$BIGDATA_ROOT/bigadm.sh

export SPARK_DEPLOYMENT_MODE=standalone

