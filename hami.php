<?php
error_reporting(0);
ini_set('display_errors', 0);

// **缓存文件**
$cache_file = "cache.json";

// **EPG API URL**
$epg_api_url = "https://hamivideo.hinet.net/channel/epg.do";

// **检查 `cache.json` 是否存在**
if (!file_exists($cache_file)) {
    die("❌ `cache.json` 不存在，请先运行频道抓取脚本！");
}

// **读取 `cache.json`**
$channels = json_decode(file_get_contents($cache_file), true);
if (!$channels) {
    die("❌ `cache.json` 解析失败！");
}

// **获取最近 3 天日期**
$dates = [];
for ($i = 0; $i < 3; $i++) {
    $dates[] = date("Y-m-d", strtotime("+$i days"));
}

// **EPG 数据数组**
$epg_data = [];

// **批量获取 EPG**
foreach ($channels as $channel) {
    $channel_id = $channel['id'];
    $channel_name = $channel['name'];

    foreach ($dates as $date) {
        $post_data = http_build_query([
            "contentPk" => $channel_id,
            "date" => $date
        ]);

        // **cURL 请求**
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $epg_api_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            "Content-Type: application/x-www-form-urlencoded; charset=UTF-8"
        ]);
        $response = curl_exec($ch);
        curl_close($ch);

        // **解析 JSON**
        $epg_list = json_decode($response, true);
        if (!$epg_list) {
            continue;
        }

        // **存入 EPG 数据**
        foreach ($epg_list as $program) {
            $epg_data[] = [
                "channel" => $channel_id,
                "name" => $channel_name,
                "title" => $program["programName"],
                "start" => date("YmdHis O", $program["startTime"]),
                "end" => date("YmdHis O", $program["endTime"])
            ];
        }
    }
}

// **生成 `XMLTV`**
$xml = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><tv></tv>');
$xml->addAttribute("generator-info-name", "HamiVideo EPG");

// **添加频道信息**
foreach ($channels as $channel) {
    $channel_element = $xml->addChild("channel");
    $channel_element->addAttribute("id", $channel['id']);
    $channel_element->addChild("display-name", htmlspecialchars($channel['name']));
    $channel_element->addChild("icon")->addAttribute("src", $channel['logo']);
}

// **添加 EPG 节目信息**
foreach ($epg_data as $program) {
    $programme = $xml->addChild("programme");
    $programme->addAttribute("start", $program["start"]);
    $programme->addAttribute("stop", $program["end"]);
    $programme->addAttribute("channel", $program["channel"]);
    $programme->addChild("title", htmlspecialchars($program["title"]));
}

// **保存 `XMLTV`**
$xml->asXML("hami_epg.xml");

echo "✅ `hami_epg.xml` 生成成功！";
?>
