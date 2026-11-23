# -*- coding: utf-8 -*-
"""Phase 8.35: evidence-linked entity co-mention network.
Edges mean co-mention in the same collected item only, never a verified relationship.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

import entity_intelligence as entity_intel


def _domain(url, explicit=''):
    if explicit:
        return str(explicit).lower().removeprefix('www.')
    try:
        from urllib.parse import urlparse
        return urlparse(str(url or '')).netloc.lower().removeprefix('www.')
    except Exception:
        return ''


def build_network(articles, cases=(), min_co_mentions=1, max_edges=250):
    """Build a conservative network from curated entity mentions in article text.

    A link is strictly a co-mention, backed by one or more article references.
    """
    nodes = {}
    edge_refs = defaultdict(dict)
    article_rows = []
    for i, article in enumerate(articles or []):
        title = article.get('title') or article.get('title_ar') or 'مادة بلا عنوان'
        text = '\n'.join([title, str(article.get('text') or article.get('summary') or '')])
        ents = entity_intel.extract_entities(text)
        unique = sorted({e['name'] for e in ents})
        url = str(article.get('url') or '')
        ref_id = hashlib.sha1((url or f'{title}:{i}').encode('utf-8')).hexdigest()[:12]
        domain = _domain(url, article.get('domain') or '')
        row = {'id': ref_id, 'title': title, 'url': url, 'domain': domain,
               'source': article.get('source_name') or article.get('source') or domain,
               'published_at': entity_intel._date(article), 'entities': unique}
        article_rows.append(row)
        for ent in ents:
            n = nodes.setdefault(ent['name'], {'id': ent['name'], 'name': ent['name'], 'type': ent['type'],
                'mention_count': 0, 'domains': set(), 'article_ids': set(), 'case_ids': set()})
            n['mention_count'] += 1
            n['article_ids'].add(ref_id)
            if domain: n['domains'].add(domain)
        for pos, a in enumerate(unique):
            for b in unique[pos+1:]:
                key = (a, b)
                edge_refs[key][ref_id] = row
    for case in cases or ():
        case_id = str(case.get('id') or '')
        case_text = ''
        try:
            import case_links
            case_text = case_links.case_text(case)
        except Exception:
            case_text = str(case)
        for ent in entity_intel.extract_entities(case_text):
            if ent['name'] in nodes and case_id:
                nodes[ent['name']]['case_ids'].add(case_id)

    node_out = []
    for node in nodes.values():
        node_out.append({**node, 'domains': sorted(node['domains']), 'article_ids': sorted(node['article_ids']),
                         'case_ids': sorted(node['case_ids']), 'article_count': len(node['article_ids']),
                         'domain_count': len(node['domains'])})
    node_out.sort(key=lambda x: (-x['mention_count'], x['name']))
    edges = []
    for (a, b), refs in edge_refs.items():
        if len(refs) < max(1, int(min_co_mentions)):
            continue
        sources = sorted({r['domain'] for r in refs.values() if r['domain']})
        edges.append({'source': a, 'target': b, 'weight': len(refs), 'article_ids': sorted(refs),
                      'source_domains': sources, 'source_count': len(sources),
                      'evidence': list(refs.values())[:20],
                      'relation_type': 'co_mentioned',
                      'caveat': 'ظهور الكيانين في المادة نفسها فقط؛ لا يثبت تحالفاً أو اتصالاً أو علاقة سببية.'})
    edges.sort(key=lambda x: (-x['weight'], x['source'], x['target']))
    truncated = max(0, len(edges) - max(1, int(max_edges)))
    edges = edges[:max(1, int(max_edges))]
    return {'nodes': node_out, 'edges': edges, 'articles': article_rows,
            'stats': {'node_count': len(node_out), 'edge_count': len(edges),
                      'candidate_edge_count': len(edge_refs), 'article_count': len(article_rows),
                      'truncated_edges': truncated},
            'methodology': [
                'العُقد مستخرجة من قاموس الكيانات المحدد في المرصد، والقاموس ليس شاملاً.',
                'الرابط بين كيانين يعني ظهورهما معاً في مادة مرصودة فقط، وليس علاقة مثبتة.',
                'عدد المواد والنطاقات يصف العينة المجموعة، ولا يمثل قياساً كاملاً للتغطية الإعلامية.',
                'لا تُستنتج علاقات اتصال أو قيادة أو تمويل أو تحالف من مجرد التزامن النصي.']}


def to_dot(network, max_nodes=45):
    """Safe Graphviz DOT rendering source; labels are escaped."""
    def q(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'
    nodes = (network or {}).get('nodes', [])[:max_nodes]
    keep = {n['name'] for n in nodes}
    edges = [e for e in (network or {}).get('edges', []) if e['source'] in keep and e['target'] in keep]
    lines = ['graph Marsad {', '  graph [overlap=false, splines=true];', '  node [shape=ellipse, style=filled, fillcolor="#183153", fontcolor="white", color="#6ca6cd"];', '  edge [color="#7792ad", fontcolor="#d5e4f2"];']
    for n in nodes:
        label = f"{n['name']}\\n{n['type']} · {n['mention_count']} ذكر"
        lines.append(f'  {q(n["name"])} [label={q(label)}];')
    for e in edges:
        lines.append(f'  {q(e["source"])} -- {q(e["target"])} [label={q(str(e["weight"]))}, penwidth={min(5, 1 + e["weight"] * .35):.1f}];')
    lines.append('}')
    return '\n'.join(lines)


def build_review_prompt(case_title, network):
    import json
    compact = {'stats': (network or {}).get('stats', {}), 'nodes': (network or {}).get('nodes', [])[:100],
               'edges': (network or {}).get('edges', [])[:150], 'methodology': (network or {}).get('methodology', [])}
    return ('حلّل شبكة الكيانات التالية للقضية: ' + str(case_title) + '\n'
            'تعامل مع الروابط باعتبارها تزامناً في الذكر داخل المواد فقط، ولا تحولها إلى علاقات واقعية مثبتة. '
            'ميّز بين المعلومة المنقولة والاستنتاج والفرضية. افحص مصادر كل رابط واستقلالها وتواريخها، '
            'واذكر ما لا تسمح الأدلة باستنتاجه. لا تستنتج اتصالاً أو تحالفاً أو تمويلاً أو مسؤولية دون دليل مستقل.\n\n'
            + json.dumps(compact, ensure_ascii=False, indent=2))
