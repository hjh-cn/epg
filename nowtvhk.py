import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# **API 配置**
API_URL = "https://nowplayer.now.com/tvguide/epglist"
CHANNELS = [
    102, 105, 108, 111, 112, 113, 114, 115, 116, 119, 133, 138, 150, 155, 156, 162,
    200, 321, 325, 328, 329, 330, 331, 332, 333, 366, 367, 371, 502, 512, 513, 517,
    538, 540, 541, 542, 543, 545, 548, 551, 552, 553, 555, 561, 630, 631, "099", "096"
]
DAYS = [1, 2, 3]  # **抓取 3 天数据**
COOKIE = "NOWSESSIONID=; _ga=GA1.1.1244346033.1740285872; WZRK_G=ee5ee1a535d345f7a96bdd89a14c08f1; NOW_SESSION=b0c4fc0487e5b349296f55d969de215610470549-NOWSESSIONID=&mupType=NORMAL&nowDollarBalance=0&isBinded=false&isMobileId=false&mobile=&isOTTMode=N&firstMupUser=false&is4K=false&isLogin=false&isMobileGuest=false&fsaType=&mupShow=login&lang=zh; LANG=zh; WZRK_S_TEST-5R6-647-885Z=%7B%22p%22%3A2%2C%22s%22%3A1740285871%2C%22t%22%3A1740285873%7D; _ga_K0993SPMC0=GS1.1.1740285871.1.1.1740285876.0.0.0"

HEADERS = {
    "Accept": "text/plain, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",  # **确保 API 以中文返回**
    "Cache-Control": "no-cache",
    "Cookie": COOKIE,
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    "Referer": "https://nowplayer.now.com/tvguide",
    "X-Requested-With": "XMLHttpRequest"
}

# **创建 XML 结构**
tv = ET.Element("tv")
tv.set("source-info-name", "Now TV")
tv.set("generator-info-name", "Now TV EPG Scraper")

# **添加频道信息**
channel_elements = {}
for channel_id in CHANNELS:
    channel_elem = ET.SubElement(tv, "channel", id=str(channel_id))
    ET.SubElement(channel_elem, "display-name").text = f"Channel {channel_id}"
    ET.SubElement(channel_elem, "icon", src=f"https://images.now-tv.com/shares/channelPreview/img/en_hk/color/ch{channel_id}_170_122")
    channel_elements[channel_id] = channel_elem

# **时间格式转换**
def convert_timestamp(timestamp):
    return datetime.utcfromtimestamp(timestamp / 1000).strftime("%Y%m%d%H%M%S") + " +0000"

# **请求 EPG 数据**
def fetch_epg_data(day, channel):
    url = f"{API_URL}?day={day}&channelIdList={channel}"
    print(f"🔍 请求 URL: {url}")  # Debug: 输出请求的 URL

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None

# **遍历每一天和每个频道**
for day in DAYS:
    for channel in CHANNELS:
        data = fetch_epg_data(day, channel)
        time.sleep(0.5)  # **加上延迟，避免触发 API 频率限制**

        if not data or not isinstance(data, list):
            print(f"⚠️ 频道 {channel} 第 {day} 天 没有数据，跳过。")
            continue

        # **API 返回的是多个数组，需要合并解析**
        for program_list in data:
            for program in program_list:
                if not isinstance(program, dict) or "name" not in program:
                    continue  # 跳过无效数据
                
                programme_elem = ET.SubElement(tv, "programme", channel=str(channel))
                programme_elem.set("start", convert_timestamp(program["start"]))
                programme_elem.set("stop", convert_timestamp(program["end"]))

                ET.SubElement(programme_elem, "title").text = program["name"]
                if "cc" in program and program["cc"]:
                    ET.SubElement(programme_elem, "category").text = program["cc"]
                if "recordable" in program:
                    ET.SubElement(programme_elem, "recordable").text = str(program["recordable"]).lower()

print("✅ EPG 数据解析完成，正在生成 XML 文件...")

# **生成 XML 文件**
tree = ET.ElementTree(tv)
xml_filename = "nowtvepg.xml"
tree.write(xml_filename, encoding="utf-8", xml_declaration=True)

print(f"✅ EPG XML 生成成功！文件名：{xml_filename}")
