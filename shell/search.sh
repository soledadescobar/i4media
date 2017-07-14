while getopts s:e:d:c:m: option
do
 case "${option}"
 in
 s) START=${OPTARG};;
 e) END=${OPTARG};;
 d) DATE="--until ${OPTARG}";;
 c) COUNT="--limit ${OPTARG}";;
 m) METHOD="--method ${OPTARG}";;
 esac
done
if [ -z "$END" ]
then
    : END="$START";
fi

source ../venv/bin/activate
for i in $(seq $START $END); do
    echo python search.py --keywords keywords-$i $DATE $COUNT $METHOD > last_cmd.log;
    python search.py --keywords keywords-$i $DATE $COUNT $METHOD;
done
