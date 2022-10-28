#!/bin/bash

pip3 install aws
pip3 install boto3
pip3 install paramiko
pip3 install requests

cat creds.txt > ~/.aws/credentials
chmod 400 labsuser.pem

python3 launching.py