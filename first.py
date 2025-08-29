import requests
from bs4 import BeautifulSoup
from datetime import datetime

def parse_weather_forecast(soup):
    """
    從 BeautifulSoup 物件中解析天氣預報資料。
    
    回傳:
        dict: 日期對應到該日各時間點的資料，每個時間點包含「time」與「降雨機率」。
    """
    weather_data = {}
    
    # 解析日期：找到所有 headers 為 "PC3_D" 的 <th> 元素，
    # 並利用 colspan 屬性表示該日期所涵蓋的時間數量。
    date_elements = soup.find_all('th', headers="PC3_D")
    dates = {}
    for date_raw in date_elements:
        colspan = int(date_raw.get('colspan', 1))  # 若無 colspan 則預設為 1
        date_text = date_raw.get_text(strip=True)
        dates[date_text] = colspan

    # 解析時間：找到所有 headers 中含有 "PC3_Ti" 的 <th> 元素，
    # 並抽取其文字作為各時間點的標示。
    time_elements = soup.find_all('th', {'headers': lambda x: x and 'PC3_Ti' in x.split()})
    times = [time_elem.get_text() for time_elem in time_elements]

    # 根據每個日期的 colspan 將時間指派到各日期
    time_index = 0
    for date, col in dates.items():
        weather_data[date] = []
        for _ in range(col):
            weather_data[date].append({'time': times[time_index]})
            time_index += 1

    # 解析降雨機率：找到所有 headers 中含有 "PC3_Po" 的 <td> 元素，
    # 並根據 colspan 重複降雨數值。
    pre_elements = soup.find_all('td', {'headers': lambda x: x and 'PC3_Po' in x.split()})
    precipitation_values = []
    for pre_elem in pre_elements:
        percent = pre_elem.get_text()
        colspan = int(pre_elem.get('colspan', 1))
        for _ in range(colspan):
            precipitation_values.append(percent)

    # 將降雨機率依序對應到各日期各時間點
    pre_index = 0
    for date, time_list in weather_data.items():
        for item in time_list:
            item["降雨機率"] = precipitation_values[pre_index]
            pre_index += 1

    # 解析天氣：找到所有 headers 中含有 "PC3_Wx" 的 <td> 元素，
    # 並根據 colspan 重複天氣。
    wx_elements = soup.find_all('td', {'headers': lambda x: x and 'PC3_Wx' in x.split()})
    wx_values = []
    for wx_elem in wx_elements:
        img_tag = wx_elem.find('img')
        if img_tag and 'title' in img_tag.attrs:
            weather = img_tag['title']
        else:
            weather = "無"
        # print(weather)
        colspan = int(wx_elem.get('colspan', 1))
        for _ in range(colspan):
            wx_values.append(weather)

    # 將天氣依序對應到各日期各時間點
    wx_index = 0
    for date, time_list in weather_data.items():
        for item in time_list:
            item["天氣"] = wx_values[wx_index]
            wx_index += 1
    return weather_data

def main(stadium = "臺中洲際棒球場"):
    # 取得目前日期與時間，並依照需求建立查詢參數 T
    current_dt = datetime.now()
    T = f"{current_dt.year}{current_dt.month}{current_dt.day}{current_dt.hour}-{current_dt.minute // 10}"
    stadium_id = {
        "天母棒球場" : "K001",
        "臺北大巨蛋" : "K017",
        "新莊棒球場" : "K002",
        "桃園國際棒球場" : "K003",
        "臺中洲際棒球場" : "K005",
        "臺南市立棒球場" : "K009",
        "澄清湖棒球場" : "K010",
    }
    uid = stadium_id[stadium]
    # 建構目標 URL
    url = f"https://www.cwa.gov.tw/V8/C/L/Ballpark/MOD/3hr/{uid}_3hr_PC.html?T={T}"
    print("Request URL:", url)

    # 設定 HTTP 請求標頭，模擬瀏覽器
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0.0.0 Safari/537.36')
    }

    # 發送 GET 請求
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"無法取得資料，狀態碼：{response.status_code}")
        return

    # 解析 HTML 內容
    soup = BeautifulSoup(response.text, "html.parser")
    data = parse_weather_forecast(soup)
    print("Parsed Weather Data:")
    print(data)

if __name__ == "__main__":
    main()