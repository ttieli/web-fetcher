"""Tests for WeChat parser — guards regression bugs in templates.py wechat_to_markdown()."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from webfetcher.parsing.templates import wechat_to_markdown


def _wechat_normal_article_html(body_text: str = "这是文章正文。") -> str:
    """Minimal WeChat HTML: 正常文章（非图集）+ og:image 封面图。

    关键特征：
    - 含 #js_content 容器（标准微信文章）
    - **不**含 js_image_content（不是图集）
    - 有 og:image 封面图（任何微信文章都有）
    - **不**含 <div data-src> 和 background-image style（图集专属）
    """
    return f"""<!DOCTYPE html><html><head>
<meta property="og:image" content="https://mmbiz.qpic.cn/mmbiz_jpg/cover-image-12345/0?wx_fmt=jpeg">
<title>测试文章</title>
</head><body>
<h1 class="rich_media_title" id="activity-name">测试文章标题</h1>
<a id="js_name" class="rich_media_meta">测试作者</a>
<em id="publish_time" class="rich_media_meta">2026-05-15 11:00</em>
<div class="rich_media_content" id="js_content">
<p>{body_text}</p>
<p>这里是第二段，继续展开论述。</p>
</div>
<script>
var msg_title = '测试文章标题';
var biz = "MzY4NzA1MjUxNw==";
</script>
</body></html>"""


def test_wechat_normal_article_preserves_body():
    """回归 bug: og:image fallback 拿到封面图后，
    is_gallery 不应被错误反推为 True 导致正文被清空。

    场景：mp.weixin.qq.com/s/teDI2pT7DODpZbpKaBETKQ 实测
    - js_image_content NOT in html
    - 模板提取到 5077 字符正文
    - 但 metadata.images 为空 → fallback 拿到 og:image 封面 → 错误标记 gallery → 正文清空
    """
    html = _wechat_normal_article_html(body_text="只会用 AI 编程是没有竞争力的，还是要深度学习其中的思想。")
    date_only, md, metadata = wechat_to_markdown(html, 'https://mp.weixin.qq.com/s/teDI2pT7DODpZbpKaBETKQ')

    # 关键断言：正文必须保留（之前 bug 时会被清空）
    assert "只会用 AI 编程" in md, (
        f"正文被错误清空（is_gallery 反推 bug 回归）。"
        f"完整 markdown: {md[:300]}")
    assert "继续展开论述" in md
    # 标题/作者元数据也要正常
    assert "测试文章标题" in md


def test_wechat_real_gallery_still_gets_gallery_treatment():
    """正向：真正的图集（含 js_image_content 容器）应走 gallery 路径，
    用 <div data-src> 提取多张图，正文文本可清空。
    """
    html = """<!DOCTYPE html><html><head>
<meta property="og:image" content="https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg">
</head><body>
<h1 class="rich_media_title" id="activity-name">图集文章</h1>
<a id="js_name" class="rich_media_meta">作者</a>
<div id="js_image_content">
<div data-src="https://mmbiz.qpic.cn/img/aaa/0?wx_fmt=jpeg">slide 1</div>
<div data-src="https://mmbiz.qpic.cn/img/bbb/0?wx_fmt=jpeg">slide 2</div>
<div data-src="https://mmbiz.qpic.cn/img/ccc/0?wx_fmt=jpeg">slide 3</div>
</div>
</body></html>"""
    date_only, md, metadata = wechat_to_markdown(html, 'https://mp.weixin.qq.com/s/gallery-test')

    # 图集应提取到 3 张图（不是 og:image 那张）
    images = metadata.get('images', [])
    assert len(images) == 3, f"expected 3 gallery images, got {len(images)}: {images}"
    assert any('aaa' in img for img in images)
    assert any('bbb' in img for img in images)
    assert any('ccc' in img for img in images)


def test_wechat_no_images_no_gallery():
    """无 og:image 也无 gallery 标志的文章，images 应为空但正文保留。"""
    html = """<!DOCTYPE html><html><head><title>纯文字</title></head><body>
<h1 class="rich_media_title" id="activity-name">纯文字文章</h1>
<a id="js_name" class="rich_media_meta">作者</a>
<div class="rich_media_content" id="js_content">
<p>这是一篇纯文字文章，没有任何图片。</p>
</div>
</body></html>"""
    date_only, md, metadata = wechat_to_markdown(html, 'https://mp.weixin.qq.com/s/text-only')
    assert "纯文字文章" in md
    assert "纯文字文章，没有任何图片" in md
