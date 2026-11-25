# -*- coding: utf-8 -*-
"""حماية مهام GitHub من التعليق.
1) أي اتصال بالنت من غير مهلة (زي مكتبة الترجمة deep-translator) بقى ليه أقصى 45 ثانية، بدل ما يفضل مستني للأبد.
2) run_limited: بيشغّل خطوة بحدّ أقصى للوقت. كل 5 دقايق بيطبع «لسه شغال في السطر الفلاني» (تشخيص)،
   ولو عدّت المهلة بيطبع مكان التعليق بالظبط ويكمل في اللي بعده بدل ما يقعد ساعات."""
import socket
import sys
import threading
import time
import traceback

NET_TIMEOUT = 45
socket.setdefaulttimeout(NET_TIMEOUT)


def where(thread):
    """آخر 4 أماكن في الكود الخيط ده واقف فيها (ملف:سطر دالة)"""
    fr = sys._current_frames().get(thread.ident)
    if fr is None:
        return "؟"
    st = traceback.extract_stack(fr)[-4:]
    return " ← ".join(f"{s.filename.split('/')[-1]}:{s.lineno} {s.name}" for s in st)


def run_limited(name, limit_s, fn, *args, beat_s=300, log=print):
    box = {}

    def work():
        try:
            box["v"] = fn(*args)
        except BaseException as e:  # noqa: BLE001 — بننقله للخيط الأساسي زي ما هو
            box["e"] = e

    th = threading.Thread(target=work, name=f"job-{name}", daemon=True)
    t0 = time.time()
    th.start()
    next_beat = beat_s
    while th.is_alive():
        th.join(max(0.5, min(15, beat_s, limit_s / 2)))
        el = time.time() - t0
        if not th.is_alive():
            break
        if el >= limit_s:
            w = where(th)
            log(f"⛔ {name}: علّق أكتر من {int(limit_s // 60)} دقيقة — واقف في: {w}")
            raise TimeoutError(f"علّق أكتر من {int(limit_s // 60)} دقيقة عند {w}")
        if el >= next_beat:
            log(f"⏳ {name}: لسه شغال ({int(el // 60)} دقيقة) — دلوقتي في: {where(th)}")
            next_beat += beat_s
    if "e" in box:
        raise box["e"]
    return box.get("v")
