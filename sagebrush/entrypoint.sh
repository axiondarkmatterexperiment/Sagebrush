#!/bin/bash


#trap cleanup SIGINT SIGTERM EXIT

#cleanup() {
queue_name=`echo ${queue_name}`
master_host_name=`echo ${master_host_name}`
user=`echo $DRIPLINE_USER`
password=`echo $DRIPLINE_PASSWORD`
chmod 777 /root/rabbitmqadmin
file="temp_${queue_name}.txt"

cmd0=`/root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672" list consumers channel_details.connection_name queue.name > $file`

string="`grep "$queue_name" $file `"
echo $string
connection=$(cut -d '|' -f 2  <<< "$string" )
echo "${connection}"
if [[ "$connection" =~ "->" ]]; then
  connection="${connection:1:-1}"
  cmd=`/root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672"  close connection name="${connection}" `
fi
rm ${file}
#}

# Run whatever the image CMD or `docker run` command is

exec "$@"
