docker stop order
docker rm order
docker run --name order -d \
      -v /home/xiaozy/docker/files/opt/order/:/root/order/ \
      -p 9090:9090 \
      -p 3000:3000 \
      order:1.0 \
      /bin/bash -c 'sleep inf'

docker exec order /bin/bash -c 'echo "192.168.50.88 dev" >> /etc/hosts'
docker exec order /bin/bash -c 'service grafana-server start'
docker exec order /bin/bash -c 'cd /opt/prometheus/ && bash -c "nohup ./prometheus  --config.file=/opt/prometheus/prometheus.yml &"'
docker exec order /bin/bash -c 'cd /root/order && bash -c "nohup ./async_test.py &"'
