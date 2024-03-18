SPARK_WORKER_CORES=2
HADOOP_CONF_DIR={{ BIGDATA_DIR }}/Envs/hadoop/etc/hadoop
SPARK_PID_DIR={{ BIGDATA_DIR }}/pids
SPARK_LOG_DIR={{ BIGDATA_DIR }}/logs

source ~/.bash_profile
export SPARK_DIST_CLASSPATH=$(hadoop classpath)
