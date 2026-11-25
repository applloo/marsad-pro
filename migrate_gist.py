# -*- coding: utf-8 -*-
"""نقل بيانات مرصد برو من الـGist المشترك مع التطبيق القديم لـGist جديد خاص ببرو (مرة واحدة).
بينسخ كل الملفات زي ما هي (المحفوظات، المصادر، الشفرات، النتايج، الملفات والخيوط...). الـGist القديم مابيتلمسش.
OLD_GIST_ID: الـGist القديم (بتكتبه وانت بتشغّل المهمة). GIST_ID: الجديد (من Secrets). GIST_TOKEN: نفس التوكن."""
import os
import sys
import time

import requests

API = "https://api.github.com/gists/"


def headers(tok):
    return {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "User-Agent": "marsad-pro-migrate"}


def main():
    tok, new, old = os.getenv("GIST_TOKEN"), (os.getenv("GIST_ID") or "").strip(), (os.getenv("OLD_GIST_ID") or "").strip()
    if not (tok and new and old):
        sys.exit("محتاج GIST_TOKEN و GIST_ID (الجديد) في Secrets، و OLD_GIST_ID (القديم) وانت بتشغّل المهمة")
    if new == old:
        sys.exit("الـGist الجديد هو نفس القديم! غيّر GIST_ID في Secrets بتاعة الـrepo ده للرقم الجديد الأول.")
    r = requests.get(API + old, headers=headers(tok), timeout=30)
    r.raise_for_status()
    files = r.json().get("files") or {}
    print(f"في الـGist القديم {len(files)} ملف", flush=True)
    copied = []
    for name, f in files.items():
        content = f.get("content") or ""
        if f.get("truncated") and f.get("raw_url"):
            content = requests.get(f["raw_url"], headers=headers(tok), timeout=60).text
        if not content.strip():
            continue
        for attempt in range(3):
            try:
                p = requests.patch(API + new, headers=headers(tok), json={"files": {name: {"content": content}}}, timeout=90)
                p.raise_for_status()
                copied.append(name)
                print(f"✅ {name} ({len(content):,} حرف)", flush=True)
                break
            except Exception as e:
                print(f"محاولة {attempt + 1} لـ {name} فشلت: {e}", flush=True)
                time.sleep(3)
        else:
            print(f"❌ ماتنسخش: {name}", flush=True)
    print(f"خلص: اتنسخ {len(copied)} من {len(files)} ملف. الـGist القديم زي ما هو.", flush=True)
    if len(copied) < len([f for f in files.values() if (f.get('content') or f.get('raw_url'))]):
        sys.exit(1)


if __name__ == "__main__":
    main()
