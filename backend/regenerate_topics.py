"""Regenerate topic suggestion doc with URLs for each reference material."""
import sys, json, re
sys.path.insert(0, '.')
from datetime import date
from app.database import SessionLocal
from app.models import Article
from app.services.feishu_service import append_to_doc, clear_doc, _h1, _h2, _p, _rich, _empty
from app.services.ai_client import chat
from app.config import settings

db = SessionLocal()
bookmarks = db.query(Article).filter(
    Article.is_bookmarked == True, Article.relevance_score >= 7
).order_by(Article.publish_date.desc()).all()
print(f'Bookmarks: {len(bookmarks)}')

all_articles_text = '\n\n'.join([
    f'[{i+1}] {a.title}\n链接: {a.url or "无"}\n摘要: {a.summary_cn or (a.content_preview or "")[:150]}\n标签: {", ".join(a.tags or [])}'
    for i, a in enumerate(bookmarks)
])

topic_prompt = f"""你是资深技术编辑。基于以下收藏的技术文章，推荐 5-8 个公众号文章选题。

对每个选题，输出：
- title: 吸引人的标题（15-25字，要有悬念或明确判断）
- thesis: 文章核心观点（一句话说清楚要论证什么）
- materials: 使用哪些素材编号（如 [1, 3, 5]）
- angle: 写作角度（从什么切入点展开论述）

素材：
{all_articles_text[:4000]}

返回 JSON: {{"topics": [{{"title": "...", "thesis": "...", "materials": [1,2], "angle": "..."}}]}}"""

topic_result = chat(topic_prompt, "You are a senior tech editor. Always reply with valid JSON only.")

# Extract JSON
m = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', topic_result, re.DOTALL)
if m:
    topic_result = m.group(1)
try:
    topics_data = json.loads(topic_result)
    topics = topics_data if isinstance(topics_data, list) else topics_data.get('topics', [])
except json.JSONDecodeError:
    topics = []

print(f'Topics generated: {len(topics)}')

topic_blocks = [
    _h1('公众号选题推荐'),
    _p(f'基于 {len(bookmarks)} 篇收藏文章生成以下选题（{date.today().isoformat()} 更新）：'),
    _empty(),
]

for i, t in enumerate(topics[:8], 1):
    topic_blocks.append(_h2(f'选题 {i}：{t.get("title", "")}'))
    topic_blocks.append(_p(f'核心观点：{t.get("thesis", "")}'))
    materials = t.get('materials', [])
    if materials:
        topic_blocks.append(_p('参考素材：'))
        for m_id in materials:
            if isinstance(m_id, int) and 1 <= m_id <= len(bookmarks):
                bm = bookmarks[m_id - 1]
                topic_blocks.append(_h2(f'[{m_id}] {bm.title[:60]}'))
                if bm.url:
                    topic_blocks.append(_rich([
                        {'text_run': {'content': '链接：', 'text_element_style': {'bold': True}}},
                        {'text_run': {'content': bm.url or '', 'text_element_style': {'link': {'url': bm.url or ''}}}},
                    ]))
                if bm.summary_cn:
                    topic_blocks.append(_p(f'摘要：{bm.summary_cn[:150]}'))
    topic_blocks.append(_p(f'写作角度：{t.get("angle", "")}'))
    topic_blocks.append(_empty())

doc_id = settings.feishu_topic_doc_id
if doc_id:
    clear_doc(doc_id)
    info = append_to_doc(doc_id, topic_blocks)
    print(f'Topic doc updated: {info["url"]}')
else:
    print('No topic doc ID configured')

db.close()
