FROM ubuntu:20.04

ADD ./files/etc /etc
ADD ./files/opt /opt

SHELL ["/bin/bash", "-c"]
RUN chown root: -R /etc/apt &&\ 
  # install apt package
  rm -rf /var/lib/apt/lists/* &&\
  apt-get update &&\
  apt-get install -y curl vim python3 python3-pip adduser libfontconfig1 coreutils &&\
  apt-get clean &&\
  # install pip package
  mv /opt/.pip /root/ &&\
  pip3 install httpx httpx[http2] prometheus-client asyncio-pool h2 &&\
  # install grafana
  dpkg -i /opt/grafana.deb &&\
  true
