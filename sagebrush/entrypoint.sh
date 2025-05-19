#!/bin/bash


#trap cleanup SIGINT SIGTERM EXIT

#cleanup() {
#queue_name=`echo ${queue_name}`
#master_host_name=`echo ${master_host_name}`
echo ${queue_name}
echo ${master_host_name}
user=`echo $DRIPLINE_USER`
password=`echo $DRIPLINE_PASSWORD`
chmod 777 /root/rabbitmqadmin
file="temp_${queue_name}.txt"

cmd0=`/root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672" list consumers channel_details.connection_name queue.name > $file`

string="`grep "${queue_name}" $file `"
echo $string
connection=$(cut -d '|' -f 2  <<< "$string" )
if [[ "$connection" =~ "->" ]]; then
  #$connection="${connection:1:-1}"
  string_no_spaces=$(echo "$connection" | tr -d ' ')
  connection=${string_no_spaces/\-\>/\ \-\>\ }
  echo $connection
  cmd=`/root/rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672"  close connection name="${connection}" `
fi
rm ${file}
#}
sleep 3
# Run whatever the image CMD or `docker run` command is

exec "$@"
