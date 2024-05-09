# 使用官方的Ubuntu 20.04镜像作为基础
FROM ubuntu:20.04

# 设置时区和非交互式安装环境变量
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 更新软件包并安装所需软件包和依赖项
RUN apt-get update && \
    apt-get -y install python3 python3-pip build-essential python3-dev libnetfilter-queue-dev && \
    pip3 install netfilterqueue scapy schedule && \
    apt-get clean

# 复制a.py文件到容器的/opt目录
#COPY nfqueue_monitor.py /opt/nfqueue_monitor.py

# 在容器启动时运行a.py文件
CMD ["python3", "/opt/nfqueue_monitor.py"]
