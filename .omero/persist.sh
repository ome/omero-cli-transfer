#!/bin/bash

set -u
set -e
dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

. ${dir}/utils
PROJECT=${PROJECT:-$(get_project_name)}
p_or_b=backup
if [ $# -lt 1 ];
then
    echo "persist.sh [--restore] backupdir"
    exit 2
elif [ $1 == "--restore" ];
then
    p_or_b=restore
    shift
fi

backup_path=$1
shift

function backup_volume {
  volume_name=$1
  backup_destination=$2
  echo "Backup $volume_name to $backup_destination"
  docker run --rm -v $volume_name:/data -v $backup_destination:/backup ubuntu tar -zcf /backup/$volume_name.tar /data
}

function restore_volume {
  volume_name=$1
  backup_destination=$2
  echo "Restore $volume_name from $backup_destination"
  docker run --rm -v $volume_name:/data ubuntu find /data -mindepth 1 -delete
  docker run --rm -v $volume_name:/data -v $backup_destination:/backup ubuntu tar -xf /backup/$volume_name.tar -C .
}

function main {
  echo "Mounting volumes and performing $p_or_b"
  for v in ${PROJECT}_dbdata ${PROJECT}_omerodata
  do
    if [ "$p_or_b" == "backup" ]
    then
      backup_volume $v $backup_path
    elif [ "$p_or_b" == "restore" ]
    then
      restore_volume $v $backup_path
    else
      echo "Unknown command: $p_or_b"
      exit 2
    fi
  done
}

main
