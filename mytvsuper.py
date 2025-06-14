import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import re
import pytz

# 过滤非法 XML 字符
def clean_text(text):
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text) if text else ""

# TVB 频道列表
network_codes = ["SVAR", "SEYT", "SFOO", "STRA", "SMUS", "SGOL", "SSIT", "STVM",
                 "SDOC", "J", "JUHD", "B", "C", "P", "CWIN", "C18", "C28", "TVG",
                 "CDR3", "CCLM", "CTVS", "TVO", "CTVE", "CCOC", "KID", "ZOO",
                 "CNIKO", "CNIJR", "CMAM", "CTHR", "CCCM", "CMC", "CRTX", "CKIX",
                 "LNH", "LN4", "SMS", "CRTE", "CAXN", "CANI", "CJTV", "CTS1",
                 "CRE", "FBX", "CMEZ", "DTV", "PCC", "PIN", "PHK", "POPC", "CC1",
                 "CGD", "CGE", "CMN1", "CTSN", "CCNA", "CJAZ", "CF24", "CDW1",
                 "CNHK", "CARI", "EVT3", "EVT4", "EVT5", "EVT6", "C3", "C2" ,"CTVC"]

# XMLTV 根节点
tv = ET.Element("tv", {"generator-info-name": "myTV SUPER EPG", "source-info-name": "myTV SUPER"})

# 计算最近三天
today = datetime.today()
dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]

# 遍历每个频道和日期，获取 EPG 数据
for network_code in network_codes:
    for date in dates:
        url = f"https://content-api.mytvsuper.com/v1/epg?platform=web&country_code=HK&network_code={network_code}&from={date}&to={date}"
        headers = {"accept": "application/json"}

        print(f"📡 请求频道 {network_code} 日期 {date} 的 EPG 数据...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            continue  # 跳过错误的请求

        try:
            epg_data = response.json()
            print(f"✅ 成功获取 {network_code} - {date} 的数据")

            # API 数据结构校验
            if not isinstance(epg_data, list) or len(epg_data) == 0:
                print(f"⚠️ API 返回格式错误: {epg_data}")
                continue

            # 解析 "item" 内的 "epg" 列表
            epg_list = []
            for item in epg_data:
                if "item" in item and isinstance(item["item"], list):
                    for epg_item in item["item"]:
                        if "epg" in epg_item and isinstance(epg_item["epg"], list):
                            epg_list.extend(epg_item["epg"])

            if not epg_list:
                print(f"⚠️ {network_code} 在 {date} 没有有效节目数据")
                continue

            # 添加频道信息（只添加一次）
            if not any(channel.get("id") == network_code for channel in tv.findall("channel")):
                channel = ET.Element("channel", {"id": network_code})
                display_name = ET.SubElement(channel, "display-name")
                display_name.text = clean_text(network_code)
                tv.append(channel)

            # 处理节目数据
            for i in range(len(epg_list)):
                program = epg_list[i]
                start_time = program.get("start_datetime")
                title_tc = clean_text(program.get("programme_title_tc", "未知節目"))
                desc_tc = clean_text(program.get("episode_synopsis_tc", ""))

                # 过滤无效数据
                if not start_time or title_tc == "暫時未有節目播映":
                    continue  # 跳过无效节目

                # 解析开始时间
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                start_time_xml = start_dt.strftime("%Y%m%d%H%M%S") + " +0800"

                # 计算结束时间（使用下一个节目的 `start_time`）
                if i + 1 < len(epg_list):
                    next_start_time = epg_list[i + 1].get("start_datetime")
                    if next_start_time:
                        end_dt = datetime.strptime(next_start_time, "%Y-%m-%d %H:%M:%S")
                    else:
                        end_dt = start_dt + timedelta(minutes=30)  # 默认 30 分钟
                else:
                    end_dt = start_dt + timedelta(minutes=30)  # 默认 30 分钟

                stop_time_xml = end_dt.strftime("%Y%m%d%H%M%S") + " +0800"

                # Debug: 输出每个节目详情
                print(f"📺 解析节目: {title_tc} ({start_time_xml} - {stop_time_xml})")

                # 创建 XML 结构
                programme = ET.Element("programme", {"start": start_time_xml, "stop": stop_time_xml, "channel": network_code})
                title_elem = ET.SubElement(programme, "title", {"lang": "zh"})
                title_elem.text = title_tc
                desc_elem = ET.SubElement(programme, "desc", {"lang": "zh"})
                desc_elem.text = desc_tc

                tv.append(programme)

        except Exception as e:
            print(f"❌ 解析 {network_code} {date} EPG 时发生错误: {e}")

# 生成 XMLTV 文件
tree = ET.ElementTree(tv)
with open("mytvsuper.xml", "wb") as f:
    tree.write(f, encoding="utf-8", xml_declaration=True)

print("✅ TVB EPG 已保存为 mytvsuper.xml")
