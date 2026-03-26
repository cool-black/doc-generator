"""测试 scrapling 库"""
import ssl
import urllib3
urllib3.disable_warnings()

# 尝试修复 SSL
import os
os.environ['SSL_CERT_FILE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

from scrapling import Fetcher

# 测试1: 基本页面获取
print("=== 测试1: 获取简单页面 ===")
fetcher = Fetcher()

try:
    page = fetcher.get("https://example.com", verify=False)
    print(f"状态码: {page.status}")
    print(f"标题: {page.css_first('title::text')}")
    print(f"内容预览: {page.text[:200]}...")
except Exception as e:
    print(f"第一个URL失败: {e}")

    # 尝试另一个URL
    try:
        page = fetcher.get("http://httpbin.org/html", verify=False)
        print(f"状态码: {page.status}")
        print(f"内容预览: {page.text[:200]}...")
    except Exception as e2:
        print(f"第二个URL也失败: {e2}")

# 测试2: CSS选择器
print("\n=== 测试2: CSS选择器 ===")
try:
    page = fetcher.get("https://example.com", verify=False)
    links = page.css('a')
    print(f"链接数量: {len(links)}")
    for link in links[:3]:
        print(f"  - {link.attrib.get('href', '')}: {link.text}")
except Exception as e:
    print(f"CSS选择器测试失败: {e}")

# 测试3: XPath选择器
print("\n=== 测试3: XPath选择器 ===")
try:
    page = fetcher.get("https://example.com", verify=False)
    title = page.xpath_first('//title/text()')
    print(f"XPath提取的标题: {title}")
except Exception as e:
    print(f"XPath测试失败: {e}")

print("\n=== scrapling 测试完成 ===")
