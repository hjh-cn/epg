import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import time
import re

# 过滤非法 XML 字符
def clean_text(text):
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text) if text else ""

# 将 UNIX 时间戳转换为中国标准时间（UTC+8），考虑时移
def convert_to_china_time(unix_timestamp, timeshift=0):
    utc_dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    china_dt = utc_dt + timedelta(hours=8) + timedelta(minutes=timeshift)
    return china_dt.strftime("%Y%m%d%H%M%S")

# 频道列表
channels = [
    {"network_code": "I-JADE", "channel_name": "翡翠台 (香港時區)", "timeshift": 0},
    {"network_code": "I-NEWS", "channel_name": "無綫新聞台", "timeshift": 0},
    {"network_code": "I-STYLE", "channel_name": "TVB生活台", "timeshift": 0},
    {"network_code": "I-ENEW", "channel_name": "娛樂新聞台", "timeshift": 0},
    {"network_code": "I-XHCC", "channel_name": "TVB星河頻道", "timeshift": 0},
    {"network_code": "I-J-AUS", "channel_name": "翡翠台 (澳新時區)", "timeshift": 0},
    {"network_code": "I-J-CAE", "channel_name": "翡翠台 (美加東岸時區)", "timeshift": 0},
    {"network_code": "I-J-CAW", "channel_name": "翡翠台 (美加西岸時區)", "timeshift": 0},
    {"network_code": "I-J-UK", "channel_name": "翡翠台 (英國時區)", "timeshift": 0},
    {"network_code": "I-88", "channel_name": "88台", "timeshift": 0},
    {"network_code": "I-TSN", "channel_name": "TVBS 新聞台", "timeshift": 0},
    {"network_code": "I-TSA", "channel_name": "TVBS ASIA", "timeshift": 0},
    {"network_code": "I-AACT", "channel_name": "功夫台", "timeshift": 0},
    #{"network_code": "I-MN1", "channel_name": "神州新聞台", "timeshift": 0},
    {"network_code": "I-CLM", "channel_name": "粵語片台", "timeshift": 0},
    {"network_code": "CCCTV4", "channel_name": "中國中央電視台中文國際頻道", "timeshift": 0},
    {"network_code": "CCCTV4A", "channel_name": "中國中央電視台中文國際頻道 (亞洲版)", "timeshift": 0},
    {"network_code": "CSOUTV", "channel_name": "大灣區衛視", "timeshift": 0},
    {"network_code": "CCMC", "channel_name": "中國電影頻道CMC", "timeshift": 0},
    {"network_code": "CZHJIA", "channel_name": "浙江電視台國際頻道", "timeshift": 0},
    {"network_code": "CSHZHN", "channel_name": "深圳衛視國際頻道", "timeshift": 0},
    {"network_code": "CSTRTV", "channel_name": "海峽衛視國際頻道", "timeshift": 0},
    {"network_code": "CANHUI", "channel_name": "安徽廣播電視台國際頻道", "timeshift": 0},
    {"network_code": "CCCTVE", "channel_name": "CCTV娛樂頻道", "timeshift": 0},
    {"network_code": "CDRAGN", "channel_name": "上海東方電視台國際頻道", "timeshift": 0},
    {"network_code": "CJIAAU", "channel_name": "江蘇國際頻道", "timeshift": 0},
    {"network_code": "CGUGUX", "channel_name": "廣西電視台國際頻道", "timeshift": 0},
    {"network_code": "CHUNAN", "channel_name": "湖南國際頻道", "timeshift": 0},
    {"network_code": "CBTVS", "channel_name": "北京電視台國際頻道", "timeshift": 0},
    {"network_code": "CYNGJ", "channel_name": "雲南國際頻道", "timeshift": 0},
    {"network_code": "CCCTVO", "channel_name": "中國中央電視台戲曲頻道", "timeshift": 0},
    {"network_code": "CCGTND", "channel_name": "中國環球電視網紀錄片頻道", "timeshift": 0},
    {"network_code": "I-FISH", "channel_name": "快樂垂釣頻道", "timeshift": 0},
    {"network_code": "I-TEA", "channel_name": "茶頻道", "timeshift": 0}
]

# 获取 EPG 数据
def fetch_epg(network_code, date):
    url = f"https://apisfm.tvbanywhere.com.sg/epg/get/{network_code}/{date}/language/tc/+08"
    print(f"📡 请求EPG: {url}")

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return []
        epg_data = response.json()
        if "error" in epg_data:
            print(f"⚠️ {network_code} 未提供节目单")
            return []
        return epg_data.get("programmes", [])
    except Exception as e:
        print(f"❌ 解析EPG数据时发生错误: {e}")
        return []

# 生成 XMLTV
def generate_xml():
    tv = ET.Element("tv", {"generator-info-name": "TVB Anywhere EPG", "source-info-name": "TVB Anywhere"})
    today = datetime.now().strftime("%Y-%m-%d")

    for channel in channels:
        network_code = channel["network_code"]
        channel_name = channel["channel_name"]
        timeshift = channel["timeshift"]

        # 创建频道信息
        channel_elem = ET.Element("channel", {"id": network_code})
        display_name = ET.SubElement(channel_elem, "display-name")
        display_name.text = clean_text(channel_name)
        tv.append(channel_elem)

        # 获取 EPG 数据
        programmes = fetch_epg(network_code, today)

        for i, program in enumerate(programmes):
            start_time_unix = program.get("start_datetime")
            title_tc = clean_text(program.get("programme_name", "未知節目"))
            desc_tc = clean_text(program.get("programme_desc", ""))

            if not start_time_unix:
                continue

            start_time_xml = convert_to_china_time(start_time_unix, timeshift)

            # 计算结束时间
            if i + 1 < len(programmes):
                end_time_unix = programmes[i + 1]["start_datetime"]
            else:
                # 最后一个节目的结束时间为次日第一个节目的开始时间
                next_day = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                next_day_programmes = fetch_epg(network_code, next_day)
                end_time_unix = next_day_programmes[0]["start_datetime"] if next_day_programmes else start_time_unix + 1800

            stop_time_xml = convert_to_china_time(end_time_unix, timeshift)

            print(f"📺 处理 {network_code} 节目: {title_tc} ({start_time_xml} - {stop_time_xml})")

            # 创建 XML 节目节点
            programme = ET.Element("programme", {
                "start": f"{start_time_xml} +0800",
                "stop": f"{stop_time_xml} +0800",
                "channel": network_code
            })
            ET.SubElement(programme, "title", {"lang": "zh"}).text = title_tc
            ET.SubElement(programme, "desc", {"lang": "zh"}).text = desc_tc

            tv.append(programme)

    # 生成 XML 文件
    tree = ET.ElementTree(tv)
    with open("any.xml", "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    print("✅ EPG 已保存为 any.xml")

# 主程序
if __name__ == "__main__":
    generate_xml()
