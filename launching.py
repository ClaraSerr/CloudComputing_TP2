import boto3
from botocore.exceptions import ClientError
import paramiko
import time
import requests
import datetime


ec2_RESSOURCE = boto3.resource('ec2', region_name='us-east-1')
ec2_CLIENT = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')


# Creates a security group with 3 inbound rules allowing TCP traffic through custom ports
def create_security_group(vpc_id, ports):
    # We will create a security group in the existing VPC
    try:
        security_group = ec2_RESSOURCE.create_security_group(GroupName='security_group',
                                             Description='Flask_Security_Group',
                                             VpcId=vpc_id,
                                             )
        security_group_id = security_group.group_id
        for port in ports: # In our use case, ports = [22, 80, 443]
            # Create inbound rule for port
            security_group.authorize_ingress(
                DryRun=False,
                IpPermissions=[
                    {
                        'FromPort': port,
                        'ToPort': port,
                        'IpProtocol': 'TCP',
                        'IpRanges': [
                            {
                                'CidrIp': '0.0.0.0/0',
                                'Description': "Flask_authorize"
                            },
                        ]
                    }
                ]
            )
            # Create outbound rule for port
            ec2_CLIENT.authorize_security_group_egress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'FromPort': port,
                        'ToPort': port,
                        'IpProtocol': 'TCP',
                        'IpRanges': [
                            {
                                'CidrIp': '0.0.0.0/0',
                                'Description': "Flask_authorize"
                            },
                        ]
                    }
                ]
            )
        print('Security Group Created %s in vpc %s.' %
              (security_group_id, vpc_id))
        return security_group_id
    except ClientError as e:
        print(e)

def create_instance(id_min,id_max,instance_type,keyname,name,security_id,availability_zone):
    Instances=[] # To save instance info after creation
    for i in range(id_min,id_max+1):
        Instances+=ec2_RESSOURCE.create_instances(
            ImageId="ami-08c40ec9ead489470",
            InstanceType=instance_type,
            KeyName=keyname,
            MinCount=1,
            MaxCount=1,
            # Specify the id of the instances in its Tag Name (did not made it work)
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value':  name+str(i)
                        },
                    ]
                },
            ],
            SecurityGroupIds=[security_id],
            Placement={
                'AvailabilityZone': availability_zone})
    print('{} instances created'.format(instance_type))
    return Instances



def create_commands():
    ### stores in a list the set of commands needed to :
    ### install java
    ### instal and setup hadoop
    commands = [

    # Install java
    'sudo add-apt-repository ppa:webupd8team/java',
    'sudo apt-get update', 
    'yes | sudo apt-get install oracle-java8-installer',
    'sudo apt-get install oracle-java8-set-default',

    # Install Python3
    'yes | sudo apt-get install python3-pip',

    # adds to path the location of java
    '''echo "export JAVA_HOME=/usr/lib/jvm/java-7-oracle
export PATH=$JAVA_HOME/bin" >> ~/.profile''',
    'source ~/.profile ',

    # Download hadoop
    'wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz',
    'tar -xf hadoop-3.3.4.tar.gz -C /usr/local/',

    # adds to path the location of hadoop
    '''echo "export HADOOP_PREFIX=/usr/local/hadoop-3.3.4
export PATH=$HADOOP_PREFIX/bin:$PATH" >> ~/.profile''',

    # add paths of java and hadoop to script
    '''echo "export JAVA_HOME=/usr/lib/jvm/java-8-oracle$ 
export HADOOP_PREFIX=/usr/local/hadoop-3.3.4" >> etc/hadoop/hadoop-env.sh''',
    #'hadoop',

    # Switch to Pseudo-Distributed Mode
    '''sed 's/<name>fs.defaultFS<\/name>
        <value>.*<\/value>/<name>fs.defaultFS<\/name>
        <value>hdfs:\/\/localhost:9000<\/value>' etc/hadoop/core-site.xml''',
    '''sed 's/<name>dfs.replication<\/name>
        <value>.*<\/value>/<name>dfs.replication<\/name>
        <value>1<\/value>' etc/hadoop/hdfs-site.xml''',

    # Setting up SSH
    'sudo apt-get install ssh ',
    'ssh-keygen -t dsa -P '' -f ~/.ssh/id_dsa',
    'cat ~/.ssh/id_dsa.pub >> ~/.ssh/authorized_keys',

    #optionnal
    'mkdir /var/lib/hadoop',
    'chmod 777 /var/lib/hadoop',
    '''sed 's/<name>hadoop.tmp.dir<\/name>
        <value>.*<\/value>/<name>hadoop.tmp.dir<\/name>
        <value>\/var\/lib\/hadoop<\/value>' etc/hadoop/core-site.xml''',

    #Formatting the HDFS Filesystem
    'hdfs namenode -format ',

    #Starting NameNode Daemon and DataNode Daemon
    '$HADOOP_PREFIX/sbin/start-dfs.sh ',

    #Creating the Home Directory
    'hdfs dfs -mkdir /user',
    'hdfs dfs -mkdir /user/hadoop',

    #Starting a MapReduce Job
    'hdfs dfs -mkdir input ',
    'hdfs dfs -put $HADOOP_PREFIX/etc/hadoop input ',
    'hadoop jar $HADOOP_PREFIX/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.4.jar grep input output "dfs+"',

    # output the results
    'hdfs dfs -get output output',
    'cat output/*',
    ]
    return commands


