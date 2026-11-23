# -*- coding: utf-8 -*-
"""Safe intake of search results into an existing research case."""
from __future__ import annotations
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


def canonical_url(url):
    try:
        p = urlsplit(str(url or '').strip())
        return urlunsplit((p.scheme.lower(), p.netloc.lower().removeprefix('www.'), p.path.rstrip('/'), '', ''))
    except Exception:
        return str(url or '').strip()


def _tokens(value):
    return {x for x in re.findall(r'[\w\u0600-\u06ff]{3,}', str(value or '').lower())
            if x not in {'the','and','for','with','من','في','على','الى','عن','هذا','هذه','حول','بعد','قبل'}}


def suggest_cases(title, tags, cases, *, limit=5):
    """Rank likely existing cases; suggestions never auto-select or merge."""
    query = _tokens(' '.join([str(title or ''), *(tags or [])]))
    ranked = []
    for case in cases or []:
        case_tokens = _tokens(' '.join([case.get('title',''), case.get('description',''), ' '.join(case.get('tags',[]))]))
        overlap = len(query & case_tokens)
        score = overlap / max(1, len(query | case_tokens))
        if overlap:
            ranked.append({'case_id': case.get('id'), 'title': case.get('title',''),
                           'overlap': overlap, 'score': round(score, 3)})
    return sorted(ranked, key=lambda x: (x['score'], x['overlap']), reverse=True)[:max(1, int(limit))]


def import_search_results(case, items, *, material_type='خبر', max_items=300):
    """Deduplicate by canonical URL, retain provenance, and return only newly added rows."""
    from casebook import add_material
    existing = {canonical_url(x.get('url')) for x in case.get('materials', []) if x.get('url')}
    added, skipped = [], 0
    for item in (items or [])[:max_items]:
        if not isinstance(item, dict):
            continue
        url = canonical_url(item.get('url') or item.get('link'))
        if url and url in existing:
            skipped += 1
            continue
        source_id = hashlib.sha256((url or str(item.get('title') or item.get('title_ar') or '')).encode('utf-8')).hexdigest()[:16]
        row = dict(item)
        row['url'] = item.get('url') or item.get('link') or ''
        row['source_id'] = source_id
        row['text'] = (item.get('text') or item.get('full_text') or item.get('summary') or
                       item.get('snip_ar') or item.get('description') or item.get('snippet') or '')
        row['date'] = item.get('date') or item.get('seendate') or item.get('published_at') or ''
        row['domain'] = item.get('domain') or item.get('source') or ''
        if add_material(case, row, material_type):
            added.append(case['materials'][-1])
            if url:
                existing.add(url)
        else:
            skipped += 1
    return {'added': added, 'skipped': skipped, 'total_seen': min(len(items or []), max_items)}


def batch_from_materials(case, materials, *, batch_size=8):
    """Create a provenance-preserving batch only from newly imported case materials."""
    if not materials:
        return None
    from research_batches import create_batch
    batch = create_batch(
        f"{case.get('title','ملف بحثي')} | تجميع تلقائي من نتائج البحث",
        materials, batch_size=batch_size,
        instructions=('مواد مستوردة من نتائج بحث محفوظة في ملف القضية. '
                      'تعامل مع العناوين والمقتطفات باعتبارها مادة محدودة، ولا تفترض قراءة المقال كاملاً. '
                      'احتفظ بمعرف المصدر والرابط، وميّز تاريخ النشر عن تاريخ الحدث، وافحص استقلالية المصادر.')
    )
    batch['case_id'] = case.get('id')
    batch['case_title'] = case.get('title', '')
    batch['origin'] = 'search_results_import'
    return batch
