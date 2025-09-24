#!/usr/bin/env python3
"""
快速Safari Cookie复用解决方案
用于从Safari提取Cookie并下载中央纪委网站内容

使用方法:
1. 在Safari中访问目标网站并通过验证
2. 运行此脚本提取Cookie
3. 使用提取的Cookie下载内容
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import argparse

class SafariCookieExtractor:
    """Safari Cookie提取器"""
    
    def __init__(self):
        self.cookie_dir = Path.home() / '.wf_safari_cookies'
        self.cookie_dir.mkdir(exist_ok=True)
        
    def extract_via_developer_tools(self):
        """通过开发者工具导出Cookie（手动方法）"""
        print("\n=== Safari Cookie手动提取步骤 ===")
        print("1. 在Safari中打开目标网站并确保已通过验证")
        print("2. 打开开发者工具 (Command+Option+I)")
        print("3. 切换到Network标签")
        print("4. 刷新页面 (Command+R)")
        print("5. 找到主文档请求（通常是第一个）")
        print("6. 右键点击 -> Copy -> Copy as cURL")
        print("7. 将复制的内容粘贴到文本编辑器")
        print("8. 找到 -H 'Cookie: ...' 这一行")
        print("9. 复制Cookie值（不包括引号）")
        print("\n请将Cookie值粘贴到下面（按Enter结束）:")
        
        cookie_string = input().strip()
        
        if cookie_string:
            self.save_cookies(cookie_string)
            print(f"✅ Cookie已保存到: {self.cookie_dir}/cookies.txt")
            return True
        else:
            print("❌ 未输入Cookie")
            return False
    
    def extract_via_applescript(self):
        """通过AppleScript自动提取Cookie"""
        print("\n正在通过AppleScript提取Cookie...")
        
        script = '''
        tell application "Safari"
            if (count of windows) = 0 then
                return "ERROR: No Safari window open"
            end if
            
            set currentURL to URL of current tab of window 1
            
            if currentURL does not contain "ccdi.gov.cn" then
                return "ERROR: Please navigate to ccdi.gov.cn first"
            end if
            
            try
                set cookieData to do JavaScript "document.cookie" in current tab of window 1
                return cookieData
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        output = result.stdout.strip()
        
        if output.startswith("ERROR:"):
            print(f"❌ {output}")
            return False
        elif output:
            self.save_cookies(output)
            print(f"✅ Cookie已自动提取并保存")
            return True
        else:
            print("❌ 无法获取Cookie，请确保Safari已打开并访问了目标网站")
            return False
    
    def save_cookies(self, cookie_string):
        """保存Cookie到文件"""
        cookie_file = self.cookie_dir / 'cookies.txt'
        with open(cookie_file, 'w') as f:
            f.write(cookie_string)
        
        # 同时保存为JSON格式
        cookies_dict = self.parse_cookie_string(cookie_string)
        json_file = self.cookie_dir / 'cookies.json'
        with open(json_file, 'w') as f:
            json.dump(cookies_dict, f, indent=2)
    
    def parse_cookie_string(self, cookie_string):
        """解析Cookie字符串为字典"""
        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        return cookies
    
    def load_cookies(self):
        """加载保存的Cookie"""
        cookie_file = self.cookie_dir / 'cookies.txt'
        if cookie_file.exists():
            return cookie_file.read_text().strip()
        return None

class CCDIDownloader:
    """中央纪委网站内容下载器"""
    
    def __init__(self, cookie_extractor):
        self.cookie_extractor = cookie_extractor
        self.output_dir = Path.cwd() / 'ccdi_downloads'
        self.output_dir.mkdir(exist_ok=True)
        
    def download_with_cookies(self, url):
        """使用Cookie下载内容"""
        cookies = self.cookie_extractor.load_cookies()
        
        if not cookies:
            print("❌ 未找到Cookie，请先提取Cookie")
            return None
        
        print(f"\n正在下载: {url}")
        
        # 准备curl命令
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        cmd = [
            'curl',
            '-s',  # 静默模式
            '-L',  # 跟随重定向
            '-H', f'Cookie: {cookies}',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: zh-CN,zh;q=0.9',
            '-H', 'Accept-Encoding: gzip, deflate, br',
            '-H', 'DNT: 1',
            '-H', 'Connection: keep-alive',
            '-H', 'Upgrade-Insecure-Requests: 1',
            '-o', temp_path,
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ 内容已下载到临时文件: {temp_path}")
            
            # 检查是否被重定向到验证页面
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'seccaptcha' in content or '验证' in content[:1000]:
                    print("⚠️ 检测到验证页面，Cookie可能已失效")
                    print("请重新在Safari中通过验证，然后重新提取Cookie")
                    return None
            
            return temp_path
        else:
            print(f"❌ 下载失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return None
    
    def convert_to_markdown(self, html_path, url):
        """使用webfetcher转换HTML为Markdown"""
        print("\n正在转换为Markdown...")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        output_file = self.output_dir / f"ccdi_{timestamp}.md"
        
        # 查找webfetcher.py
        webfetcher_paths = [
            Path.cwd() / 'webfetcher.py',
            Path.cwd().parent / 'webfetcher.py',
            Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/webfetcher.py'
        ]
        
        webfetcher = None
        for path in webfetcher_paths:
            if path.exists():
                webfetcher = path
                break
        
        if not webfetcher:
            print("❌ 未找到webfetcher.py")
            print("请确保webfetcher.py在当前目录或父目录中")
            return None
        
        # 调用webfetcher
        cmd = [
            sys.executable,
            str(webfetcher),
            f'file://{html_path}',
            '-o', str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ Markdown已生成: {output_file}")
            
            # 添加源URL信息
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Source: {url} -->\n")
                f.write(f"<!-- Downloaded: {datetime.now().isoformat()} -->\n\n")
                f.write(content)
            
            return output_file
        else:
            print(f"❌ 转换失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return None
    
    def process_url(self, url):
        """处理单个URL的完整流程"""
        # 下载内容
        html_path = self.download_with_cookies(url)
        if not html_path:
            return False
        
        # 转换为Markdown
        md_path = self.convert_to_markdown(html_path, url)
        
        # 清理临时文件
        try:
            os.unlink(html_path)
        except:
            pass
        
        return md_path is not None

def check_cookie_validity(cookie_extractor):
    """检查Cookie是否有效"""
    cookies = cookie_extractor.load_cookies()
    if not cookies:
        return False
    
    print("\n检查Cookie有效性...")
    
    # 尝试访问一个简单页面
    test_url = "https://www.ccdi.gov.cn/"
    
    cmd = [
        'curl',
        '-s',
        '-I',  # 只获取头部
        '-H', f'Cookie: {cookies}',
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        test_url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if 'HTTP/2 200' in result.stdout or 'HTTP/1.1 200' in result.stdout:
        print("✅ Cookie有效")
        return True
    elif 'HTTP/2 302' in result.stdout or 'HTTP/1.1 302' in result.stdout:
        print("⚠️ Cookie可能已失效（检测到重定向）")
        return False
    else:
        print("⚠️ 无法确定Cookie状态")
        return None

def main():
    parser = argparse.ArgumentParser(description='Safari Cookie复用工具 - 下载中央纪委网站内容')
    parser.add_argument('--extract', action='store_true', help='提取Safari Cookie')
    parser.add_argument('--auto', action='store_true', help='自动提取Cookie（使用AppleScript）')
    parser.add_argument('--check', action='store_true', help='检查Cookie有效性')
    parser.add_argument('--download', help='下载指定URL的内容')
    parser.add_argument('--batch', help='批量下载URL列表文件')
    
    args = parser.parse_args()
    
    extractor = SafariCookieExtractor()
    downloader = CCDIDownloader(extractor)
    
    # 显示欢迎信息
    print("=" * 60)
    print("Safari Cookie复用工具 - 中央纪委网站内容下载器")
    print("=" * 60)
    
    # 处理命令
    if args.extract:
        if args.auto:
            extractor.extract_via_applescript()
        else:
            extractor.extract_via_developer_tools()
    
    elif args.check:
        check_cookie_validity(extractor)
    
    elif args.download:
        # 检查Cookie
        if not extractor.load_cookies():
            print("❌ 未找到Cookie，请先运行: python quick_safari_cookie_solution.py --extract")
            sys.exit(1)
        
        # 下载内容
        success = downloader.process_url(args.download)
        if success:
            print("\n✅ 处理完成！")
        else:
            print("\n❌ 处理失败")
    
    elif args.batch:
        # 批量下载
        if not Path(args.batch).exists():
            print(f"❌ 文件不存在: {args.batch}")
            sys.exit(1)
        
        with open(args.batch, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"\n准备下载 {len(urls)} 个URL")
        
        success_count = 0
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 处理中...")
            if downloader.process_url(url):
                success_count += 1
        
        print(f"\n完成: {success_count}/{len(urls)} 个成功")
    
    else:
        # 显示使用说明
        print("\n使用步骤:")
        print("1. 在Safari中访问 https://www.ccdi.gov.cn 并通过验证")
        print("2. 提取Cookie: python quick_safari_cookie_solution.py --extract")
        print("3. 下载内容: python quick_safari_cookie_solution.py --download <URL>")
        print("\n可用命令:")
        print("  --extract       手动提取Cookie")
        print("  --extract --auto 自动提取Cookie")
        print("  --check         检查Cookie有效性")
        print("  --download URL  下载指定URL")
        print("  --batch FILE    批量下载URL列表")

if __name__ == '__main__':
    main()