def main():
    # Get global Vpc in use
    response = ec2_CLIENT.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    
    # Launches custom security group
    security_group_id = create_security_group(vpc_id, [22, 80, 443])

    # Launches 1 m4_large instance
    Instances_m4=create_instance(1,1,"m4.large","vockey","m4_large_",security_group_id,"us-east-1b")

    # Stores DNS and IP adress of the instance
    DNS_addresses_m4=[]
    IP_addresses_m4=[]

    # Generic code in case of creation of multiple instances
    for instance in Instances_m4:
        instance.wait_until_running()
        # Reload the instance attributes
        instance.load()
        DNS_addresses_m4.append(instance.public_dns_name)
        IP_addresses_m4.append(instance.public_ip_address)
        print("DNS = ",instance.public_dns_name)
        print("IPV4 = ",instance.public_ip_address)
        # Enable detailed monitoring
        instance.monitor(
            DryRun=False
        )
        
    # Configure SSH connection to AWS
    k = paramiko.RSAKey.from_private_key_file("labsuser.pem")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # wait to make sure connection will be possible
    time.sleep(10)

    for i in range(len(DNS_addresses_m4)):
        print("Connecting to ", DNS_addresses_m4[i])
        # SSH connection to instance
        c.connect( hostname = DNS_addresses_m4[i], username = "ubuntu", pkey = k )
        print("Connected")
        # Commands to be executed on the instance
        commands = create_commands()
 
        for command in commands[:-1]:
            print("Executing {}".format( command ))
            stdin , stdout, stderr = c.exec_command(command)
            print(stdout.read())
            print(stderr.read())

        # OUTDATED ?
        # The last command to be executed does not send anything to stdout, so we don't read it not to be stuck
        print("Executing {}".format( commands[-1] ))
        stdin , stdout, stderr = c.exec_command(commands[-1])
        print("Go to http://"+str(IP_addresses_m4[i]))


    time.sleep(5)
    c.close()

    #print(cluster_1, cluster_2)
    
    print('Launching complete')

    # Cloudwatch metrics getter
    '''
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'test',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ApplicationELB',
                        'MetricName': 'RequestCount',
                        'Dimensions': [
                            {
                                    'Name': "LoadBalancer",
                                    'Value': 'firstelb',
                                },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum'
                    },
            },
        ],
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
        EndTime=datetime.datetime.utcnow()
    )
    print(response)'''

main()