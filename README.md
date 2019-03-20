# Installation and Set Up a 3-Node Hadoop Cluster v.3.1.2 on Ubuntu v.16.04 with Ansible

How To
------------
1. After Vagrant setup all enviroment log into EGHome as user:vagrant pswd:vagrant
2. git clone https://github.com/Lunnasi/EG.git --branch EG/home_work
3. cd EG/
4. source suorce.sh (istall all prerequisites)
5. ansible all -m ping (check if all vm is available)
6. ansible-playbook install_playbook.yml (install all hadoop env and configure)
7. ansible-playbook clickhouse_playbook.yml (instal clickhouse)
8. ansible-playbook task3_playbook.yml

Multi-node cluster install
------------
1. Download and intall JAva and Hadoop on all the systems
2. Specify the IP address of each system followed by their host names in host file of each system
3. COnfigure hadoop configuration files (core-site,hdfs-site,mapred-site,yasrn-site)
4. Edit slaves file on master node
5. Format namenode and start all hadoop services
6. Check live nodes on Hadoop namenode UI
   hdfs dfsadmin report 

Infrastructure
--------------

Infrastructure was provisioned by HashiCorp Vagrant. Please look into Vagrantfile for a details

Deploy server:
* EGHome  -  192.168.56.105

Master Deamons will run on
* master  -  192.168.56.11
- HDFS - Name node
- YARN - Resource Manager

Slave Deamons will run on
* node1  -  192.168.56.12
* node2  -  192.168.56.13
- HDFS - Data node
- YARN - Node manager


Host File
------------
host_file:
* 192.168.56.11 master master
* 192.168.56.12 node1 node1
* 192.168.56.13 node2 node2
* 192.168.56.14 clickhouse clickhouse
* 192.168.56.105 eghome eghome

Property Files
----------------


role/deploy_hadoop/tasks
----------------
main.yml
  include_tasks:
  *  config.yml
    -  property files + env variables
  *  infrastructure.yml
    -  create folders user permitions
  *  install.yml
    -  install prerequesites, download hadoop instalation && unarchve it.
  *  ssh_keys.yml
    -  SSH Key Exchange between multiple hosts

Example Playbook
----------------

ansible-playbook install-playbook.yml

License
-------

BSD

Author Information
------------------

This role was created as a part of "Evolution Games" Interview home works subtask.
