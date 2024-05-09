import time
import schedule
import netfilterqueue
from scapy.all import *

# 设置日志文件夹的绝对路径
logs_folder = '/opt/logs'

# 创建 logs 文件夹
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)

def packet_handler(pkt):
    # 转换数据包为 Scapy 格式
    scapy_packet = IP(pkt.get_payload())

    # 只处理 UDP 数据包
    if scapy_packet.haslayer(UDP):
        # 获取源 IP 地址和端口
        src_ip = scapy_packet[IP].src
        src_port = scapy_packet[UDP].sport
        
        # 提取 UDP 负载数据
        payload = bytes(scapy_packet[UDP].payload)
        decoded_payload = payload.decode('utf-8')

        now = time.localtime()

        log = "\n\n\n\n\n\n"
        log += time.strftime("%Y-%m-%d %H:%M:%S", now) + "\n"
        log += "start ----------------------------------------------------------------------------------\n"
        log += 'Original message:\n' + decoded_payload

        # 只对接收到的数据包为 "200 OK" 进行处理
        if "200 OK" in decoded_payload:
            # 匹配 SIP 消息头Contact中的 IP和端口
            sip_header_pattern = r'Contact:\s*<sip:(.*?)@(.*?):(\d+)'
            sip_header_match = re.search(sip_header_pattern, decoded_payload)

            log += "\n\n---- The current packet is 200 ok. src_ip: " + str(src_ip) + ", src_port:" + str(src_port) + "\n\n"

            if sip_header_match:
                # 获取匹配到Contact中的 IP和端口
                contact_user = sip_header_match.group(1)
                contact_ip = sip_header_match.group(2)
                contact_port = sip_header_match.group(3)

                # 判断Contact中的 IP和端口 是否与 源IP和端口 一致
                if str(contact_ip) == str(src_ip) and str(contact_port) == str(src_port):
                    log += "\n\n---- Contact IP and Port are consistent with the Source IP and Port.\n\n"
                else:
                    log += "\n\n---- Contact IP and Port are NOT consistent with the Source IP and Port.\n\n"

                    # 替换消息体中的Contact内容 为 来源IP:来源端口
                    modified_payload = decoded_payload.replace(f'Contact: <sip:{contact_user}@{contact_ip}:{contact_port}', f'Contact: <sip:{contact_user}@{src_ip}:{src_port}')

                    # 打印修改后的消息体
                    log += 'Modified message:\n' + modified_payload

                    # 构造新的UDP数据包
                    new_udp_payload = bytes(modified_payload, 'utf-8')
                    new_udp = UDP(sport=scapy_packet[UDP].sport, dport=scapy_packet[UDP].dport) / new_udp_payload
                    new_ip = IP(src=scapy_packet[IP].src, dst=scapy_packet[IP].dst) / new_udp

                    # 更新原始数据包负载为新数据包负载
                    pkt.set_payload(bytes(new_ip))
        
        log += "end ------------------------------------------------------------------------------------"

        # 获取当前日期并将其格式化为年月日
        today_date = datetime.now().strftime("%Y-%m-%d")

        # 构造日志文件名
        logfile_name = os.path.join(logs_folder, f"logfile_{today_date}.txt")

        # 将日志写入文件
        with open(logfile_name, 'a') as logfile:
            logfile.write(log)

    # 接受数据包，不做任何修改
    pkt.accept()


# 清理 logs 文件夹中超过 7 天的日志文件
def cleanup_logs():
    current_date = datetime.now()
    for file in os.listdir(logs_folder):
        file_path = os.path.join(logs_folder, file)
        if os.path.isfile(file_path):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if current_date - file_creation_time > timedelta(days=7):
                os.remove(file_path)

# 每天的固定时间执行清理日志的任务
schedule.every().day.at("01:00").do(cleanup_logs)

queue = netfilterqueue.NetfilterQueue()
queue.bind(5080, packet_handler)
queue.run()