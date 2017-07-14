#!/usr/bin/env bash
while getopts s:e:d:c: option
do
 case "${option}"
 in
 s) START=${OPTARG};;
 e) END=$OPTARG;;
 d) DATE=$OPTARG;;
 c) COUNT=$OPTARG;;
 m) METHOD=$OPTARG;;
 esac
done
if [ -z "$END" ]
then
    : END=$START;
fi
if [ ! -z "$DATE" ]
then
    : CMDDATE="--until $DATE";
else
    : CMDDATE="";
fi
if [ ! -z "$COUNT" ]
then
    : CMDCOUNT="--count $COUNT";
else
    : CMDCOUNT="";
fi
if [ ! -z "$METHOD" ]
then
    : CMDMETHOD="--method $METHOD";
else
    : CMDMETHOD="";
fi

source ../venv/bin/activate
for i in $(seq $START $END); do
    echo "echo python search.py --keywords keywords-$i $CMDMETHOD $CMDDATE $CMDCOUNT > last_cmd.log" ;
    python search.py --keywords keywords-$i $CMDMETHOD $CMDDATE $CMDCOUNT;
done
