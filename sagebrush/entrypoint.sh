#!/bin/bash

# Delete the pid file, if it exists
#queue_name="my_store"
#host_name="10.95.101.121"
queue_name=`echo ${queue_name}`
master_host_name=`echo ${master_host_name}`
#service_name=`echo ${service_name}`
cleanup() {
  chmod 777 /root/rabbitmqadmin
  file="temp_${queue_name}.txt"
  user=`echo $DRIPLINE_USER`
  password=`echo $DRIPLINE_PASSWORD`
  
  /root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${host_name} -P 15672 list consumers channel_details.connection_name queue.name > $file
  
  string="`grep "$queue_name" $file `"
  echo $string
  connection=$(cut -d '|' -f 2  <<< "$string" )
  echo "${connection}"
  connection="${connection:1:-1}"
  /root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${host_name} -P 15672  close connection name="${connection}"
  rm ${file}
}
`echo $user` 
#dl-serve -c ${service_name}
# Run whatever the image CMD or `docker run` command is

#chown -R root:root /root/
exec "$@"
