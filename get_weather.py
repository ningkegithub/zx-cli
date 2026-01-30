#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

def get_shenzhen_weather():
    url = "https://www.weather.com.cn/weather/101280601.shtml"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试查找今天的天气信息
        # 方法1：查找包含"今天"或"今日"的天气信息
        today_weather = None
        
        # 查找天气详情
        weather_divs = soup.find_all('div', class_=re.compile(r'weather|tianqi|forecast'))
        
        for div in weather_divs:
            text = div.get_text(strip=True)
            if '深圳' in text and ('今天' in text or '今日' in text or '1天' in text):
                today_weather = text
                break
        
        # 方法2：查找温度信息
        if not today_weather:
            temp_spans = soup.find_all('span', class_=re.compile(r'temp|tem|temperature'))
            for span in temp_spans:
                text = span.get_text(strip=True)
                if '°C' in text or '℃' in text or re.search(r'\d+[°℃]', text):
                    parent_text = span.parent.get_text(strip=True) if span.parent else ""
                    if '深圳' in parent_text or not today_weather:
                        today_weather = f"温度: {text}"
        
        # 方法3：查找天气描述
        if not today_weather:
            weather_desc = soup.find_all(string=re.compile(r'晴|阴|雨|多云|雾|雪'))
            if weather_desc:
                today_weather = f"天气: {weather_desc[0]}"
        
        if today_weather:
            return f"深圳今天的天气信息：{today_weather}"
        else:
            # 返回页面标题作为基本信息
            title = soup.title.string if soup.title else "未知"
            return f"深圳天气页面标题：{title}\n（具体天气信息解析失败，建议直接访问：{url}）"
            
    except Exception as e:
        return f"获取天气信息时出错：{str(e)}"

if __name__ == "__main__":
    print(get_shenzhen_weather())