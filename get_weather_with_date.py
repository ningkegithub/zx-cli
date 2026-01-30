#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def get_shenzhen_weather_with_details():
    try:
        # 尝试从中国天气网获取深圳天气
        url = "http://www.weather.com.cn/weather/101280601.shtml"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print("正在获取深圳天气信息...")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取系统当前日期
        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        # 查找天气信息
        weather_info = {
            'system_date': current_date,
            'source_url': url,
            'city_code': '101280601'
        }
        
        # 查找今天天气
        today_div = soup.find('div', class_='today')
        if today_div:
            # 日期
            date_elem = today_div.find('span', class_='date')
            if date_elem:
                weather_info['page_date'] = date_elem.text.strip()
            
            # 天气状况
            wea = today_div.find('p', class_='wea')
            if wea:
                weather_info['condition'] = wea.text.strip()
            
            # 温度
            tem = today_div.find('p', class_='tem')
            if tem:
                temperature = tem.text.strip().replace('\n', ' ')
                weather_info['temperature'] = temperature
            
            # 风力
            win = today_div.find('p', class_='win')
            if win:
                wind = win.text.strip().replace('\n', ' ')
                weather_info['wind'] = wind
        
        # 如果没找到，尝试其他选择器
        if not 'condition' in weather_info:
            # 查找7天天气预报中的今天
            days = soup.find_all('li', class_='sky')
            if days and len(days) > 0:
                today = days[0]
                
                # 日期
                date = today.find('h1')
                if date:
                    weather_info['page_date'] = date.text.strip()
                
                # 天气
                wea = today.find('p', class_='wea')
                if wea:
                    weather_info['condition'] = wea.text.strip()
                
                # 温度
                tem = today.find('p', class_='tem')
                if tem:
                    temperature = tem.text.strip().replace('\n', ' ')
                    weather_info['temperature'] = temperature
                
                # 风力
                win = today.find('p', class_='win')
                if win:
                    wind = win.text.strip().replace('\n', ' ')
                    weather_info['wind'] = wind
        
        return weather_info
        
    except Exception as e:
        print(f"获取天气信息时出错: {e}")
        return None

if __name__ == "__main__":
    weather = get_shenzhen_weather_with_details()
    
    if weather:
        print("\n=== 天气查询详情 ===")
        print(f"系统当前日期: {weather['system_date']}")
        print(f"数据来源URL: {weather['source_url']}")
        print(f"城市代码: {weather['city_code']}")
        
        if 'page_date' in weather:
            print(f"页面显示日期: {weather['page_date']}")
        
        print("\n=== 深圳天气信息 ===")
        if 'condition' in weather:
            print(f"天气: {weather['condition']}")
        if 'temperature' in weather:
            print(f"温度: {weather['temperature']}")
        if 'wind' in weather:
            print(f"风力: {weather['wind']}")
    else:
        print("无法获取天气信息，请稍后重试。")