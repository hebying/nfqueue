### 问题场景
FreeSWITCH外呼时通话一分钟中断，经过查看抓包分析是落地网关发送到FreeSWITCH服务器的200ok数据包中的Contact值有问题

### 解决方法
将FreeSWITCH收到的SIP数据包放到nfqueue队列里，写一个python脚本实时监听nfqueue队列，根据判断条件修改200ok里的Contact值，修改完成后，再转发到sip server服器上。
关于iptables的配置参见：
https://asphaltt.github.io/post/iptables-nfqueue-usage/
https://www.hyuuhit.com/2018/07/13/nfqueue/

### 实现方法
编写python脚本，在ubuntu容器中运行

### 构建镜像
```shell
# 构建前先使用docker load加载镜像
docker load -i /home/nfqueue/ubuntu.22.04.tar
# 打tag
docker tag  b2c9e106c9d9 ubuntu:20.04
# 构建
docker build -t nfqueue .
```

### 运行容器
```shell
docker run -itd --name nfqueue_01 --net=host --restart=always --privileged=true -v /home/nfqueue/nfqueue_monitor.py:/opt/nfqueue_monitor.py -v /home/nfqueue/logs:/opt/logs nfqueue
# 注：-v 主机目录:容器目录 映射情况
```

### iptables策略
```shell
iptables -A INPUT -p udp -m udp --dport 6660 -j NFQUEUE --queue-num 5080 --queue-bypass
# 注：5080需要与python脚本中的一致
#    --queue-bypass 如果没有用户空间程序侦听NFQUEUE上的数据包，则将要排队的所有数据包都将被丢弃；使用此选项时，NFQUEUE规则的行为类似于ACCEPT，数据包将移动到下一个表
```

### 查看queue队列
```shell
cat /proc/net/netfilter/nfnetlink_queue
   40  23948     0   2   65531     0     0      106   1
# 队列号：由 --queue-number 指定
# 对端接口 ID：监听队列的 pid
# 队列数量：当前在队列里等待的网络包数量
# 复制模式：0 和 1 只提供元数据；2 同时还会提供限定复制范围的部分网络包内容（a part of packet of size copy range）。
# 复制范围：放进消息里的网络包长度
# 队列丢包数量：因队列满了而丢包的网络包数量
# 用户丢包数量：因不能发送到用户态而丢包的网络包数量。如果该数值不为 0，尝试增大 netlink 缓存大小（increase netlink buffer size）。在程序侧，如果发生丢包，可以看到整数索引不连续了（see gap in packet id）。
# ID 序列：最后一个网络包的整数索引
# 1
```

### 将指定镜像保存为tar归档文件
```
docker save [OPTIONS] IMAGE [IMAGE...]
   OPTIONS说明:
   -o: 输出到的文件
   IMAGE: 镜像名称 或 镜像ID
如：docker save -o /tmp/aa.tar 4c42fc326802
```

### 导入并创建docker镜像
```
docker load -i [docker镜像tar路径]
如：docker load -i /tmp/aa.tar

# 导入成功以后，向新导入的镜像进行命名
docker tag [IMAGE ID] [REPOSITORY[:TAG]]
如：docker tag 35cdes freeswitch_ex:external
```