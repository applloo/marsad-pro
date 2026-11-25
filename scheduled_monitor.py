# -*- coding: utf-8 -*-
"""Phase 8.38 scheduled case monitor. Runs after search_job.py and uses Gist as shared state."""
from __future__ import annotations
import os, re, json, hashlib
from datetime import datetime, timezone
import job_guard  # noqa: F401 — بيدي كل اتصالات النت مهلة عشان مايعلّقش
import store
import automated_workflow

CONFIG = 'marsad_watch_cases.json'
STATUS = 'marsad_watch_status.json'
RESULTS = 'marsad_results.json'

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def norm(s): return re.sub(r'[^\w\u0600-\u06ff]+', ' ', str(s or '').lower()).strip()

def terms_for(case):
    vals = [case.get('title',''), case.get('name','')]
    vals += case.get('tags') or []
    vals += [x for x in re.split(r'[,،;\n]+', case.get('monitor_terms') or '') if x.strip()]
    out=[]; seen=set()
    for v in vals:
        v=str(v).strip(); k=norm(v)
        if len(k) > 2 and k not in seen: seen.add(k); out.append(v)
    return out

def relevant(item, terms):
    hay = norm(' '.join(str(item.get(k,'')) for k in ('title','title_ar','snippet','summary','text','description')))
    return any(norm(t) in hay for t in terms if len(norm(t)) > 2)

def item_key(x):
    u=(x.get('url') or '').split('?')[0].rstrip('/')
    return u or hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()

def main():
    token, gid = os.getenv('GIST_TOKEN'), os.getenv('GIST_ID')
    if not token or not gid: raise SystemExit('GIST_TOKEN و GIST_ID مطلوبان')
    cfg=store.load_file(token,gid,CONFIG,{}) or {}
    state={'state':'running','started_at':now(),'cases':[],'errors':[],'new_materials':0}
    store.save_file(token,gid,STATUS,state)
    data=store.load(token,gid)
    results=store.load_file(token,gid,RESULTS,{}) or {}
    scopes=cfg.get('scopes') or ['il','us','uk','rg','eg','wr','wa']
    pool=[]
    for scope in scopes:
        pool += (results.get(scope) or {}).get('items',[])
    # stable URL dedupe across all result groups
    dedup={item_key(x):x for x in pool if isinstance(x,dict)}
    pool=list(dedup.values())
    cases=data.get('research_cases') or []
    selected=set(str(x) for x in (cfg.get('case_ids') or []))
    reports=0
    for case in cases:
        cid=str(case.get('id',''))
        if selected and cid not in selected: continue
        terms=terms_for(case)
        if not terms: continue
        matches=[x for x in pool if relevant(x,terms)]
        materials=case.setdefault('materials',[])
        known={item_key(x) for x in materials if isinstance(x,dict)}
        added=0
        for x in matches:
            k=item_key(x)
            if k in known: continue
            materials.append({**x,'id':x.get('id') or hashlib.sha1(k.encode()).hexdigest()[:16], 'collected_by':'scheduled_monitor_8.38','collected_at':now()})
            known.add(k); added+=1
        if added:
            case['updated_at']=now()
            result=automated_workflow.run_case_workflow(case,data)
            data=result['store_data']; reports += int(not result.get('duplicate_report'))
        state['cases'].append({'case_id':cid,'title':case.get('title'),'matched':len(matches),'added':added,'status':'updated' if added else 'no_change'})
        state['new_materials'] += added
    store.save(token,gid,data)
    state.update({'state':'done','finished_at':now(),'pool_items':len(pool),'reports_created':reports,'message':'لا توجد مواد جديدة مطابقة' if not state['new_materials'] else 'تم تحديث ملفات القضايا بالمواد الجديدة'})
    store.save_file(token,gid,STATUS,state)
    print(json.dumps(state,ensure_ascii=False))

if __name__=='__main__': main()
