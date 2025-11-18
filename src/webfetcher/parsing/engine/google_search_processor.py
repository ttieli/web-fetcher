"""
Google Search Results Post-Processor
专门处理Google搜索结果的后处理器，提取结构化数据并格式化输出
"""

import re
import urllib.parse
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Any


class GoogleSearchProcessor:
    """Google搜索结果专用处理器"""

    def __init__(self):
        """初始化处理器"""
        pass

    def process_html(self, html: str, url: str) -> str:
        """
        处理Google搜索结果HTML，提取结构化数据

        Args:
            html: 原始HTML内容
            url: 页面URL

        Returns:
            格式化后的Markdown内容
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 提取结构化数据
        results = {
            'knowledge_panel': self._extract_knowledge_panel(soup),
            'ai_overview': self._extract_ai_overview(soup),
            'images': self._extract_images(soup),
            'related_questions': self._extract_related_questions(soup),
            'web_results': self._extract_web_results(soup),
            'videos': self._extract_videos(soup),
            'news': self._extract_news(soup),
            'related_searches': self._extract_related_searches(soup),
        }

        # 生成格式化的Markdown
        return self._format_markdown(results, url)

    def _extract_knowledge_panel(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取知识面板"""
        # Google知识面板通常在右侧
        panel = soup.find('div', class_='kp-wholepage') or soup.find('div', {'data-attrid': True})

        if not panel:
            return None

        knowledge = {
            'title': None,
            'subtitle': None,
            'description': None,
            'facts': []
        }

        # 提取标题
        title_elem = panel.find('h2') or panel.find('span', class_='qrShPb')
        if title_elem:
            knowledge['title'] = title_elem.get_text(strip=True)

        # 提取描述
        desc_elem = panel.find('div', class_='kno-rdesc') or panel.find('span', class_='hb8SAc')
        if desc_elem:
            knowledge['description'] = desc_elem.get_text(strip=True)

        return knowledge if knowledge['title'] else None

    def _extract_ai_overview(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取AI概览"""
        # AI概览通常包含data-sgrd或特定class
        ai_container = soup.find('div', {'data-sgrd': True}) or soup.find('div', class_='ymu2H')

        if not ai_container:
            return None

        overview = {
            'summary': None,
            'points': []
        }

        # 提取摘要文本
        summary_elem = ai_container.find('div', recursive=False)
        if summary_elem:
            # 获取主要文本，排除链接
            text_parts = []
            for elem in summary_elem.descendants:
                if isinstance(elem, str) and elem.strip():
                    text_parts.append(elem.strip())
            overview['summary'] = ' '.join(text_parts[:3]) if text_parts else None

        # 提取要点列表
        for li in ai_container.find_all('li'):
            point_text = li.get_text(strip=True)
            if point_text and len(point_text) > 10:  # 过滤太短的内容
                # 清理URL编码的文本
                if '#:~:text=' not in point_text and 'http' not in point_text[:20]:
                    overview['points'].append(point_text[:200])  # 限制长度

        return overview if (overview['summary'] or overview['points']) else None

    def _extract_related_questions(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """提取相关问题 (People Also Ask)"""
        questions = []

        # 查找相关问题容器
        question_containers = soup.find_all('div', {'jsname': True, 'data-q': True})

        for container in question_containers[:5]:  # 限制数量
            question = container.get('data-q', '')
            if not question:
                continue

            # 提取答案
            answer_elem = container.find('div', {'data-attrid': True}) or container.find('span')
            answer = ''

            if answer_elem:
                answer = answer_elem.get_text(strip=True)
                # 限制答案长度
                if len(answer) > 300:
                    answer = answer[:297] + '...'

            if question:
                questions.append({
                    'question': question,
                    'answer': answer
                })

        return questions

    def _extract_web_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取网页搜索结果 - 使用更通用的方法"""
        results = []

        # 方法1: 查找所有包含h3标题的链接（这是Google搜索结果的通用特征）
        # 查找所有h3标题
        h3_elements = soup.find_all('h3')

        for h3 in h3_elements[:20]:  # 限制结果数量
            result = {
                'title': None,
                'url': None,
                'snippet': None,
                'source': None
            }

            # 获取标题文本
            result['title'] = h3.get_text(strip=True)

            # 查找父级链接
            parent_a = h3.find_parent('a')
            if parent_a and parent_a.get('href'):
                url = parent_a['href']
                # 清理Google重定向和相对路径
                if url.startswith('/url?'):
                    match = re.search(r'[?&]url=([^&]+)', url)
                    if match:
                        url = match.group(1)
                elif url.startswith('/search') or url.startswith('/webhp'):
                    # 跳过Google内部链接
                    continue
                result['url'] = url

            # 尝试在h3附近找到描述文本和来源
            # 获取h3所在的最近几层父级容器
            parent_div = h3.find_parent('div')

            if parent_div:
                # 提取cite（来源URL显示）
                cite = parent_div.find('cite')
                if cite:
                    result['source'] = cite.get_text(strip=True)

                # 提取snippet - 使用更简单的方法
                # 获取父容器的所有文本，然后移除已知的部分
                full_text = parent_div.get_text(separator=' ', strip=True)

                # 移除标题部分
                text_without_title = full_text.replace(result['title'], '')

                # 移除来源URL部分（所有出现）
                if result.get('source'):
                    # 移除所有出现的source
                    while result['source'] in text_without_title:
                        text_without_title = text_without_title.replace(result['source'], '')

                # 移除URL本身（如果它出现在文本中）
                if result.get('url'):
                    text_without_title = text_without_title.replace(result['url'], '')

                # 移除常见的无用前缀
                for prefix in ['·', '› ', '转为简体网页', '翻译此页', '...']:
                    text_without_title = text_without_title.replace(prefix, '')

                # 清理多余空格和特殊字符
                text_without_title = ' '.join(text_without_title.split())
                text_without_title = text_without_title.strip()

                # 如果清理后的文本长度合理，则作为snippet
                if 10 < len(text_without_title) < 1000:
                    # 限制长度
                    result['snippet'] = text_without_title if len(text_without_title) <= 400 else text_without_title[:397] + '...'

            # 只添加有效结果（必须有标题和URL）
            if result['title'] and result['url'] and len(result['title']) > 3:
                # 去重检查
                if not any(r['url'] == result['url'] for r in results):
                    results.append(result)

        return results

    def _extract_videos(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取视频结果"""
        videos = []

        # 查找视频容器
        video_containers = soup.find_all('div', {'data-ved': True, 'data-md': True})

        for container in video_containers[:5]:
            video = {
                'title': None,
                'url': None,
                'source': None,
                'duration': None
            }

            # 提取标题
            title_elem = container.find('h3') or container.find('div', role='heading')
            if title_elem:
                video['title'] = title_elem.get_text(strip=True)

            # 提取URL
            link = container.find('a', href=True)
            if link:
                video['url'] = link['href']

            # 提取来源
            source_elem = container.find('cite') or container.find('span', class_='Zu0yb')
            if source_elem:
                video['source'] = source_elem.get_text(strip=True)

            if video['title'] and video['url']:
                videos.append(video)

        return videos

    def _extract_news(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取新闻结果"""
        news_items = []

        # 查找新闻容器
        news_containers = soup.find_all('div', {'role': 'heading'})

        for container in news_containers[:5]:
            news = {
                'title': None,
                'url': None,
                'source': None,
                'time': None
            }

            # 提取标题
            news['title'] = container.get_text(strip=True)

            # 提取URL
            parent_div = container.find_parent('div')
            if parent_div:
                link = parent_div.find('a', href=True)
                if link:
                    news['url'] = link['href']

            # 提取时间
            time_elem = parent_div.find('span', class_='OSrXXb') if parent_div else None
            if time_elem:
                news['time'] = time_elem.get_text(strip=True)

            if news['title'] and news['url']:
                news_items.append(news)

        return news_items

    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取图片搜索结果"""
        images = []

        # 方法1: 查找带有图片链接的容器 (/imgres? 链接)
        img_containers = soup.find_all('a', href=lambda x: x and '/imgres?' in x if x else False)

        for container in img_containers[:6]:  # 限制数量
            image = {
                'title': None,
                'url': None,
                'source': None,
                'thumbnail': None
            }

            # 提取缩略图URL
            img_tag = container.find('img')
            if img_tag:
                # 获取src或data-src
                image['thumbnail'] = img_tag.get('src') or img_tag.get('data-src')
                # 获取alt作为标题
                image['title'] = img_tag.get('alt', '')

            # 提取原图URL - 从href参数中解析
            href = container.get('href', '')
            if '/imgres?' in href:
                # 解析imgurl参数
                params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                if 'imgurl' in params:
                    image['url'] = params['imgurl'][0]
                if 'imgrefurl' in params:
                    image['source'] = params['imgrefurl'][0]

            # 只添加有效图片
            if image['thumbnail'] and (image['url'] or image['title']):
                images.append(image)

        # 方法2: 如果方法1没找到，尝试查找所有图片（但过滤掉logo等）
        if not images:
            all_images = soup.find_all('img')
            for img in all_images[:10]:  # 只查看前10个
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '')

                # 过滤条件：有src，有alt，不是logo或图标
                if (src and alt and
                    len(alt) > 5 and  # alt文本足够长
                    not any(x in src.lower() for x in ['logo', 'icon', 'sprite', 'button'])):

                    image = {
                        'title': alt,
                        'thumbnail': src,
                        'url': None,
                        'source': None
                    }
                    images.append(image)
                    if len(images) >= 3:  # 限制数量
                        break

        return images

    def _extract_related_searches(self, soup: BeautifulSoup) -> List[str]:
        """提取相关搜索建议 (用户还搜索了)"""
        related = []
        seen = set()

        # 方法1: 查找特定的"相关搜索"容器
        # Google通常在页面底部有 "Searches related to..." 或类似的容器
        related_section = soup.find('div', text=re.compile(r'(Related searches|相关搜索|Searches related to)'))
        if related_section:
            parent = related_section.find_parent('div')
            if parent:
                # 在这个容器中查找所有搜索链接
                links = parent.find_all('a', href=lambda x: x and '/search?q=' in x if x else False)
                for link in links[:10]:
                    text = link.get_text(strip=True)
                    if text and 2 < len(text) < 50 and text not in seen:
                        related.append(text)
                        seen.add(text)

        # 方法2: 查找所有搜索链接，过滤出可能是相关搜索的
        if not related:
            search_links = soup.find_all('a', href=lambda x: x and '/search?q=' in x if x else False)

            for link in search_links:
                # 获取链接文本
                text = link.get_text(strip=True)

                # 过滤条件：
                # 1. 文本不为空
                # 2. 长度合理（2-50字符）
                # 3. 不包含特殊字符、URL或导航文本
                # 4. 未见过
                # 5. 不是当前搜索页面的主要导航（如"全部"、"图片"等）
                nav_keywords = ['全部', '图片', '视频', '新闻', '购物', 'All', 'Images', 'Videos', 'News', 'Shopping']

                if (text and
                    2 < len(text) < 50 and
                    not any(char in text for char in ['http', '›', '...', '▸', '|']) and
                    text not in nav_keywords and
                    text not in seen):

                    # 优先使用href中的q参数
                    href = link.get('href', '')
                    if '/search?q=' in href:
                        try:
                            parsed = urllib.parse.urlparse(href)
                            params = urllib.parse.parse_qs(parsed.query)

                            if 'q' in params:
                                query = params['q'][0]
                                if 2 < len(query) < 50 and query not in seen:
                                    related.append(query)
                                    seen.add(query)
                            elif text:
                                related.append(text)
                                seen.add(text)
                        except:
                            # 解析失败，使用文本
                            if text and text not in seen:
                                related.append(text)
                                seen.add(text)

                    # 限制数量
                    if len(related) >= 10:
                        break

        return related[:10]  # 返回最多10个

    def _format_markdown(self, results: Dict[str, Any], url: str) -> str:
        """将提取的结构化数据格式化为Markdown"""
        md_parts = []

        # 知识面板
        if results.get('knowledge_panel'):
            kp = results['knowledge_panel']
            md_parts.append('## 📊 知识面板\n')
            if kp['title']:
                md_parts.append(f"**{kp['title']}**\n")
            if kp['description']:
                md_parts.append(f"{kp['description']}\n")
            md_parts.append('')

        # AI概览
        if results.get('ai_overview'):
            ai = results['ai_overview']
            md_parts.append('## 🤖 AI 概览\n')
            if ai['summary']:
                md_parts.append(f"{ai['summary']}\n")
            if ai['points']:
                md_parts.append('\n**关键点：**\n')
                for point in ai['points'][:5]:
                    md_parts.append(f"- {point}")
            md_parts.append('')

        # 图片结果
        if results.get('images'):
            md_parts.append('## 📸 图片\n')
            for i, img in enumerate(results['images'], 1):
                if img.get('title'):
                    md_parts.append(f"**{i}. {img['title']}**\n")
                else:
                    md_parts.append(f"**{i}. 图片**\n")

                # 显示缩略图（Markdown图片格式）
                if img.get('thumbnail'):
                    title_text = img.get('title', '图片')
                    md_parts.append(f"![{title_text}]({img['thumbnail']})\n")

                # 显示来源链接
                if img.get('source'):
                    md_parts.append(f"- 来源: <{img['source']}>\n")
                elif img.get('url'):
                    md_parts.append(f"- 原图: <{img['url']}>\n")

                md_parts.append('')

        # 相关问题
        if results.get('related_questions'):
            md_parts.append('## ❓ 相关问题\n')
            for qa in results['related_questions']:
                md_parts.append(f"### {qa['question']}\n")
                if qa['answer']:
                    md_parts.append(f"{qa['answer']}\n")
            md_parts.append('')

        # 网页搜索结果
        if results.get('web_results'):
            md_parts.append('## 🔍 搜索结果\n')
            for i, result in enumerate(results['web_results'], 1):
                md_parts.append(f"### {i}. {result['title']}\n")

                # 格式化来源为超链接
                if result.get('source'):
                    md_parts.append(f"**来源:** [{result['source']}]({result['url']})\n")

                # 格式化链接为超链接（使用尖括号格式自动生成链接）
                md_parts.append(f"**链接:** <{result['url']}>\n")

                # 只显示有意义的snippet（过滤掉重复和无用内容）
                if result.get('snippet'):
                    snippet = result['snippet'].strip()
                    # 过滤太短或重复的snippet
                    if len(snippet) > 20 and snippet not in [result['title'], result.get('source', '')]:
                        md_parts.append(f"\n{snippet}\n")

                md_parts.append('')

        # 视频结果
        if results.get('videos'):
            md_parts.append('## 🎬 视频\n')
            for video in results['videos']:
                md_parts.append(f"- **{video['title']}**")
                md_parts.append(f"  - 链接: {video['url']}")
                if video.get('source'):
                    md_parts.append(f"  - 来源: {video['source']}")
                md_parts.append('')

        # 新闻结果
        if results.get('news'):
            md_parts.append('## 📰 新闻\n')
            for news in results['news']:
                md_parts.append(f"- **{news['title']}**")
                md_parts.append(f"  - {news['url']}")
                if news.get('time'):
                    md_parts.append(f"  - {news['time']}")
                md_parts.append('')

        # 相关搜索建议
        if results.get('related_searches'):
            md_parts.append('## 🔗 相关搜索\n')
            md_parts.append('**用户还搜索了：**\n')
            for search in results['related_searches']:
                # 创建搜索链接
                encoded = urllib.parse.quote(search)
                search_url = f"https://www.google.com/search?q={encoded}"
                md_parts.append(f"- [{search}]({search_url})")
            md_parts.append('')

        return '\n'.join(md_parts)


def process_google_search(html: str, url: str) -> str:
    """
    处理Google搜索结果的入口函数

    Args:
        html: HTML内容
        url: 页面URL

    Returns:
        格式化后的Markdown
    """
    processor = GoogleSearchProcessor()
    return processor.process_html(html, url)
