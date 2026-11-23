# -*- coding: utf-8 -*-
"""Automatic, provenance-preserving preparation of collected news for research."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from collections import Counter
import hashlib, re
from urllib.parse import urlsplit, urlunsplit

WINDOWS_HOURS = {
    "آخر 6 ساعات": 6, "آخر 12 ساعة": 12, "آخر 24 ساعة": 24,
    "آخر يومين": 48, "آخر 3 أيام": 72, "آخر 5 أيام": 120,
    "آخر 7 أيام": 168, "آخر 14 يوماً": 336, "آخر 30 يوماً": 720,
}

def utc_dt(value):
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value or '').strip()
        if not raw: return None
        try:
            if re.fullmatch(r'\d{8}T\d{6}Z', raw):
                dt = datetime.strptime(raw, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            else:
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def window_bounds(hours, *, now=None):
    end = utc_dt(now) or datetime.now(timezone.utc)
    return end - timedelta(hours=float(hours)), end

def in_window(item, start, end):
    dt = utc_dt(item.get('seendate') or item.get('published_at') or item.get('date'))
    return dt is None or (start <= dt <= end)

def filter_window(items, hours, *, now=None):
    start, end = window_bounds(hours, now=now)
    # Keep undated results but label them, rather than silently discarding them.
    out=[]
    for item in items or []:
        row=dict(item)
        dt=utc_dt(row.get('seendate') or row.get('published_at') or row.get('date'))
        if dt is None:
            row['date_window_status']='unknown_date'
            out.append(row)
        elif start <= dt <= end:
            row['date_window_status']='within_window'
            out.append(row)
    return out

def canonical_url(url):
    try:
        p=urlsplit(str(url or '').strip())
        return urlunsplit((p.scheme.lower(),p.netloc.lower().removeprefix('www.'),p.path.rstrip('/'),'', ''))
    except Exception: return str(url or '').strip()

def _terms(text):
    return {x for x in re.findall(r'[\w\u0600-\u06ff]{3,}', str(text or '').lower()) if x not in {'the','and','for','with','من','في','على','الى','عن','هذا','هذه','بعد','قبل'}}

def cluster_items(items, *, threshold=2):
    """Conservative lexical clusters; labels are candidates, never factual conclusions."""
    clusters=[]
    for item in items or []:
        title=item.get('title_ar') or item.get('title') or ''
        tokens=_terms(title)
        best=None; score=0
        for c in clusters:
            overlap=len(tokens & c['_tokens'])
            if overlap>score: best,score=c,overlap
        if best is not None and score>=threshold:
            best['items'].append(item); best['_tokens'] |= tokens
        else:
            clusters.append({'id':hashlib.sha256((title+str(len(clusters))).encode()).hexdigest()[:12],
                'label':title[:140] or 'خيط إخباري غير معنّون','items':[item],'_tokens':tokens})
    result=[]
    for c in clusters:
        rows=c.pop('_tokens')
        c['count']=len(c['items'])
        c['domains']=sorted({x.get('domain','') for x in c['items'] if x.get('domain')})
        c['source_ids']=[hashlib.sha256((canonical_url(x.get('url')) or x.get('title','')).encode()).hexdigest()[:16] for x in c['items']]
        result.append(c)
    return sorted(result,key=lambda x:x['count'],reverse=True)

def prepare_cards(items, translate_text=None):
    """Make an honest Arabic card summary from available snippet/description only."""
    rows=list(items or [])
    pending=[]; indexes=[]
    for i,row in enumerate(rows):
        snippet=str(row.get('summary') or row.get('description') or row.get('snippet') or row.get('content') or '').strip()
        if snippet and not row.get('summary_ar'):
            pending.append(snippet[:1200]); indexes.append(i)
        elif not snippet:
            row.setdefault('summary_ar','ملخص غير متاح: المصدر لم يوفّر مقتطفاً كافياً. افتح صفحة المقال لمحاولة استخراج النص.')
            row.setdefault('summary_status','missing_snippet')
    if pending and callable(translate_text):
        try: translated=translate_text(pending)
        except Exception: translated=[]
        if not isinstance(translated,(list,tuple)): translated=[]
        for j,idx in enumerate(indexes):
            val=str(translated[j] if j<len(translated) else '').strip()
            if val and val != pending[j]:
                rows[idx]['summary_ar']=val
                rows[idx]['summary_status']='translated_snippet'
            else:
                rows[idx]['summary_ar']='المقتطف متاح، لكن تعذّرت ترجمته حالياً.'
                rows[idx]['summary_status']='translation_failed'
    elif pending:
        for idx in indexes:
            rows[idx]['summary_ar']='المقتطف متاح، والترجمة لم تُنفّذ في هذه المرحلة.'
            rows[idx]['summary_status']='translation_pending'
    for row in rows:
        row.setdefault('summary_status','missing_snippet')
        row['publisher']=row.get('outlet') or row.get('publisher') or row.get('domain') or 'غير محدد'
        row['metadata_completeness']={k:bool(row.get(k)) for k in ('publisher','writer','seendate','url','language')}
    return rows

def build_research_bundle(title, items):
    """Ready-to-run prompt bundle built automatically from collected search results."""
    from research_batches import create_batch
    safe=[dict(x) for x in (items or []) if isinstance(x,dict) and (x.get('url') or x.get('title'))]
    return create_batch(title or 'بحث إخباري تلقائي',safe,batch_size=8,
        instructions='هذه مواد جُمعت آلياً من نتائج البحث. راجع استقلالية المصادر، ولا تعتبر التشابه تأكيداً مستقلاً. ميّز تاريخ النشر عن تاريخ الحدث، واذكر أي نقص في النص أو الترجمة.')
