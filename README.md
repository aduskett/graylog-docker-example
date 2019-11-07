# GrayLog docker-compose
This directory contains everything needed to quickly bring up a Greylog server using docker-compose.

# Requirements
- A computer running Linux, SystemD, and Docker.
- Python3.4+.
- Docker-compose.

# Host Setup
- Add the following to /etc/sysctl.conf
  - net.ipv4.ip_forward=1
  - vm.max_map_count=262144
- Copy and paste the following in the terminal:
- `echo 'never' > /sys/kernel/mm/transparent_hugepage/defrag`
- `echo 'never' > /sys/kernel/mm/transparent_hugepage/enabled`

# How to install
- Place the graylog directory in `/etc/docker-compose/`. If `/etc/docker-compose` does not exist,
  create it with `sudo mkdir -p /etc/docker-compose/`
- Edit the file `docker-compose.yml` and edit the line `GRAYLOG_HTTP_EXTERNAL_URI` with the appropriate URI.
- Run the following commands:
	- `cd /etc/docker-compose/graylog`
	- `cp ./systemd/graylog.service /usr/lib/systemd/system/`
	- `systemctl enable graylog.service`
	- `docker-compose build`
	- `systemctl start graylog`

After a few moments, the graylog server will start and you should be able to access it via the URI that was set in the docker-compose.yml

## Volumes
The following volumes are used for persistent storage. Changing files in these folders and restarting the
docker containers will effect the servers.

**Mongo:**
- ./mongo/volumes/db -> /data/db

**Elasticsearch:**
- ./elasticsearch/volumes/data -> /usr/share/elasticsearch/data

**Graylog:**
- ./graylog/volumes/journal -> /usr/share/graylog/data/journal
- ./graylog/volumes/config -> /usr/share/graylog/data/config


## Testing
To test if graylog is working correctly, there is a provided python script in the test_python_app directory.
