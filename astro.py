import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
from dateutil import parser

VALID_FILE = 'valid_channels.txt'

def fetch_channel_json(channel_id):
    url = f"https://contenthub-api.eco.astro.com.my/channel/{channel_id}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Channel {channel_id} error: {e}")
    return None

def format_xmltv_time(iso_time):
    dt = parser.isoparse(iso_time)
    return dt.strftime("%Y%m%d%H%M%S %z")

def load_valid_channels():
    if not os.path.exists(VALID_FILE):
        return {}
    valid = {}
    with open(VALID_FILE, 'r') as f:
        for line in f:
            if '|' in line:
                cid, cname = line.strip().split('|', 1)
                valid[cid] = cname
    return valid

def save_valid_channel(channel_id, channel_name):
    with open(VALID_FILE, 'a') as f:
        f.write(f"{channel_id}|{channel_name}\n")

def generate_epg(start_id=1, end_id=5000, output="astro.xml", use_valid_only=False):
    tv = ET.Element('tv', attrib={"generator-info-name": "astro"})
    valid_channels = load_valid_channels()

    for channel_id in range(start_id, end_id + 1):
        data = fetch_channel_json(channel_id)
        if not data or 'response' not in data or 'schedule' not in data['response']:
            continue

        resp = data['response']

        # ✅ 使用 stbNumber，若无或为 0，则使用 id
        stb_raw = resp.get("stbNumber", 0)
        if not stb_raw or str(stb_raw) == "0":
            chan_id = str(resp.get("id", channel_id))
        else:
            chan_id = str(stb_raw)

        channel_name = resp.get("title", f"Channel {chan_id}")
        chan_icon = resp.get("imageUrl", "")

        if use_valid_only and chan_id not in valid_channels:
            continue
        if not use_valid_only and chan_id in valid_channels:
            print(f"✅ 已处理频道 {chan_id}: {valid_channels[chan_id]}")
            continue

        # <channel> 信息
        channel = ET.SubElement(tv, 'channel', id=chan_id)
        ET.SubElement(channel, 'display-name').text = channel_name
        if chan_icon:
            ET.SubElement(channel, 'icon', src=chan_icon)

        # <programme> 列表
        schedule = resp.get("schedule", {})
        for day, programs in schedule.items():
            for prog in programs:
                try:
                    start = format_xmltv_time(prog['eventStartUtc'])
                    stop = format_xmltv_time(prog['eventEndUtc'])

                    programme = ET.SubElement(tv, 'programme', start=start, stop=stop, channel=chan_id)
                    ET.SubElement(programme, 'title', lang="en").text = prog.get("title", "No Title")
                    ET.SubElement(programme, 'desc', lang="en").text = prog.get("description", "No Description")

                    genre = prog.get("genre")
                    if genre:
                        ET.SubElement(programme, 'category', lang="en").text = genre

                    subgenre = prog.get("subGenre")
                    if subgenre:
                        ET.SubElement(programme, 'sub-title', lang="en").text = subgenre

                    icon_url = prog.get("imageUrl")
                    if icon_url:
                        ET.SubElement(programme, 'icon', src=icon_url)

                except Exception as e:
                    print(f"⚠️ 节目解析失败 (频道 {chan_id}): {e}")
                    continue

        print(f"✔️ 频道 {chan_id} - {channel_name} 处理完成")
        if chan_id not in valid_channels:
            save_valid_channel(chan_id, channel_name)

        time.sleep(0.1)  # 防止访问过快被封

    tree = ET.ElementTree(tv)
    tree.write(output, encoding='utf-8', xml_declaration=True)
    print(f"\n🎉 EPG 文件生成成功：{output}")

# 主运行点
if __name__ == '__main__':
    #generate_epg(1, 1000)
    # 想只处理已验证频道时使用：
    generate_epg(1, 1000, use_valid_only=True)
