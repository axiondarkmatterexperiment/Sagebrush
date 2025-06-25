#!/bin/bash


##This is a script to close a ghost connection of rabbitmq (if any) before luanching the container
##Expected enviornment variables set: queue_name, master_host_name, DRIPLINE_USER, DRIPLINE_PASSWORD
##queue_name: queue name of the service (only expect one return of the connection with the queue_name search)
##master_host_name: host ip of the rabbitmq
##DRIPLINE_USER: username of the rabbitmq service
##DRIPLINE_PASSWORD: password of the rabbitmq service


echo ${queue_name}
echo ${master_host_name}
user=`echo $DRIPLINE_USER`
password=`echo $DRIPLINE_PASSWORD`
file="temp_${queue_name}.txt"

cmd0=`rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672" list consumers channel_details.connection_name queue.name > $file`

string="`grep "${queue_name}" $file `"
echo $string
connection=$(cut -d '|' -f 2  <<< "$string" )
if [[ "$connection" =~ "->" ]]; then
  #$connection="${connection:1:-1}"
  string_no_spaces=$(echo "$connection" | tr -d ' ')
  connection=${string_no_spaces/\-\>/\ \-\>\ }
  echo $connection
  cmd=`rabbitmqadmin --vhost '/' -u $user -p $password -H ${master_host_name} -P "15672"  close connection name="${connection}" `
fi
rm ${file}
#}
sleep 3

exec "$@"
