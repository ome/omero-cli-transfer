#!/bin/bash

if [ $# -ne 2 ];
then
    echo "download.sh backupurl backupdir"
    exit 2
fi

set -u
set -e
dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
. ${dir}/utils
project=${PROJECT:-$(get_project_name)}
backupurl=$1
backupdir=$2
backupsrc=${BACKUPSRC:-"${backupdir}/omero_test_infra_backup.zip"}

if [ ! -d ${backupdir} ]; then
    echo "Creating ${backupdir}..."
    mkdir -p ${backupdir}
fi

if [ ! -f ${backupdir}/${project}_dbdata.tar ] || [ ! -f ${backupdir}/${project}_omerodata.tar ]; then
    echo "Tarballs not found..."
    if [ ! -f ${backupsrc} ]; then
        echo "Backup zip not found..."
        curl ${backupurl} > ${backupsrc}
    fi
    unzip -d ${backupdir} ${backupsrc}
fi
echo "Backup ready"
