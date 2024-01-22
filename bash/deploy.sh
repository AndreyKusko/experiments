#!/bin/bash

#echo "platform =$platform"
#echo "platform =${platform}"
#echo "OSTYPE =$OSTYPE"
file_name="docker-compose.yaml"
operation_system=""
ENV_DEV="dev"

ENV=$ENV_DEV


if [[ $OSTYPE == 'linux' ]]; then
  operation_system='linux'
elif [[ $OSTYPE == 'freebsd' ]]; then
    operation_system='freebsd'
elif [[ $OSTYPE == *'darwin'* ]]; then
    operation_system='darwin'
    file_name="docker-compose-osx-dev.yaml"
fi

# перменные файла
#перменные работают или флаг или аргументы
while getopts ":ab" flag; do
while getopts e: arg

#sh deploy.sh -e test
while getopts e: arg
do
    case "${arg}" in
        e) ENV=${OPTARG};;
    esac
done


if [ "$ENV" = "test" ]; then
    echo 'environment is test'
    file_name="docker-compose-osx-dev.yaml"
else
    echo 'environment is not test'
fi

echo "operation_system=operation_system"
echo "file_name=$file_name"
echo "ENV: $ENV";

# если дергать по флагам
#sh deploy.sh -a -b
#OPTSTRING=":ab"
#while getopts ${OPTSTRING} flag; do
while getopts ":ab" flag; do
  case ${flag} in
    a)
      echo "Option -a was triggered."
      ;;
    b)
      echo "Option -b was triggered."
      ;;
    ?)
      echo "Invalid option: -${OPTARG}."
      exit 1
      ;;
  esac
done


while getopts u:a:f: arg
do
    case "${arg}" in
        u) username=${OPTARG};;
        a) age=${OPTARG};;
        f) fullname=${OPTARG};;
    esac
done
echo "Username: $username";
echo "Age: $age";
echo "Full Name: $fullname";




default_environment=dev
environment=$env

#var = "-f docker-compose-osx-dev.yaml"
#docker compose $var stop

#if not default_environment
#  then
#    environment = $default_environment
#myvariable=$1
#myvariable=$myvariable
#myvariable2=Hello
#echo $myvariable
#echo $myvariable2
echo $environment


echo "ENV = $ENV"
echo "ENV_DEV = $ENV_DEV"


[[ "string1" == "string2" ]] && echo "Equal" || echo "Not equal"
[[ "string1" == "string2" ]] && echo "Equal"
[[ "string1" != "string2" ]] && echo "Not equal"

[[ "$ENV" == "$ENV_DEV" ]] && git pull || git pull -f
[[ "$ENV" != "$ENV_DEV"  ]] && echo "Not equal"

#sh deploy.sh -e test
#if [ "$ENV" = "$ENV_DEV" ]; then
#    git pull
#else
#    git pull -f
#fi
#echo 'containers at start'
#docker ps
#docker compose -f "$file_name" stop
#docker-compose -f "$file_name" stop
#docker compose -f "$file_name" down
#echo 'containers after stop'
#docker ps
#docker-compose -f "$file_name" up --build -d
#docker ps
#echo 'containers result'
