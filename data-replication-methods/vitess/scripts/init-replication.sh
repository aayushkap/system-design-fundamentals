#!/usr/bin/env sh
set -eux

# give MySQL a moment
sleep 10

# 1) Create a replication user on each primary
mysql -h mysql-s1-primary -uroot -proot -e "CREATE USER 'repl'@'%' IDENTIFIED BY 'repl'; GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';"
mysql -h mysql-s2-primary -uroot -proot -e "CREATE USER 'repl'@'%' IDENTIFIED BY 'repl'; GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';"

# 2) Grab primary positions
POS1=$(mysql -h mysql-s1-primary -uroot -proot -BN -e "SELECT GTID_SUBSET(GTID_EXECUTED, '')")
POS2=$(mysql -h mysql-s2-primary -uroot -proot -BN -e "SELECT GTID_SUBSET(GTID_EXECUTED, '')")

# 3) Configure each replica
mysql -h mysql-s1-replica -uroot -proot -e "
STOP SLAVE; 
CHANGE MASTER TO MASTER_HOST='mysql-s1-primary', MASTER_USER='repl', MASTER_PASSWORD='repl', MASTER_AUTO_POSITION=1; 
START SLAVE;"
mysql -h mysql-s2-replica -uroot -proot -e "
STOP SLAVE; 
CHANGE MASTER TO MASTER_HOST='mysql-s2-primary', MASTER_USER='repl', MASTER_PASSWORD='repl', MASTER_AUTO_POSITION=1; 
START SLAVE;"
