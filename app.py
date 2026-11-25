# -*- coding: utf-8 -*-
"""
رادار الأخبار العالمية — بحث بالعربية في مصادر إسرائيلية وأمريكية وبريطانية + بحث عام عبر GDELT
"""
import hashlib
import copy
from collections import Counter
import html
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, unquote, urlparse

import streamlit as st

import core
import article_reader as article_reader_mod
import article_script_prompts as article_script_prompts_mod
import dossiers as dossiers_mod
import analysis_lab as analysis_lab_mod
import analysis_packages as analysis_packages_mod
import content_factory as content_factory_mod
import production_bundle as production_bundle_mod
import image_generation as image_generation_mod
import ai_providers as ai_providers_mod
import ai_router as ai_router_mod
import ai_billing as ai_billing_mod
import job_control as job_control_mod
import research_batches as research_batches_mod
import intelligence_pipeline as intelligence_pipeline_mod
import video_storyteller as video_storyteller_mod
import prompt_workbench as prompt_workbench_mod
import casebook as casebook_mod
import case_intake as case_intake_mod
import case_links as case_links_mod
import early_warning as early_warning_mod
import stance_scenarios as stance_scenarios_mod
import intel
import paid_radar as paid_radar_mod
import source_intelligence as source_intel_mod
import entity_intelligence as entity_intel_mod
import narrative_analysis as narrative_analysis_mod
import case_intelligence as case_intel_mod
import user_guide as user_guide_mod
import github_sync as github_sync_mod
from core import fmt_seen, tr
import gh_actions
import watch as watch_mod
import hmac
import links as links_mod
from about import TAB_HELP, TAB_NAMES, plain as about_plain, sections as about_sections
import keys as keys_mod
import store
import time
import uuid
import writers as writers_mod
from sources import ARAB_EG_GROUP, ARABIC, EGYPT, EGYPT_ARABIC, FLAGS, ISRAEL, REGION, SECTIONS, UK, USA, egypt_only, source_country
from writers import WRITERS

DOMAIN_LABELS = {}
for _g in (ISRAEL, USA, UK, REGION, ARABIC, EGYPT):
    for _entries in _g.values():
        for _label, _doms, _ in _entries:
            for _d in _doms.split("|"):
                DOMAIN_LABELS.setdefault(_d, _label)
for _n, _d, *_rest in intel.SOURCES:
    DOMAIN_LABELS.setdefault(_d, _n)


def source_name(domain):
    domain = (domain or "").lower().replace("www.", "")
    for d, label in DOMAIN_LABELS.items():
        if domain == d or domain.endswith("." + d):
            return label
    return domain


AR_NAMES = {  # أسماء الجرايد بالعربي زي ما بنقولها (الترجمة الآلية ممكن تقول «الحارس» بدل الجارديان)
    "AP News": "أسوشيتد برس", "Al-Monitor": "المونيتور", "Atlantic Council": "المجلس الأطلسي", "Axios": "أكسيوس", "BBC": "بي بي سي",
    "Baker Institute (Rice)": "معهد بيكر (جامعة رايس)", "Bloomberg": "بلومبرج", "Brookings": "معهد بروكينجز", "CNN": "سي إن إن",
    "CSIS": "مركز الدراسات الاستراتيجية والدولية", "Chatham House": "تشاتام هاوس", "Council on Foreign Relations": "مجلس العلاقات الخارجية",
    "DEBKAfile": "ديبكا", "Defense One": "ديفنس وان", "Financial Times": "فايننشال تايمز", "Foreign Affairs": "فورين أفيرز",
    "Foreign Policy": "فورين بوليسي", "Fox News": "فوكس نيوز", "JNS (Jewish News Syndicate)": "جي إن إس (وكالة الأخبار اليهودية)",
    "Jewish Chronicle": "جويش كرونيكل", "Jewish Insider": "جويش إنسايدر", "MSNBC": "إم إس إن بي سي", "Middle East Eye": "ميدل إيست آي",
    "Middle East Institute": "معهد الشرق الأوسط", "Middle East Monitor": "ميدل إيست مونيتور", "NPR": "الإذاعة الوطنية الأمريكية NPR",
    "Politico": "بوليتيكو", "Quincy Institute": "معهد كوينسي", "RUSI": "المعهد الملكي للخدمات المتحدة RUSI", "Reuters": "رويترز",
    "Sky News": "سكاي نيوز", "The Economist": "الإيكونوميست", "The Guardian": "الجارديان", "The Hill": "ذا هيل",
    "The Independent": "الإندبندنت", "The Intercept": "ذا إنترسبت", "The New Arab": "العربي الجديد (إنجليزي)",
    "The New York Times": "نيويورك تايمز", "The Telegraph": "التلجراف", "The Times": "التايمز", "The Wall Street Journal": "وول ستريت جورنال",
    "The Washington Post": "واشنطن بوست", "Washington Institute": "معهد واشنطن", "i24NEWS": "آي 24 نيوز", "openDemocracy": "أوبن ديموقراسي",
}


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def _ar_name(label):
    if label in AR_NAMES:
        return AR_NAMES[label]
    if re.search(r"[\u0600-\u06FF]", label):
        return label
    try:
        return tr(label, "en", "ar") or label
    except Exception:
        return label


def src_label(domain, with_domain=True):
    """«اسم المصدر بالعربية · 🏳️ دولته» — يُستخدم في كل مكان يظهر فيه مصدر. لا يُسقط الصفحة أبداً"""
    try:
        dom = str(domain or "").lower().replace("www.", "")
        name = str(source_name(dom))
        name_ar = str(_ar_name(name)) if name != dom else dom
        country = str(source_country(dom) or "")
        out = html.escape(name_ar)
        if with_domain and name_ar != dom:
            out += f" ({html.escape(dom)})"
        out += (f" · {FLAGS.get(country, '🏳️')} {country}" if country else " · 🏳️ دولة غير محددة")
        return out
    except Exception as e:  # أي خطأ هنا لا يجب أن يكسر عرض الخبر
        return html.escape(str(domain or "")) + f" (تعذّر تحديد الدولة: {type(e).__name__})"


APP_VERSION = "9.0"  # بيزيد مع كل نسخة جديدة
st.set_page_config(page_title="Marsad | مركز الرصد والتحليل", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
:root { --marsad-bg:#07111f; --marsad-panel:#101e30; --marsad-line:#263c56; --marsad-accent:#168cf0; --marsad-muted:#91a4ba; }
.stApp { background: radial-gradient(ellipse at 50% -20%, #17375b 0%, #091728 42%, #07111f 78%); }
[data-testid="stHeader"] { background:rgba(7,17,31,.88); }
[data-testid="stMainBlockContainer"] { max-width:1500px; padding-top:1.1rem; padding-bottom:3rem; }
.stMarkdown, label, [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] { direction:rtl; text-align:right; }
h1,h2,h3 { letter-spacing:0; }
h1 { font-size:clamp(1.5rem,2.4vw,2.25rem)!important; font-weight:800!important; }
.ar-title {font-size:1.08rem; font-weight:750; line-height:1.8; margin-bottom:4px;}
.ltr {direction:ltr; text-align:left; color:#9aacc0; font-size:.86rem; margin-bottom:2px;}
.meta {color:var(--marsad-muted); font-size:.82rem; margin:6px 0;}
.badge {background:#16385a; color:#bfe3ff; padding:2px 9px; border-radius:999px; font-size:.76rem;}
a.btn {display:inline-block; background:#087bd4; color:#fff!important; padding:8px 16px; border-radius:10px; text-decoration:none; font-weight:650; margin-top:4px;}
a.btn:hover {background:#1596ff;}
.card,.hm-row {border:1px solid var(--marsad-line); border-radius:14px; padding:13px 15px; margin-bottom:10px; background:linear-gradient(145deg,rgba(21,42,66,.92),rgba(12,27,44,.9));}
.article-body p {line-height:2; font-size:1.05rem; margin-bottom:1rem;}
[data-testid="stTabs"] > div[role="tablist"] { gap:7px; padding:7px; border:1px solid rgba(100,145,190,.25); border-radius:15px; background:rgba(8,22,38,.76); flex-wrap:nowrap; overflow-x:auto; }
[data-testid="stTabs"] button[role="tab"] { border:1px solid #29435f!important; border-radius:11px!important; padding:10px 16px!important; min-height:44px!important; background:#12243a!important; color:#d7e7f8!important; white-space:nowrap!important; font-weight:650!important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { background:linear-gradient(135deg,#087bd4,#0755a0)!important; border-color:#28a7ff!important; color:white!important; box-shadow:0 0 0 1px rgba(40,167,255,.2),0 5px 18px rgba(0,80,160,.25)!important; }
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"] {display:none!important;}
[data-testid="stVerticalBlockBorderWrapper"] { border-color:rgba(100,145,190,.22)!important; border-radius:15px!important; }
[data-testid="stMetric"] { background:rgba(17,37,59,.8); border:1px solid var(--marsad-line); border-radius:13px; padding:12px; }
[data-testid="stButton"] button[kind="primary"],button[kind="primary"] { background:linear-gradient(120deg,#087bd4,#0755a0); border:1px solid #249dff; border-radius:11px; font-weight:750; }
[data-testid="stExpander"] { border:1px solid rgba(100,145,190,.25); border-radius:12px; background:rgba(14,30,48,.55); }
[data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius:10px!important; }
[data-testid="stCaptionContainer"] { color:#9eb1c6; }
.hm-stat {border:1px solid var(--marsad-line); border-radius:13px; padding:12px; text-align:center; background:rgba(16,34,54,.9);}
.hm-stat b {display:block; font-size:1.55rem; color:#f0f7ff;}
.hm-tag {font-size:.73rem; padding:2px 9px; border-radius:999px; color:#fff; margin-left:6px;}
@media(max-width:720px){
 [data-testid="stMainBlockContainer"] {padding-left:.7rem;padding-right:.7rem;}
 [data-testid="stTabs"] button[role="tab"] {padding:8px 11px!important;font-size:.86rem!important;}
 .ar-title {font-size:1rem;}
}
</style>
""",
    unsafe_allow_html=True,
)


# ───────────────────────── الهوية البصرية الجديدة ─────────────────────────
st.markdown("""
<style>
:root {
 --m-bg:#071326; --m-panel:#101f3b; --m-panel2:#14294b; --m-line:#30466d;
 --m-text:#f4f7ff; --m-muted:#bdc9df; --m-cyan:#35d7ee; --m-violet:#a78bfa;
 --m-blue:#4c8dff; --m-gold:#f6c76b;
}
html, body, [class*="css"] {font-family:Tahoma,Arial,sans-serif!important;}
.stApp {background:radial-gradient(ellipse at 82% -12%,rgba(85,75,190,.28),transparent 36%),radial-gradient(ellipse at 5% 25%,rgba(21,155,190,.14),transparent 34%),linear-gradient(145deg,#071326 0%,#09172c 48%,#0c1730 100%)!important;color:var(--m-text)!important;}
[data-testid="stHeader"]{background:rgba(7,19,38,.82)!important;backdrop-filter:blur(16px);}
[data-testid="stMainBlockContainer"]{width:100%!important;max-width:none!important;padding:1.1rem clamp(.8rem,1.8vw,2rem) 3rem!important;}
.stMarkdown, .stMarkdown p, .stMarkdown li, label, [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] {color:var(--m-text)!important;}
[data-testid="stCaptionContainer"], .stCaption, small {color:var(--m-muted)!important;}
h1,h2,h3,h4 {color:#fff!important;font-weight:850!important;letter-spacing:0!important;text-shadow:0 2px 18px rgba(53,215,238,.12);}
h1{font-size:clamp(1.8rem,3vw,2.55rem)!important;}
h2{font-size:clamp(1.35rem,2vw,1.8rem)!important;}
.marsad-brand img{filter:drop-shadow(0 10px 24px rgba(46,196,220,.18));max-width:100%;height:auto;}
/* Navigation: main and sub sections as big tap buttons (only the chosen section is drawn = lighter app). */
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"],
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"]{
 display:grid!important; grid-template-columns:repeat(auto-fill,minmax(170px,1fr))!important; gap:8px!important; width:100%!important; direction:rtl!important;
}
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"]{
 padding:12px!important; border:1px solid rgba(116,144,205,.24)!important; border-radius:20px!important;
 background:linear-gradient(160deg,rgba(20,39,72,.96),rgba(10,24,47,.96))!important;
 box-shadow:0 16px 40px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.06)!important;
}
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label,
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label{
 margin:0!important; min-height:50px!important; padding:10px 14px!important; border-radius:13px!important; cursor:pointer!important;
 border:1px solid rgba(116,144,205,.30)!important; background:rgba(255,255,255,.03)!important;
 display:flex!important; align-items:center!important; justify-content:center!important; text-align:center!important;
 font-size:1rem!important; font-weight:750!important; color:#e7efff!important; transition:background .2s ease,border-color .2s ease!important;
}
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label{min-height:44px!important;font-size:.95rem!important;}
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label > div:first-child,
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label > div:first-child{display:none!important;}
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label:hover,
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label:hover{
 background:rgba(70,120,190,.22)!important; border-color:rgba(83,211,233,.45)!important;
}
.stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label:has(input:checked),
.stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"] label:has(input:checked){
 background:linear-gradient(115deg,rgba(45,199,220,.28),rgba(124,93,230,.34))!important;
 border:1px solid rgba(73,215,234,.85)!important; color:#fff!important; box-shadow:0 8px 22px rgba(21,154,190,.18)!important;
}
.marsad-nav-gap{height:6px;}
/* Cards, metrics and expanders */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stMetric"], [data-testid="stExpander"]{border:1px solid rgba(120,150,205,.28)!important;border-radius:18px!important;background:linear-gradient(145deg,rgba(23,43,77,.86),rgba(12,27,52,.94))!important;box-shadow:0 12px 28px rgba(0,0,0,.16),inset 0 1px rgba(255,255,255,.045)!important;}
[data-testid="stMetric"]{padding:15px!important;}
[data-testid="stMetricValue"]{color:#fff!important;font-weight:850!important;}
[data-testid="stMetricLabel"]{color:#c5d4ee!important;}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button{border-radius:13px!important;border:1px solid rgba(87,207,232,.45)!important;background:linear-gradient(135deg,#2469b8,#5c4bb1)!important;color:#fff!important;font-weight:750!important;box-shadow:0 7px 18px rgba(31,91,166,.22)!important;transition:transform .18s ease,filter .18s ease!important;}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{filter:brightness(1.16)!important;transform:translateY(-2px)!important;}
[data-testid="stButton"] button:focus{outline:2px solid var(--m-cyan)!important;}
[data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{background:#f8faff!important;color:#17243b!important;border:1px solid #9fb2d1!important;border-radius:12px!important;}
[data-baseweb="select"] *{color:#17243b!important;}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label{color:#edf3ff!important;}
[data-testid="stAlert"]{border-radius:14px!important;}
.stProgress>div>div{background:linear-gradient(90deg,#35d7ee,#a78bfa)!important;}
a{color:#74ddf1!important;}
.card,.hm-row{border:1px solid rgba(105,160,215,.32)!important;border-radius:17px!important;background:linear-gradient(145deg,rgba(25,48,84,.96),rgba(11,27,51,.96))!important;box-shadow:0 12px 26px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.05)!important;}
.ar-title{color:#fff!important;font-size:1.12rem!important;line-height:1.9!important;}
.meta,.ltr{color:#c0cce0!important;}
.badge{background:rgba(53,215,238,.16)!important;color:#b9f4ff!important;border:1px solid rgba(53,215,238,.35)!important;}
.hm-stat{background:linear-gradient(145deg,#192f54,#101f3a)!important;border:1px solid #3b5684!important;box-shadow:0 8px 22px rgba(0,0,0,.18)!important;}
.hm-stat b{color:#fff!important;}
@media(max-width:850px){
 .stApp [role="radiogroup"] label{font-size:.9rem!important;}
 .stApp div[data-testid="stElementContainer"]:has(#marsad-main-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"],
 .stApp div[data-testid="stElementContainer"]:has(#marsad-sub-nav-start) + div[data-testid="stElementContainer"] [role="radiogroup"]{grid-template-columns:repeat(2,minmax(0,1fr))!important;}
 [data-testid="stMainBlockContainer"]{padding-left:.65rem!important;padding-right:.65rem!important;}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;}}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── القراءة الصوتية ─────────────────────────

TTS_MODES = ["العنوان + المقال كاملاً", "العنوان + ملخص قصير", "العنوان فقط"]
ORDINALS = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر"]


@st.cache_data(ttl=86400, max_entries=30, show_spinner=False)
def tts_cached(text, voice, rate):
    return core.tts(text, voice, rate)


_fragment = getattr(st, "fragment", lambda f: f)  # الجزء ده بيتحدّث لوحده من غير ما يعيد تحميل باقي التابات


def pick(container, label, options, default, key, fmt=None):
    """بديل لشريط السحب: الشريط كان بيتحرك لوحده مع الطلوع والنزول على الموبايل فيعمل تحديث للصفحة. هنا اختيارات بتتداس بس"""
    options = list(options)
    if default not in options:
        try:
            default = min(options, key=lambda o: abs(o - default))
        except Exception:
            default = options[0]
    kw = {"format_func": fmt} if fmt else {}
    if len(options) <= 6:
        return container.radio(label, options, index=options.index(default), horizontal=True, key=key, **kw)
    return container.selectbox(label, options, index=options.index(default), key=key, **kw)


def untranslated(items):
    return [x for x in items if isinstance(x, dict) and (x.get("title") or "").strip()
            and not core._HAS_AR.search(x.get("title_ar") or "") and not core._HAS_AR.search(x.get("title") or "")]


def fix_untranslated(items, limit=40):
    """بيترجم العناوين اللي فضلت بلغتها (لما الترجمة كانت واقعة وقت البحث). بيرجع عدد اللي اتصلح"""
    bad = untranslated(items)[:limit]
    if not bad:
        return 0
    try:
        core.translate_titles(bad)
    except Exception:
        return 0
    return sum(1 for x in bad if core._HAS_AR.search(x.get("title_ar") or ""))


def tts_get(name, default):
    """إعدادات الصوت بتتحفظ في نسخة احتياطية، عشان ماتضيعش لما تقفل قسم الإعدادات (ستريمليت بيمسح قيم الأزرار اللي مش ظاهرة)"""
    ss = st.session_state
    if name in ss:
        ss.setdefault("_tts_saved", {})[name] = ss[name]
        return ss[name]
    return ss.get("_tts_saved", {}).get(name, default)


def tts_settings(prefix):
    c1, c2 = st.columns(2)
    label = c1.selectbox("الصوت", list(core.VOICES), key=f"{prefix}_voice")
    rate = pick(c2, "السرعة", range(-30, 45, 5), 0, f"{prefix}_rate", fmt=lambda v: f"{v:+d}%")
    return core.VOICES[label], rate


def audio_block(entry, wk, name="marsad_news"):
    data, _engine, note = entry
    if note:
        st.caption("ℹ️ " + note)
    st.audio(data, format="audio/mpeg")
    st.download_button(
        "⬇️ تنزيل MP3 (للاستماع بدون إنترنت داخل المترو)", data=data, file_name=f"{name}.mp3", mime="audio/mpeg", key=f"dl_{wk}"
    )
    st.caption("⏸ للإيقاف المؤقت أو الإيقاف استخدم زر المشغّل. الصوت يستمر والشاشة مغلقة.")


def speech_text(url, title_ar, mode):
    """يجهّز النص العربي المراد نطقه حسب الوضع. يعيد (النص، ملاحظة)"""
    if mode == TTS_MODES[2]:
        return title_ar, ""
    art = core.fetch_article(url)
    if not art:
        return title_ar, "تعذّر جلب نص المقال (اشتراك أو حجب) فقُرئ العنوان فقط."
    if mode == TTS_MODES[1]:
        summ = core.summarize(url, verdict=False)
        summ = re.sub(r"^ملخص مبسّط[^\n]*\n+", "", summ)
        return f"{title_ar}. {summ}", ""
    return f"{title_ar}. {core.translate_long(art['text'])}", ""


def make_audio(text, voice, rate):
    try:
        return tts_cached(text, voice, rate)
    except Exception as e:
        st.error(f"تعذّر توليد الصوت ({type(e).__name__}): {e}")
        return None


def listen_widget(a, wk):
    aud = st.session_state.setdefault("audio", {})
    url = a.get("url", "")
    if st.button("🎧 استمع", key=f"ls_{wk}"):
        ss = st.session_state
        voice = core.VOICES[tts_get("tts_voice", list(core.VOICES)[0])]
        with st.spinner("جارٍ تجهيز الصوت (جلب النص وترجمته ثم النطق)… قد يستغرق دقيقة للمقالات الطويلة."):
            text, note0 = speech_text(url, a.get("title_ar", ""), tts_get("tts_mode", TTS_MODES[0]))
            res = make_audio(text, voice, tts_get("tts_rate", 0))
            if res:
                if len(aud) >= 6:
                    aud.pop(next(iter(aud)))
                aud[url] = (res[0], res[1], (note0 + " " + res[2]).strip())
    if url in aud:
        audio_block(aud[url], wk)


# ───────────────────────── صفحة قراءة المقال ─────────────────────────


@st.cache_data(ttl=3600, show_spinner=False)
def alt_cached(title, domain):
    items, note = core.find_alternatives(title, domain)
    return core.translate_titles(items), note


def _alt_cards(items):
    for a in items:
        lnk = f"?view={quote(a['url'], safe='')}&seen={a.get('seendate', '')}&t={quote(a['title'][:200], safe='')}{auth_qs()}"
        st.markdown(
            f"<div class='card'><div class='ar-title'>{html.escape(a.get('title_ar', ''))}</div>"
            f"<div class='ltr' dir='ltr'>{html.escape(a['title'])}</div>"
            f"<div class='meta'>🌐 {src_label(a['domain'])} · 🕒 {fmt_seen(a.get('seendate', ''))} · نص كامل ({a['chars']} حرف)</div>"
            f"<a class='btn' href='{html.escape(lnk)}' target='_blank' rel='noopener'>ترجم المقال</a></div>",
            unsafe_allow_html=True,
        )


def alt_block(title, url):
    st.markdown("### 🔁 تغطية بديلة مجانية للموضوع نفسه")
    host = core._host(url)
    with st.spinner("جارٍ البحث عن مصادر مفتوحة تغطي الخبر نفسه…"):
        items, note = alt_cached(title, host)
    if items:
        st.caption(f"{note} هذه مقالات من مواقع أخرى عن الموضوع نفسه (قد تختلف في الزاوية والتفاصيل عن المقال المغلق).")
        _alt_cards(items)
    else:
        st.info(f"لم أجد بديلاً مفتوحاً بنص كامل. {note}")
    # بحث يدوي: العنوان المستخرج من الرابط قد لا يكفي، فاكتب أنت كلمات الخبر
    st.markdown("**🔎 ابحث بكلماتك أنت عن بدائل:**")
    q = st.text_input("كلمات الخبر (بالإنجليزية أو أي لغة)", value="" if len(title) < 12 else title, key="alt_q",
                      placeholder="مثال: Ethiopia Egypt dam talks")
    if st.button("🔎 ابحث عن بدائل", key="alt_go", type="primary"):
        if len(q.strip()) < 6:
            st.warning("اكتب كلمات أكثر قليلاً.")
        else:
            with st.spinner("جارٍ البحث…"):
                st.session_state["alt_manual"] = alt_cached(q.strip(), host)
    man = st.session_state.get("alt_manual")
    if man:
        m_items, m_note = man
        if m_items:
            st.caption(m_note)
            _alt_cards(m_items)
        else:
            st.warning(f"لا نتائج بنص كامل. {m_note}")
    if q.strip():
        from urllib.parse import quote_plus
        qq = quote_plus(q.strip())
        st.markdown(f"أو افتح البحث في موقع خارجي: [أخبار Google](https://news.google.com/search?q={qq}) · "
                    f"[Google](https://www.google.com/search?q={qq}) · [Bing أخبار](https://www.bing.com/news/search?q={qq})")


def translate_proxy_url(url, tl="ar"):
    """رابط نسخة مترجمة من الصفحة عبر ترجمة جوجل (translate.goog)"""
    from urllib.parse import urlsplit
    s = urlsplit(url)
    host = (s.hostname or "").replace("-", "--").replace(".", "-")
    q = (s.query + "&" if s.query else "") + f"_x_tr_sl=auto&_x_tr_tl={tl}&_x_tr_hl={tl}&_x_tr_pto=wapp"
    return f"https://{host}.translate.goog{s.path or '/'}?{q}"


def embed_browser(url):
    """فتح الصفحة الأصلية مترجمة: أزرار تاب جديد (الأضمن) + إطار داخلي اختياري"""
    import streamlit.components.v1 as components
    with st.expander("🌐 افتح الصفحة الأصلية مترجمة للعربية", expanded=True):
        c1, c2 = st.columns(2)
        c1.link_button("🌐 مترجمة (ترجمة جوجل) ↗️", translate_proxy_url(url), use_container_width=True, type="primary")
        c2.link_button("📄 الأصلية ↗️", url, use_container_width=True)
        st.caption("لو الأصلية فتحت عندك، اضغط بيمين الماوس ← «ترجمة إلى العربية» (متصفح كروم بيترجم أي لغة). "
                   "الزرارين بيفتحوا في تاب جديد وده أضمن من الإطار.")
        if st.checkbox("جرّب عرضها داخل هذه الصفحة (قد لا يعمل مع بعض المواقع)", key="emb_on"):
            mode = st.radio("العرض", ["مترجمة للعربية", "الأصلية بلغتها"], horizontal=True, key="emb_mode")
            src = translate_proxy_url(url) if mode.startswith("مترجمة") else url
            components.html(
                f"<iframe src='{html.escape(src, quote=True)}' style='width:100%;height:690px;border:1px solid #334155;border-radius:8px;background:#fff' "
                "referrerpolicy='no-referrer'></iframe>", height=700, scrolling=False)
            st.caption("لو ظهرت علامة وش حزين، يبقى الموقع مانع العرض داخل صفحات تانية. استخدم الزرارين اللي فوق.")


_SCRIPT_RULES = (
    "القواعد: اكتب بالعامية المصرية البسيطة كأني بحكي لواحد صاحبي، بجمل قصيرة تتقال بصوت عالي من غير تعقيد. "
    "ماتختلقش أي معلومة أو رقم مش موجود في المقالات المرفقة، وكل ما فيه شك قول «حسب ما نشر...» واذكر اسم المصدر والدولة. "
    "فرّق بين اللي المصدر قاله وبين تحليلي أنا. لو في تضارب بين مصدرين وضّحه. ركّز على علاقة الموضوع بمصر. "
    "في الآخر ضيف سطر قصير: «ده تحليل مبني على مصادر مفتوحة ومش تأكيد رسمي».\n\n"
)

SCRIPT_KINDS = {
    "بدون تعليمات (النص بس)": "",
    "تحليل وربط عام": (
        "المطلوب: اقرأ المقال التالي (مترجم للعربية) كمادة تحليل. لخّص أهم ما فيه في 5 نقاط، واستخرج الأطراف والأرقام والتواريخ، "
        "ثم اذكر ما يخص مصر. وإذا أرسلتُ لك مقالات أخرى بعده فاربط بينها: ما الخيط المشترك؟ أين التناقض؟ وما الاستنتاج السياسي المحتمل؟ "
        "ميّز بين ما ورد في النص وما هو استنتاجك.\n\n"
    ),
    "🎬 ريلز فيسبوك (60–90 ثانية)": (
        "المطلوب: اكتب سكريبت ريلز فيسبوك من 150 إلى 220 كلمة (60–90 ثانية) مبني على المقال/المقالات التالية. الهيكل: "
        "(1) خطّاف أول 3 ثواني: سؤال أو معلومة صادمة. (2) الخبر في 3 أو 4 جمل. (3) ليه ده مهم لمصر. (4) جملة ختام + سؤال للمتابعين في التعليقات. "
        "اكتب بجانب كل جزء اقتراح لنص يظهر على الشاشة (3–6 كلمات).\n" + _SCRIPT_RULES
    ),
    "▶️ فيديو يوتيوب (5 دقايق)": (
        "المطلوب: اكتب سكريبت فيديو يوتيوب مدته 5 دقايق (حوالي 700 كلمة) مبني على المقال/المقالات التالية. الهيكل: "
        "(1) خطّاف 10 ثواني. (2) مقدمة قصيرة: إيه اللي حصل؟ (3) الخلفية في فقرة. (4) التحليل: أهم 3 نقاط، لكل واحدة عنوان فرعي. "
        "(5) إيه علاقة ده بمصر؟ (6) الخلاصة + سؤال للتعليقات. حدّد تقريباً الوقت لكل جزء، واقترح لقطات أو صور تظهر مع كل جزء.\n" + _SCRIPT_RULES
    ),
    "▶️ فيديو يوتيوب (9 دقايق)": (
        "المطلوب: اكتب سكريبت فيديو يوتيوب مدته حوالي 9 دقايق (1200 إلى 1300 كلمة) مبني على المقال/المقالات التالية. الهيكل: "
        "(1) خطّاف 10–15 ثانية. (2) مقدمة: إيه اللي حصل. (3) الخلفية التاريخية أو السياق. (4) عرض كل مصدر وروايته على حدة. "
        "(5) الربط: ما الخيط المشترك بين المصادر؟ وأين التناقض؟ (6) السيناريوهات المحتملة (2 أو 3) بدون جزم. (7) إيه معنى ده بالنسبة لمصر. "
        "(8) خلاصة + سؤال للتعليقات. حدّد تقريباً الوقت لكل جزء، واقترح لقطات وخرائط أو صور مناسبة.\n" + _SCRIPT_RULES
    ),
}


def copy_block(url, title, title_ar, art, body_ar):
    """نص جاهز للنسخ (نوت / ذكاء اصطناعي): العنوان والمصدر والتاريخ والرابط ثم النص المترجم"""
    dom = core._host(url)
    with st.expander("📋 انسخ المقال المترجم (للنوت أو لأي ذكاء اصطناعي)", expanded=False):
        kind = st.selectbox("أضف في أول النص تعليمات جاهزة للذكاء الاصطناعي", list(SCRIPT_KINDS), key="cp_kind")
        st.caption("لو هتبعت أكتر من مقال: اختار التعليمات مع **أول** مقال بس، ولمّا تخلّص المقالات كلها اكتب: «دلوقتي اكتب السكريبت».")
        with_orig = st.checkbox("أضف النص الأصلي بعد الترجمة", value=False, key="cp_orig")
        head = (f"العنوان: {title_ar}\nالعنوان الأصلي: {title}\nالمصدر: {source_name(dom)} ({dom}) · {source_country(dom)}\n"
                f"التاريخ: {art.get('date') or 'غير معروف'}\nالرابط: {url}\n\n")
        txt = SCRIPT_KINDS[kind] + head + body_ar.strip()
        if with_orig:
            txt += "\n\n----- النص الأصلي -----\n" + art["text"].strip()
        st.caption("اضغط أيقونة النسخ 📋 في الركن العلوي من الصندوق (بتظهر لما تقف عليه أو تلمسه)، وبعدين الصق في أي مكان. "
                   "كرر نفس الشيء مع كل مقال ولصقهم ورا بعض عشان يحصل الربط بينهم.")
        try:
            st.code(txt, language=None, wrap_lines=True)
        except TypeError:
            st.code(txt, language=None)
        st.download_button("⬇️ نزّله كملف نصي (.txt)", txt, file_name="article.txt", mime="text/plain", use_container_width=True, key="cp_dl")


def reader_head(title_en, url, wr, outlet, title_ar=""):
    """رأس صفحة المقال: العنوان بالعربي والأصلي + الجريدة + الكاتب + الموقع"""
    if title_en:
        title_ar = title_ar or tr(title_en, "auto", "ar")
        st.markdown(f"### {title_ar}")
        st.markdown(f"<div class='ltr' dir='ltr'>{html.escape(title_en)}</div>", unsafe_allow_html=True)
    bits = []
    if outlet:
        bits.append(f"📰 **الجريدة:** {html.escape(outlet)}")
    if wr:
        bits.append(f"✍️ **الكاتب:** {html.escape(wr)}")
    host = core._host(url)
    if host and host != "news.google.com":
        bits.append(f"🌐 **الموقع:** {src_label(host)}")
    if bits:
        st.markdown("  \n".join(bits), unsafe_allow_html=True)


def search_suggestions(title):
    """اقتراحات بحث بالعنوان في مصادر تانية (روابط تفتح في تاب جديد)"""
    q = re.sub(r"\s+[-|–]\s+[^-|–]{2,40}$", "", (title or "").strip())[:140]
    if len(q) < 6:
        return
    from urllib.parse import quote_plus
    qq = quote_plus(q)
    st.markdown("### 🔎 اقتراحات بحث بالعنوان في مصادر تانية")
    sites = [("Google", f"https://www.google.com/search?q={qq}"), ("أخبار Google", f"https://news.google.com/search?q={qq}"),
             ("Bing أخبار", f"https://www.bing.com/news/search?q={qq}"),
             ("AP", f"https://www.google.com/search?q={qq}+site:apnews.com"), ("Reuters", f"https://www.google.com/search?q={qq}+site:reuters.com"),
             ("BBC", f"https://www.google.com/search?q={qq}+site:bbc.com"), ("الجزيرة", f"https://www.google.com/search?q={qq}+site:aljazeera.net"),
             ("Times of Israel", f"https://www.google.com/search?q={qq}+site:timesofisrael.com"),
             ("Axios", f"https://www.google.com/search?q={qq}+site:axios.com"), ("Al-Monitor", f"https://www.google.com/search?q={qq}+site:al-monitor.com"),
             ("Middle East Eye", f"https://www.google.com/search?q={qq}+site:middleeasteye.net"), ("X (تويتر)", f"https://x.com/search?q={qq}&f=live")]
    st.markdown(" · ".join(f"[{n}]({u})" for n, u in sites))
    st.caption("كل رابط بيفتح تاب جديد ببحث بعنوان المقال، علشان تلاقي نفس الخبر عند ناس تانية.")


def reader_scroll_tool():
    """ازرار عائمة للتحكم الدقيق في التمرير اثناء قراءة المقال (الشريط الجانبي وعجلة الماوس بيقفزوا جمل كاملة)"""
    import streamlit.components.v1 as components
    components.html("""
<script>
(function(){
  try{
    var P=window.parent, D=P.document;
    var old=D.getElementById('rd-scroll-tool'); if(old) old.remove();
    var box=D.createElement('div'); box.id='rd-scroll-tool';
    box.style.cssText='position:fixed;left:10px;bottom:90px;z-index:99999;display:flex;flex-direction:column;gap:6px;direction:ltr;font-family:sans-serif';
    function btn(t,title){var b=D.createElement('button');b.textContent=t;b.title=title;
      b.style.cssText='width:56px;height:56px;border-radius:14px;border:2px solid rgba(255,255,255,.6);background:rgba(30,30,40,.92);color:#fff;font-size:26px;cursor:pointer;touch-action:manipulation;user-select:none;-webkit-user-select:none';
      return b;}
    function area(){return D.querySelector('[data-testid="stMain"]')||D.querySelector('section.main')||D.scrollingElement||D.documentElement;}
    var speed=14, timer=null, auto=false, autoTimer=null, autoSpeed=1;
    function step(dy){var el=area(); el.scrollBy({top:dy,behavior:'auto'});}
    function holdStart(dir){step(dir*speed); stopHold(); timer=setInterval(function(){step(dir*speed);},40);}
    function stopHold(){if(timer){clearInterval(timer);timer=null;}}
    function bindHold(b,dir){
      ['mousedown','touchstart'].forEach(function(e){b.addEventListener(e,function(ev){ev.preventDefault();holdStart(dir);},{passive:false});});
      ['mouseup','mouseleave','touchend','touchcancel'].forEach(function(e){b.addEventListener(e,stopHold);});
    }
    var up=btn('▲','لفوق (اضغط واستمر)'), down=btn('▼','لتحت (اضغط واستمر)');
    var play=btn('▶','تمرير تلقائي بطيء'), plus=btn('+','أسرع'), minus=btn('−','أبطأ');
    bindHold(up,-1); bindHold(down,1);
    function setAuto(on){
      auto=on; play.textContent=on?'⏸':'▶';
      if(autoTimer){clearInterval(autoTimer);autoTimer=null;}
      if(on){autoTimer=setInterval(function(){step(autoSpeed);},40);}
    }
    play.onclick=function(){setAuto(!auto);};
    plus.onclick=function(){autoSpeed=Math.min(8,autoSpeed+0.5);speed=Math.min(40,speed+4);};
    minus.onclick=function(){autoSpeed=Math.max(0.5,autoSpeed-0.5);speed=Math.max(4,speed-4);};
    [up,play,plus,minus,down].forEach(function(b){box.appendChild(b);});
    D.body.appendChild(box);
  }catch(e){}
})();
</script>""", height=0)


def reader_page():
    url = unquote(st.query_params.get("view", ""))
    seen = st.query_params.get("seen", "")
    orig_title = unquote(st.query_params.get("t", ""))
    wr = unquote(st.query_params.get("wr", ""))
    outlet = unquote(st.query_params.get("o", ""))

    st.markdown("## 📖 قراءة المقال مترجماً")
    reader_scroll_tool()
    if not url.startswith(("http://", "https://")):
        st.error("رابط غير صالح.")
        return
    gnews_link = core._host(url) == "news.google.com"
    if gnews_link:  # رابط أخبار جوجل: نحاول نوصل للرابط الاصلي للجريدة
        with st.spinner("جارٍ الوصول للرابط الاصلي للمقال…"):
            real = core.decode_gnews(url)
        if core._host(real) != "news.google.com":
            url, gnews_link = real, False
    st.markdown(f"🔗 **الرابط الأصلي:** [{html.escape(url)}]({url})")
    reader_head(orig_title, url, wr, outlet)

    embed_browser(url)

    with st.spinner("جارٍ جلب المقال وترجمته…"):
        art = None if gnews_link else core.fetch_article(url)
        if not art:
            if gnews_link:
                st.warning("رابط أخبار جوجل ما اتفكش (جوجل بيمنع فكّه من التطبيق). العنوان اللي فوق هو العنوان الحقيقي للمقال. "
                           "افتح «الأصلية» من فوق في متصفحك، او استخدم الاقتراحات تحت.")
            else:
                st.warning("تعذّر استخراج نص المقال: " + core.FETCH_WHY.get(url, "جدار اشتراك أو حجب") +
                           ". (الصفحة قد تفتح في متصفحك عادي لكن الموقع يعامل التطبيق كزائر آلي.)")
            search_suggestions(orig_title or core.title_from_url(url))
            alt_block(orig_title or core.title_from_url(url), url)
            return
        title = art["title"] if art["title"] and art["title"].lower() not in ("google news", "أخبار جوجل") else orig_title
        title = title or orig_title
        title_ar = tr(title, "auto", "ar")
        body_ar = art["text"] if art.get("pre_ar") else core.translate_long(art["text"])
        body_ok = core.translated_ok(art["text"], body_ar)

    if not body_ok:
        st.warning("⚠️ الترجمة التلقائية للنص لم تكتمل الآن (غالباً جوجل مشغول). اضغط «أعد الترجمة» بعد لحظات، "
                   "أو استخدم زرار «مترجمة (ترجمة جوجل)» فوق في التاب.")
        if st.button("🔁 أعد الترجمة", key="rd_retry"):
            st.rerun()
    extraction = article_reader_mod.inspect_article(art.get("text", ""))
    trunc_alt = extraction["status"] != "usable_unverified"
    if extraction["status"] == "insufficient":
        st.warning(f"⚠️ {extraction['detail']} ({extraction['chars']} حرفاً). جرّب فتح الأصلية أو التغطية البديلة المفتوحة.")
    elif extraction["status"] == "possibly_partial":
        st.warning(f"⚠️ {extraction['label']}: {extraction['detail']} ({extraction['chars']} حرفاً). لا يتجاوز التطبيق الاشتراكات أو الحجب.")
    else:
        st.info(f"📄 {extraction['label']}. {extraction['words']} كلمة تقريباً · {extraction['reading_minutes']} دقيقة قراءة. {extraction['detail']}")
    via = art.get("via") or "غير معروفة (نسخة محفوظة من قبل)"
    if via.startswith("الفتح المباشر"):
        st.success(f"🟢 طريقة جلب المقال: {via}")
    else:
        st.info(f"🟡 طريقة جلب المقال: {via} — لأن الموقع رفض فتحه مباشرة. (النص قد يختلف شكله قليلاً عن الأصل.)")
    if core._host(url) and core._host(url) != "news.google.com":
        st.markdown(f"📰 **الجريدة والبلد:** {src_label(core._host(url), with_domain=False)}", unsafe_allow_html=True)
    for _meta_label, _meta_value in article_reader_mod.metadata_rows(art):
        if _meta_label == "الكاتب" and wr:
            _meta_value = wr
        st.caption(f"ℹ️ **{_meta_label}:** {_meta_value}")
    if seen:
        st.markdown(f"🛰️ **وقت رصد المقال (توقيت القاهرة):** {fmt_seen(seen)}")

    if not orig_title or title.strip().lower() != orig_title.strip().lower():  # العنوان ظهر فوق؛ نكرره فقط لو الصفحة لها عنوان مختلف
        st.markdown(f"### {title_ar}")
        st.markdown(f"<div class='ltr' dir='ltr'>{html.escape(title)}</div>", unsafe_allow_html=True)

    if extraction["summary_allowed"]:
        if st.button("📝 ملخص المقال في نقاط", key="rd_summary"):
            with st.spinner("جارٍ استخراج أهم الجمل من النص المتاح وترجمتها…"):
                st.info(core.summarize(url))
        st.caption("الملخص المجاني يستخرج أهم الجمل من النص الذي أمكن الوصول إليه، وليس حكماً على اكتمال المقال.")
    else:
        st.warning("لن نقترح ملخصاً آلياً لهذا النص لأنه أقصر من الحد الأدنى المناسب؛ لتجنب ملخص مضلل.")

    copy_block(url, title, title_ar, art, body_ar)

    with st.expander("🎧 استمع للمقال بصوت مسموع", expanded=False):
        voice, rate = tts_settings("rd")
        part = st.radio("ما الذي يُقرأ؟", ["المقال كاملاً", "أول فقرات فقط (حوالي دقيقتين)"], horizontal=True, key="rd_part")
        rd_aud = st.session_state.setdefault("rd_audio", {})
        if st.button("🔊 ولّد الصوت", key="rd_go", use_container_width=True):
            txt = f"{title_ar}. {body_ar}"
            if part != "المقال كاملاً":
                txt = txt[:1800].rsplit(".", 1)[0] + "."
            with st.spinner("جارٍ تجهيز الصوت…"):
                res = make_audio(txt, voice, rate)
            if res:
                rd_aud.clear()
                rd_aud[url] = res
        if url in rd_aud:
            audio_block(rd_aud[url], "rd")

    st.divider()
    paras = "".join(
        f"<p>{html.escape(p)}</p>" for p in body_ar.split("\n") if p.strip() and p.strip().strip(".…") not in ("تحميل", "جار التحميل", "جارٍ التحميل")
    )
    st.markdown(f"<div class='article-body'>{paras}</div>", unsafe_allow_html=True)
    with st.expander("النص الأصلي"):
        st.text(art["text"])
    search_suggestions(title)
    if trunc_alt:
        st.divider()
        alt_block(title, url)



import base64 as _b64

_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 150" width="520" height="150" role="img" aria-label="Marsad Intelligence Center">
<defs>
 <linearGradient id="orb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a78bfa"/><stop offset=".48" stop-color="#22d3ee"/><stop offset="1" stop-color="#2563eb"/></linearGradient>
 <linearGradient id="glass" x1="0" y1="0" x2="0.9" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".48"/><stop offset="1" stop-color="#fff" stop-opacity=".02"/></linearGradient>
 <filter id="shadow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="8"/></filter>
</defs>
<circle cx="76" cy="76" r="64" fill="#22d3ee" opacity=".18" filter="url(#shadow)"/>
<circle cx="76" cy="76" r="57" fill="#101d36" stroke="#5267c9" stroke-width="2"/>
<circle cx="76" cy="76" r="43" fill="none" stroke="#39d8ed" stroke-width="2" opacity=".9"/>
<circle cx="76" cy="76" r="29" fill="none" stroke="#a78bfa" stroke-width="2" opacity=".9"/>
<path d="M76 18 A58 58 0 0 1 130 55 L76 76Z" fill="url(#orb)" opacity=".9"/>
<path d="M76 76 L119 48" stroke="#f8fafc" stroke-width="3" stroke-linecap="round"/>
<circle cx="119" cy="48" r="6" fill="#fbbf24" stroke="#fff" stroke-width="2"/>
<circle cx="76" cy="76" r="9" fill="url(#orb)" stroke="#fff" stroke-width="2"/>
<path d="M35 104 Q76 126 117 104" fill="none" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/>
<text x="160" y="70" font-family="Arial,Tahoma,sans-serif" font-size="49" font-weight="800" fill="#f8fafc" letter-spacing="1">MARSAD</text>
<text x="163" y="108" font-family="Tahoma,Arial,sans-serif" font-size="22" font-weight="600" fill="#a5b4fc">مركز الرصد والتحليل الاستخباراتي</text>
</svg>"""

def show_logo(width=300):
    """شعار المالك (Ehab Ibrahim) فوق في التاب"""
    b = _b64.b64encode(_LOGO_SVG.encode("utf-8")).decode()
    st.markdown(f"<div class='marsad-brand' style='direction:ltr;text-align:left;margin:0 0 12px'><img alt='Marsad Intelligence Center' width='{width}' src='data:image/svg+xml;base64,{b}'></div>",
                unsafe_allow_html=True)


def show_footer():
    st.divider()
    st.markdown(f"<div style='text-align:center;color:#94a3b8;font-size:.85rem'>© Ehab Ibrahim — رادار الأخبار العالمية · جميع الحقوق محفوظة · النسخة {APP_VERSION}</div>",
                unsafe_allow_html=True)


# ───────────────────────── بوابة الشفرات (اختيارية: تعمل فقط إن وُجد ADMIN_KEY في Secrets) ─────────────────────────

def _sec(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        v = None
    return v or os.getenv(name)


ADMIN_KEY, _GT, _GG = _sec("ADMIN_KEY"), _sec("GITHUB_TOKEN"), _sec("GIST_ID")
GATE_ON = bool(ADMIN_KEY and _GT and _GG)


def _adm_tok():
    """رمز جلسة المالك المشتق من ADMIN_KEY (لا يكشف المفتاح نفسه): يوضع في الرابط فيُعاد الدخول تلقائياً بعد انقطاع الجلسة"""
    import hashlib
    return hashlib.sha256(("marsad-session|" + (ADMIN_KEY or "")).encode("utf-8")).hexdigest()[:40]


def auth_qs():
    """يُلحق الشفرة بروابط صفحة القراءة (تُفتح في تبويب جديد = جلسة جديدة)"""
    a = st.session_state.get("auth") or {}
    return f"&k={quote(a['token'], safe='')}" if a.get("token") else ""


def _try_code(code):
    """يحاول الدخول بالشفرة؛ يعيد رسالة الخطأ أو '' عند النجاح"""
    code = (code or "").strip()
    if not code:
        return ""
    if hmac.compare_digest(code, ADMIN_KEY) or hmac.compare_digest(code, _adm_tok()):
        st.session_state["auth"] = {"role": "admin", "token": _adm_tok()}
        return ""
    try:
        k, why = keys_mod.touch(_GT, _GG, code)
    except Exception as e:
        return f"تعذّر التحقق الآن ({type(e).__name__}). أعد المحاولة بعد لحظات."
    if not k:
        return why
    st.session_state["auth"] = {"role": "guest", "token": keys_mod.norm(code), "label": k.get("label", ""),
                                "exp": keys_mod.iso(keys_mod.expires_at(k)), "checked": time.time(),
                                "scope": k.get("scope", "full")}
    return ""


def gate():
    ss = st.session_state
    if not GATE_ON:
        ss["auth"] = {"role": "admin", "token": ""}
        return
    a = ss.get("auth")
    msg = ""
    if a and a["role"] == "guest":
        exp = keys_mod.parse(a.get("exp"))
        if exp and keys_mod.now() > exp:
            ss.pop("auth")
            a, msg = None, "انتهت مدة التجربة."
        elif time.time() - a["checked"] > keys_mod.RECHECK_SECONDS:
            try:
                ok = keys_mod.recheck(_GT, _GG, a["token"])
            except Exception:
                ok = True  # تعذّر الفحص مؤقتاً: لا نطرد الضيف
            a["checked"] = time.time()
            if not ok:
                ss.pop("auth")
                a, msg = None, "أُلغيت هذه الشفرة أو انتهت مدتها."
    if a:
        # ثبّت الرمز في رابط الصفحة: لو انقطعت الجلسة (قفل شاشة الموبايل مثلاً) يُعاد الدخول تلقائياً بدل طلب الشفرة
        if a.get("token") and st.query_params.get("k", "") != a["token"]:
            st.query_params["k"] = a["token"]
        return
    code = st.query_params.get("k", "")
    if code and not ss.get("k_tried") == code:
        ss["k_tried"] = code
        msg = _try_code(code) or msg
        if ss.get("auth"):
            if ss["auth"].get("token"):
                st.query_params["k"] = ss["auth"]["token"]
            return
    show_logo()
    st.title("🔒 رادار الأخبار العالمية")
    st.markdown("هذه النسخة بالدعوة فقط. اكتب الشفرة التي وصلتك مع الرابط.")
    if msg:
        st.error(msg)
    entered = st.text_input("الشفرة", key="gate_code", type="password", placeholder="MR-XXXX-XXXX")
    if st.button("دخول", type="primary"):
        err = _try_code(entered)
        if err:
            st.error(err)
        else:
            st.rerun()
    st.stop()


gate()
IS_ADMIN = st.session_state["auth"]["role"] == "admin"

if "view" in st.query_params:
    reader_page()
    st.stop()

# ───────────────────────── التخزين: المحفوظات + المصادر المضافة ─────────────────────────

DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}$")
# فواصل العبارات: , ، ; سطر جديد، وكذلك النقطة بعد حرف عربي (مثل: مصر. الجيش المصري.) دون المساس بالاختصارات الإنجليزية
TERM_SPLIT = re.compile(r"[,،;\n]+|(?<=[\u0600-\u06FF])\.+(?=\s|$)")



def _secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        v = None
    return v or os.getenv(name)


GH_TOKEN, GH_GIST = _secret("GITHUB_TOKEN"), _secret("GIST_ID")
PERSIST = bool(GH_TOKEN and GH_GIST) and IS_ADMIN  # الضيف لا يرى بيانات المالك ولا يكتب فيها

if "store" not in st.session_state:
    _data, _err = store.empty(), None
    if PERSIST:
        try:
            _data = store.load(GH_TOKEN, GH_GIST)
        except Exception as _e:
            _err = f"تعذّر تحميل التخزين الدائم ({type(_e).__name__})"
    st.session_state["store"] = _data
    st.session_state["store_base"] = copy.deepcopy(_data)
    st.session_state["store_err"] = _err


def S():
    return st.session_state["store"]


def persist():
    if not PERSIST:
        return
    try:
        fresh = store.load(GH_TOKEN, GH_GIST)
        base = st.session_state.get("store_base", store.empty())
        local = S()
        merged, conflicts = store.three_way_merge(base, local, fresh)
        if conflicts:
            st.session_state["store_err"] = (
                "تم إيقاف الحفظ لحماية بياناتك: اكتشف المرصد تعديلات متعارضة من جلسة أخرى في "
                + ", ".join(conflicts[:8])
                + ". لم يتم استبدال البيانات الموجودة على Gist. أعد تحميل التطبيق وراجع التعديلات قبل إعادة المحاولة."
            )
            return False
        store.save(GH_TOKEN, GH_GIST, merged)
        st.session_state["store"] = merged
        st.session_state["store_base"] = copy.deepcopy(merged)
        st.session_state["store_err"] = None
        return True
    except Exception as e:
        st.session_state["store_err"] = f"تعذّر الحفظ الدائم ({type(e).__name__})"
        return False


def dispatch_tracked(workflow, label, dispatch_fn, *args):
    """يسجل طلب التشغيل قبل إرساله، ثم يسجل قبول GitHub أو فشله."""
    task = job_control_mod.new_task(workflow, label)
    S().setdefault("job_tasks", [])
    S()["job_tasks"] = job_control_mod.append_event(S()["job_tasks"], task)
    if PERSIST and not persist():
        return False, "لم يتم إرسال المهمة لأن حفظ سجل التشغيل تعذّر. راجع رسالة التخزين ثم أعد المحاولة."
    try:
        ok, message = dispatch_fn(*args)
        target = "submitted" if ok else "failed"
        job_control_mod.transition(task, target, message)
        S()["job_tasks"] = job_control_mod.append_event(S()["job_tasks"], task)
        if PERSIST:
            persist()
        return ok, message
    except Exception as exc:
        job_control_mod.transition(task, "failed", f"{type(exc).__name__}: {str(exc)[:250]}")
        S()["job_tasks"] = job_control_mod.append_event(S()["job_tasks"], task)
        if PERSIST:
            persist()
        return False, f"تعذّر إرسال المهمة ({type(exc).__name__})."


for _s in S()["sources"]:
    DOMAIN_LABELS[_s["domain"]] = _s["label"]

SAVE_KEYS = [
    "url", "title", "title_ar", "title_en", "seendate", "domain", "sourcecountry", "country_ar", "language",
    "ctype", "ctype_sure", "writer", "outlet", "wsrc", "snips", "snip_ar", "found", "fetched", "checked",
]


def flash(msg):
    st.session_state["flash"] = msg


def clean_domain(x):
    return (x or "").strip().lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/").split("/")[0]


def save_item(a, tab=""):
    s = S()
    if any(x.get("url") == a.get("url") for x in s["saved"]):
        return
    it = {k: a[k] for k in SAVE_KEYS if k in a}
    it["saved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    it["note"], it["tab"] = "", tab
    s["saved"].insert(0, it)
    persist()


def delete_item(url):
    S()["saved"] = [x for x in S()["saved"] if x.get("url") != url]
    persist()


def set_note(url, wkey):
    for x in S()["saved"]:
        if x.get("url") == url:
            x["note"] = st.session_state.get(wkey, "")
    persist()


def add_source():
    ss = st.session_state
    dom = clean_domain(ss.get("ms_domain", ""))
    if not DOMAIN_RE.match(dom):
        return flash("⚠️ الدومين غير صالح (مثال: example.com).")
    name = (ss.get("ms_name", "") or "").strip() or dom
    gname = ss.get("ms_group", "أمريكية")
    group = {"إسرائيلية": "il", "أمريكية": "us", "بريطانية": "uk", "تركيا/إيران/إثيوبيا": "rg"}[gname]
    lang = {"عبري": "he", "إنجليزي": "en", "كلاهما": "both", "تركي": "tr", "فارسي": "fa", "أمهري": "am", "عربي": "ar"}[ss.get("ms_lang", "إنجليزي")]
    if any(x["domain"] == dom and x["group"] == group for x in S()["sources"]):
        return flash("هذا المصدر مضاف مسبقاً.")
    S()["sources"].append({"label": name, "domain": dom, "lang": lang, "group": group})
    DOMAIN_LABELS[dom] = name
    persist()
    flash(f"✅ أُضيف «{name}» إلى مصادر التاب ({gname}) — يظهر هناك ضمن «مصادر أضفتَها».")


def add_writer():
    ss = st.session_state
    en = (ss.get("mw_en", "") or "").strip()
    ar = (ss.get("mw_ar", "") or "").strip()
    tw = core.twitter_handle(ss.get("mw_tw", ""))
    sites = [d for d in (clean_domain(x) for x in re.split(r"[,\s]+", ss.get("mw_sites", ""))) if DOMAIN_RE.match(d) and d not in ("x.com", "twitter.com")]
    country = {"أمريكي": "US", "بريطاني": "UK", "إسرائيلي": "IL", "سعودي": "SA", "خليجي": "GCC", "مصري": "EG", "عربي آخر": "AR"}[ss.get("mw_country", "أمريكي")]
    msg = lambda m: ss.__setitem__("mw_msg", m)
    if not (en or ar):
        return msg("⚠️ اكتب اسم الكاتب (بالعربي او بالانجليزي).")
    if country in ("US", "UK", "IL") and not sites:
        return msg("⚠️ الكاتب الاجنبي محتاج دومين موقع نشر واحد على الاقل (مثل nytimes.com).")
    if country not in ("US", "UK", "IL") and not (tw or sites):
        return msg("⚠️ للكاتب العربي لازم تكتب حساب تويتر (مثل @alfihrest) او موقع نشر.")
    if ss.get("mw_tw", "").strip() and not tw:
        return msg("⚠️ حساب تويتر مش مفهوم. اكتبه زي @name او الصق رابط الحساب.")
    ar = ar or (tr(en, "en", "ar") if en else "")
    en = en or ar
    heb = (ss.get("mw_heb", "") or "").strip()
    wid = "c_" + hashlib.md5((en + tw + ",".join(sites)).encode()).hexdigest()[:8]
    if any(w["id"] == wid for w in S()["writers"]):
        return msg("الكاتب ده مضاف قبل كده.")
    S()["writers"].append(
        {"id": wid, "name_ar": ar, "name_en": en, "outlet": (ss.get("mw_outlet", "") or "").strip() or (f"تويتر @{tw}" if tw else sites[0]),
         "country": country, "kind": ss.get("mw_kind", "رأي"), "sites": sites, "aliases": [],
         "heb": [heb, sites] if heb and sites else None, "twitter": tw}
    )
    persist()
    msg(f"✅ اتضاف الكاتب «{ar}»" + (f" (تويتر @{tw})" if tw else "") + " — هتلاقيه في تاب «كتّاب ومحللون» تحت قسم "
        + GROUP_LABELS.get(country, "") + ". وتقدر تلاقيه تحت في «ما أضفتَه».")


def remove_source(dom, group):
    S()["sources"] = [x for x in S()["sources"] if not (x["domain"] == dom and x["group"] == group)]
    persist()


def remove_writer(wid):
    S()["writers"] = [x for x in S()["writers"] if x["id"] != wid]
    persist()


def fill_author(idx):
    ss = st.session_state
    a = (ss.get("analysis") or {}).get("authors", [])[idx]
    ss["mw_en"] = a.get("en") or a["raw"]
    ss["mw_ar"] = a.get("ar", "")
    ss["mw_heb"] = a["raw"] if a.get("heb") else ""


def pick_author():
    names = [a["raw"] for a in (st.session_state.get("analysis") or {}).get("authors", [])]
    if st.session_state.get("mw_pick") in names:
        fill_author(names.index(st.session_state["mw_pick"]))


def do_analyze():
    ss = st.session_state
    url = (ss.get("ms_url", "") or "").strip()
    if not url:
        return
    try:
        res = core.analyze_url(url)
    except Exception as e:
        res = {"error": f"تعذّر التحليل ({type(e).__name__})", "authors": []}
    ss["analysis"] = res
    if res.get("domain"):
        ss["ms_domain"] = res["domain"]
        ss["ms_name"] = res.get("site_name") or res["domain"]
        g = res.get("group", "us")
        ss["ms_group"] = {"il": "إسرائيلية", "uk": "بريطانية", "us": "أمريكية"}[g]
        ss["ms_lang"] = "عبري" if res.get("lang") == "he" else "إنجليزي"
        ss["mw_sites"], ss["mw_outlet"] = res["domain"], ss["ms_name"]
        ss["mw_country"] = {"il": "إسرائيلي", "uk": "بريطاني", "us": "أمريكي"}[g]
    if (res.get("tweet") or {}).get("handle"):
        ss["mw_tw"] = res["tweet"]["handle"]
    if res.get("authors"):
        ss["mw_pick"] = res["authors"][0]["raw"]
        fill_author(0)


# ───────────────────────── الواجهة الرئيسية ─────────────────────────

show_logo()
st.title("مركز مرصد | الرصد والتحليل")
st.caption("منصة استخبارات المصادر المفتوحة · اجمع الإشارات، اربط الأدلة، وافهم الصورة الكاملة")
if not IS_ADMIN:
    _a = st.session_state["auth"]
    st.info(f"🎟️ نسخة تجريبية لـ «{_a.get('label', '')}» — "
            f"تنتهي {keys_mod.parse(_a['exp']).astimezone(core.TZ).strftime('%Y-%m-%d %H:%M')} بتوقيت القاهرة. "
            "لا يُحفظ شيء بعد إغلاق الصفحة.")


def render_about():
    """قسم «ما هذا التطبيق؟»: يُبنى من بيانات التطبيق نفسها فيتحدّث تلقائياً"""
    n_src = len({d for g in (ISRAEL, USA, UK, REGION, ARABIC, EGYPT) for ents in g.values() for _, d, _ in ents})
    stats = {"n_sources": n_src, "langs": [core.LANG_NAME_AR.get(c, c) for c, _, _, _ in core.LANGS],
             "n_writers": len(WRITERS), "n_files": len(intel.FILES), "file_names": list(intel.FILES), "threads": list(links_mod.THREADS)}
    with st.expander(about_plain("ما هذا التطبيق؟ وايه اللي بيعمله؟")):
        for title, body in about_sections(stats):
            st.markdown(f"**{about_plain(title)}**")
            if body is None:  # قائمة التابات من TAB_HELP
                st.markdown("\n".join(f"- **{about_plain(n)}:** {about_plain(TAB_HELP[n])}" for n in TAB_NAMES))
            else:
                st.markdown(about_plain(body))


def render_run_report():
    """زر المالك: تشغيل التقرير اليومي الآن من التطبيق (يستدعي GitHub Actions)"""
    tok, repo, branch = _sec("ACTIONS_TOKEN"), _sec("GH_REPO") or gh_actions.DEFAULT_REPO, _sec("GH_BRANCH") or "main"
    with st.expander("🔄 تحديث التقرير الآن (للمالك فقط)"):
        if not tok:
            st.info("لتفعيل الزر أضف في Secrets قيمة **ACTIONS_TOKEN**. أنشئ توكن من GitHub ← الصورة الشخصية ← Settings ← Developer settings ← "
                    "Personal access tokens ← Tokens (classic) ← Generate new token، وفعّل صلاحيتين: **repo** و**workflow**، ثم الصق قيمته. "
                    f"(المستودع الحالي: {repo})")
            return
        try:
            lr = gh_actions.last_run(tok, repo)
        except Exception as e:
            st.error(f"تعذّر قراءة حالة التشغيل ({type(e).__name__}). غالباً التوكن ناقص الصلاحية.")
            lr = None
        busy = bool(lr and lr["status"] in ("queued", "in_progress", "waiting", "requested"))
        if lr:
            ico = {"success": "✅ نجح", "failure": "❌ فشل", "cancelled": "⚪ أُلغي"}.get(lr["conclusion"] or "", "⏳ يعمل الآن" if busy else "—")
            when = keys_mod.parse(lr["created"])
            when_txt = when.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if when else ""
            st.markdown(f"آخر تشغيل: **{ico}** — بدأ {when_txt} (القاهرة) · [تفاصيله على GitHub]({lr['url']})")
        c1, c2 = st.columns(2)
        if c1.button("▶️ شغّل التقرير الآن", type="primary", disabled=busy, key="run_rep", use_container_width=True):
            ok, msg = dispatch_tracked("daily.yml", "التقرير اليومي", gh_actions.dispatch, tok, repo, branch)
            (st.success if ok else st.error)(msg)
        if c2.button("🔁 حدّث الحالة", key="run_status", use_container_width=True):
            st.rerun()
        if busy:
            st.caption("هناك تشغيل جارٍ، لذلك الزر معطّل حتى ينتهي. اضغط «حدّث الحالة» بين فترة وأخرى، ثم أعد تحميل الصفحة ليظهر التقرير الجديد.")


def render_workflow_overview():
    """لوحة مراقبة حديثة لتشغيلات GitHub Actions؛ لا تدّعي وجود Queue مشتركة."""
    tok = _sec("ACTIONS_TOKEN")
    repo = _sec("GH_REPO") or gh_actions.DEFAULT_REPO
    with st.expander("🧭 لوحة متابعة مهام المرصد عبر GitHub Actions", expanded=False):
        st.caption(f"المستودع: {repo} · تعرض آخر التشغيلات لكل Workflow. هذه لوحة متابعة وليست طابوراً مركزياً يمنع التزامن.")
        if not tok:
            st.info("أضف ACTIONS_TOKEN في Streamlit Secrets لعرض حالة التشغيلات. لا تضع التوكن داخل المحادثة.")
            return
        if st.button("🔄 تحديث جميع حالات التشغيل", key="refresh_all_workflows"):
            st.session_state.pop("workflow_overview_cache", None)
        cache = st.session_state.get("workflow_overview_cache")
        if not cache or time.time() - cache.get("at", 0) > 90:
            try:
                cache = {"at": time.time(), "rows": gh_actions.recent_runs(tok, repo, 3), "error": None}
            except Exception as exc:
                cache = {"at": time.time(), "rows": [], "error": f"{type(exc).__name__}: {str(exc)[:180]}"}
            st.session_state["workflow_overview_cache"] = cache
        if cache.get("error"):
            st.error(f"تعذر جلب حالات GitHub: {cache['error']}")
            return
        rows = cache.get("rows", [])
        if not rows:
            st.info("لم يرجع GitHub أي تشغيلات لهذه الـ Workflows حتى الآن.")
            return
        for row in rows[:15]:
            busy = row.get("status") in ("queued", "in_progress", "waiting", "requested")
            state = ("يعمل الآن" if busy else row.get("conclusion") or row.get("status") or "غير معروف")
            created = keys_mod.parse(row.get("created"))
            stamp = created.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if created else ""
            st.markdown(f"**{row['label']}** · {state} · {stamp} · [تفاصيل التشغيل]({row.get('url')})")
        stale_changed = job_control_mod.mark_stale(S().get("job_tasks", []), stale_after_minutes=90)
        if stale_changed and PERSIST:
            persist()
        task_rows = S().get("job_tasks", [])[:12]
        if task_rows:
            st.markdown("#### سجل طلبات التشغيل من داخل المرصد")
            labels = {"queued": "في انتظار الإرسال", "submitted": "قبله GitHub", "running": "يعمل", "succeeded": "نجح", "failed": "فشل", "cancelled": "أُلغي", "stale": "يحتاج مراجعة"}
            for task in task_rows:
                state = labels.get(task.get("state"), task.get("state", "غير معروف"))
                created = keys_mod.parse(task.get("created_at"))
                stamp = created.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if created else ""
                last_event = (task.get("events") or [{}])[-1]
                st.caption(f"{task.get('label', task.get('workflow'))} · {state} · {stamp} · {last_event.get('message', '')}")
        else:
            st.caption("لم تُسجّل طلبات تشغيل من داخل هذه النسخة بعد.")
        st.caption("تنبيه هندسي: السجل يوثق طلب الإرسال ورد GitHub فقط. حالة التنفيذ النهائية تُقرأ من GitHub Actions، ولا يوجد حتى الآن قفل ذري مشترك بين كل أنواع المهام.")


def render_daily():
    st.caption("نشرة تُولَّد تلقائياً كل صباح (نحو 6 بتوقيت القاهرة) لكل ملف، من عناوين عشرات المصادر العالمية والعربية، "
               "مع ما يخص مصر. ترتيب وتجميع للعناوين نفسها (بلا ذكاء اصطناعي)، وليس حكماً على صحة الأخبار.")
    if IS_ADMIN:
        render_run_report()
    if not (_GT and _GG):
        st.info("التقرير اليومي يحتاج التخزين الدائم (GITHUB_TOKEN وGIST_ID).")
        return
    if "reports" not in st.session_state or time.time() - st.session_state.get("reports_t", 0) > 600:
        try:
            st.session_state["reports"] = store.load_reports(_GT, _GG)
        except Exception as e:
            st.error(f"تعذّر تحميل التقارير ({type(e).__name__}).")
            return
        st.session_state["reports_t"] = time.time()
    rp = st.session_state["reports"]
    days = sorted((rp.get("archive") or {}).keys(), reverse=True)
    if not days:
        st.info("لا يوجد تقرير بعد. شغّل خطوة «التقرير اليومي» من GitHub Actions أول مرة (راجع README)، وبعدها يتجدد وحده كل صباح.")
        return
    day = st.selectbox("التاريخ", days, key="dr_day")
    rep = rp["archive"][day]
    gen = keys_mod.parse(rep.get("generated"))
    if gen:
        st.caption(f"آخر تحديث: {gen.astimezone(core.TZ).strftime('%Y-%m-%d %H:%M')} بتوقيت القاهرة")
    names = list(rep["files"].keys())
    pick_ = st.radio("الملف", (["📌 نشرة اليوم"] if rep.get("overview") else []) + names, horizontal=True, key="dr_file")
    if pick_.startswith("📌"):
        st.markdown(rep["overview"])
        return
    f = rep["files"][pick_]
    st.caption(f"عدد العناوين التي فُحصت: {f.get('total', '—')} · منها يخص مصر: {f.get('egypt', '—')}")
    if f.get("brief"):
        st.markdown(f["brief"])
    elif f.get("error"):
        st.warning("تعذّر توليد هذا الملف اليوم.")
    else:
        st.info("لا ملخص لهذا الملف (العناوين أدناه).")
    shown = f.get("items", [])
    if not shown:
        return
    only_eg = st.checkbox("🇪🇬 المتعلق بمصر فقط", value=False, key="dr_eg")
    with st.expander(f"📋 العناوين ({len(shown)})", expanded=not f.get("brief")):
        for a in shown:
            if only_eg and not a.get("egypt"):
                continue
            try:
                lnk = f"?view={quote(a['url'], safe='')}&seen={a.get('seendate', '')}&t={quote(a['title'][:200], safe='')}{auth_qs()}"
                eg_mark = "🇪🇬 " if a.get("egypt") else ""
                side_txt = intel.SIDES.get(a.get("side", ""), "")
                line = (f"- {eg_mark}**{a.get('title_ar', '')}** — {src_label(a.get('domain', ''))} · {a.get('ctype', '')} · "
                        f"{side_txt}  \n  [ترجم المقال]({lnk}) · [الأصل]({a.get('url', '')})")
                if a.get("ents"):
                    line += "  \n  🏷️ " + "، ".join(str(x) for x in a["ents"])
                if a.get("snip_ar"):
                    line += "  \n  > " + str(a["snip_ar"])
                st.markdown(line)
            except Exception as e:
                st.caption(f"⚠️ تعذّر عرض عنوان ({type(e).__name__}: {e})")


render_about()
if not IS_ADMIN and st.session_state["auth"].get("scope") == "reports":
    render_daily()  # اشتراك «تقرير فقط»: لا يرى بقية التطبيق
    show_footer()
    st.stop()

# ───────── حفظ نتائج البحث: تبقى (للمالك) حتى تبحث من جديد، حتى لو انقطع الاتصال او فتحت التطبيق لاحقا ─────────
RES_FILE = "marsad_results.json"


def _res_sig(d):
    its = d.get("items") or []
    # Include query metadata and a compact digest of URLs so a new search with
    # the same result count is still recognized and persisted.
    urls = "\n".join(str(x.get("url", "")) for x in its[:200] if isinstance(x, dict))
    digest = hashlib.sha256(urls.encode("utf-8")).hexdigest()[:16]
    return [len(its), digest, str(d.get("query") or d.get("keyword") or ""),
            len(d.get("summaries") or {}), len(d.get("used") or [])]


if PERSIST and "_res_loaded" not in st.session_state:
    st.session_state["_res_loaded"] = True
    st.session_state["_res_loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    st.session_state["_res_sigs"] = {}
    try:
        for _k, _v in (store.load_file(GH_TOKEN, GH_GIST, RES_FILE, {}) or {}).items():
            if isinstance(_v, dict) and f"res_{_k}" not in st.session_state:
                st.session_state[f"res_{_k}"] = _v
                st.session_state["_res_sigs"][_k] = _res_sig(_v)
    except Exception:
        pass


AUTO_INTEL_FILE = "marsad_auto_intel.json"


def auto_intel(force=False):
    """نتايج «تحديث الأقسام الذكية» اللي بتشتغل لوحدها على GitHub (بنقراها مرة كل دقيقتين بالكتير)"""
    ss = st.session_state
    if not PERSIST:
        return {}
    if force or time.time() - ss.get("_auto_intel_at", 0) > 120:
        try:
            ss["_auto_intel"] = store.load_file(GH_TOKEN, GH_GIST, AUTO_INTEL_FILE, {}) or {}
        except Exception:
            ss.setdefault("_auto_intel", {})
        ss["_auto_intel_at"] = time.time()
    return ss.get("_auto_intel") or {}


def seed_from_auto():
    """لو مفيش نتيجة يدوي في التاب، اعرض آخر نتيجة تلقائية بدل الصفحة الفاضية"""
    ai = auto_intel()
    ss = st.session_state
    if not ai or ss.get("_auto_seeded") == ai.get("finished"):
        return
    ss["_auto_seeded"] = ai.get("finished")
    if ai.get("paid") and (not ss.get("paid_radar_results") or ss["paid_radar_results"].get("auto")):
        ss["paid_radar_results"] = {**ai["paid"], "auto": True}
    if ai.get("health") and (not ss.get("source_health_latest") or ss["source_health_latest"].get("auto")):
        ss["source_health_latest"] = {**ai["health"], "auto": True}
    if ai.get("dossier") and (not ss.get("intel_cluster_latest") or ss["intel_cluster_latest"].get("auto")):
        ss["intel_cluster_latest"] = ai["dossier"]
        ss["intel_cluster_notes"] = [f"📥 دي حصيلة تلقائية من البحث الشامل ({len(ai['dossier'].get('articles', []))} عنوان)."]
    w = ai.get("warning") or {}
    if w.get("alerts") and not ss.get("early_warning_last_alerts"):
        ss["early_warning_last_alerts"] = w["alerts"]


def auto_note(kind):
    """سطر صغير فوق التاب يقول آخر تحديث تلقائي كان إمتى"""
    ai = auto_intel()
    at = {"paid": (ai.get("paid") or {}).get("at"), "health": (ai.get("health") or {}).get("checked_at"),
          "dossier": (ai.get("dossier") or {}).get("created_at"), "warning": (ai.get("warning") or {}).get("at")}.get(kind)
    t = keys_mod.parse(at) if at else None
    if t:
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        st.caption(f"🤖 آخر تحديث تلقائي (GitHub): {t.astimezone(core.TZ).strftime('%Y-%m-%d %H:%M')} بتوقيت القاهرة. "
                   "بيتحدّث لوحده كل يوم بعد البحث الشامل، والأزرار تحت لو عايز تعمل فحص بنفسك دلوقتي.")
    else:
        st.caption("🤖 القسم ده بيتحدّث لوحده كل يوم بعد البحث الشامل (من «غرفة العمليات» ← تحديث الأقسام الذكية). لسه ماتعملش تحديث تلقائي.")


def render_auto_intel_panel():
    """زرار تشغيل «تحديث الأقسام الذكية» على GitHub وحالته"""
    with st.expander("🤖 تحديث الأقسام الذكية تلقائياً (الرادار المدفوع، التجميع، الكيانات، الإنذار المبكر، صحة المصادر)", expanded=False):
        st.caption("بيشتغل لوحده كل يوم بعد ما البحث الشامل يخلص، من غير ذكاء اصطناعي ومن غير تكلفة. وتقدر تشغّله دلوقتي من هنا.")
        ai = auto_intel()
        if ai.get("finished") or ai.get("started"):
            t = keys_mod.parse(ai.get("finished") or ai.get("started"))
            if t and t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            st.markdown(f"آخر تشغيل: **{'✅ خلص' if ai.get('state') == 'done' else '⏳ شغال'}** · "
                        f"{t.astimezone(core.TZ).strftime('%Y-%m-%d %H:%M') if t else ''} · أخبار اتحللت: {ai.get('pool_size', 0)}")
            for name, stt in (ai.get("steps") or {}).items():
                st.caption(("✅ " if stt.get("ok") else "❌ ") + name + (" (اتأجل، بيتعمل كل 3 أيام)" if stt.get("skipped") else "")
                           + (f" — {stt.get('error')}" if stt.get("error") else ""))
        tok = _sec("ACTIONS_TOKEN")
        b1, b2 = st.columns(2)
        if b1.button("▶️ شغّل التحديث دلوقتي", type="primary", use_container_width=True, key="auto_intel_run", disabled=not tok):
            ok, msg = gh_actions.dispatch(tok, _sec("GH_REPO") or gh_actions.DEFAULT_REPO, _sec("GH_BRANCH") or "main", "monitor.yml")
            (st.success if ok else st.error)(msg)
        if b2.button("🔄 حمّل آخر نتيجة", use_container_width=True, key="auto_intel_reload"):
            auto_intel(force=True)
            st.session_state.pop("_auto_seeded", None)
            seed_from_auto()
            st.success("✅ اتحمّلت. افتح أي قسم من الأقسام الذكية تلاقي النتيجة.")
        if not tok:
            st.caption("محتاج ACTIONS_TOKEN في Secrets عشان زرار التشغيل.")


def _pack_res(v):
    out = {**v, "items": (v.get("items") or [])[:200], "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    return json.loads(json.dumps(out, ensure_ascii=False, default=str))


def reload_results():
    """يجيب آخر نتائج محفوظة (بما فيها نتيجة البحث الشامل اللي اشتغل على GitHub) ويستبدل بيها اللي في الصفحة"""
    got = store.load_file(GH_TOKEN, GH_GIST, RES_FILE, {}) or {}
    st.session_state["_res_sigs"] = {}
    n = 0
    for _k, _v in got.items():
        if isinstance(_v, dict) and "items" in _v:
            st.session_state[f"res_{_k}"] = _v
            st.session_state["_res_sigs"][_k] = _res_sig(_v)
            n += 1
    st.session_state["_res_loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return n


def auto_pull_jobs():
    """لو بحث GitHub (الشامل أو تتبّع موضوع) خلص بعد ما فتحت الصفحة، بنحمّل نتيجته لوحدنا (بنبص كل دقيقتين بس)"""
    ss = st.session_state
    if not PERSIST or time.time() - ss.get("_jobs_chk", 0) < 120:
        return False
    ss["_jobs_chk"] = time.time()
    loaded = keys_mod.parse(ss.get("_res_loaded_at") or "")
    newest = None
    for fname in (SEARCH_STATUS, TOPIC_STATUS):
        try:
            stt = store.load_file(GH_TOKEN, GH_GIST, fname, {}) or {}
        except Exception:
            continue
        fin = keys_mod.parse(stt.get("finished") or "") if stt.get("state") == "done" else None
        if fin and (newest is None or fin > newest):
            newest = fin
    if newest and (loaded is None or newest > loaded):
        try:
            reload_results()
            ss["_res_loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            ss["sa_status"] = store.load_file(GH_TOKEN, GH_GIST, SEARCH_STATUS, {}) or {}
            return True
        except Exception:
            return False
    return False


def save_results():
    """بيحفظ بس التابات اللي اتغيرت في الصفحة دي، وبيدمجها فوق المحفوظ (عشان ما يمسحش نتايج البحث الشامل بتاع GitHub)"""
    if not PERSIST:
        return
    sigs = st.session_state.setdefault("_res_sigs", {})
    cur = {k[4:]: v for k, v in st.session_state.items() if k.startswith("res_") and isinstance(v, dict) and "items" in v}
    changed = {k: v for k, v in cur.items() if sigs.get(k) != _res_sig(v)}
    if not changed:
        return
    try:
        remote = store.load_file(GH_TOKEN, GH_GIST, RES_FILE, {}) or {}
        remote.update({k: _pack_res(v) for k, v in changed.items()})
        store.save_file(GH_TOKEN, GH_GIST, RES_FILE, remote)
        for k, v in changed.items():
            st.session_state["_res_sigs"][k] = _res_sig(v)
    except Exception:
        pass


# ───────── التابات فوق، وكل تاب بحث يعرض فلاترَه داخله (القيم تُقرأ كمتغيرات عامة وقت تنفيذ التاب) ─────────
_now0 = datetime.now(timezone.utc)
query, match, joiner, ctype = "", core.MATCH_MODES[0], "AND", "الكل"
start_utc, end_utc, max_rec, verify, hide_nomatch = _now0 - timedelta(days=7), _now0, 30, True, False

# التنقّل: اختيار القسم بيرسم القسم ده بس (قبل كده كل الأقسام والتابات كانت بتترسم مع كل دوسة، فالتطبيق كان تقيل).
MAIN_SECTIONS = {"home": "🏠 الرئيسية", "search": "🔎 البحث والرصد", "intel": "🛰️ التحليل والاستخبارات",
                 "ops": "⏱️ غرفة العمليات", "library": "🗂️ الملفات والأرشيف", "settings": "⚙️ المصادر والإعدادات",
                 "guide": "📘 دليل الاستخدام"}
SUB_SECTIONS = {
    "search": {"geo": "🌍 بحث حسب المنطقة", "eg": "🇪🇬 الشأن المصري", "ml": "🔤 ترجمة ثم بحث", "br": "🗞️ تصفح المصادر",
               "paid": "🧾 رادار التقارير المدفوعة", "gd": "🌐 بحث GDELT"},
    "intel": {"wr": "✍️ كتّاب ومحللون", "in": "🛰️ مكتب الاستخبارات", "health": "🩺 صحة المصادر",
              "clusters": "🧩 تجميع الأحداث والروايات", "entities": "🧭 الكيانات والتناقضات"},
    "library": {"dos": "🧵 الملفات والخيوط", "sv": "📌 المحفوظات", "lab": "🧠 ورشة التحليل"},
}


def _nav_pick(label, options, key, qp):
    """اختيار بيتفتكر في رابط الصفحة، فلو عملت تحديث للصفحة بترجع لنفس المكان"""
    opts = list(options)
    if key not in st.session_state:
        try:
            v = st.query_params.get(qp)
        except Exception:
            v = None
        st.session_state[key] = v if v in opts else opts[0]
    val = st.radio(label, opts, format_func=options.get, horizontal=True, key=key, label_visibility="collapsed")
    try:
        if st.query_params.get(qp) != val:
            st.query_params[qp] = val
    except Exception:
        pass
    return val


st.markdown("<div id='marsad-main-nav-start'></div>", unsafe_allow_html=True)
NAV_MAIN = _nav_pick("القسم", MAIN_SECTIONS, "nav_main", "sec")
NAV_SUB = ""
if NAV_MAIN in SUB_SECTIONS:
    st.markdown("<div id='marsad-sub-nav-start'></div>", unsafe_allow_html=True)
    NAV_SUB = _nav_pick("القسم الفرعي", SUB_SECTIONS[NAV_MAIN], f"nav_sub_{NAV_MAIN}", "sub")
st.markdown("<div class='marsad-nav-gap'></div>", unsafe_allow_html=True)


def _on(main, sub=""):
    return NAV_MAIN == main and (not sub or NAV_SUB == sub)


_page = st.container()
tab_home = tab_search = tab_intel = tab_ops = tab_library = tab_settings = tab_guide = _page
tab_geo = tab_eg = tab_ml = tab_br = tab_paid = tab_gd = _page
tab_wr = tab_in = tab_health = tab_clusters = tab_entities = _page
tab_dos = tab_sv = tab_lab = _page
tab_dr = tab_ops
tab_ms = tab_settings
home_box = tab_home


def use_filters(p, level="full"):
    """يرسم فلاتر هذا التاب (مفاتيحها تبدأ بـ p) ويضبط المتغيرات العامة التي تقرأها دوال البحث.
    level: full = كلمات + وقت + نوع، kw = كلمات + نوع فقط"""
    g = globals()
    g["query"] = st.text_input(
        "🔎 كلمات البحث", key=f"{p}_q",
        placeholder="مثال: وزير الخارجية المصري   —   او عدة مواضيع بفاصلة: اليمن، الحوثيين، مصر",
        help="كل ما بين فاصلتين (، او , او . بعد كلمة عربية) يُعامل كموضوع مستقل. بدون فاصلة تُعتبر الجملة كلها عبارة واحدة. للعرض بدون كلمات استخدم «اعرض كل ما نُشر».",
    )
    with st.expander("⚙️ فلاتر متقدمة (المطابقة، الوقت، نوع المحتوى)" if level == "full" else "⚙️ فلاتر (نوع المحتوى وربط العبارات)"):
        c1, c2 = st.columns(2)
        if level == "full":
            g["match"] = c1.radio("طريقة مطابقة كل عبارة", core.MATCH_MODES, key=f"{p}_match",
                                  help="Near: الكلمات متقاربة بأي ترتيب (الأنسب للجمل). Exact: العبارة بنصها المترجم حرفياً. AND: الكلمات موجودة في المقال في أي موضع.")
        jl = c2.radio("عند وجود أكثر من عبارة", ["كلها معاً (AND)", "أيٌّ منها (OR)"], key=f"{p}_join")
        g["joiner"] = "OR" if "OR" in jl else "AND"
        g["ctype"] = st.selectbox("نوع المحتوى", ["الكل", "خبر", "تحليل", "رأي"], key=f"{p}_ct0")
        if level == "full":
            mode = st.radio("النطاق الزمني", ["آخر ساعات", "آخر أيام", "تواريخ محددة"], horizontal=True, key=f"{p}_mode")
            now_utc = datetime.now(timezone.utc)
            if mode == "آخر ساعات":
                h = pick(st, "عدد الساعات", [1, 2, 3, 6, 12, 24, 36, 48, 72], 24, f"{p}_h")
                g["start_utc"], g["end_utc"] = now_utc - timedelta(hours=h), now_utc
            elif mode == "آخر أيام":
                d = pick(st, "عدد الأيام", [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90], 7, f"{p}_d")
                g["start_utc"], g["end_utc"] = now_utc - timedelta(days=d), now_utc
            else:
                today = datetime.now(core.TZ).date()
                rng = st.date_input("من – إلى", value=(today - timedelta(days=3), today), max_value=today, key=f"{p}_rng")
                if isinstance(rng, (list, tuple)) and len(rng) == 2:
                    s, e = rng
                else:
                    s = e = rng[0] if isinstance(rng, (list, tuple)) else rng
                g["start_utc"] = datetime(s.year, s.month, s.day, tzinfo=core.TZ).astimezone(timezone.utc)
                g["end_utc"] = datetime(e.year, e.month, e.day, 23, 59, 59, tzinfo=core.TZ).astimezone(timezone.utc)
            g["max_rec"] = pick(st, "عدد النتائج الأقصى", range(10, 110, 10), 30, f"{p}_max")
            g["verify"] = st.checkbox("🔍 افحص نص كل مقال واعرض جملة ذُكرت فيها كلمتك (أبطأ)", value=True, key=f"{p}_ver")
            g["hide_nomatch"] = st.checkbox("🚫 أخفِ المقالات التي لا تظهر كلمتك في نصها (موصى به)", value=True, key=f"{p}_hide",
                                            help="أخبار جوجل وGDELT أحياناً يرجّعوا مقالات الكلمة فيها بعيدة عن العنوان او مش موجودة. الفحص بيقرا نص المقال ويشيل اللي مفيهوش كلمتك.")
    if level == "full":
        st.caption("النتايج اللي تطلع بتفضل محفوظة، ومبتتمسحش غير لما تبحث من جديد.")


def pick_sources(key, groups, allow_custom=True):
    custom_lang = "en" if key == "rg" else ("ar" if key == "eg" else "both")
    """يعرض اختيار المصادر ويعيد قائمة (label, domains, lang)"""
    chosen = []
    extra_src = [(x["label"], x["domain"], x["lang"]) for x in S()["sources"] if x["group"] == key]
    if extra_src:
        groups = {**groups, "➕ مصادر أضفتَها": extra_src}
    for gname, entries in groups.items():
        labels = [e[0] for e in entries]
        sel = st.multiselect(gname, labels, default=labels, key=f"{key}_{gname}")
        chosen += [e for e in entries if e[0] in sel]
    if allow_custom:
        extra = st.text_input(
            "➕ مواقع إضافية (دومين واحد أو أكثر، بفاصلة)", placeholder="example.com, another.org", key=f"{key}_extra"
        )
        for dmn in re.split(r"[,\s]+", extra.strip().lower()):
            dmn = dmn.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
            if dmn and DOMAIN_RE.match(dmn):
                chosen.append((dmn, dmn, custom_lang))
    return chosen


def update_meta(data, sel):
    counts, ctry = {}, {}
    for a in data["items"]:
        n = source_name(a.get("domain", ""))
        counts[n] = counts.get(n, 0) + 1
        ctry[n] = source_country(a.get("domain", ""))
    data["counts"], data["ctry"] = counts, ctry
    data["silent"] = [lbl for lbl, _, _ in (sel or []) if lbl not in counts]


def do_search(key, jobs, sel=None, terms=None, pre=False, seed=None):
    terms = terms or [t.strip() for t in TERM_SPLIT.split(query) if t.strip()]
    if not terms:
        st.warning("اكتب كلمة بحث أولاً (في الخانة فوق في التاب).")
        return
    if not jobs:
        st.warning("اختر مصدراً واحداً على الأقل.")
        return
    # زر الإيقاف: الضغط عليه يقطع التنفيذ الجاري، وما ظهر حتى الآن محفوظ في session_state ويُعرض كاملاً
    st.button("⏹ إيقاف البحث والاكتفاء بالنتائج الظاهرة", key=f"stop_{key}")
    status_ph, live_ph = st.empty(), st.empty()
    status_ph.info("⏳ جارٍ التحضير والترجمة…")
    matchers = core.make_matchers_pre(jobs) if pre else core.make_matchers(terms, [j["code"] for j in jobs])
    hl = sorted({st_ for alts in matchers for stems in alts for st_ in stems}, key=len, reverse=True)
    data = {
        "items": [], "errors": [], "used": [], "summaries": {}, "counts": {}, "silent": [],
        "hidden": 0, "hl": hl, "partial": True,
    }
    st.session_state[f"res_{key}"] = data
    seed = seed or []

    def merged(items):
        have = {a["url"] for a in items}
        return sorted(items + [a for a in seed if a["url"] not in have], key=lambda a: a.get("seendate", ""), reverse=True)

    if seed:
        data["items"] = merged([])
        update_meta(data, sel)
        live_ph.markdown(live_html(data["items"], hl), unsafe_allow_html=True)
    for ev in core.search_iter(terms, joiner, match, jobs, start_utc, end_utc, max_rec, ctype):
        status_ph.info(f"🔎 {ev['msg']}")
        data["errors"], data["used"] = ev["errors"], ev["used"]
        if ev["items"] is not None:
            core.translate_titles([a for a in ev["items"] if "title_ar" not in a])
            data["items"] = merged(ev["items"])
            update_meta(data, sel)
            live_ph.markdown(live_html(data["items"], hl), unsafe_allow_html=True)
    if verify and data["items"]:
        items = data["items"]
        total = min(len(items), 80)
        for i in range(0, total, 8):
            status_ph.info(f"🔍 جارٍ فحص نصوص المقالات… ({i}/{total})")
            core.enrich_items(items[i:i + 8], matchers, joiner, limit=8)
            live_ph.markdown(live_html(items, hl), unsafe_allow_html=True)
    # تشديد نافذة التاريخ بعد دمج نتائج GDELT وGoogle News والخلاصات المباشرة.
    # النتائج بلا تاريخ تظل ظاهرة لكن تُوسم بأنها غير مؤرخة.
    window_hours = max(1.0, (end_utc - start_utc).total_seconds() / 3600)
    data["items"] = intelligence_pipeline_mod.filter_window(data["items"], window_hours, now=end_utc)
    # ترجمة مقتطفات البطاقات تلقائياً، دون استدعاء أي API مدفوع.
    data["items"] = intelligence_pipeline_mod.prepare_cards(
        data["items"], translate_text=lambda texts: core._batch_tr(texts, "ar")
    )
    data["threads"] = intelligence_pipeline_mod.cluster_items(data["items"])
    update_meta(data, sel)
    if hide_nomatch:
        raw = data["items"]
        data["items"] = [a for a in raw if not (a.get("fetched") and not a.get("found"))]
        data["hidden"] = len(raw) - len(data["items"])
    data["partial"] = False
    # ملف بحث تلقائي من كل النتائج، مع حفظ المصدر والرابط والمعرّفات. لا يحتاج اختياراً يدوياً.
    if data["items"]:
        try:
            batch = intelligence_pipeline_mod.build_research_bundle(
                f"{key} | {', '.join(terms[:4])} | آخر {window_hours:g} ساعة", data["items"]
            )
            S().setdefault("research_batches", []).append(batch)
            S()["research_batches"] = S()["research_batches"][-30:]
            data["auto_research_batch_id"] = batch["id"]
            data["auto_research_batch_title"] = batch["title"]
            persist()
        except Exception as exc:
            data["auto_research_error"] = type(exc).__name__
    status_ph.success(f"✅ اكتمل البحث والتجهيز — {len(data['items'])} نتيجة")
    live_ph.empty()


def highlight(text, stems):
    out = html.escape(text)
    for st_ in stems:
        out = re.sub(f"({re.escape(html.escape(st_))})", r"<b>\1</b>", out, flags=re.I)
    return out


def card_html(a):
    url = a.get("url", "")
    link = (f"?view={quote(url, safe='')}&seen={a.get('seendate', '')}&t={quote(a.get('title', '')[:200], safe='')}"
            f"&wr={quote(a.get('writer', '') or '', safe='')}&o={quote(a.get('outlet', '') or '', safe='')}{auth_qs()}")
    orig = html.escape(a.get("title", ""))
    en = a.get("title_en", "")
    en_line = f"<div class='ltr' dir='ltr'>EN: {html.escape(en)}</div>" if en and en != a.get("title") else ""
    dom = a.get("domain", "")
    src = src_label(dom)
    ctag = a.get("ctype", "") + ("" if a.get("ctype_sure") else " (تقدير)")
    wline = (
        f"✍️ الكاتب: <b>{html.escape(a['writer'])}</b> — {html.escape(a.get('outlet', ''))} "
        + ("· 📌 من صفحة الكاتب" if a.get("wsrc") == "feed" else "· 🔎 بحث باسم الكاتب")
        + {True: " · ✅ الاسم مؤكَّد في توقيع المقال", False: " · ⚠️ الاسم لم يظهر في توقيع الصفحة"}.get(a.get("byline"), "")
        + "<br>"
        if a.get("writer")
        else ""
    )
    return (
        f"<div class='ar-title'>{html.escape(a.get('title_ar', ''))}</div>"
        f"<div class='ltr' dir='ltr'>{orig}</div>{en_line}"
        f"<div class='meta'>🕒 {fmt_seen(a.get('seendate', ''))} (القاهرة)<br>{wline}"
        f"🌐 المصدر: {src}"
        + (f" · 🧭 {html.escape(a['country_ar'])}" if a.get("side") and a.get("country_ar") else "")
        + f" · <span class='badge'>{html.escape(ctag)}</span></div>"
        f"<a class='btn' href='{html.escape(link)}' target='_blank' rel='noopener'>ترجم المقال</a>"
    )


_MLVL = {"محوري": "🟢 المقال عن كلمتك فعلاً", "ملحوظ": "🟡 ذُكرت بشكل ملحوظ", "عابر": "⚪ ذكر عابر غالباً (مش موضوع المقال)"}


def mention_line(a):
    if a.get("mcount") is None or not a.get("fetched"):
        return ""
    n, w = a["mcount"], max(1, a.get("words", 1))
    return f"🔢 كلمتك ذُكرت **{n}** مرة في مقال حوالي {w} كلمة — {_MLVL.get(a.get('mlevel'), '')}"


def snippet_html(a, hl):
    if not a.get("checked"):
        return ""
    if not a.get("fetched"):
        return "<div class='meta'>ℹ️ تعذّر فحص نص المقال (قد يكون خلف اشتراك أو يحجب الزحف).</div>"
    if a.get("found"):
        ml = mention_line(a).replace("**", "")
        out = f"<div class='meta'>✅ ذُكرت كلمتك في نص المقال:</div>" + (f"<div class='meta'>{html.escape(ml)}</div>" if ml else "") + f"<div>{html.escape(a.get('snip_ar', ''))}</div>"
        for sn in a.get("snips", []):
            out += f"<div class='ltr' dir='ltr'>{highlight(sn, hl)}</div>"
        return out
    return "<div class='meta'>⚠️ كلمتك لم تظهر في نص هذا المقال.</div>"


def live_html(items, hl):
    """عرض خفيف (بدون أزرار) أثناء البحث؛ تُرسم الأزرار الكاملة بعد الانتهاء أو الإيقاف"""
    return "".join(f"<div class='card'>{card_html(a)}{snippet_html(a, hl)}</div>" for a in items)


def render_results(key):
    data = st.session_state.get(f"res_{key}")
    if data is None:
        if PERSIST:
            st.info("لا توجد نتائج محمّلة في هذه الجلسة. يمكنك استرجاع آخر نتائج البحث المحفوظة من الأرشيف.")
            if st.button("↻ استرجاع نتائج البحث المحفوظة", key=f"restore_results_{key}"):
                n_restored = reload_results()
                st.success(f"تم استرجاع {n_restored} مجموعة نتائج محفوظة.")
                st.rerun()
        else:
            st.info("نتائج البحث تظل في الجلسة الحالية. لتظل متاحة بعد إغلاق التطبيق أو فتحه من جهاز آخر، فعّل التخزين الدائم عبر GitHub Gist.")
        return
    st.caption("📌 نتائج هذا التاب تظل محفوظة عند التنقل بين أقسام التطبيق، ولا تُستبدل إلا عند إجراء بحث جديد في التاب نفسه. ومع تفعيل GitHub Gist يمكن استرجاعها بعد إعادة فتح التطبيق.")
    if data.get("partial"):
        st.warning("⏹ توقّف البحث قبل اكتماله — هذه هي النتائج التي وُجدت حتى الآن (وقد لا تشمل فحص النصوص كاملاً).")
    for err in data["errors"]:
        st.warning(f"تنبيه من مصدر البيانات: {err}")
    with st.expander("الاستعلام المُرسل فعلياً (بعد الترجمة)"):
        for u in data["used"]:
            st.code(u, language=None)
    with st.expander("📊 توزيع النتائج على المصادر"):
        if data["counts"]:
            st.markdown("  \n".join(f"- **{n}** ({FLAGS.get(data.get('ctry', {}).get(n, ''), '🏳️')} {data.get('ctry', {}).get(n, '') or 'غير محددة'}): {c}" for n, c in sorted(data["counts"].items(), key=lambda x: -x[1])))
        if data["silent"]:
            st.markdown("**مصادر مختارة لم تُرجع نتائج:** " + "، ".join(data["silent"]))
            st.caption("غياب مصدر يعني أن GDELT لم يرصد له مقالات مطابقة في هذه الفترة، وليس أنه غير مدعوم في التطبيق.")
    if data.get("hidden"):
        st.caption(f"تم إخفاء {data['hidden']} مقالاً لم تظهر كلمتك في نصّه.")
    if data.get("threads"):
        with st.expander(f"🧵 خيوط إخبارية مرشحة تلقائياً ({len(data['threads'])})"):
            st.caption("التجميع آلي اعتماداً على تشابه الكلمات في العناوين، وهو اقتراح للربط وليس حكماً بأن الأخبار تتناول الحدث نفسه.")
            for thread in data["threads"][:20]:
                st.markdown(f"**{thread['label']}** · {thread['count']} مادة · {', '.join(thread['domains'][:6]) or 'مصادر غير محددة'}")
    if data.get("auto_research_batch_id"):
        with st.expander("🧠 ملف البحث التلقائي الجاهز للتحليل", expanded=True):
            st.success(f"تم تجميع {len(data.get('items', []))} مادة في ملف بحث مستقل: {data.get('auto_research_batch_title')}")
            batch = next((x for x in S().get("research_batches", []) if x.get("id") == data["auto_research_batch_id"]), None)
            if batch:
                st.caption("الملف محفوظ داخل إدارة دفعات البحث، ويمكن متابعة دفعاته يدوياً أو إرسال البرومبت لمساعد ذكاء اصطناعي.")
                first = next((x for x in batch.get("chunks", []) if x.get("state") == "pending"), None)
                if first:
                    prompt_text = research_batches_mod.chunk_prompt(batch, first)
                    st.download_button("⬇️ تحميل برومبت أول دفعة", prompt_text, file_name="marsad_research_prompt.txt", mime="text/plain", key=f"auto_rb_{key}")
    elif data.get("auto_research_error"):
        st.warning("تعذّر إنشاء ملف البحث التلقائي: " + data["auto_research_error"])
    if not data["items"]:
        st.info("لا نتائج ضمن هذه الفلاتر. جرّب «كل الكلمات (AND)» أو وسّع النطاق الزمني أو زِد المصادر.")
    view_items = data["items"]
    if (view_items and not data.get("tr_retry") and time.time() > st.session_state.get("tr_down_until", 0)
            and untranslated(view_items[:20])):  # مرة واحدة لكل نتيجة: ترجم اللي فضل بلغته في أول صفحة
        data["tr_retry"] = True
        with st.spinner("جارٍ ترجمة العناوين اللي لسه مش مترجمة…"):
            if not fix_untranslated(view_items[:20], limit=20):
                st.session_state["tr_down_until"] = time.time() + 180  # خدمة الترجمة واقعة: ماتعطلش باقي التابات
    left_tr = len(untranslated(view_items))
    if left_tr:
        if st.button(f"🔁 ترجم العناوين اللي لسه مش مترجمة ({left_tr})", key=f"trfix_{key}"):
            with st.spinner("جارٍ الترجمة…"):
                n_fx = fix_untranslated(view_items, limit=80)
            st.caption(f"اتترجم {n_fx} عنوان." if n_fx else "خدمة الترجمة مش بترد دلوقتي. جرّب تاني بعد دقيقة.")
    if any(x.get("mcount") for x in view_items):
        if st.checkbox("🔢 رتّب حسب عدد مرات ذكر كلمتك (الأكثر ذكراً أولاً)", value=False, key=f"msort_{key}"):
            view_items = sorted(view_items, key=lambda x: (x.get("mcount") or 0), reverse=True)
    n_show = int(st.session_state.get(f"more_{key}", 20))
    total_items = len(view_items)
    for i, a in enumerate(view_items[:n_show]):
        url = a.get("url", "")
        with st.container(border=True):
            st.markdown(card_html(a), unsafe_allow_html=True)
            _article_key = key + "_" + hashlib.sha256(str(url or f"{key}_{i}").encode("utf-8")).hexdigest()[:12] + f"_{i}"  # فيه اسم التاب ورقم الكارت عشان مايتكررش
            st.checkbox("☑️ ضمّ المقال إلى البرومبت التحليلي الجماعي", key=f"script_pick_{_article_key}")
            _act1, _act2 = st.columns(2)
            if _act1.button("🎬 توليد برومبت سكريبت لهذا المقال", key=f"script_one_{_article_key}", use_container_width=True):
                st.session_state["article_prompt_active"] = {"title": a.get("title_ar") or a.get("title") or "مقال", "prompt": article_script_prompts_mod.build_script_prompt([a])}
            if _act2.button("🔎 بدائل مجانية مفتوحة", key=f"alt_one_{_article_key}", use_container_width=True):
                st.session_state["article_alt_active"] = {"title": a.get("title_ar") or a.get("title") or "مقال", "links": article_script_prompts_mod.alternative_search_links(a)}
            if a.get("summary_ar"):
                st.markdown("**📝 ملخص/مقتطف مترجم:** " + a["summary_ar"])
                if a.get("summary_status") != "translated_snippet":
                    st.caption("حالة الملخص: " + str(a.get("summary_status")))
            if a.get("checked"):
                if not a.get("fetched"):
                    st.caption("ℹ️ تعذّر فحص نص المقال (قد يكون خلف اشتراك أو يحجب الزحف).")
                elif a.get("found"):
                    st.success("✅ ذُكرت كلمتك في نص المقال:")
                    if mention_line(a):
                        st.markdown(mention_line(a))
                    st.markdown(a.get("snip_ar", ""))
                    for sn in a.get("snips", []):
                        st.markdown(f"<div class='ltr' dir='ltr'>{highlight(sn, data['hl'])}</div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ كلمتك لم تظهر في نص هذا المقال — ربما تطابق GDELT مع الصفحة أو الروابط الجانبية.")
            if st.button("📝 ملخص المقال في نقاط", key=f"sum_{key}_{i}"):
                with st.spinner("جارٍ التلخيص…"):
                    data["summaries"][url] = core.summarize(url)
            if url in data["summaries"]:
                st.info(data["summaries"][url])
            listen_widget(a, f"{key}_{i}")
            if any(x.get("url") == url for x in S()["saved"]):
                st.caption("✅ محفوظ — تجده في تاب «المحفوظات»")
            else:
                st.button("💾 حفظ للقراءة لاحقاً", key=f"save_{key}_{i}", on_click=save_item, args=(a, key))
    _selected_articles = []
    for _idx, _article in enumerate(view_items[:n_show]):
        _u = _article.get("url", "")
        _ak = key + "_" + hashlib.sha256(str(_u or f"{key}_{_idx}").encode("utf-8")).hexdigest()[:12] + f"_{_idx}"
        if st.session_state.get(f"script_pick_{_ak}"):
            _selected_articles.append(_article)
    if _selected_articles:
        st.info(f"تم اختيار {len(_selected_articles)} مقال/مقالات للبرومبت الجماعي.")
        if st.button(f"🧠 توليد برومبت تحليلي وسكريبت للمقالات المحددة ({len(_selected_articles)})", key=f"script_many_{key}", use_container_width=True):
            st.session_state["article_prompt_active"] = {"title": f"تحليل مجموعة من {len(_selected_articles)} مواد", "prompt": article_script_prompts_mod.build_script_prompt(_selected_articles)}
    _active_prompt = st.session_state.get("article_prompt_active")
    if _active_prompt:
        with st.expander("🧠 البرومبت الجاهز للإرسال إلى الذكاء الاصطناعي", expanded=True):
            st.caption(_active_prompt.get("title", "برومبت تحليلي"))
            st.text_area("راجع البرومبت وانسخه إلى ChatGPT أو أي نموذج آخر", _active_prompt["prompt"], height=360, key=f"article_prompt_text_{key}")
            st.download_button("⬇️ تنزيل البرومبت TXT", _active_prompt["prompt"], file_name="marsad_article_script_prompt.txt", mime="text/plain", key=f"article_prompt_dl_{key}")
    _active_alt = st.session_state.get("article_alt_active")
    if _active_alt:
        with st.expander("🔎 مسارات البحث عن تغطيات مفتوحة بديلة", expanded=True):
            st.caption("هذه روابط بحث قانونية عن تغطيات مستقلة أو مقابلات أو تصريحات أصلية. لا تضمن وجود نسخة مجانية مكافئة للتقرير المدفوع.")
            for _lnk in _active_alt.get("links", []):
                st.markdown(f"**{_lnk['label']}**  ·  [Google]({_lnk['google']})  ·  [Google News]({_lnk['news']})")
    if total_items > n_show:
        st.caption(f"معروض {n_show} من {total_items} نتيجة (بنعرضهم على دفعات عشان الصفحة تفضل خفيفة).")
        if st.button(f"⬇️ اعرض 20 كمان (باقي {total_items - n_show})", key=f"morebtn_{key}", use_container_width=True):
            st.session_state[f"more_{key}"] = n_show + 20
            st.rerun()


def render_global_results_dock():
    """Persistent, cross-section dock for the latest result sets loaded in this app session."""
    sets = [(k[4:], v) for k, v in st.session_state.items()
            if k.startswith("res_") and isinstance(v, dict) and isinstance(v.get("items"), list) and v.get("items")]
    if not sets:
        return
    labels = {f"{name} · {len(data.get('items', []))} نتيجة · {data.get('saved_at', 'جلسة حالية')[:16]}": (name, data)
              for name, data in sorted(sets, key=lambda pair: pair[1].get("saved_at", ""), reverse=True)}
    with st.expander(f"📌 درج نتائج البحث المحفوظة · {sum(len(v.get('items', [])) for _, v in sets)} نتيجة متاحة من {len(sets)} تبويبات", expanded=False):
        st.caption("الدرج ده ظاهر في كل أقسام التطبيق. البحث الجديد يستبدل نتائج التبويب نفسه فقط؛ باقي التبويبات تظل كما هي. الاسترجاع بعد إغلاق التطبيق يعتمد على تفعيل GitHub Gist.")
        chosen = st.selectbox("اعرض نتائج أي تبويب؟", list(labels), key="global_results_dock_select")
        _name, _data = labels[chosen]
        for _idx, _item in enumerate(_data.get("items", [])[:30]):
            st.markdown(card_html(_item), unsafe_allow_html=True)
            _url = _item.get("url", "")
            if _url and any(x.get("url") == _url for x in S().get("saved", [])):
                st.caption("✅ محفوظ للقراءة لاحقاً")
            elif _url:
                st.button("💾 حفظ للقراءة لاحقاً", key=f"global_save_{hashlib.sha256(_url.encode()).hexdigest()[:12]}",
                          on_click=save_item, args=(_item, _name))


# درج عام يظهر خارج التبويبات، فتظل النتائج متاحة أثناء التنقل بين أقسام التطبيق.
render_global_results_dock()


def all_entries(key, groups):
    out = []
    for entries in groups.values():
        out += list(entries)
    out += [(x["label"], x["domain"], x["lang"]) for x in S()["sources"] if x["group"] == key]
    return out


def author_variants(raw):
    """يعيد (الاسم بالإنجليزية، الاسم بالعبرية أو '') من أي لغة يكتبها المستخدم"""
    raw = raw.strip()
    if core._HAS_AR.search(raw):
        return tr(raw, "ar", "en"), tr(raw, "ar", "iw")
    if core._HEB.search(raw):
        return tr(raw, "iw", "en"), raw
    return raw, ""


def days_in_range():
    return max(1, int(-(-(end_utc - start_utc).total_seconds() // 86400)))


def add_gnews(key, sel, country, terms):
    """يضمّ نتائج أخبار Google (site:) إلى نتائج GDELT المعروضة"""
    data = st.session_state.get(f"res_{key}")
    if data is None or not terms:
        return
    with st.spinner("جارٍ ضمّ نتائج أخبار Google…"):
        items, notes = core.gnews_site_search(sel, days_in_range(), terms=terms, joiner=joiner, country=country)
    have = {a["url"] for a in data["items"]}
    new = [a for a in items if a["url"] not in have]
    if ctype != "الكل":
        new = [a for a in new if a.get("ctype") == ctype]
    if new:
        core.translate_titles(new)
        if verify:
            matchers = core.make_matchers(terms, core.codes_for(sel))
            core.enrich_items(new[:16], matchers, joiner, limit=16)
            if hide_nomatch:
                new = [a for a in new if not (a.get("fetched") and not a.get("found"))]
        data["items"] = sorted(data["items"] + new, key=lambda a: a.get("seendate", ""), reverse=True)
    data["used"] = data["used"] + notes
    update_meta(data, sel)


def gn_seed(sel, country, terms):
    """نتائج أخبار Google (سريعة) تُعرض فوراً بينما يعمل GDELT"""
    items, notes = core.gnews_site_search(sel, days_in_range(), terms=terms, joiner=joiner, country=country)
    if ctype != "الكل":
        items = [a for a in items if a.get("ctype") == ctype]
    core.translate_titles(items)
    return items, notes


def author_search(key, sel, country, author_raw, he_raw, only_confirmed, with_terms, terms):
    en, he = author_variants(author_raw)
    he = he_raw.strip() or he
    with st.spinner(f"جارٍ البحث عن مقالات «{author_raw}» في {len(sel)} مصدراً والتحقق من التوقيع…"):
        items, notes = core.gnews_site_search(
            sel, days_in_range(), terms=terms if with_terms else None, joiner=joiner,
            author=en, author_he=he or None, country=country,
        )
        if ctype != "الكل":
            items = [a for a in items if a.get("ctype") == ctype]
        core.translate_titles(items)
    hidden = 0
    if only_confirmed:
        kept = [a for a in items if a.get("byline") is not False]
        hidden, items = len(items) - len(kept), kept
    data = {
        "items": items, "errors": [] if items else ["لم يُعثر على مقالات بهذا الاسم — جرّب كتابته بالإنجليزية كما يظهر في توقيع المقال، أو وسّع النطاق الزمني."],
        "used": notes, "summaries": {}, "counts": {}, "silent": [], "hidden": hidden,
        "hl": sorted({t for t in core._name_tokens(en + " " + he)}, key=len, reverse=True),
    }
    st.session_state[f"res_{key}"] = data
    update_meta(data, sel)


def direct_title_hits(key, sel, terms):
    """بحث سريع بالكلمات في عناوين خلاصات المصادر المباشرة (RSS/الصفحة الرئيسية)، لأن GDELT وأخبار Google لا يغطيان كل المواقع"""
    d_items, d_notes = core.direct_headlines(sel, days_in_range())
    if ctype != "الكل":
        d_items = [a for a in d_items if a.get("ctype") == ctype]
    matchers = core.make_matchers(terms, core.codes_for(sel))
    hits = [a for a in d_items if core.find_mentions(a.get("title", ""), matchers, joiner)[0]]
    core.translate_titles(hits)
    data = st.session_state.get(f"res_{key}") or {"items": [], "errors": [], "used": [], "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
    have = {x["url"].split("?")[0].rstrip("/") for x in data["items"]}
    new = [a for a in hits if a["url"].split("?")[0].rstrip("/") not in have]
    hl = sorted({st_ for alts in matchers for stems in alts for st_ in stems}, key=len, reverse=True)
    data["items"] = sorted(data["items"] + new, key=lambda a: a.get("seendate", ""), reverse=True)
    data["used"] = list(data.get("used", [])) + d_notes + [f"بحث العناوين المباشر ⟵ فُحص {len(d_items)} عنواناً من خلاصات المصادر ⟵ طابق {len(hits)} (جديد: {len(new)})"]
    data["hl"] = sorted(set(data.get("hl", [])) | set(hl), key=len, reverse=True)
    data["partial"] = False
    if new:
        data["errors"] = []  # وُجدت نتائج، فلا داعي لتحذير «لا نتائج»
    st.session_state[f"res_{key}"] = data
    update_meta(data, sel)
    if new:
        st.success(f"📡 لقيت {len(new)} نتيجة إضافية من خلاصة المصدر المباشرة (غير موجودة في GDELT ولا أخبار Google).")


def body_search(key, sel, terms, gn_country, n):
    """بحث في نص المقالات: يجمع أحدث عناوين المصادر (من مواقعها ثم أخبار Google) ويقرأ نص كل مقال ويُبقي ما ذُكرت فيه كلماتك"""
    bar = st.progress(0.0, text="جارٍ جمع أحدث مقالات المصادر…")
    d_items, d_notes = core.direct_headlines(sel, days_in_range())
    g_items, g_notes = core.gnews_site_search(sel, days_in_range(), terms=None, joiner=joiner, country=gn_country, max_items=200)
    pool = core.merge_items(d_items, g_items)
    if ctype != "الكل":
        pool = [a for a in pool if a.get("ctype") == ctype]
    pool = pool[:n]
    matchers = core.make_matchers(terms, core.codes_for(sel))
    hl = sorted({st_ for alts in matchers for stems in alts for st_ in stems}, key=len, reverse=True)
    for i in range(0, len(pool), 8):
        bar.progress(min(1.0, i / max(1, len(pool))), text=f"🔬 جارٍ قراءة نصوص المقالات… ({i}/{len(pool)})")
        core.enrich_items(pool[i:i + 8], matchers, joiner, limit=8)
    bar.empty()
    hits = [a for a in pool if a.get("found")]
    unread = sum(1 for a in pool if a.get("checked") and not a.get("fetched"))
    core.translate_titles(hits)
    note = f"بحث النص ⟵ قُرئ {len(pool) - unread} مقالاً من {len(pool)} ⟵ وُجدت الكلمات في {len(hits)}" + (f" ⟵ تعذّر فتح {unread} (حجب أو اشتراك)" if unread else "")
    data = st.session_state.get(f"res_{key}") or {"items": [], "errors": [], "used": [], "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
    have = {x["url"] for x in data["items"]}
    data["items"] = sorted(data["items"] + [a for a in hits if a["url"] not in have], key=lambda a: a.get("seendate", ""), reverse=True)
    data["used"] = list(data.get("used", [])) + d_notes + [note]
    data["hl"] = sorted(set(data.get("hl", [])) | set(hl), key=len, reverse=True)
    data["partial"] = False
    st.session_state[f"res_{key}"] = data
    update_meta(data, sel)
    if hits:
        st.success(f"🔬 لقيت {len(hits)} مقال بيذكر كلمتك داخل النص (من {len(pool) - unread} مقال اتقرا).")
    else:
        st.info(f"🔬 قرأت {len(pool) - unread} مقال ومالقيتش كلمتك في نصوصهم." + (f" وتعذّر فتح {unread}." if unread else ""))


def curated_tab(key, groups, gd_country, gn_country, btn_label):
    with st.expander("🗂️ اختيار المصادر ونطاق التغطية", expanded=False):
        sel = pick_sources(key, groups)
    st.caption(f"المصادر المحددة: {len(sel)} — افتح اختيار المصادر لتخصيص الصحف والمواقع.")
    pool = all_entries(key, groups)
    scope = st.radio("نطاق البحث", ["كل المصادر المختارة أعلاه", "🎯 داخل مصدر واحد فقط"], horizontal=True, key=f"{key}_scope")
    if scope.startswith("🎯"):
        names = [e[0] for e in pool]
        one = st.selectbox("اختر المصدر الذي تبحث بداخله", names, key=f"{key}_one")
        sel = [e for e in pool if e[0] == one][:1]
        st.caption("سيُبحث عن كلمتك داخل هذا الموقع وحده (عبر GDELT وأخبار Google معاً). المصادر التي أضفتَها من رابط تظهر أيضاً في القائمة.")
    qm = st.radio("طريقة البحث", ["🔎 بكلمة البحث (فوق في التاب)", "📰 اعرض كل ما نُشر (بدون كلمات)"], horizontal=True, key=f"{key}_qm")
    if qm.startswith("📰"):
        st.caption("هيقرا عناوين المصادر اللي اخترتها (أو المصدر الواحد) من مواقعها مباشرة (خلاصة RSS أو الصفحة الرئيسية)، ويكمّلها من أخبار Google، خلال الفترة المحددة فوق في التاب، من غير ما تكتب كلمة. "
                   f"عدد المصادر دلوقتي: {len(sel)}.")
        if st.button("📰 اعرض كل ما نُشر", type="primary", use_container_width=True, key=f"goall_{key}"):
            if not sel:
                st.warning("اختر مصدراً واحداً على الأقل.")
            else:
                with st.spinner(f"جارٍ قراءة عناوين {len(sel)} مصدراً من مواقعها مباشرة ثم تكميلها من أخبار Google…"):
                    d_items, d_notes = core.direct_headlines(sel, days_in_range())
                    g_items, g_notes = core.gnews_site_search(sel, days_in_range(), terms=None, joiner=joiner, country=gn_country, max_items=200)
                    items, notes = core.merge_items(d_items, g_items), d_notes + g_notes
                    if key in ("eg", "egt"):
                        items = egypt_only(items)
                    if ctype != "الكل":
                        items = [a for a in items if a.get("ctype") == ctype]
                    core.translate_titles(items)
                dd = {"items": items, "errors": [] if items else ["لم تُرجع أخبار Google عناوين لهذه المصادر في الفترة. وسّع الفترة أو غيّر المصادر."],
                      "used": notes, "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
                st.session_state[f"res_{key}"] = dd
                update_meta(dd, sel)
        render_results(key)
        return
    c1_, c2_ = st.columns(2)
    author_raw = c1_.text_input(
        "✍️ اسم كاتب أو مراسل (اختياري)", key=f"{key}_author",
        placeholder="مثال: Barak Ravid أو باراك رافيد", help="عند كتابته يُبحث عن مقالات هذا الشخص داخل المصادر أعلاه. يمكن الكتابة بالعربية أو الإنجليزية أو العبرية.",
    )
    he_raw = c2_.text_input("اسمه بالعبرية (اختياري، لدقة أعلى)", key=f"{key}_author_he") if key == "il" else ""
    if author_raw.strip():
        o1, o2 = st.columns(2)
        with_terms = o1.checkbox("قيّد بكلمة البحث فوق في التاب أيضاً", value=False, key=f"{key}_awt")
        only_conf = o2.checkbox("أخفِ ما ثبت أن اسمه ليس في توقيع المقال", value=False, key=f"{key}_aoc")
    else:
        with_terms = only_conf = False
        use_gn = st.checkbox("➕ ضمّ نتائج أخبار Google إلى GDELT (يغطي ما يفوته GDELT)", value=True, key=f"{key}_gn")
        use_body = st.checkbox("🔬 ابحث كمان داخل نص المقالات (يقرا أحدث مقالات المصدر ويدوّر فيها؛ أبطأ بس بيلقط اللي كلمتك في وسطه)", value=False, key=f"{key}_body")
        body_n = pick(st, "عدد المقالات اللي هتتقرا", range(20, 130, 10), 60, f"{key}_bn") if use_body else 0
    if st.button(btn_label, type="primary", use_container_width=True, key=f"go_{key}"):
        terms = [t.strip() for t in TERM_SPLIT.split(query) if t.strip()]
        if author_raw.strip():
            if with_terms and not terms:
                st.warning("اكتب كلمة البحث فوق في التاب أو ألغِ التقييد بها.")
            elif not sel:
                st.warning("اختر مصدراً واحداً على الأقل.")
            else:
                author_search(key, sel, gn_country, author_raw, he_raw, only_conf, with_terms, terms)
        else:
            seed, gnotes = [], []
            if use_gn and sel and terms:
                with st.spinner("جارٍ جلب نتائج أخبار Google أولاً (سريعة)…"):
                    try:
                        seed, gnotes = gn_seed(sel, gn_country, terms)
                    except Exception as ex:
                        gnotes = [f"Google News تعذّر: {type(ex).__name__}"]
            do_search(key, core.jobs_for_sources(sel, gd_country), sel, seed=seed)
            if gnotes and st.session_state.get(f"res_{key}"):
                st.session_state[f"res_{key}"]["used"] += gnotes
            if use_body and sel and terms:
                body_search(key, sel, terms, gn_country, body_n)
            elif sel and terms:
                with st.spinner("جارٍ البحث كمان في عناوين خلاصات المصادر مباشرة…"):
                    try:
                        direct_title_hits(key, sel, terms)
                    except Exception as ex:
                        st.caption(f"تعذّر البحث المباشر في الخلاصات: {type(ex).__name__}")
            if use_body and not terms:
                st.warning("اكتب كلمة بحث فوق في التاب عشان البحث داخل النص.")
    render_results(key)


def style_tabs():
    """يلوّن التابات الرئيسية ويكبّرها بجافاسكربت (لأن الـCSS وحده مش بيمسك في كل نسخ Streamlit)"""
    import streamlit.components.v1 as components
    components.html("""
<script>
(function(){
  var COL=["#c0392b","#2563c9","#d9822b","#2a8f55","#8a5a00"];
  function paint(){
    try{
      var doc=window.parent.document;
      var lists=doc.querySelectorAll('[role="tablist"]');
      if(!lists.length) return;
      var tabs=lists[0].querySelectorAll('[role="tab"]');
      tabs.forEach(function(t,i){
        t.style.setProperty('border-radius','14px','important');
        t.style.setProperty('padding','10px 14px','important');
        t.style.setProperty('min-height','48px','important');
        t.style.setProperty('border','1px solid rgba(128,128,128,.4)','important');
        t.style.setProperty('margin','3px','important');
        if(i>=3&&i<=7){
          t.style.setProperty('background',COL[i-3],'important');
          t.style.setProperty('color','#fff','important');
          t.style.setProperty('font-weight','700','important');
          t.style.setProperty('min-height','54px','important');
          var sel=t.getAttribute('aria-selected')==='true';
          t.style.setProperty('box-shadow',sel?'0 0 0 3px rgba(255,255,255,.7),0 4px 14px rgba(0,0,0,.5)':'none','important');
          t.style.setProperty('opacity',sel?'1':'.85','important');
        } else {
          var s2=t.getAttribute('aria-selected')==='true';
          t.style.setProperty('background',s2?'rgba(255,75,75,.25)':'rgba(128,128,128,.12)','important');
        }
      });
      lists[0].style.setProperty('flex-wrap','wrap','important');
    }catch(e){}
  }
  paint(); setInterval(paint,700);
})();
</script>""", height=0)


HOME_SECTIONS = {"il": ("اسرائيلي", ISRAEL, "IL", "#c0392b"), "us": ("امريكي", USA, "US", "#2563c9"),
                 "uk": ("بريطاني", UK, "UK", "#d9822b"), "rg": ("تركيا وايران واثيوبيا", REGION, "US", "#2a8f55")}
HOME_GD = {"il": "IS", "us": "US", "uk": "UK", "rg": None}


def _ago(seen):
    try:
        dt = datetime.strptime(seen, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        m = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
        return f"منذ {m} دقيقة" if m < 60 else (f"منذ {m // 60} ساعة" if m < 2880 else f"منذ {m // 1440} يوم")
    except Exception:
        return ""


def home_search(q, keys, days, join, bar, use_gd=False):
    terms = [t.strip() for t in TERM_SPLIT.split(q) if t.strip()]
    got = {}
    for n, key in enumerate(keys):
        label, groups, gn_c, _col = HOME_SECTIONS[key]
        bar.progress(n / max(1, len(keys)), text=f"جارٍ البحث في القسم {label}…")
        sel = all_entries(key, groups)
        try:
            g_items, g_notes = core.gnews_site_search(sel, days, terms=terms, joiner=join, country=gn_c, max_items=80)
            d_items, d_notes = core.direct_headlines(sel, days)
            m = core.make_matchers(terms, core.codes_for(sel))
            d_hits = [a for a in d_items if core.find_mentions(a.get("title", ""), m, join)[0]]
            gd_items = []
            if use_gd:
                now_ = datetime.now(timezone.utc)
                last = None
                for ev in core.search_iter(terms, join, core.MATCH_MODES[0], core.jobs_for_sources(sel, HOME_GD[key]),
                                           now_ - timedelta(days=days), now_, 60, "الكل"):
                    if ev["items"] is not None:
                        last = ev["items"]
                gd_items = last or []
                g_notes = g_notes + [f"GDELT ⟵ {len(gd_items)} نتيجة"]
            items = core.merge_items(g_items, d_hits, gd_items)
            core.translate_titles(items)
        except Exception as ex:
            items, g_notes, d_notes = [], [f"تعذّر ({type(ex).__name__})"], []
        dd = {"items": items, "errors": [] if items else ["لا نتائج في الفترة دي. جرب فترة اطول او كلمات تانية."],
              "used": g_notes + d_notes, "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
        update_meta(dd, sel)
        st.session_state[f"res_{key}"] = dd
        got[key] = items
    bar.progress(1.0, text="تم")
    merged = []
    for key, its in got.items():
        for a in its:
            merged.append({**a, "_sec": key})
    merged.sort(key=lambda a: a.get("seendate", ""), reverse=True)
    st.session_state["res_home"] = {"items": merged[:150], "q": q, "counts": {k: len(v) for k, v in got.items()},
                                    "days": days, "errors": [], "used": [], "summaries": {}}


def render_home():
    st.markdown("<div class='marsad-topline'><div><div class='marsad-kicker'>MARSAD INTELLIGENCE DESK</div><div style='font-size:1.35rem;font-weight:850;color:#fff'>مركز القيادة والرصد</div><div class='sub'>تابع الإشارات الإخبارية وافتح أدوات التحليل من مساحة عمل واحدة</div></div><div style='font-size:2.5rem;filter:drop-shadow(0 8px 16px rgba(53,215,238,.28))'>📡</div></div>", unsafe_allow_html=True)
    st.markdown("#### 🏠 لوحة القيادة")
    q = st.text_input("🔎 بحث شامل في المرصد", key="home_q", placeholder="اكتب موضوعاً أو دولة أو شخصية أو حدثاً...")
    c1, c2, c3 = st.columns([3, 2, 2])
    keys = c1.multiselect("الأقسام", list(HOME_SECTIONS), default=list(HOME_SECTIONS), format_func=lambda k: HOME_SECTIONS[k][0], key="home_secs")
    days = pick(c2, "الفترة (أيام)", [1, 2, 3, 5, 7, 14, 30], 3, "home_days")
    jl = c3.radio("لو أكتر من كلمة", ["أي منها", "كلها"], key="home_join")
    use_gd = st.checkbox("🌐 ضم GDELT (أدق وأبطأ)", value=False, key="home_gd",
                         help="بيضيف نتائج GDELT لكل قسم. ممكن يستغرق عدة دقائق، استخدمه للموضوعات المهمة.")
    if st.button("🔎 ابدأ البحث الشامل", type="primary", use_container_width=True, key="home_go"):
        if not q.strip() or not keys:
            st.warning("اكتب موضوع البحث واختار قسماً واحداً على الأقل.")
        else:
            bar = st.progress(0.0, text="بدأنا...")
            home_search(q, keys, days, "AND" if jl == "كلها" else "OR", bar, use_gd)
            bar.empty()
    h = st.session_state.get("res_home")
    now_utc0 = datetime.now(timezone.utc).strftime("%Y%m%d")
    all_items = [a for k in HOME_SECTIONS for a in (st.session_state.get(f"res_{k}") or {}).get("items", [])]
    today_n = sum(1 for a in all_items if str(a.get("seendate", "")).startswith(now_utc0))
    n_src = len({d for g in (ISRAEL, USA, UK, REGION, ARABIC, EGYPT) for ents in g.values() for _, d, _ in ents})
    case_store = S().get("intel_case_files", {})
    active_cases = len(case_store) if isinstance(case_store, dict) else 0
    metrics = st.columns(4)
    for col, num, lab in zip(metrics, (today_n, len(all_items), active_cases, n_src),
                             ("نتائج مرصودة اليوم", "نتائج البحث المحفوظة", "ملفات القضايا التراكمية", "مصدر في كتالوج الرصد")):
        col.markdown(f"<div class='hm-stat'><span style='color:#aebfd8;font-size:.88rem'>{lab}</span><b>{num:,}</b></div>", unsafe_allow_html=True)
    st.markdown("<div style='display:flex;align-items:center;justify-content:space-between;margin:24px 0 10px'><h3 style='margin:0'>آخر ما تم رصده</h3><span style='color:#41d8e9;font-size:.82rem'>MONITORING FEED</span></div>", unsafe_allow_html=True)
    if h:
        cnt = " · ".join(f"{HOME_SECTIONS[k][0]}: {n}" for k, n in h.get("counts", {}).items())
        st.markdown(f"**نتيجة «{html.escape(h.get('q', ''))}»** — آخر {h.get('days')} يوم — {cnt}")
        st.caption("نتائج البحث الشامل مرتبة زمنياً. افتح الخبر لقراءة المصدر، واستخدم قسم البحث والرصد للترجمة والتلخيص والحفظ.")
        display_items = h.get("items", [])[:25]
    else:
        display_items = sorted(all_items, key=lambda a: a.get("seendate", ""), reverse=True)[:12]
        if display_items:
            st.caption("أحدث النتائج المتاحة من عمليات البحث المحفوظة في الجلسة.")
        else:
            st.info("لا توجد نتائج محفوظة في الجلسة حالياً. اكتب موضوعاً بالأعلى لبدء البحث الشامل، أو افتح البحث والرصد من القائمة الجانبية.")
    for a in display_items:
        sec = HOME_SECTIONS.get(a.get("_sec"), ("", None, "", "#315b85"))
        ttl = html.escape(a.get("title_ar") or a.get("title") or "عنوان غير متاح")
        url = html.escape(a.get("url", ""))
        st.markdown(
            f"<div class='hm-row'><span class='hm-tag' style='background:{sec[3]}'>{sec[0] or 'رصد'}</span> "
            f"<a href='{url}' target='_blank' rel='noopener'><b>{ttl}</b></a><br>"
            f"<span class='meta'>{src_label(a.get('domain', ''), False)} · {_ago(a.get('seendate', ''))}</span></div>",
            unsafe_allow_html=True)


if _on("home"):
    with home_box:
        render_home()
if _on("search", "geo"):
    with tab_geo:
        geo_options = {
            "🇮🇱 إسرائيل": ("il", ISRAEL, "IS", "IL", "ابحث في المصادر الإسرائيلية",
                             "يُترجم بحثك إلى العبرية للمصادر العبرية، وإلى الإنجليزية للنسخ الإنجليزية."),
            "🇺🇸 الولايات المتحدة": ("us", USA, "US", "US", "ابحث في المصادر الأمريكية",
                                      "مصادر أمريكية ومراكز أبحاث وصحافة دولية ناطقة بالإنجليزية."),
            "🇬🇧 بريطانيا": ("uk", UK, "UK", "UK", "ابحث في المصادر البريطانية",
                              "صحف وقنوات بريطانية ومصادر متخصصة بالشرق الأوسط."),
            "🌍 تركيا وإيران وإثيوبيا": ("rg", REGION, None, "US", "ابحث في مصادر تركيا وإيران وإثيوبيا",
                                         "مصادر محلية بلغاتها: التركية والفارسية والأمهرية والإنجليزية.")
        }
        geo_choice = st.radio("نطاق الرصد", list(geo_options), horizontal=True, key="geo_scope")
        geo_key, geo_groups, geo_gd, geo_gn, geo_label, geo_help = geo_options[geo_choice]
        use_filters(geo_key, "full")
        st.caption(geo_help)
        if geo_key == "rg":
            st.caption("اختر مصدراً واحداً أو عدة مصادر أو كلها، أو ابحث داخل مصدر واحد.")
        curated_tab(geo_key, geo_groups, geo_gd, geo_gn, geo_label)

DAY_OPTS = {"آخر 24 ساعة": 1, "آخر 3 أيام": 3, "آخر 7 أيام": 7, "آخر 14 يوماً": 14, "آخر 30 يوماً": 30}


def browse_run(label, doms, lang, sec_name, url, kind):
    with st.spinner("جارٍ فتح القسم وترجمة العناوين…"):
        items, err = core.browse_section(url, doms)
        how = "فتح الصفحة مباشرة"
        if not items:
            pu = urlparse_path(url)
            items, notes = core.gnews_site_search([(label, pu, lang)], 14, country="IL" if lang == "he" else "US", max_items=40)
            how = "أخبار Google (الموقع يحجب الفتح المباشر)"
            err = err + " " + " | ".join(notes[:1])
        for a in items:
            ct, sure = core.classify(a["url"], a["title"])
            a["ctype"], a["ctype_sure"] = (kind, True) if kind else (ct, sure)
        core.translate_titles(items)
    data = {"items": items, "errors": [] if items else [f"تعذّر جلب القسم. {err}"], "used": [f"{url} ⟵ {how}: {len(items)}"],
            "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
    st.session_state["res_br"] = data
    update_meta(data, None)


def urlparse_path(url):
    p = urlparse(url)
    host = p.netloc.replace("www.", "")
    path = p.path.rstrip("/")
    return host + path


if _on("search", "br"):
    with tab_br:
        use_filters("br", "kw")
        st.caption("افتح مصدراً وتصفّح أقسامه (الرأي، الأخبار…) بعناوين مترجمة للعربية؛ اضغط «ترجم المقال» على أي عنوان لقراءته مترجماً، أو احفظه. "
                   "بعض المواقع المدفوعة تحجب الفتح المباشر فيُستعان بأخبار Google بدلاً منه.")
        pool_all = {}
        for grp_key, groups in (("il", ISRAEL), ("us", USA), ("uk", UK), ("rg", REGION)):
            for e in all_entries(grp_key, groups):
                pool_all[e[0]] = e
        bmode = st.radio("طريقة العرض", ["📂 أقسام موقع واحد", "📅 عناوين عدة مصادر خلال فترة"], horizontal=True, key="br_mode")
        if bmode.startswith("📅"):
            scope_all = st.radio("المصادر", ["كل المصادر", "أختار مصادر بعينها"], horizontal=True, key="br_scope")
            chosen_src = list(pool_all.keys())
            if scope_all.startswith("أختار"):
                chosen_src = st.multiselect("اختر المصادر", list(pool_all.keys()), default=["تايمز أوف إسرائيل", "جيروزاليم بوست", "Axios", "Al-Monitor", "The Guardian"], key="br_multi")
            bdays = st.selectbox("الفترة", list(DAY_OPTS.keys()), index=1, key="br_days")
            use_kw = st.checkbox("اقتصر على كلمة البحث فوق في التاب (اتركه فارغاً لعرض كل العناوين)", value=False, key="br_kw")
            if st.button("اعرض العناوين", type="primary", use_container_width=True, key="go_br2"):
                kw = [t.strip() for t in TERM_SPLIT.split(query) if t.strip()] if use_kw else None
                sel_b = [pool_all[n] for n in chosen_src]
                if not sel_b:
                    st.warning("اختر مصدراً واحداً على الأقل.")
                else:
                    with st.spinner(f"جارٍ جلب عناوين {len(sel_b)} مصدراً…"):
                        items, notes = core.gnews_site_search(sel_b, DAY_OPTS[bdays], terms=kw, joiner=joiner, country="US", max_items=150)
                        if ctype != "الكل":
                            items = [a for a in items if a.get("ctype") == ctype]
                        core.translate_titles(items)
                    dd = {"items": items, "errors": [] if items else ["لم تُرجع أخبار Google عناوين لهذه المصادر في الفترة."],
                          "used": notes, "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": []}
                    st.session_state["res_br"] = dd
                    update_meta(dd, sel_b)
            render_results("br")
        else:
            br_pick = st.selectbox("المصدر", list(pool_all.keys()), key="br_src")
            lbl, dom_s, lang_s = pool_all[br_pick]
            dlist = [d for d in dom_s.split("|") if d]
            secs = []
            for d in dlist:
                secs += [(n, u, k) for n, u, k in SECTIONS.get(d, [])]
            secs.append(("الصفحة الرئيسية", f"https://{dlist[0]}/", None))
            secs.append(("🔗 رابط قسم آخر (أدخله بنفسك)", "", None))
            sec_names = [x[0] for x in secs]
            sec_pick = st.radio("القسم", sec_names, horizontal=True, key="br_sec")
            sname_, surl_, skind_ = secs[sec_names.index(sec_pick)]
            if not surl_:
                surl_ = st.text_input("رابط صفحة القسم (من موقع هذا المصدر)", key="br_url", placeholder=f"https://{dlist[0]}/opinion").strip()
            if st.button("افتح القسم وترجمه", type="primary", use_container_width=True, key="go_br"):
                if not surl_.startswith("http"):
                    st.warning("أدخل رابطاً صحيحاً.")
                else:
                    browse_run(lbl, dlist, "he" if lang_s == "he" else "en", sname_, surl_, skind_)
            render_results("br")


try:
    seed_from_auto()
except Exception:
    pass

if _on("search", "paid"):
    with tab_paid:
        auto_note("paid")
        st.markdown("### 🧾 رادار المقالات والتقارير المدفوعة")
        st.caption("يرصد العناوين والبيانات المنشورة علناً في المصادر ذات المحتوى المدفوع أو المحدود الوصول، ثم يبحث عن تغطية مفتوحة لنفس الخبر أو الموضوع. لا يحاول تجاوز الاشتراك ولا يعرض نصاً محمياً.")
        st.markdown("[فهرس تقارير Tactical Report](https://www.tacticalreport.com/reports) · [النشرات والتنبيهات](https://www.tacticalreport.com/newsletters) · [المنتجات وطرق الاشتراك](https://www.tacticalreport.com/products)")
        paid_names = [x[0] for x in paid_radar_mod.PAID_SOURCES]
        paid_defaults = paid_radar_mod.AUTO_DEFAULTS
        chosen_paid = st.multiselect("المصادر التي تريد مراقبة عناوينها", paid_names,
                                     default=[x for x in paid_defaults if x in paid_names], key="paid_sources_pick")
        pcol1, pcol2 = st.columns([1, 2])
        with pcol1:
            paid_days_label = st.selectbox("الفترة الزمنية", ["آخر 24 ساعة", "آخر 3 أيام", "آخر 7 أيام", "آخر 14 يوماً", "آخر 30 يوماً"],
                                           index=2, key="paid_days")
        with pcol2:
            paid_query = st.text_input("كلمات أو ملف بحث (اختياري)", placeholder="إيران، البحر الأحمر، مصر، صفقات السلاح...", key="paid_query")
        paid_days = {"آخر 24 ساعة": 1, "آخر 3 أيام": 3, "آخر 7 أيام": 7, "آخر 14 يوماً": 14, "آخر 30 يوماً": 30}[paid_days_label]
        with st.expander("🔎 عندك عنوان تقرير مدفوع بالفعل؟ ابحث عنه مباشرة"):
            manual_title = st.text_input("الصق عنوان التقرير أو المقال", key="paid_manual_title", placeholder="Paste the exact English or Hebrew headline...")
            if st.button("ابحث عن إعادة نشر وتغطيات مفتوحة", key="paid_manual_find", disabled=len(manual_title.strip()) < 8):
                with st.spinner("جارٍ البحث عن العنوان والتغطيات المرتبطة في المصادر المفتوحة…"):
                    manual_alts, manual_note = paid_radar_mod.find_open_coverage(manual_title.strip(), "", paid_days, 10)
                st.session_state["paid_manual_alternatives"] = {"items": manual_alts, "note": manual_note, "title": manual_title.strip()}
            manual_data = st.session_state.get("paid_manual_alternatives")
            if manual_data:
                st.info(manual_data.get("note", ""))
                st.markdown(f"**العنوان:** {core.tr(manual_data.get('title', ''), 'auto', 'ar')}")
                for k, alt in enumerate(manual_data.get("items", [])):
                    st.markdown(f"**{k+1}. {alt.get('title_ar') or alt.get('title')}**")
                    st.caption(f"{alt.get('source_name')} · {alt.get('domain')} · {alt.get('match_label')}")
                    st.markdown(f"[فتح التغطية]({alt.get('url')})")
        if st.button("🔎 اجمع العناوين المدفوعة وابحث عن الجديد", type="primary", use_container_width=True, key="paid_scan"):
            if not chosen_paid:
                st.warning("اختار مصدراً واحداً على الأقل.")
            else:
                terms_paid = [x.strip() for x in TERM_SPLIT.split(paid_query) if x.strip()] if paid_query.strip() else None
                with st.spinner("جارٍ رصد العناوين المنشورة علناً وترجمتها للعربية…"):
                    paid_items, paid_notes = paid_radar_mod.search_paid_headlines(chosen_paid, paid_days, terms_paid, max_items=120)
                    core.translate_titles(paid_items)
                st.session_state["paid_radar_results"] = {"items": paid_items, "notes": paid_notes, "days": paid_days}
                st.session_state["paid_radar_alternatives"] = {}
                st.session_state["paid_radar_read"] = {}
        paid_data = st.session_state.get("paid_radar_results")
        if paid_data:
            for note in paid_data.get("notes", []):
                st.caption(note)
            paid_items = paid_data.get("items", [])
            st.markdown(f"**{len(paid_items)} عنواناً مرصوداً** خلال آخر {paid_data.get('days', paid_days)} يوم")
            if not paid_items:
                st.info("لم تظهر عناوين من المصادر المحددة في الفترة. جرّب توسيع الفترة أو إزالة الكلمات المفتاحية.")
            for ix, item in enumerate(paid_items):
                original = item.get("original_paid_url") or item.get("url", "")
                host = item.get("domain", "")
                title_ar = item.get("title_ar") or item.get("title", "")
                title_en = item.get("title", "")
                key = hashlib.sha256((original or title_en).encode("utf-8")).hexdigest()[:14]
                with st.expander(f"{ix+1}. {title_ar[:150]}", expanded=False):
                    st.markdown(f"**العنوان بالعربية:** {title_ar}")
                    st.markdown(f"**العنوان الأصلي:** {title_en}")
                    st.markdown(f"**المصدر:** {item.get('paid_source', source_name(host))} · {item.get('paid_country', '')} · `{host}`")
                    st.markdown(f"**التاريخ:** {fmt_seen(item.get('seendate', ''))}")
                    if original:
                        st.markdown(f"[فتح صفحة المصدر الأصلية]({original})")
                    st.caption("المتاح هنا عنوان وبيانات وصفية علنية. لو النص الكامل خلف اشتراك، لن نحاول استخراجه أو تخطي بوابة الدفع.")
                    links_paid = paid_radar_mod.legal_search_links(title_en, original)
                    st.markdown("**مسارات البحث والوصول القانوني:** " + " · ".join(f"[{label}]({url})" for label, url in links_paid))
                    if st.button("🌐 ابحث عن تغطيات مفتوحة لنفس الموضوع", key=f"paid_alt_{key}", use_container_width=True):
                        with st.spinner("بنقارن العنوان بمصادر مفتوحة ووكالات أنباء ومراكز أبحاث…"):
                            alts, note_alt = paid_radar_mod.find_open_coverage(title_en, host, paid_data.get("days", 30), 8)
                        st.session_state["paid_radar_alternatives"][key] = {"items": alts, "note": note_alt}
                    alt_data = st.session_state.get("paid_radar_alternatives", {}).get(key)
                    if alt_data:
                        st.info(alt_data.get("note", ""))
                        for j, alt in enumerate(alt_data.get("items", [])):
                            st.markdown(f"**{j+1}. {alt.get('title_ar') or alt.get('title')}**")
                            st.caption(f"{alt.get('source_name')} · {alt.get('domain')} · {alt.get('match_label')} · درجة تشابه العنوان {alt.get('match_score', 0):.0%}")
                            st.markdown(f"[فتح التغطية المفتوحة]({alt.get('url')})")
                            alt_key = hashlib.sha256(alt.get("url", "").encode("utf-8")).hexdigest()[:14]
                            if st.button("📖 اقرأ وترجم النص المتاح مباشرة", key=f"paid_read_{key}_{alt_key}"):
                                with st.spinner("جارٍ قراءة الصفحة المفتوحة وترجمتها…"):
                                    article, read_note = paid_radar_mod.read_open_article(alt.get("url", ""))
                                st.session_state["paid_radar_read"][alt_key] = {"article": article, "note": read_note}
                            read_data = st.session_state.get("paid_radar_read", {}).get(alt_key)
                            if read_data:
                                st.caption(read_data.get("note", ""))
                                if read_data.get("article"):
                                    art = read_data["article"]
                                    st.markdown(f"**النص المترجم للعربية:**\n\n{art.get('text_ar', '')}")
                                    with st.expander("عرض النص الأصلي"):
                                        st.write(art.get("text", ""))
                            st.divider()
        else:
            st.info("ابدأ بجمع العناوين. بعد ظهورها، افتح أي عنوان واضغط البحث عن تغطيات مفتوحة.")


if _on("intel", "health"):
    with tab_health:
        st.markdown("### 🩺 صحة المصادر واكتشاف تغيّر RSS")
        auto_note("health")
        st.caption("يفحص الوصول للموقع الرئيسي، ويبحث عن RSS/Atom المعلن أو المسارات الشائعة. فشل الفحص لا يعني بالضرورة أن المصدر متوقف؛ بعض المواقع تحجب الطلبات الآلية أو تغيّر سياساتها.")
        health_names = sorted({x["name"] for x in source_intel_mod.SOURCE_CATALOG})
        priority_health = [n for n in ("Reuters", "BBC", "The Guardian", "The New York Times", "The Washington Post", "Haaretz (عبري)", "هآرتس (إنجليزي)", "Ynetnews (إنجليزي)", "Times of Israel", "IDF Spokesperson", "Pentagon / US Department of Defense", "ODNI", "CIA", "UK Government (MOD / FCDO)", "SIS", "Tactical Report", "Sudan Tribune", "Radio Dabanga", "Sana'a Center", "Yemen Monitor") if n in health_names]
        health_scope = st.radio("نطاق الفحص", ["المصادر الأساسية المقترحة", "اختيار المصادر", "كل المصادر المسجلة"], horizontal=True, key="src_health_scope")
        if health_scope == "المصادر الأساسية المقترحة":
            health_selected = priority_health or health_names[:20]
        elif health_scope == "اختيار المصادر":
            health_selected = st.multiselect("اختار المصادر المراد فحصها", health_names, default=priority_health, key="src_health_pick")
        else:
            health_selected = health_names
            st.warning(f"سيتم فحص {len(source_intel_mod.SOURCE_CATALOG)} نطاقاً. بعض المواقع قد تستغرق وقتاً أو تحجب الفحص الآلي.")
        hc1, hc2 = st.columns([1, 2])
        health_timeout = pick(hc1, "مهلة كل موقع (ثانية)", [4, 6, 8, 10, 12], 8, "src_health_timeout")
        if hc2.button("🔍 افحص المصادر الآن", type="primary", use_container_width=True, key="run_source_health", disabled=not health_selected):
            with st.spinner(f"جارٍ فحص {len(health_selected)} نطاقاً واكتشاف خلاصات RSS/Atom…"):
                health_result = source_intel_mod.scan_sources(health_selected, timeout=health_timeout)
                previous_health = next((x for x in S().get("source_health_runs", []) if x.get("rows")), None)
                health_result = source_intel_mod.compare_health_runs(health_result, previous_health)
            st.session_state["source_health_latest"] = health_result
            S()["source_health_runs"] = ([health_result] + S().get("source_health_runs", []))[:3]
            persist()
        health_result = st.session_state.get("source_health_latest")
        if health_result:
            counts = health_result.get("counts", {})
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("إجمالي الفحص", health_result.get("total", 0))
            m2.metric("موقع + RSS", counts.get("healthy_feed", 0))
            m3.metric("موقع متاح بلا RSS", counts.get("healthy_no_feed", 0))
            m4.metric("تعذر الوصول/أخطاء", sum(v for k, v in counts.items() if k not in ("healthy_feed", "healthy_no_feed")))
            st.caption(f"وقت الفحص: {health_result.get('checked_at', '')}")
            display_rows = [{"المصدر": x.get("name"), "النطاق": x.get("domain"), "المنظور": source_intel_mod.SIDE_LABELS.get(x.get("side"), "دولي"),
                             "الحالة": x.get("status"), "HTTP": x.get("http_status"), "الزمن ms": x.get("latency_ms"),
                             "RSS/Atom": x.get("feed_url"), "آخر عنوان": x.get("latest_item"), "آخر تاريخ": x.get("latest_item_date"),
                             "التغير عن الفحص السابق": x.get("change_note", ""), "آخر فحص ناجح": x.get("last_successful_check", ""), "ملاحظة": x.get("error")} for x in health_result.get("rows", [])]
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
            import csv, io
            csv_buffer = io.StringIO()
            if display_rows:
                writer = csv.DictWriter(csv_buffer, fieldnames=list(display_rows[0].keys()))
                writer.writeheader(); writer.writerows(display_rows)
            st.download_button("⬇️ تنزيل تقرير صحة المصادر CSV", csv_buffer.getvalue().encode("utf-8-sig"), file_name="marsad_source_health.csv", mime="text/csv", key="download_source_health")
            st.caption("healthy_no_feed = الموقع متاح لكن لم نعثر على RSS عام. unreachable_or_blocked/timeout لا يثبتان توقف الموقع؛ قد يكون الحجب أو DNS أو مهلة الاتصال.")
        else:
            st.info("ابدأ بفحص المصادر الأساسية، أو اختر مجموعة أكبر لمراجعة حالة المواقع وخلاصاتها.")


if _on("intel", "clusters"):
    with tab_clusters:
        st.markdown("### 🧩 تجميع الأحداث ومقارنة الروايات")
        auto_note("dossier")
        st.caption("يجمع عناوين من GDELT وGoogle News RSS، ثم يربط التغطيات المتقاربة ويقسمها حسب المنظور الجغرافي. لا يستنتج الموقف السياسي من العنوان وحده ولا يعتبر التشابه دليلاً على إعادة النشر.")
        cluster_query = st.text_input("موضوع القضية أو الحدث", placeholder="مثال: تحركات الأسطول الأمريكي في البحر الأحمر أو مفاوضات إيران النووية", key="intel_cluster_query")
        cc1, cc2 = st.columns(2)
        cluster_days = cc1.selectbox("الفترة", [1, 3, 7, 14, 30, 60, 90], index=2, key="intel_cluster_days")
        cluster_limit = cc2.selectbox("الحد الأقصى للعناوين", [40, 80, 120, 180, 240], index=2, key="intel_cluster_limit")
        cluster_sides = st.multiselect("المنظورات المطلوب مقارنتها", ["us", "il", "uk", "ar"], default=["us", "il", "uk", "ar"],
                                       format_func=lambda x: {"us": "🇺🇸 أمريكي", "il": "🇮🇱 إسرائيلي", "uk": "🇬🇧 بريطاني", "ar": "🌍 عربي/إقليمي"}[x], key="intel_cluster_sides")
        if st.button("🛰️ اجمع التغطيات واربط الأحداث", type="primary", use_container_width=True, key="run_intel_cluster", disabled=len(cluster_query.strip()) < 3):
            with st.spinner("جارٍ البحث في GDELT وGoogle News RSS، وترجمة العناوين وربط التغطيات…"):
                cluster_articles, cluster_notes = source_intel_mod.collect_articles(cluster_query, cluster_days, cluster_limit, tuple(cluster_sides))
                cluster_groups = source_intel_mod.cluster_articles(cluster_articles)
                dossier = source_intel_mod.build_case_dossier(cluster_query, cluster_articles, cluster_groups)
            st.session_state["intel_cluster_latest"] = dossier
            st.session_state["intel_cluster_notes"] = cluster_notes
            S()["intel_dossiers"] = ([dossier] + S().get("intel_dossiers", []))[:5]
            persist()
        dossier = st.session_state.get("intel_cluster_latest")
        if dossier:
            notes = st.session_state.get("intel_cluster_notes", [])
            for note in notes[:12]:
                st.caption(note)
            d1, d2, d3 = st.columns(3)
            d1.metric("العناوين المرصودة", dossier.get("article_count", 0))
            d2.metric("مجموعات الأحداث", dossier.get("cluster_count", 0))
            d3.metric("المصادر المختلفة", len({x.get("domain") for x in dossier.get("articles", [])}))
            st.markdown(f"**ملف القضية:** {dossier.get('title_ar') or dossier.get('title')}")
            if not dossier.get("event_clusters"):
                st.info("ظهرت عناوين، لكن لم تتكون مجموعات متقاربة من مصدرين أو أكثر. يمكنك مراجعة كل العناوين أو توسيع الفترة.")
            for ci, group in enumerate(dossier.get("event_clusters", []), 1):
                with st.expander(f"{ci}. {group.get('topic_ar')} · {group.get('article_count')} تغطية · {group.get('source_count')} مصدر", expanded=ci == 1):
                    st.caption("المنظورات الموجودة: " + "، ".join(group.get("sides", [])))
                    st.markdown("**مقارنة التغطيات حسب المنظور**")
                    for side_label, narrative_items in group.get("narratives", {}).items():
                        st.markdown(f"**{side_label}**")
                        for ni in narrative_items:
                            st.markdown(f"- [{ni.get('title_ar') or ni.get('title')}]({ni.get('url')}) · {ni.get('source')} · {ni.get('kind')}")
                    st.markdown("**تقدير الأصل وإعادة النشر**")
                    for assessment in group.get("origin_assessments", []):
                        st.markdown(f"- {assessment.get('source')} (`{assessment.get('domain')}`): {assessment.get('assessment')} · [المصدر]({assessment.get('url')})")
                    st.warning(group.get("caveat", "التصنيف آلي مبدئي ويحتاج مراجعة."))
            with st.expander("كل العناوين المرصودة", expanded=False):
                for article in dossier.get("articles", []):
                    st.markdown(f"- **{article.get('title_ar') or article.get('title')}** · {article.get('source_name')} · {article.get('side_label')} · {article.get('kind')} · [الرابط الأصلي]({article.get('url')})")
            st.download_button("⬇️ تنزيل ملف القضية الموحد JSON", json.dumps(dossier, ensure_ascii=False, indent=2),
                               file_name=f"marsad-case-{dossier.get('case_id', 'export')}.json", mime="application/json", key="download_intel_dossier")
            st.markdown("**حدود المنهج:** أقدم تاريخ ظهر في نتائجنا لا يعني بالضرورة أن هذا هو الناشر الأصلي. تطابق العناوين قد ينتج عن إعادة صياغة مستقلة، والتغطية العربية/الأجنبية قد تختلف في التوقيت والتفاصيل.")
        else:
            st.info("اكتب موضوعاً وحدد المنظورات والفترة، ثم ابدأ الجمع. سيُنشأ ملف قضية موحد قابل للتنزيل والحفظ في المرصد.")


if _on("intel", "entities"):
    with tab_entities:
        st.markdown("### 🧭 الكيانات والخط الزمني والتناقضات")
        st.caption("طبقة ربط فوق ملفات 8.19: استخراج أسماء محددة من قاموس قابل للتوسيع، وربطها بالمصادر والقضايا القديمة. التناقضات مرشحات للمراجعة وليست أحكاماً آلية.")
        saved_dossiers = S().get("intel_dossiers", [])
        auto_note("dossier")
        _auto_d = auto_intel().get("dossier")
        if _auto_d and _auto_d.get("id") not in {x.get("id") for x in saved_dossiers}:
            saved_dossiers = [_auto_d] + list(saved_dossiers)
        dossier_options = {f"{x.get('title_ar') or x.get('title') or 'ملف'} · {x.get('created_at','')[:10]} · {x.get('id','')[-6:]}": x for x in saved_dossiers}
        if dossier_options:
            selected_dossier_label = st.selectbox("اختر ملف تغطيات محفوظاً", list(dossier_options), key="entity_dossier_pick")
            entity_case_pool = S().get("research_cases", [])
            if st.button("🧠 حلّل الكيانات واربطه بالقضايا القديمة", type="primary", use_container_width=True, key="enrich_entity_dossier"):
                with st.spinner("جارٍ استخراج الكيانات وبناء الخط الزمني وفحص المرشحات وربط الملفات…"):
                    enriched = entity_intel_mod.enrich_dossier(dossier_options[selected_dossier_label], entity_case_pool)
                S()["intel_dossiers"] = [enriched if x.get("id") == enriched.get("id") else x for x in saved_dossiers if not x.get("auto")]
                st.session_state["entity_intel_latest"] = enriched
                persist()
            enriched = st.session_state.get("entity_intel_latest")
            if not enriched or enriched.get("id") != dossier_options[selected_dossier_label].get("id"):
                enriched = dossier_options[selected_dossier_label]
            if enriched.get("entity_index") is not None:
                entities = enriched.get("entity_index", [])
                timeline = enriched.get("publication_timeline", [])
                contradictions = enriched.get("contradiction_candidates", [])
                prior_matches = enriched.get("prior_case_matches", [])
                e1, e2, e3, e4 = st.columns(4)
                e1.metric("كيانات مستخرجة", len(entities)); e2.metric("مواد مؤرخة", len(timeline))
                e3.metric("تعارضات مرشحة", len(contradictions)); e4.metric("روابط لقضايا قديمة", len(prior_matches))
                with st.expander("🧩 فهرس الكيانات ومصادر ذكرها", expanded=True):
                    for ent in entities:
                        st.markdown(f"**{ent['name']}** · `{ent['type']}` · {ent['mention_count']} ذكر · {len(ent['source_domains'])} نطاق")
                        for mention in ent.get("mentions", [])[:5]:
                            st.markdown(f"- {mention.get('published_at') or 'تاريخ غير متاح'} · {mention.get('source') or mention.get('domain')} · [{mention.get('title') or 'المادة'}]({mention.get('url')})")
                with st.expander("🕒 الخط الزمني للنشر", expanded=False):
                    for item in timeline:
                        st.markdown(f"- **{item['timestamp']}** · {item['source']} · [{item['title']}]({item['url']})")
                        st.caption(item['time_basis'])
                with st.expander("⚖️ مرشحات التناقض بين الادعاءات", expanded=False):
                    if not contradictions: st.info("لم يظهر تعارض لغوي واضح ضمن العينة الحالية. هذا لا يعني عدم وجود تناقضات.")
                    for item in contradictions:
                        st.markdown(f"**مرشح مراجعة · تشابه مفردات {item['overlap']:.0%}**")
                        st.write("الادعاء/النص الأول: " + item['claim_a'][:700])
                        st.markdown(f"المصدر: [{item['source_a']['name'] or 'رابط'}]({item['source_a']['url']})")
                        st.write("الادعاء/النص الثاني: " + item['claim_b'][:700])
                        st.markdown(f"المصدر: [{item['source_b']['name'] or 'رابط'}]({item['source_b']['url']})")
                        st.warning(item['caveat'])
                with st.expander("🔗 ربط التغطيات بملفات القضايا السابقة", expanded=False):
                    if not prior_matches: st.info("لم يظهر تطابق موضوعي كافٍ مع الملفات البحثية المحفوظة.")
                    for match in prior_matches:
                        st.markdown(f"**{match['article']['title']}** · [{match['article']['source'] or 'المصدر'}]({match['article']['url']})")
                        for candidate in match['matches']:
                            st.markdown(f"- **{candidate['case_title']}** · درجة التشابه الإرشادية {candidate['score']}/100 · {candidate['level']}")
                            st.caption("؛ ".join(candidate.get('reasons', [])))
                            if st.button("➕ أضف المادة إلى هذا الملف البحثي", key=f"attach_entity_article_{candidate['case_id']}_{hashlib.sha1(match['article']['url'].encode()).hexdigest()[:8]}"):
                                target_case = next((x for x in S().get("research_cases", []) if x.get("id") == candidate["case_id"]), None)
                                original_article = next((x for x in enriched.get("articles", []) if x.get("url") == match["article"]["url"]), None)
                                if target_case and original_article:
                                    added = casebook_mod.add_material(target_case, original_article, material_type="خبر", note="أضيف بعد مراجعة اقتراح الربط من Phase 8.20")
                                    persist()
                                    st.success("تمت إضافة المادة إلى الملف." if added else "المادة موجودة بالفعل في الملف.")
                                    st.rerun()
                st.download_button("⬇️ تنزيل ملف التحليل الموسع JSON", json.dumps(enriched, ensure_ascii=False, indent=2),
                    file_name=f"marsad-entity-analysis-{enriched.get('id','case')}.json", mime="application/json", key="download_entity_enriched")
                st.caption("ملاحظة منهجية: قاموس الكيانات ليس شاملاً. تواريخ المواد هي تواريخ نشر لا أوقات وقوع الأحداث. تشابه القضايا لا يثبت علاقة سببية، والتعارض يحتاج مراجعة النصوص الأصلية والسياق.")
            else:
                st.info("اختر ملفاً ثم اضغط تحليل الكيانات لبناء الفهرس والخط الزمني والروابط.")
        else:
            st.info("لا توجد ملفات تغطيات محفوظة بعد. أنشئ ملفاً من تبويب تجميع الأحداث والروايات أولاً، ثم ارجع هنا لتحليله وربطه بالقضايا القديمة.")

for _n, _d, _sd, _k, _f in intel.SOURCES:
    DOMAIN_LABELS.setdefault(_d, _n)


def intel_run(file_name, terms, days, picked, with_media, media_sel, ar_sel=()):
    meta = {}
    for n, d, sd, k, f in intel.SOURCES:
        if n in picked:
            meta[d] = (sd, k)
    sel = [(n, d, "en") for n, d, sd, k, f in intel.SOURCES if n in picked]
    media = []
    if with_media:
        for grp, groups, sd in (("il", ISRAEL, "il"), ("us", USA, "us"), ("uk", UK, "uk")):
            for e in all_entries(grp, groups):
                if e[0] in media_sel and e[2] in ("en", "both"):
                    media.append((e[0], e[1], "en"))
                    for dd in e[1].split("|"):
                        meta.setdefault(dd, (sd, "media"))
    for grp in ARABIC.values():
        for lbl_, dom_, _l in grp:
            if lbl_ in ar_sel:
                media.append((lbl_, dom_, "ar"))
                meta.setdefault(dom_, ("eg" if dom_ in EGYPT_ARABIC else "ar", "media"))
    allsel = sel + [m for m in media if m[1] not in {x[1] for x in sel}]
    with st.spinner("جارٍ البحث في المؤسسات والمصادر وتصنيف النتائج…"):
        items, notes = core.gnews_site_search(allsel, days, terms=terms or None, joiner="OR", country="US", max_items=200)
        for a in items:
            sd, k = next(((v[0], v[1]) for dd, v in meta.items() if core.domain_match(a["domain"], [dd])), ("osint", "think"))
            a["ctype"], a["ctype_sure"] = intel.classify_intel(a["title"], a["url"], k), False
            a["side"] = sd
            a["egypt"] = bool(intel.EGYPT_RE.search(a["title"]))
        core.translate_titles(items)
        for a in items:
            a["country_ar"] = intel.SIDES.get(a["side"], "") + (" · 🇪🇬 يخص مصر" if a["egypt"] else "")
    data = {"items": items, "errors": [] if items else ["لم تُرجع أخبار Google نتائج — وسّع الفترة أو غيّر الكلمات."],
            "used": notes, "summaries": {}, "counts": {}, "silent": [], "hidden": 0, "hl": [],
            "meta": {"file": file_name, "terms": terms or ["(كل ما نُشر)"], "days": days}}
    update_meta(data, None)
    st.session_state["res_in_all"] = data


def intel_matrix(view):
    """جدول ربط: المنظورات × أنواع المعلومة، وما يقوله كل منظور عن مصر"""
    rows = ["| المنظور | " + " | ".join(intel.INTEL_TYPES) + " | يخص مصر |", "|" + "---|" * (len(intel.INTEL_TYPES) + 2)]
    for code, name in intel.SIDES.items():
        sub = [a for a in view if a.get("side") == code]
        if not sub:
            continue
        cells = [str(sum(1 for a in sub if a.get("ctype") == t)) for t in intel.INTEL_TYPES]
        rows.append(f"| {name} | " + " | ".join(cells) + f" | {sum(1 for a in sub if a.get('egypt'))} |")
    st.markdown("\n".join(rows))
    eg_items = [a for a in view if a.get("egypt")]
    if eg_items:
        st.markdown("**🇪🇬 ما تقوله كل جهة عن مصر في هذا الملف:**")
        for code, name in intel.SIDES.items():
            sub = [a for a in eg_items if a.get("side") == code][:6]
            if sub:
                st.markdown(f"*{name}*")
                st.markdown("\n".join(f"- [{a.get('title_ar', '')}]({a['url']}) — {src_label(a['domain'])}" for a in sub))
    else:
        st.caption("لا توجد عناوين تخص مصر ضمن النتائج الحالية.")


if _on("intel", "in"):
    with tab_in:
        st.caption("مكتب استخبارات مفتوح المصدر للشرق الأوسط والقرن الأفريقي: تصفّح مؤسسة واحدة أو عدة مؤسسات أو كلها، وأضف التحركات المصرية لأي ملف، "
                   "وقارن المنظورات في جدول ربط، ثم اصنع تقريراً. التصنيف تقديري من العنوان والرابط ولا يُغني عن مراجعة المصدر.")
        all_files = list(intel.FILES.keys())
        if st.checkbox("اختر كل الملفات دفعة واحدة", value=False, key="in_allfiles"):
            fnames = all_files
        else:
            fnames = st.multiselect("الملفات (اختر ملفاً أو أكثر، وسيُبحث فيها كلها معاً)", all_files, default=all_files[:1], key="in_files")
        if not fnames:
            st.warning("اختر ملفاً واحداً على الأقل.")
            fnames = all_files[:1]
        fname = " + ".join(fnames)
        fmeta = {"terms": list(dict.fromkeys(t for f in fnames for t in intel.FILES[f]["terms"])),
                 "egypt": list(dict.fromkeys(t for f in fnames for t in intel.FILES[f]["egypt"])),
                 "axes": "؛ ".join(intel.FILES[f]["axes"] for f in fnames)}
        st.markdown(f"**المحاور:** {fmeta['axes']}")
        egm = st.radio("التحركات المصرية", ["الملف + التحركات المصرية", "الملف فقط", "التحركات المصرية فقط"], horizontal=True, key="in_eg")
        base_terms = fmeta["terms"] if egm != "التحركات المصرية فقط" else []
        eg_terms = fmeta["egypt"] if egm != "الملف فقط" else []
        qmode = st.radio("طريقة العرض", ["🔎 بحث بكلمات الملف", "📰 اعرض كل ما نُشر (بدون كلمات)"], horizontal=True, key="in_qmode")
        terms_txt = ""
        if qmode.startswith("🔎"):
            terms_txt = st.text_input("كلمات البحث (يمكن تعديلها؛ بالإنجليزية أو العربية، بفاصلة)", value="، ".join(base_terms + eg_terms),
                                      key=f"in_terms_{fname}_{egm}")
            if len(fnames) > 1:
                st.caption(f"سيُبحث في {len(fnames)} ملفات معاً بكلماتها مجتمعة؛ قصّ الكلمات إن كانت كثيرة.")
        names = [x[0] for x in intel.SOURCES]
        side_list = [v for k, v in intel.SIDES.items() if k != "uk"]
        side_codes = {v: k for k, v in intel.SIDES.items()}
        scope_i = st.radio("المؤسسات", ["مؤسسة واحدة", "عدة مؤسسات", "كل المؤسسات"], horizontal=True, key="in_scope", index=1)
        if scope_i == "مؤسسة واحدة":
            picked = [st.selectbox("المؤسسة", names, key="in_one")]
        elif scope_i == "كل المؤسسات":
            picked = names
        else:
            sides_pick = st.multiselect("المنظورات", side_list, default=side_list, key="in_sides")
            default_src = [x[0] for x in intel.SOURCES if intel.SIDES[x[2]] in sides_pick]
            picked = st.multiselect("المؤسسات", names, default=default_src, key=f"in_src_{'_'.join(sorted(side_codes[x] for x in sides_pick))}")
        days_i = st.selectbox("الفترة", ["آخر 7 أيام", "آخر 14 يوماً", "آخر 30 يوماً", "آخر 90 يوماً"], index=1, key="in_days")
        days_n = int(re.findall(r"\d+", days_i)[0])
        with_media = st.checkbox("➕ ضمّ تغطية الإعلام الإسرائيلي والأمريكي والبريطاني (للمقارنة)", value=True, key="in_media")
        media_sel = []
        if with_media:
            media_pool = [e[0] for g, gr in (("il", ISRAEL), ("us", USA), ("uk", UK)) for e in all_entries(g, gr) if e[2] in ("en", "both")]
            media_sel = st.multiselect("الصحف المضمومة", media_pool, default=[m for m in media_pool if m in (
                "تايمز أوف إسرائيل", "جيروزاليم بوست", "Axios", "Al-Monitor", "BBC", "The Guardian", "Reuters",
                "Foreign Policy", "Middle East Eye", "Ynetnews (إنجليزي)", "هآرتس (إنجليزي)")], key="in_media_sel")
        use_ar = st.checkbox("➕ ضمّ الصحافة العربية (مصرية وخليجية) للمقارنة", value=False, key="in_ar")
        ar_sel = []
        if use_ar:
            ar_pool = [e[0] for grp in ARABIC.values() for e in grp]
            ar_sel = st.multiselect("الصحف العربية", ar_pool, default=ar_pool[:5] + ["الشرق الأوسط", "العربية", "الجزيرة"], key="in_ar_sel")
            st.caption("تُترجم كلمات البحث تلقائياً إلى العربية. بحث اسم الكاتب لا يشمل الصحف العربية.")
        if st.button("🛰️ ابحث / اعرض", type="primary", use_container_width=True, key="go_in"):
            tl = [t.strip() for t in TERM_SPLIT.split(terms_txt) if t.strip()]
            if qmode.startswith("🔎") and not tl:
                st.warning("اكتب كلمات البحث أو اختر «اعرض كل ما نُشر».")
            elif not picked:
                st.warning("اختر مؤسسة واحدة على الأقل.")
            else:
                intel_run(fname, tl, days_n, picked, with_media, media_sel, ar_sel)

        allr = st.session_state.get("res_in_all")
        if allr:
            items = allr["items"]
            c1_, c2_ = st.columns(2)
            f_type = c1_.multiselect("نوع المعلومة", intel.INTEL_TYPES, default=intel.INTEL_TYPES, key="in_ftype")
            f_side = c2_.multiselect("المنظور", list(intel.SIDES.values()), default=list(intel.SIDES.values()), key="in_fside")
            only_eg = st.checkbox("🇪🇬 اعرض ما يخص مصر فقط", value=False, key="in_onlyeg")
            view = [a for a in items if a.get("ctype") in f_type and intel.SIDES.get(a.get("side"), "") in f_side and (a.get("egypt") or not only_eg)]
            st.caption(f"{len(view)} نتيجة من {len(items)}")
            with st.expander("🔗 خريطة الربط: المنظورات × أنواع المعلومة، وما يخص مصر"):
                intel_matrix(view)
            st.session_state["res_in"] = {**allr, "items": sorted(view, key=lambda a: a.get("seendate", ""), reverse=True)}
            m = allr["meta"]
            rep = intel.build_report(f"تقرير: {m['file']}", m["file"], m["terms"], m["days"], view)
            d1_, d2_ = st.columns(2)
            d1_.download_button("📄 نزّل التقرير التجميعي (Markdown)", rep, file_name="intel_report.md", mime="text/markdown", use_container_width=True)
            with d2_.popover("👁️ معاينة التقرير", use_container_width=True):
                st.markdown(rep)
            with st.expander("🧩 أسئلة الربط: كيف يتقاطع هذا الملف مع غيره؟"):
                st.markdown("لكل خبر أو تقرير مهم اسأل:\n" + "\n".join(f"- {q}" for q in intel.LINK_QUESTIONS))
                st.caption("تلميح: غيّر «الملف» أعلاه وأعد البحث بنفس الأطراف لترى كيف يتقاطع البحر الأحمر مع القرن الأفريقي والخليج.")
            render_results("in")

        with st.expander("🔎 العثور على التقارير المجانية (PDF ومستودعات الأبحاث)"):
            q_free = st.text_input("عنوان التقرير أو موضوعه", key="in_free", placeholder="Egypt military assessment")
            if q_free.strip():
                for lbl_, u_ in intel.search_links(q_free):
                    st.markdown(f"- [{lbl_}]({u_})")
                st.caption("ابحث عن النسخ المنشورة بإذن أصحابها أو الملخصات العلنية، أو اطلب نسخة من المؤلف.")
            else:
                st.caption("اكتب موضوعاً لتظهر روابط البحث الجاهزة.")
        with st.expander("📚 دليل المؤسسات"):
            for sd_code, sd_name in intel.SIDES.items():
                rows = [x for x in intel.SOURCES if x[2] == sd_code]
                if rows:
                    st.markdown(f"**{sd_name}**")
                    st.markdown("\n".join(f"- [{n}](https://{d}) — {f}" for n, d, _s, _k, f in rows))
            st.markdown("- [SIPRI — قاعدة صفقات السلاح (تصدير CSV)](https://armstransfers.sipri.org/ArmsTransfer/TransferRegister)")
            st.caption("الدومينات كتبتُها من معرفتي ولم أجرّبها كلها؛ إن لم يظهر مصدر في البحث فتحقق من دومينه.")

if _on("search", "gd"):
    with tab_gd:
        use_filters("gd", "full")
        st.caption("بحث واسع في كل ما يرصده GDELT حسب بلد المصدر، دون تحديد مواقع بعينها.")
        scope = st.selectbox("المصادر", list(core.GLOBAL_SCOPES.keys()), key="gd_scope")
        if st.button("ابحث (GDELT عام)", type="primary", use_container_width=True, key="go_gd"):
            do_search("gd", core.GLOBAL_SCOPES[scope])
        render_results("gd")

COUNTRIES = {"كل الدول": None, "الولايات المتحدة": "US", "بريطانيا": "UK", "إسرائيل": "IS", "البرازيل": "BR", "البرتغال": "PO", "فرنسا": "FR", "إسبانيا": "SP"}

if _on("search", "ml"):
    with tab_ml:
        query = ""
        st.caption(
            "ترجم كلماتك إلى عدة لغات، **عدّل أي ترجمة بيدك أو اكتبها بنفسك**، ثم ابحث بها. "
            "كل لغة تُبحث في المقالات المنشورة بها. التركية والفارسية والأمهرية تعرض ما تقوله تلك الدول بلسانها؛ تغطية GDELT لها أضعف، فإن لم تظهر نتائج فوسّع الفترة."
        )
        src_txt = st.text_input(
            "العبارة بالعربية", key="ml_src",
            help="افصل بين المواضيع بفاصلة.",
        )
        base_terms = [x.strip() for x in TERM_SPLIT.split(src_txt or query) if x.strip()]
        if st.button("🔤 ترجم إلى اللغات المختارة", use_container_width=True, key="ml_tr"):
            if not base_terms:
                st.warning("اكتب كلمة أو جملة بالعربية أولاً.")
            else:
                with st.spinner("جارٍ الترجمة…"):
                    for code, _, _, _ in core.LANGS:
                        if st.session_state.get(f"ml_use_{code}", dict((c, d) for c, _, _, d in core.LANGS)[code]):
                            out, ok = core.translate_terms(base_terms, code)
                            st.session_state[f"ml_txt_{code}"] = "، ".join(out) if ok else ""
                            st.session_state[f"ml_fail_{code}"] = not ok
        chosen = []
        for code, name, gl, default in core.LANGS:
            c1_, c2_ = st.columns([1, 3])
            use = c1_.checkbox(name, value=default, key=f"ml_use_{code}")
            txt = c2_.text_input(f"الترجمة إلى {name}", key=f"ml_txt_{code}", label_visibility="collapsed",
                                 placeholder=f"اكتب أو عدّل الترجمة ({name})")
            if st.session_state.get(f"ml_fail_{code}"):
                c2_.caption("⚠️ فشلت الترجمة الآلية — اكتبها بنفسك.")
            if use and txt.strip():
                chosen.append((code, gl, [x.strip() for x in TERM_SPLIT.split(txt) if x.strip()]))
        country_label = st.selectbox("حصر في مصادر بلد معيّن (اختياري)", list(COUNTRIES.keys()), key="ml_country")
        if st.button("ابحث بهذه الترجمات", type="primary", use_container_width=True, key="go_ml"):
            cc = COUNTRIES[country_label]
            jobs = [
                {"code": code, "extra": f"sourcelang:{gl}" + (f" sourcecountry:{cc}" if cc else ""), "terms": terms_}
                for code, gl, terms_ in chosen
            ]
            if not jobs:
                st.warning("اختر لغة واحدة على الأقل واكتب ترجمتها (اضغط «ترجم» أولاً).")
            else:
                do_search("ml", jobs, None, terms=base_terms or ["x"], pre=True)
        render_results("ml")



GROUP_LABELS = {"US": "🇺🇸 أمريكيون", "UK": "🇬🇧 بريطانيون", "IL": "🇮🇱 إسرائيليون", "SA": "🇸🇦 سعوديون (حسابات تويتر وغيرها)",
                "GCC": "🌍 خليجيون", "EG": "🇪🇬 مصريون", "AR": "🌍 عرب آخرون"}


def current_writers():
    return WRITERS + [writers_mod.W(**dict(sp, default=True)) for sp in S()["writers"]]


@st.cache_data(ttl=1800, show_spinner=False)
def cached_writers(ids, days, extra_json="[]"):
    allw = WRITERS + [writers_mod.W(**dict(sp, default=True)) for sp in json.loads(extra_json)]
    ws = [w for w in allw if w["id"] in ids]
    items, notes = core.fetch_writers(ws, days)
    return core.translate_titles(items), notes


def writers_panel(pfx, gcodes, btn_label, codes):
    """قائمة كتّاب لمجموعة جنسيات + زرها الخاص ونتائجها المستقلة (pfx يفصل بين الاجانب والعرب)"""
    days_label = st.selectbox("الفترة", list(DAY_OPTS.keys()), index=2, key=f"{pfx}_days")
    sel_ids = []
    all_w = current_writers()
    with st.expander("👥 اختيار الكُتّاب والمحللين", expanded=False):
        kinds = st.multiselect("تخصص الكاتب", ["رأي", "تحليل", "خبر"], default=["رأي", "تحليل", "خبر"],
                               key=f"{pfx}_writer_kinds", help="فلتر الكُتّاب حسب طبيعة إنتاجهم، وليس نوع المقال وحده.")
        for gcode in gcodes:
            gname = GROUP_LABELS[gcode]
            ws_ = [w for w in all_w if w["country"] == gcode and w.get("kind", "رأي") in kinds]
            if not ws_:
                continue
            label_to_id = {f"{w['name_ar']} — {w['outlet']} · {w.get('kind', 'رأي')}": w["id"] for w in ws_}
            picked = st.multiselect(
                gname, list(label_to_id), default=[l for l, i in label_to_id.items() if next(w for w in ws_ if w["id"] == i)["default"]],
                key=f"{pfx}_{gname}",
            )
            sel_ids += [label_to_id[p] for p in picked]
    st.caption(f"عدد الكُتّاب المختارين: {len(sel_ids)} من {sum(1 for w in all_w if w['country'] in gcodes)}")
    if pfx == "wa" and not sel_ids:
        st.info("لسه ما اضفتش كتّاب عرب. روح تاب «مصادري» ← «إضافة ككاتب» واكتب الاسم وحساب تويتر واختار الجنسية.")
    if pfx == "wa":
        links_ = [f"[🐦 @{w['twitter']}](https://x.com/{w['twitter']})" for w in all_w if w["id"] in sel_ids and w.get("twitter")]
        if links_:
            st.markdown("افتح حساباتهم على X مباشرة: " + " · ".join(links_))
    qm_w = st.radio("طريقة البحث", ["📰 اعرض آخر ما كتبوه (بدون كلمات بحث)", "🔎 اعرض بس اللي يذكر كلماتي (الخانة فوق)"],
                    horizontal=True, key=f"{pfx}_qm")
    use_kw = qm_w.startswith("🔎")
    if use_kw:
        st.caption("هيفحص نص كل مقال/تغريدة ويعرض بس اللي فيه كلماتك. اكتب الكلمات في خانة «🔎 كلمات البحث» اللي فوق. وده ابطأ.")
    else:
        st.caption("هيعرض كل ما نشروه في الفترة من غير ما تكتب كلمة، مرتب بالأحدث.")
    use_ctype = st.checkbox("طبّق فلتر «نوع المحتوى» (من الفلاتر فوق)", value=False, key=f"{pfx}_ct")
    if st.button(btn_label, type="primary", use_container_width=True, key=f"go_{pfx}"):
        if not sel_ids:
            st.warning("اختر كاتباً واحداً على الأقل.")
        else:
            with st.spinner("جارٍ جلب المقالات والتغريدات وترجمة العناوين…"):
                items, notes = cached_writers(
                    tuple(sorted(sel_ids)), DAY_OPTS[days_label], json.dumps(S()["writers"], ensure_ascii=False, sort_keys=True)
                )
                items = [dict(a) for a in items]
            kw_terms = [t_.strip() for t_ in TERM_SPLIT.split(query) if t_.strip()]
            if use_ctype and ctype != "الكل":
                items = [a for a in items if a.get("ctype") == ctype]
            matchers = []
            if use_kw and not kw_terms:
                st.warning("اكتب كلمات البحث في الخانة فوق، او غيّر الطريقة لـ «اعرض آخر ما كتبوه».")
            if use_kw and kw_terms and items:
                with st.spinner("جارٍ فحص النصوص…"):
                    matchers = core.make_matchers(kw_terms, codes)
                    if pfx == "wa":  # التغريدة نصها هو العنوان: نفحص العنوان بلا جلب صفحات
                        for a in items:
                            a["found"] = core.find_mentions(a.get("title", ""), matchers, joiner)[0]
                        items = [a for a in items if a["found"]]
                    else:
                        core.enrich_items(items, matchers, joiner, limit=60)
                        items = [a for a in items if not (a.get("fetched") and not a.get("found"))]
            counts = {}
            for a in items:
                counts[a["writer"]] = counts.get(a["writer"], 0) + 1
            chosen = [w["name_ar"] for w in all_w if w["id"] in sel_ids]
            hl = sorted({s_ for alts in matchers for stems in alts for s_ in stems}, key=len, reverse=True)
            st.session_state[f"res_{pfx}"] = {
                "items": items, "errors": [] if items else ["لم يُعثر على شيء — راجع «الاستعلام المُرسل فعلياً» لمعرفة ما جُرّب (وهل تويتر رد)."],
                "used": notes, "summaries": {}, "counts": counts,
                "silent": [n for n in chosen if n not in counts], "hidden": 0, "hl": hl,
            }
    render_results(pfx)


if _on("intel", "wr"):
    with tab_wr:
        use_filters("wr", "kw")
        st.caption(
            "أحدث مقالات الرأي والتحليل لكتّاب ومراسلين مهتمين بالشرق الأوسط، بعناوين مترجمة، وزر «ترجم المقال» لقراءة النص مترجماً. "
            "النتائج تُحفظ نصف ساعة، فالفتح المتكرر سريع."
        )
        sub_f, sub_a = st.tabs(["🌐 الكتّاب الأجانب", "🇸🇦 الكتّاب العرب (تويتر وغيره)"])
        with sub_f:
            writers_panel("wr", ["US", "UK", "IL"], "اعرض أحدث مقالات الكتّاب الأجانب", ["en", "iw"])
            st.caption("ℹ️ مواقع مثل نيويورك تايمز وواشنطن بوست وفاينانشال تايمز وهآرتس مدفوعة: يظهر عنوانها مترجماً، وقد يتعذّر عرض نصها الكامل.")
        with sub_a:
            st.caption("هنا الكتّاب العرب اللي ضفتهم (سعوديون وخليجيون ومصريون وغيرهم): آخر تغريداتهم ومقالاتهم باسمهم. "
                       "الإضافة من تاب «مصادري» ← «إضافة ككاتب». تويتر بيحجب الأدوات الآلية، فممكن التغريدات تتأخر أو متظهرش في بعض الأوقات.")
            writers_panel("wa", ["SA", "GCC", "EG", "AR"], "🐦 اعرض أحدث ما كتبه الكتّاب العرب", ["ar"])


def render_saved():
    s = S()
    if not PERSIST:
        st.warning(
            "💡 التخزين الدائم غير مفعّل: ما تحفظه هنا يضيع عند تحديث الصفحة أو إعادة تشغيل التطبيق. "
            "فعّله بخطوتين (الشرح في README: GITHUB_TOKEN و GIST_ID)."
        )
    if st.session_state.get("store_err"):
        st.error(st.session_state["store_err"])
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("🔎 ابحث داخل المحفوظات (عنوان، كاتب، موقع، ملاحظة)", key="sv_q")
    order = c2.selectbox("الترتيب", ["الأحدث حفظاً", "الأحدث نشراً", "الأقدم نشراً (خط زمني)"], key="sv_order")
    items = list(s["saved"])
    if q.strip():
        ql = q.strip().lower()
        items = [
            x for x in items
            if ql in " ".join(str(x.get(k, "")) for k in ("title_ar", "title", "writer", "domain", "note", "outlet")).lower()
        ]
    if order == "الأحدث نشراً":
        items.sort(key=lambda x: x.get("seendate", ""), reverse=True)
    elif order.startswith("الأقدم"):
        items.sort(key=lambda x: x.get("seendate", ""))
    with st.expander("🎙️ نشرة صوتية من المحفوظات (مثالية للمترو)"):
        labels = {f"{n + 1}. {x.get('title_ar', '')[:70]}": x for n, x in enumerate(s["saved"])}
        picked = st.multiselect("اختر المقالات (بالترتيب الذي تُقرأ به)", list(labels), default=list(labels)[:5], key="bl_pick")
        st.caption("تُقرأ حسب إعدادات «🎧 إعدادات القراءة الصوتية» فوق في التاب (الصوت والسرعة وما يُقرأ).")
        if st.button("🎙️ اصنع النشرة", key="bl_go", use_container_width=True):
            if not picked:
                st.warning("اختر مقالاً واحداً على الأقل.")
            else:
                ss = st.session_state
                prog = st.progress(0.0, text="جارٍ تجهيز النصوص…")
                parts = []
                for n, lab in enumerate(picked):
                    x = labels[lab]
                    txt, _ = speech_text(x["url"], x.get("title_ar", ""), tts_get("tts_mode", TTS_MODES[0]))
                    num = ORDINALS[n] if n < len(ORDINALS) else str(n + 1)
                    parts.append(f"الخبر {num}. من {_ar_name(source_name(x.get('domain', '')))}، {source_country(x.get('domain', ''))}. {txt}")
                    prog.progress((n + 1) / (len(picked) + 1), text=f"جُهّز {n + 1} من {len(picked)}")
                full = "نشرة رادار الأخبار. " + " ... ".join(parts) + " ... انتهت النشرة."
                prog.progress(0.95, text=f"جارٍ النطق (حوالي {len(full) / 13 / 60:.0f} دقيقة صوت)…")
                res = make_audio(full, core.VOICES[tts_get("tts_voice", list(core.VOICES)[0])], tts_get("tts_rate", 0))
                prog.empty()
                if res:
                    ss["bulletin"] = res
        if st.session_state.get("bulletin"):
            audio_block(st.session_state["bulletin"], "bulletin", "marsad_bulletin")
    st.caption(f"عدد المحفوظات: {len(s['saved'])}" + (f" — المعروض: {len(items)}" if q.strip() else ""))
    sums = st.session_state.setdefault("sv_sum", {})
    for it in items:
        h = hashlib.md5(it["url"].encode()).hexdigest()[:10]
        with st.container(border=True):
            st.markdown(card_html(it) + snippet_html(it, []), unsafe_allow_html=True)
            try:
                when = datetime.fromisoformat(it.get("saved_at", "")).astimezone(core.TZ).strftime("%Y-%m-%d %H:%M")
                st.caption(f"📌 حُفظ: {when}")
            except Exception:
                pass
            st.text_area(
                "📝 ملاحظتي (لربط الأحداث ببعضها)", value=it.get("note", ""), key=f"note_{h}", height=80,
                on_change=set_note, args=(it["url"], f"note_{h}"),
            )
            b1, b2, b3 = st.columns(3)
            if b1.button("📝 ملخص سريع للمقال", key=f"svsum_{h}"):
                with st.spinner("جارٍ التلخيص…"):
                    sums[it["url"]] = core.summarize(it["url"])
            if b2.button("🎬 برومبت سكريبت", key=f"svscript_{h}"):
                st.session_state["article_prompt_active"] = {"title": it.get("title_ar") or it.get("title") or "مقال محفوظ", "prompt": article_script_prompts_mod.build_script_prompt([it])}
            b3.button("🗑️ حذف من المحفوظات", key=f"del_{h}", on_click=delete_item, args=(it["url"],))
            _sv_prompt = st.session_state.get("article_prompt_active")
            if _sv_prompt:
                with st.expander("🧠 برومبت السكريبت الجاهز", expanded=False):
                    st.text_area("البرومبت", _sv_prompt["prompt"], height=300, key=f"sv_prompt_{h}")
                    st.download_button("تنزيل البرومبت", _sv_prompt["prompt"], file_name="marsad_article_script_prompt.txt", key=f"sv_prompt_dl_{h}")
            listen_widget(it, f"sv_{h}")
            if it["url"] in sums:
                st.info(sums[it["url"]])


def render_manage():
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))
    st.markdown("### 🔗 أضف مصدراً أو كاتباً من رابط")
    st.caption(
        "الصق رابط خبر، أو رابط تغريدة (تويتر/X)، أو منشور/صفحة فيسبوك تحوي رابط مقال، وسيستخرج التطبيق الموقع والكاتب لتضيفهما بضغطة. "
        "يمكنك أيضاً تعبئة الخانات يدوياً."
    )
    st.text_input("رابط الخبر أو التغريدة", key="ms_url", placeholder="https://...")
    st.button("🔍 حلّل الرابط", on_click=do_analyze, use_container_width=True, key="ms_an")
    an = st.session_state.get("analysis")
    if an:
        if an.get("error"):
            st.warning(an["error"])
        tw = an.get("tweet")
        if tw:
            st.info(f"🐦 تغريدة {tw.get('author', '')} (@{tw.get('handle', '')}): {tw.get('text', '')}")
        if an.get("domain"):
            st.markdown(f"**الموقع:** {an.get('site_name')} (`{an['domain']}`)  \n**العنوان:** {an.get('title', '')}")
        if an.get("authors"):
            st.selectbox("الكتّاب المكتشفون (اختر لتعبئة بياناته)", [a["raw"] for a in an["authors"]], key="mw_pick", on_change=pick_author)
    st.markdown("#### ➕ إضافة كمصدر إخباري")
    st.text_input("اسم المصدر", key="ms_name")
    st.text_input("الدومين (مثال: example.com)", key="ms_domain")
    st.radio("يُضاف إلى تاب", ["إسرائيلية", "أمريكية", "بريطانية", "تركيا/إيران/إثيوبيا"], key="ms_group", horizontal=True)
    st.radio("لغة المصدر", ["إنجليزي", "عبري", "كلاهما", "تركي", "فارسي", "أمهري", "عربي"], key="ms_lang", horizontal=True)
    st.button("➕ أضف المصدر", on_click=add_source, use_container_width=True, key="ms_add")
    st.markdown("#### ➕ إضافة ككاتب")
    st.caption("للكاتب العربي من تويتر: اكتب اسمه بالعربي + حسابه (@name) + اختار الجنسية «سعودي» او «خليجي»... ومش لازم دومين. "
               "للكاتب الاجنبي: اسمه بالانجليزي + دومين موقع النشر.")
    st.text_input("الاسم بالعربية (للعرض والبحث)", key="mw_ar")
    st.text_input("حساب تويتر/X (مثال: @alfihrest او رابط الحساب)", key="mw_tw", placeholder="@alfihrest")
    st.text_input("اسم الكاتب بالإنجليزية (للكاتب الاجنبي، او اختياري)", key="mw_en")
    st.text_input("المنفذ / الصحيفة (اختياري)", key="mw_outlet")
    st.text_input("مواقع نشره (اختياري للعربي — دومين او اكتر بفاصلة)", key="mw_sites")
    st.text_input("الاسم بالعبرية (اختياري — لمواقع عبرية)", key="mw_heb")
    st.radio("جنسية الكاتب / المنفذ", ["سعودي", "خليجي", "مصري", "عربي آخر", "أمريكي", "بريطاني", "إسرائيلي"], key="mw_country", horizontal=True)
    st.radio("نوع كتاباته", ["رأي", "تحليل", "خبر"], key="mw_kind", horizontal=True)
    st.button("➕ أضف الكاتب", on_click=add_writer, use_container_width=True, key="mw_add")
    if st.session_state.get("mw_msg"):
        (st.success if st.session_state["mw_msg"].startswith("✅") else st.warning)(st.session_state["mw_msg"])
    st.markdown("#### ما أضفتَه")
    if not S()["sources"] and not S()["writers"]:
        st.caption("لم تضف شيئاً بعد.")
    for x in S()["sources"]:
        r1, r2 = st.columns([4, 1])
        r1.markdown(f"🌐 **{x['label']}** — `{x['domain']}` — تاب: {x['group']} — لغة: {x['lang']}")
        r2.button("حذف", key=f"rs_{x['domain']}_{x['group']}", on_click=remove_source, args=(x["domain"], x["group"]))
    for w in S()["writers"]:
        r1, r2 = st.columns([4, 1])
        r1.markdown(f"✍️ **{w['name_ar']}** ({w['name_en']}) — {w['outlet']} — `{', '.join(w['sites'])}`" + (f" — 🐦 @{w['twitter']}" if w.get("twitter") else ""))
        r2.button("حذف", key=f"rw_{w['id']}", on_click=remove_writer, args=(w["id"],))
    if not PERSIST:
        st.caption("⚠️ بدون التخزين الدائم تضيع هذه الإضافات عند تحديث الصفحة أو إعادة تشغيل التطبيق.")


def render_keys_admin():
    st.markdown("#### 🔑 شفرات التجربة (للمالك فقط)")
    if not GATE_ON:
        st.info("البوابة غير مفعّلة. لتفعيلها أضف في Secrets قيمة **ADMIN_KEY** (كلمة سر طويلة تخصّك) إلى جانب GITHUB_TOKEN وGIST_ID، "
                "ثم أعد تشغيل التطبيق. بعد التفعيل لن يفتح التطبيق إلا بشفرة، وتدخل أنت بكلمة ADMIN_KEY.")
        return
    def _host_url():
        try:
            h = st.context.headers.get("Host", "")
            return f"https://{h}" if h and not h.startswith(("localhost", "127.")) else ""
        except Exception:
            return ""

    base = (_sec("APP_URL") or _host_url() or st.session_state.get("app_url", "")).strip().rstrip("/")
    if not base:
        base = st.text_input("رابط التطبيق (اكتبه مرة واحدة)", placeholder="https://اسم-تطبيقك.streamlit.app", key="app_url").strip().rstrip("/")
    c1, c2 = st.columns(2)
    label = c1.text_input("اسم الشخص / الجهة (لتعرف لمن أعطيتها)", key="k_label")
    durs = {"6 ساعات": 6, "يوم": 24, "3 أيام": 72, "أسبوع": 168, "أسبوعان": 336, "شهر": 720, "مدة أخرى (بالساعات)": 0}
    dur = c2.selectbox("مدة التجربة (تبدأ من أول فتح)", list(durs), index=3, key="k_dur")
    scope_lbl = c1.selectbox("الصلاحية", ["كاملة (كل التطبيق)", "تقرير يومي فقط (اشتراك)"], key="k_scope")
    hours = durs[dur] or st.number_input("عدد الساعات", min_value=1, max_value=24 * 365, value=48, key="k_hours")
    if st.button("➕ ولّد شفرة جديدة", type="primary", key="k_new"):
        try:
            _, k = keys_mod.mutate(_GT, _GG, lambda ks: keys_mod.create(ks, label, hours, "reports" if scope_lbl.startswith("تقرير") else "full"))
            st.session_state["k_last"] = k["code"]
        except Exception as e:
            st.error(f"تعذّر الحفظ ({type(e).__name__}).")
    try:
        ks = store.load(_GT, _GG)["keys"]
    except Exception as e:
        st.error(f"تعذّر تحميل الشفرات ({type(e).__name__}).")
        return
    def link(c):
        return f"{base}/?k={c}" if base else f"?k={c}"
    if st.session_state.get("k_last"):
        st.success("تم التوليد. انسخ الرابط وأرسله:")
        st.code(link(st.session_state["k_last"]), language=None)
    icons = {"active": "🟢 فعّالة", "unused": "🟡 لم تُفتح", "expired": "⚪ انتهت", "revoked": "🔴 ملغاة", "unused_expired": "⚪ سقطت (لم تُفتح)"}
    for k in sorted(ks, key=lambda x: x.get("created", ""), reverse=True):
        stt = keys_mod.status(k)
        with st.container(border=True):
            seen = keys_mod.parse(k.get("last_seen"))
            seen_txt = seen.astimezone(core.TZ).strftime("%m-%d %H:%M") if seen else "—"
            st.markdown(f"**{k.get('label', '')}** — {icons.get(stt, stt)} — {keys_mod.human_left(k)}  \n"
                        f"{'📰 تقرير فقط' if k.get('scope') == 'reports' else 'صلاحية كاملة'} · فتحها {k.get('visits', 0)} مرة · آخر دخول: {seen_txt} (القاهرة) · المدة: {int(k.get('hours', 0))} ساعة")
            st.code(link(k["code"]), language=None)
            b1, b2 = st.columns(2)
            if stt in ("active", "unused") and b1.button("⛔ إلغاء الآن", key=f"krv_{k['code']}"):
                keys_mod.mutate(_GT, _GG, lambda ks_, c=k["code"]: keys_mod.find(ks_, c).update(revoked=True))
                st.rerun()
            if b2.button("🗑️ حذف من القائمة", key=f"kdl_{k['code']}"):
                keys_mod.mutate(_GT, _GG, lambda ks_, c=k["code"]: ks_.remove(keys_mod.find(ks_, c)))
                st.rerun()
    st.caption("ملاحظة: الضيف لا يرى محفوظاتك ولا مصادرك المضافة، وما يحفظه يزول بإغلاق الصفحة. الإلغاء يسري خلال ~10 دقائق على من هو داخل التطبيق.")


WATCH_SCOPES = {"il": "🇮🇱 اسرائيلي", "us": "🇺🇸 امريكي", "uk": "🇬🇧 بريطاني", "ar": "🇪🇬 عربي", "rg": "🌍 تركيا وايران واثيوبيا"}
WATCH_CFG, WATCH_OUT = "marsad_watch_cfg.json", "marsad_watch.json"


def _watch_load(force=False):
    if not (GH_TOKEN and GH_GIST):
        return None, {}
    if force or "watch_data" not in st.session_state or time.time() - st.session_state.get("watch_t", 0) > 300:
        try:
            st.session_state["watch_data"] = store.load_file(GH_TOKEN, GH_GIST, WATCH_OUT, None)
            st.session_state["watch_cfg"] = store.load_file(GH_TOKEN, GH_GIST, WATCH_CFG, {}) or {}
        except Exception as ex:
            st.error(f"تعذّر قراءة التقرير المحفوظ ({type(ex).__name__}).")
            return st.session_state.get("watch_data"), st.session_state.get("watch_cfg", {})
        st.session_state["watch_t"] = time.time()
    return st.session_state.get("watch_data"), st.session_state.get("watch_cfg", {})


@st.cache_data(ttl=86400, show_spinner=False)
def _tr_cached(p):
    r = tr(p, "auto", "ar")
    return r if core._HAS_AR.search(r) else p


def _watch_done_toggle(url):
    cfg = st.session_state.get("watch_cfg", {})
    done = set(cfg.get("done") or [])
    (done.discard if url in done else done.add)(url)
    cfg["done"] = sorted(done)
    st.session_state["watch_cfg"] = cfg
    try:
        store.save_file(GH_TOKEN, GH_GIST, WATCH_CFG, cfg)
    except Exception as ex:
        st.session_state["watch_err"] = f"تعذّر حفظ علامة «خلصته» ({type(ex).__name__})"


def render_watch():
    """تقرير مخصص بالكلمات والعلاقات: زر واحد يشغّله على GitHub Actions، والنتيجة محفوظة (للمالك)"""
    with st.expander("🎯 تقرير مخصص بكلمات ومواضيع معينة (زرار واحد، والنتيجة بتفضل محفوظة)", expanded=False):
        if not (GH_TOKEN and GH_GIST):
            st.info("محتاج التخزين الدائم (GITHUB_TOKEN وGIST_ID).")
            return
        data, cfg = _watch_load()
        tok, repo, branch = _sec("ACTIONS_TOKEN"), _sec("GH_REPO") or gh_actions.DEFAULT_REPO, _sec("GH_BRANCH") or "main"
        st.caption("اكتب مواضيعك، دوس زرار «شغّل»، وسيبه يشتغل على GitHub (ممكن ياخد من ربع ساعة لساعة، مش لازم تفضل فاتح التطبيق). "
                   "لما يخلص هتلاقي كل الاخبار هنا: ترجمة العنوان والمقال والملخص وعدد مرات ذكر الكلمات. وبتفضل محفوظة لحد ما تشغّل بحث جديد.")
        with st.expander("⚙️ المواضيع والاعدادات", expanded=data is None):
            txt = st.text_area("المواضيع (سطر لكل موضوع. + يعني الكلمتين مع بعض، | يعني بدائل، # تعليق)", height=280, key="watch_txt",
                               value=cfg.get("topics") or watch_mod.DEFAULT_TOPICS)
            c1, c2, c3 = st.columns(3)
            wdays = pick(c1, "الفترة (ايام)", [1, 2, 3, 4], int(cfg.get("days") or 2), "watch_days")
            per = pick(c2, "اخبار لكل موضوع", range(3, 21), int(cfg.get("per") or 10), "watch_per")
            deep = pick(c3, "اقرا وترجم اول كام خبر", range(0, 11), int(cfg["deep"]) if cfg.get("deep") is not None else 5, "watch_deep")
            keys_sel = st.multiselect("ادور في ايه؟", list(WATCH_SCOPES), default=[k for k in (cfg.get("scopes") or list(WATCH_SCOPES)) if k in WATCH_SCOPES],
                                      format_func=lambda k: WATCH_SCOPES[k], key="watch_scopes")
        if not tok:
            st.warning("زرار التشغيل محتاج ACTIONS_TOKEN في Secrets (نفس اللي عملناه للتقرير اليومي).")
        lr = None
        if tok:
            try:
                lr = gh_actions.last_run(tok, repo, "watch.yml")
            except Exception as ex:
                st.caption(f"تعذّر قراءة حالة التشغيل ({type(ex).__name__}). اتأكد انك رفعت ملف watch.yml.")
        busy = bool(lr and lr["status"] in ("queued", "in_progress", "waiting", "requested"))
        if lr:
            ico = {"success": "✅ خلص", "failure": "❌ فشل", "cancelled": "⚪ اتلغى"}.get(lr["conclusion"] or "", "⏳ شغال دلوقتي" if busy else "—")
            when = keys_mod.parse(lr["created"])
            wt = when.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if when else ""
            upd = keys_mod.parse(lr.get("updated"))
            ut = upd.astimezone(core.TZ).strftime("%H:%M") if upd else ""
            st.markdown(f"آخر تشغيل: **{ico}** — بدأ {wt} (القاهرة)" + (f" · آخر نشاط {ut}" if busy else f" · انتهى {ut}") + f" · [افتح التفاصيل على GitHub]({lr['url']})")
        elif tok:
            st.markdown("آخر تشغيل: **لسه مفيش** (لو لسه دايس من ثواني دوس «حدّث» تحت)")
        if tok:
            st.markdown(f"[📂 صفحة التقرير المخصص على GitHub](https://github.com/{repo}/actions/workflows/watch.yml)")
        if st.session_state.get("watch_msg"):
            st.success(st.session_state["watch_msg"])
        b1, b2 = st.columns(2)
        if b1.button("▶️ شغّل البحث الكبير دلوقتي", type="primary", disabled=busy or not tok, key="watch_go", use_container_width=True):
            ts = watch_mod.parse_topics(txt)
            if not ts or not keys_sel:
                st.warning("اكتب موضوع واحد على الاقل واختار قسم واحد.")
            else:
                new_cfg = {**cfg, "topics": txt, "days": wdays, "per": per, "deep": deep, "scopes": keys_sel}
                try:
                    store.save_file(GH_TOKEN, GH_GIST, WATCH_CFG, new_cfg)
                    st.session_state["watch_cfg"] = new_cfg
                    ok, msg = dispatch_tracked("watch.yml", "التقرير المخصص", gh_actions.dispatch, tok, repo, branch, "watch.yml")
                    if ok:
                        time.sleep(4)
                        st.session_state["watch_msg"] = f"✅ اتبعت الامر لـ GitHub الساعة {datetime.now(core.TZ).strftime('%H:%M')}. " + msg + " ولما يخلص دوس «حدّث»."
                        st.rerun()
                    st.error(msg)
                except Exception as ex:
                    st.error(f"مقدرتش ابدأ ({type(ex).__name__}).")
        if b2.button("🔁 حدّث (هات اخر نتيجة)", key="watch_refresh", use_container_width=True):
            st.session_state.pop("watch_msg", None)
            _watch_load(force=True)
            st.rerun()
        if st.session_state.pop("watch_err", None):
            st.warning("علامة «خلصته» ما اتحفظتش في المرة الاخيرة.")
        if not data:
            st.info("لسه مفيش نتيجة محفوظة. دوس «شغّل» وبعد ما يخلص دوس «حدّث». (اخر تحديث للنتيجة: لسه مفيش)")
            return
        done = set(cfg.get("done") or [])
        created = keys_mod.parse(data.get("created"))
        ct = created.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if created else ""
        st.markdown(f"### النتيجة المحفوظة — اتعملت {ct} (القاهرة) · اخر {data.get('days')} يوم")
        if not data.get("done", True):
            st.warning("ده تقرير مبدئي: الروابط والعناوين جاهزة، والمقالات المترجمة والملخصات لسه بتتجهز. دوس «حدّث» بعد شوية.")
        st.caption(f"اتفحص {data.get('n_sources')} موقع، وقريت {data.get('n_pool')} عنوان مباشرة.")
        scope_names = data.get("scope_names") or []
        f1, f2, f3 = st.columns([2, 2, 1])
        scope_f = f1.selectbox("القسم", ["الكل"] + scope_names, key="watch_f_scope")
        topic_f = f2.selectbox("الموضوع", ["الكل"] + [t["title"] for t in data["topics"]], key="watch_f_topic")
        hide_done = f3.checkbox("اخفي اللي خلصته", value=False, key="watch_f_done")
        shown = 0
        for t in data["topics"]:
            if topic_f != "الكل" and t["title"] != topic_f:
                continue
            items = [a for a in t["items"] if (scope_f == "الكل" or scope_f in (a.get("scopes") or [])) and not (hide_done and a["url"] in done)]
            if not items and topic_f == "الكل":
                continue
            with st.expander(f"{t['title']} — {len(items)} خبر", expanded=topic_f != "الكل"):
                for i, a in enumerate(items):
                    shown += 1
                    ttl = (a.get("title_ar") or a.get("title") or "").replace("[", "(").replace("]", ")")
                    mark = "✅ " if a["url"] in done else ""
                    st.markdown(f"**{mark}[{ttl}]({a['url']})**  \n{source_name(a.get('domain', ''))} · {fmt_seen(a.get('seendate', ''))}")
                    if a.get("fetched") and a.get("mcount") is not None:
                        st.caption(f"الكلمات اتذكرت {a['mcount']} مرة في مقال حوالي {a.get('words', 0)} كلمة — مستوى: {a.get('mlevel', '')}" + (f" — اتجاب بـ: {a['via']}" if a.get("via") else ""))
                    for p in a.get("points_ar", []):
                        st.markdown(f"- {p if core._HAS_AR.search(p) else _tr_cached(p)}")
                    rl = f"?view={quote(a['url'], safe='')}&seen={a.get('seendate', '')}&t={quote(a.get('title', '')[:200], safe='')}{auth_qs()}"
                    st.markdown(f"[📖 افتح المقال مترجم]({rl})")
                    if a.get("full_ar"):
                        with st.expander("المقال مترجم (اول جزء)"):
                            st.write(a["full_ar"])
                    st.checkbox("خلصته", value=a["url"] in done, key=f"wd_{t['title']}_{i}_{abs(hash(a['url']))}",
                                on_change=_watch_done_toggle, args=(a["url"],))
        if not shown:
            st.caption("مفيش اخبار بالفلاتر دي.")
        if data.get("overlap"):
            with st.expander("🔗 اخبار تخص اكتر من موضوع"):
                for a, ts in data["overlap"]:
                    ttl = (a.get("title_ar") or a.get("title") or "").replace("[", "(").replace("]", ")")
                    st.markdown(f"- [{ttl}]({a['url']}) ⟵ {' | '.join(ts)}")
        with st.expander("ملاحظات فنية"):
            for n in (data.get("notes") or [])[:40]:
                st.caption(n)
        md = watch_mod.to_markdown(data, source_name, fmt_seen)
        st.download_button("⬇️ نزّل التقرير (ملف نصي)", md, file_name="custom_report.md", key="watch_dl")
        with st.expander("📋 نسخ التقرير كنص (تلصقه عند اي ذكاء اصطناعي)"):
            st.code(md, language=None)


# ───────── 🧵 الملفات والخيوط: ربط كل الأخبار في ملفات وخيوط + منشورات فيس وتويتر + برومبت تحليل جاهز ─────────
DOS_RES_FILE, DOS_CFG_FILE = "marsad_dossiers.json", "marsad_dossiers_cfg.json"
TOPIC_CFG, TOPIC_STATUS = "marsad_topic_cfg.json", "marsad_topic_job.json"
EG_TABS = {"eg", "egt"}  # تابات الشأن المصري: نتايجها بتروح لربط الشأن المصري بس، ومبتتخلطش بالسياسة الإقليمية
PROFS = {"pol": {"sx": "", "cfg_file": DOS_CFG_FILE, "res_file": DOS_RES_FILE, "cfg_key": "dos_cfg", "res_key": "dos_res"},
         "eg": {"sx": "_eg", "cfg_file": "marsad_dossiers_eg_cfg.json", "res_file": "marsad_dossiers_eg.json", "cfg_key": "dos_cfg_eg", "res_key": "dos_res_eg"}}
TAB_LABELS = {"il": "الإسرائيلية", "us": "الأمريكية", "uk": "البريطانية", "rg": "تركيا وإيران وإثيوبيا", "eg": "الشأن المصري", "egt": "تتبّع موضوع", "trend": "ترند/موضوع طارئ", "ml": "ترجمة ثم بحث",
              "wr": "الكتّاب", "gd": "GDELT", "br": "تصفّح مصدر", "in": "مكتب الاستخبارات",
              "in_all": "مكتب الاستخبارات", "home": "البحث السريع"}
DOS_HELP = """
**الفكرة:** التبويب ده مش بيدور على أخبار جديدة بنفسه. هو بيرتب الأخبار اللي التطبيق جابها قبل كده، زي واحد بيرتب الجرايد اللي على الترابيزة في ملفات.

**1️⃣ جهّز الأخبار (مش لازم كلها):**
- **🚀 الأسرع:** افتح «بحث شامل في كل المصادر مرة واحدة»، اكتب كلماتك (أو سيبها فاضية)، اختار الفترة، ودوس الزرار. GitHub بيدور في كل المصادر لوحده، ولما يخلص دوس «حدّث وحمّل النتايج». هتلاقي نتيجة كل تاب جواه زي ما هي، وكلها داخلة في الربط، وبتفضل لحد ما تبحث تاني.
- **أسهل حاجة:** ما تعملش حاجة. التقرير اليومي بيتعمل لوحده كل صبح، والتبويب بياخد آخر 7 أيام منه.
- **بحثك في المصادر:** ابحث في أي تاب (أمريكية، بريطانية، إسرائيلية، تركيا وإيران...). كل نتيجة بتتحفظ لوحدها في **أرشيف البحث** (العداد اللي تحت)، حتى لو عملت بحث تاني أو قفلت التطبيق.
- **موضوع معين بعمق:** تاب «التقرير اليومي» ← «🎯 تقرير مخصص» ← اكتب المواضيع (زي `إيران + أمريكا`) ← «شغّل». بياخد من ربع ساعة لساعة على GitHub.
- **خبر عجبك:** احفظه في المحفوظات، وهو كمان بيدخل.
- **تحركات أمريكا وتصريحات ترامب:** ملف جاهز بالروابط بيدخل لوحده (فيه الحرب الأمريكية الإيرانية وأوكرانيا والسودان والقرن الأفريقي).
- **📅 مدة الأخبار:** من 6 ساعات لحد 30 يوم (الافتراضي 7 أيام)، وأي خبر أقدم بيتشال.
- **🔗 اللينكات:** تختار تفتح الصفحة الأصلية (للتصوير) أو صفحة الترجمة، وجنب كل خبر لينك للتاني.
- **ملحوظة:** لو النتيجة المعروضة قديمة، دوس «اربط واعرض» تاني عشان تتحدّث بالفترة اللي اخترتها.

**2️⃣ لو فيه ترند على فيس أو تويتر:** افتح «💬 منشورات فيس وتويتر»، الصق المنشور، ودوس «➕ أضف». المنشورات بتتعامل كادعاءات مش حقايق.

**3️⃣ دوس الزرار الأحمر «🔗 اربط واعرض الملفات والخيوط»** وسيب الأرقام زي ما هي.

**4️⃣ اختار ملف** من «📁 الملفات» (زي «الحرب الأمريكية الإيرانية»). جوه كل ملف: العناصر، والزاوية الأمريكية، و«🤖 برومبت التحليل».

**5️⃣ في «🤖 برومبت التحليل»:** اختار «🎬 اسكريبت 1» أو «اسكريبت 2» أو «🧭 اسكريبت 3» اللي بيطلّع قراءتك للمشهد (جرّب وشوف الأحسن) وحدد المدة، ودوس علامة النسخ، والصقه في شات Claude. هيرجعلك اسكريبت طويل بعامية قاهرية: هوك قاتل في أول 5 ثواني، وأفيهات سودا، وفكّ للمشهد وربط أمريكا وإيران وإسرائيل واليمن ومصر والسعودية ببعض، وأسئلة للمتابع كل نص دقيقة. ولو عايز تحليل مكتوب بس اختار «🧠 تحليل بس».

**نصيحة:** ابعت ملف واحد في المرة عشان التحليل يطلع مركز. ولو عايز كل حاجة، نزّل «⬇️ التقرير كامل» من تحت خالص.
"""
POST_PLATFORMS = ["فيسبوك", "تويتر / X", "تيك توك", "يوتيوب", "تليجرام", "تاني"]


def _dos_cfg_text(P="pol"):
    ss, pf = st.session_state, PROFS[P]
    if pf["cfg_key"] not in ss:
        txt = None
        if PERSIST:
            try:
                txt = (store.load_file(GH_TOKEN, GH_GIST, pf["cfg_file"], {}) or {}).get("text")
            except Exception:
                txt = None
        ss[pf["cfg_key"]] = txt or (dossiers_mod.egypt_config_text() if P == "eg" else dossiers_mod.default_config_text())
    return ss[pf["cfg_key"]]


def _dos_save_cfg(text, P="pol"):
    pf = PROFS[P]
    st.session_state[pf["cfg_key"]] = text
    st.session_state.pop("dos_cfg_edit" + pf["sx"], None)  # عشان مربع التعديل يعرض النسخة الجديدة
    if PERSIST:
        try:
            store.save_file(GH_TOKEN, GH_GIST, pf["cfg_file"], {"text": text})
        except Exception as e:
            st.session_state["dos_msg"] = f"⚠️ اتغيرت الملفات بس ما اتحفظتش في التخزين الدائم ({type(e).__name__})"


def _dos_result(P="pol"):
    ss, pf = st.session_state, PROFS[P]
    if pf["res_key"] not in ss:
        ss[pf["res_key"]] = None
        if PERSIST:
            try:
                ss[pf["res_key"]] = store.load_file(GH_TOKEN, GH_GIST, pf["res_file"], None)
            except Exception:
                pass
    return ss[pf["res_key"]]


DOS_POOL_FILE = "marsad_dos_pool.json"
DOS_PREFS_FILE = "marsad_dos_prefs.json"


def _dos_prefs():
    """آخر اختياراتك في تاب الخيوط (الفترة والربط واللينك)، بتتحفظ عشان تلاقيها زي ما سبتها على الموبايل والكمبيوتر"""
    ss = st.session_state
    if "dos_prefs" not in ss:
        ss["dos_prefs"] = {}
        if PERSIST:
            try:
                ss["dos_prefs"] = store.load_file(GH_TOKEN, GH_GIST, DOS_PREFS_FILE, {}) or {}
            except Exception:
                pass
    return ss["dos_prefs"]


def _dos_save_prefs(P, cur):
    prefs = _dos_prefs()
    if prefs.get(P) == cur:
        return
    prefs[P] = cur
    if PERSIST:
        try:
            store.save_file(GH_TOKEN, GH_GIST, DOS_PREFS_FILE, prefs)
        except Exception:
            pass
POOL_KEYS = ["url", "title", "title_ar", "title_en", "seendate", "domain", "country_ar", "snip_ar", "outlet"]


def _dos_pool():
    """أرشيف البحث: كل نتيجة بحث بتعملها في أي تاب بتتحفظ هنا تلقائياً (آخر 21 يوم)، عشان تدخل في الربط حتى لو بحثت تاني أو قفلت"""
    ss = st.session_state
    if "dos_pool" not in ss:
        ss["dos_pool"] = {}
        if PERSIST:
            try:
                ss["dos_pool"] = store.load_file(GH_TOKEN, GH_GIST, DOS_POOL_FILE, {}) or {}
            except Exception:
                pass
    pool, added = ss["dos_pool"], 0
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for k, v in list(ss.items()):
        if not (k.startswith("res_") and isinstance(v, dict)) or v.get("partial"):
            continue
        for a in v.get("items") or []:
            if not (isinstance(a, dict) and a.get("url")):
                continue
            if a["url"] not in pool:
                pool[a["url"]] = {**{f: a[f] for f in POOL_KEYS if a.get(f)}, "pooled": now, "tab": k[4:], "tabs": [k[4:]]}
                added += 1
            else:
                tl = pool[a["url"]].setdefault("tabs", [pool[a["url"]].get("tab", "")])
                if k[4:] not in tl:
                    tl.append(k[4:])
                    added += 1
    if added:
        cut = (datetime.now(timezone.utc) - timedelta(days=21)).strftime("%Y%m%d")
        keep = sorted(pool.values(), key=lambda a: a.get("pooled", ""), reverse=True)
        keep = [a for a in keep if (a.get("seendate") or a.get("pooled", ""))[:8] >= cut][:3000]
        ss["dos_pool"] = pool = {a["url"]: a for a in keep}
        if PERSIST:
            try:
                store.save_file(GH_TOKEN, GH_GIST, DOS_POOL_FILE, pool)
            except Exception:
                pass
    return pool


def _pool_for(P):
    """أخبار الأرشيف بتاعة القسم ده بس: الشأن المصري لوحده، والسياسة الإقليمية لوحدها"""
    out = []
    for a in _dos_pool().values():
        tabs = set(a.get("tabs") or [a.get("tab", "")])
        if (P == "eg" and tabs & EG_TABS) or (P != "eg" and tabs - EG_TABS):
            out.append(a)
    return out


def _dos_collect(use, uploads, P="pol"):
    """يجمع الأخبار من كل الأماكن اللي اخترتها في التطبيق"""
    lab = lambda d: about_plain(re.sub(r"<[^>]+>", "", html.unescape(src_label(d, with_domain=False))).split("·")[0])
    out, counts = [], {}

    def add(items, origin):
        n = 0
        for a in items or []:
            if isinstance(a, dict) and a.get("url") and (a.get("title") or a.get("title_ar")):
                out.append(dossiers_mod.from_app_item(a, lab, source_country, origin))
                n += 1
        counts[origin] = counts.get(origin, 0) + n

    if "بحث" in use:
        add(_pool_for(P), "نتايج البحث")
    if P == "eg":
        use = [u for u in use if u == "بحث"]
    if "يومي" in use and _GT and _GG:
        try:
            if "reports" not in st.session_state:
                st.session_state["reports"] = store.load_reports(_GT, _GG)
                st.session_state["reports_t"] = time.time()
            for rep in (st.session_state["reports"].get("archive") or {}).values():
                for f in (rep.get("files") or {}).values():
                    add(f.get("items"), "التقرير اليومي")
        except Exception as e:
            st.warning(f"تعذّر تحميل التقارير اليومية ({type(e).__name__})")
    if "مخصص" in use and GH_TOKEN and GH_GIST:
        data, _cfg = _watch_load()
        for t in (data or {}).get("topics") or []:
            add(t.get("items"), "التقرير المخصص")
    if "محفوظات" in use:
        add(S()["saved"], "المحفوظات")
    if "أمريكا" in use:
        us = dossiers_mod.us_moves_items()
        out += us
        counts["تحركات أمريكا"] = len(us)
    for up in uploads or []:
        try:
            got = dossiers_mod.items_from_csv(up.getvalue(), f"ملف: {up.name}")
            out += got
            counts[f"ملف: {up.name}"] = len(got)
        except Exception as e:
            st.warning(f"الملف {up.name} مش مقروء: {e}")
    posts = [dossiers_mod.from_post(p) for p in S().get("posts", []) if (p.get("scope") or "pol") == P]
    out += posts
    counts["منشورات فيس وتويتر"] = len(posts)
    return out, counts


def _dos_item_md(it):
    ttl = (it.get("title") or "").replace("[", "(").replace("]", ")")
    icon = "💬" if it.get("kind") == "منشور" else "📰"
    url = it.get("url") or ""
    if url:
        seen = str(it.get("date", "")).replace("-", "") + "T000000Z"
        tr_link = f"?view={quote(url, safe='')}&seen={seen}&t={quote((it.get('title') or '')[:200], safe='')}{auth_qs()}"
        if st.session_state.get("dos_link", "orig") == "tr":
            head, other = f"[{ttl}]({tr_link})", f" · [🌐 الأصل]({url})"
        else:
            head, other = f"[{ttl}]({url})", f" · [📖 مترجم]({tr_link})"
    else:
        head, other = ttl, ""
    line = f"- {icon} **{head}**  \n  {it.get('date', '')} · {it.get('source', '')} · {it.get('country') or 'بلد غير محدد'}{other}"
    if it.get("statement"):
        line += " · 🎤 فيه تصريح"
    if it.get("summary"):
        line += f"  \n  > {it['summary'][:300]}"
    return line


def _dos_group(g, scope, key):
    us = g.get("us_items") or []
    st.markdown(f"**{len(g['items'])} عنصر** (أخبار {g['news_count']} · منشورات {g['post_count']}) من **{len(g['sources'])} مصدر** · "
                f"من {g['first']} لحد {g['last']} · تصريحات: {g['statements']}"
                + (f" · 📈 أيام ارتفاع: {'، '.join(g['spikes'])}" if g.get("spikes") else ""))
    if g.get("long"):
        st.caption("⚠️ الخيط ده طويل (أكتر من 14 يوم)، ممكن يكون فيه أكتر من قصة. جرّب «أقل عدد أطراف مشتركة» = 3")
    names = [f"📋 العناصر ({len(g['items'])})"] + ([f"🇺🇸 الزاوية الأمريكية ({len(us)})"] if us else []) + ["🤖 برومبت التحليل"]
    tabs = st.tabs(names)
    with tabs[0]:
        if len(g["items"]) > 60:
            st.caption(f"آخر 60 من {len(g['items'])} (الباقي في التقرير اللي بيتنزل تحت)")
        st.markdown("\n".join(_dos_item_md(it) for it in g["items"][-60:]))
    if us:
        with tabs[1]:
            st.caption("تصريحات وتحركات ترامب وأمريكا اللي تخص الموضوع ده")
            st.markdown("\n".join(_dos_item_md(it) for it in us[-15:]))
    with tabs[-1]:
        st.caption("فيه المبادئ كلها: الدوافع، التبعات، الأحداث، الترابط، التصريحات ونتيجتها، قصد كل جريدة، وجهة نظر تانية، والحبكة.")
        kinds = ["🎬 اسكريبت 1 (عامية قاهرية، هوك وأفيهات وربط)", "🎬 اسكريبت 2 (نفس الروح + جدول وقايع وقواعد دقة)", "🧭 اسكريبت 3 (قراءة المشهد من وجهة نظرك)", "📜 شرح للمواطن (قانون / قرار / اقتصاد / جريمة)", "🧠 تحليل بس"]
        eg_mode_ = key.startswith("_eg") or key.startswith("egt")
        if eg_mode_:
            kinds = ["🇪🇬 اسكريبت شأن مصري (للمواطن، من غير سياسة المنطقة)"] + kinds
        if scope == "الموضوع" or eg_mode_:
            kinds = ["🔎 تقرير تتبّع (خط زمني + مقارنة المصادر + استنتاج)"] + kinds
        kind = st.radio("عايز إيه؟", kinds, horizontal=True, key=f"dos_pk_{key}")
        egy = True
        if kind.startswith("🧭"):  # الزاوية القومية في اسكريبت 3 بس
            egy_lbl = "🇪🇬 اكتب من زاوية قومية مصرية وعربية (المقياس هو مصلحة مصر والعرب)"
            egy = st.checkbox(egy_lbl, value=not eg_mode_, key=f"dos_egy_{key}")
        if kind.startswith("🇪🇬"):
            mins = pick(st, "مدة الفيديو (دقايق)", [3, 5, 8, 10, 15, 20], 8, f"dos_pme_{key}")
            txt = dossiers_mod.eg_script_prompt(g, mins)
        elif kind.startswith("🎬"):
            mins = pick(st, "مدة الفيديو (دقايق)", [3, 5, 8, 10, 15, 20], 8, f"dos_pm_{key}")
            txt = dossiers_mod.script_prompt2(scope, g, mins, egypt=egy) if kind.startswith("🎬 اسكريبت 2") else dossiers_mod.script_prompt(scope, g, mins, egypt=egy)
        elif kind.startswith("🧭"):
            mins = pick(st, "مدة الفيديو (دقايق)", [3, 5, 8, 10, 15, 20], 8, f"dos_pm3_{key}")
            view = st.text_area("رأيك المبدئي في الموضوع (اختياري، جملة أو اتنين)", key=f"dos_view_{key}", height=90,
                                placeholder="مثال: أنا شايف إن ترامب بيستعد لضربة تقيلة بس مستني اللحظة المناسبة اقتصادياً")
            st.caption("لو كتبت رأيك، الذكاء الاصطناعي هيبني عليه لو الأدلة بتسنده، ولو بتعاكسه هيقولك بصراحة. ولو سيبتها فاضية هيطلّع هو أقوى قراءة من الأخبار.")
            txt = dossiers_mod.script_prompt3(scope, g, mins, view, egypt=egy)
        elif kind.startswith("📜"):
            txt = dossiers_mod.explain_prompt(scope, g)
        elif kind.startswith("🔎"):
            txt = dossiers_mod.topic_prompt(g)
        else:
            txt = dossiers_mod.prompt_for(scope, g)
        st.info("📋 دوس علامة النسخ اللي فوق على الشمال في المربع الرمادي، وبعدين الصقه في شات Claude.")
        st.code(txt, language=None)


def render_posts(P="pol"):
    sx = PROFS[P]["sx"]
    s = S()
    s.setdefault("posts", [])
    st.caption("الصق هنا اي منشور من فيس او تويتر عن ترند او قضية، وهيتخلط مع الاخبار في نفس الملفات والخيوط. "
               "المنشورات بتتعامل كادعاءات محتاجة تحقق، مش كأخبار مؤكدة.")
    with st.form(f"dos_post_form{sx}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        pdate = c1.date_input("تاريخ المنشور", value=datetime.now(core.TZ).date())
        plat = c2.selectbox("المنصة", POST_PLATFORMS)
        author = c3.text_input("اسم الحساب")
        text = st.text_area("نص المنشور", height=150)
        c4, c5 = st.columns(2)
        url = c4.text_input("رابط المنشور (اختياري)")
        country = c5.text_input("بلد صاحب الحساب (اختياري)")
        if st.form_submit_button("➕ أضف المنشور", use_container_width=True):
            if text.strip():
                s["posts"].insert(0, {"date": pdate.isoformat(), "platform": plat, "author": author.strip(),
                                      "text": text.strip(), "url": url.strip(), "country": country.strip(), "scope": P})
                persist()
                st.session_state["dos_msg"] = "✅ المنشور اتضاف. دوس «اربط» تاني عشان يدخل في التحليل."
            else:
                st.warning("اكتب نص المنشور الأول.")
    mine = [(i0, p0) for i0, p0 in enumerate(s["posts"]) if (p0.get("scope") or "pol") == P]
    if mine and st.toggle(f"💬 اعرض المنشورات المحفوظة ({len(mine)})", key=f"dos_show_posts{sx}"):
        if True:
            for i, p in mine:
                c1, c2 = st.columns([6, 1])
                c1.markdown(f"**{p.get('platform', '')} · {p.get('author') or 'حساب'}** · {p.get('date', '')}  \n{p.get('text', '')[:400]}")
                if c2.button("🗑️ امسح", key=f"dos_pdel{sx}_{i}"):
                    s["posts"].pop(i)
                    persist()
                    st.rerun()


@_fragment
def render_topic_track(P="eg"):
    """تتبّع موضوع أو ترند: بيدور عليه في المصادر، يجمّع الأخبار في ملف واحد وخيوط، ويطلّعلك برومبت تحليل. P = "eg" للشأن المصري، "pol" للسياسة والمنطقة"""
    egp = P == "eg"
    pk, rk = ("egt", "egt") if egp else ("trd", "trend")
    st.markdown("### 🔎 تتبّع موضوع كامل (من كل المصادر)" if egp else "### 🔎 تتبّع ترند أو موضوع طارئ")
    st.caption("اكتب الموضوع زي ما بتقوله (" + ("مثال: ارتفاع أسعار الطماطم في الأسواق، أو جريمة عروس الإسماعيلية" if egp else
               "مثال: وقف الطيران الأمريكي بين الولايات، أو توقف مايكروسوفت في دول كتير") + "). هيدور عليه في المصادر اللي تختارها، "
               "ويجمّع الأخبار في ملف واحد مرتب بالتاريخ، ويربطها في خيوط، ويجهزلك برومبت تحليل واستنتاج. المنشورات اللي ضفتها في «💬 منشورات فيس وتويتر» بتدخل لو فيها نفس الكلمات. "
               "ولو الموضوع هيفضل معاك، دوس تحت «💾 خلّيه ملف دائم».")
    c1, c2 = st.columns([3, 2])
    topic = c1.text_input("🎯 الموضوع", key=f"{pk}_topic", placeholder="ارتفاع أسعار الطماطم في الأسواق" if egp else "وقف الطيران الأمريكي بين الولايات")
    alts = c2.text_input("كلمات بديلة (بفاصلة)", key=f"{pk}_alts", placeholder="سعر الطماطم، الطماطم، أسعار الخضار" if egp else "ground stop، FAA، تأخير الرحلات، مطارات أمريكا")
    c3, c4 = st.columns(2)
    days = pick(c3, "الفترة (أيام)", [1, 2, 3, 7, 14, 30, 60], 3 if not egp else 7, f"{pk}_days")
    if egp:
        scopes = ["🇪🇬 المصادر المصرية بس", "🇪🇬 + القنوات العربية (تغطيتها لمصر)", "🌐 كل حاجة (مصرية وعربية وإسرائيلية وأمريكية وبريطانية)"]
    else:
        scopes = ["🌍 كل مصادر المنطقة والعالم (إسرائيلية وأمريكية وبريطانية وتركيا وإيران وإثيوبيا وعربية)", "🇺🇸🇬🇧 الأمريكية والبريطانية بس", "🌐 كل ده + المصرية"]
    scope = c4.radio("هدور فين؟", scopes, key=f"{pk}_scope")
    if egp:
        sel = [e for g, ents in EGYPT.items() if g != ARAB_EG_GROUP for e in ents]
        if scope.startswith("🇪🇬 +") or scope.startswith("🌐"):
            sel += list(EGYPT[ARAB_EG_GROUP])
        if scope.startswith("🌐"):
            seen = {e[1] for e in sel}
            sel += [e for gg in (ARABIC, ISRAEL, USA, UK) for ents in gg.values() for e in ents if e[1] not in seen]
        gcode, gn_c = "EG", "EG"
    else:
        groups_ = (USA, UK) if scope.startswith("🇺🇸") else (ISRAEL, USA, UK, REGION, ARABIC)
        sel = [e for gg in groups_ for ents in gg.values() for e in ents]
        if scope.startswith("🌐"):
            sel += [e for g, ents in EGYPT.items() if g != ARAB_EG_GROUP for e in ents]
        seen_d, uniq = set(), []
        for e in sel:
            if e[1] not in seen_d:
                seen_d.add(e[1])
                uniq.append(e)
        sel, gcode, gn_c = uniq, None, "US"
    sel += [(x["label"], x["domain"], x["lang"]) for x in S()["sources"] if x["group"] in (("eg", "egt") if egp else ("il", "us", "uk", "rg", "trend"))]
    st.caption(f"عدد المصادر اللي هيدور فيها: {len(sel)}" + ("" if egp else " (ممكن ياخد كام دقيقة)"))
    tok_ = _sec("ACTIONS_TOKEN")
    gh_ok = bool(tok_ and GH_GIST and GH_TOKEN)
    runmode = st.radio("التشغيل", ["🚀 على GitHub (تقدر تقفل التطبيق وترجع بعدين)", "⚡ هنا في التطبيق دلوقتي (لازم تفضل فاتحه)"],
                       index=0 if gh_ok else 1, horizontal=True, key=f"{pk}_runmode")
    on_gh = runmode.startswith("🚀")
    if on_gh:
        if not gh_ok:
            st.warning("التشغيل على GitHub محتاج ACTIONS_TOKEN في Secrets (نفس اللي عملناه للبحث الشامل) واتأكد إنك رفعت ملف topic.yml.")
        else:
            ss_ = st.session_state
            repo_, branch_ = _sec("GH_REPO") or gh_actions.DEFAULT_REPO, _sec("GH_BRANCH") or "main"
            t0_, lr_ = ss_.get(f"{pk}_lr", (0, None))
            if time.time() - t0_ > 45:
                try:
                    lr_ = gh_actions.last_run(tok_, repo_, "topic.yml")
                except Exception as ex:
                    lr_ = None
                    st.caption(f"تعذّر قراءة حالة التشغيل ({type(ex).__name__}). اتأكد إنك رفعت ملف topic.yml.")
                ss_[f"{pk}_lr"] = (time.time(), lr_)
            busy_ = bool(lr_ and lr_["status"] in ("queued", "in_progress", "waiting", "requested"))
            t1_, tst = ss_.get(f"{pk}_tst", (0, {}))
            if time.time() - t1_ > 60:
                try:
                    tst = store.load_file(GH_TOKEN, GH_GIST, TOPIC_STATUS, {}) or {}
                except Exception:
                    tst = {}
                ss_[f"{pk}_tst"] = (time.time(), tst)
            if lr_:
                ico_ = {"success": "✅ خلص", "failure": "❌ فشل", "cancelled": "⚪ اتلغى"}.get(lr_["conclusion"] or "", "⏳ شغال دلوقتي" if busy_ else "—")
                st.markdown(f"آخر تشغيل على GitHub: **{ico_}** · [التفاصيل]({lr_['url']})")
            if tst.get("topic"):
                st.caption(f"آخر موضوع اتبعت: «{tst['topic']}» · الحالة: {tst.get('state', '')}" + (f" · {tst.get('count', 0)} نتيجة" if tst.get("count") is not None else "")
                           + (f" · {tst.get('error', '')[:100]}" if tst.get("error") else ""))
            b1_, b2_ = st.columns(2)
            if b1_.button("🚀 ابعت التتبّع لـ GitHub", type="primary", disabled=busy_, use_container_width=True, key=f"{pk}_ghgo"):
                if not topic.strip():
                    st.warning("اكتب الموضوع الأول.")
                else:
                    code_ = (["local", "arab", "all"] if egp else ["world", "us_uk", "plus_eg"])[scopes.index(scope)]
                    try:
                        store.save_file(GH_TOKEN, GH_GIST, TOPIC_CFG, {"topic": topic.strip(), "alts": alts.strip(), "days": days, "scope": code_, "profile": P})
                        ok_, msg_ = dispatch_tracked("topic.yml", "تتبّع موضوع", gh_actions.dispatch, tok_, repo_, branch_, "topic.yml")
                        if ok_:
                            time.sleep(3)
                            ss_.pop(f"{pk}_lr", None)
                            ss_.pop(f"{pk}_tst", None)
                            st.success(f"✅ اتبعت لـ GitHub الساعة {datetime.now(core.TZ).strftime('%H:%M')}. " + msg_ + " ولما يخلص دوس «حدّث وحمّل النتيجة».")
                        else:
                            st.error(msg_)
                    except Exception as ex:
                        st.error(f"مقدرتش أبدأ ({type(ex).__name__}).")
            if b2_.button("🔄 حدّث وحمّل النتيجة", use_container_width=True, key=f"{pk}_ghref"):
                ss_.pop(f"{pk}_lr", None)
                ss_.pop(f"{pk}_tst", None)
                try:
                    n_ = reload_results()
                    st.success(f"✅ اتحمّل آخر نتايج محفوظة ({n_} قسم). النتيجة تحت.")
                except Exception as ex:
                    st.error(f"تعذّر التحميل ({type(ex).__name__}).")
    if (not on_gh) and st.button("🔎 تتبّع الموضوع", type="primary", use_container_width=True, key=f"{pk}_go"):
        if not topic.strip():
            st.warning("اكتب الموضوع الأول.")
        else:
            terms = [topic.strip()] + [t.strip() for t in TERM_SPLIT.split(alts) if t.strip()]
            g_ = globals()
            keep = {k: g_[k] for k in ("query", "match", "joiner", "ctype", "start_utc", "end_utc", "max_rec", "verify", "hide_nomatch")}
            end_ = datetime.now(timezone.utc)
            g_.update(query="، ".join(terms), match=core.MATCH_MODES[0], joiner="OR", ctype="الكل",
                      start_utc=end_ - timedelta(days=days), end_utc=end_, max_rec=40, verify=True, hide_nomatch=True)
            try:
                seed, gnotes = [], []
                with st.spinner("جارٍ جلب نتائج أخبار Google أولاً…"):
                    try:
                        seed, gnotes = gn_seed(sel, gn_c, terms)
                    except Exception as ex:
                        gnotes = [f"Google News تعذّر: {type(ex).__name__}"]
                do_search(rk, core.jobs_for_sources(sel, gcode), sel, terms=terms, seed=seed)
                if gnotes and st.session_state.get(f"res_{rk}"):
                    st.session_state[f"res_{rk}"]["used"] += gnotes
                try:
                    direct_title_hits(rk, sel, terms)
                except Exception as ex:
                    st.caption(f"تعذّر البحث المباشر في الخلاصات: {type(ex).__name__}")
            finally:
                g_.update(keep)
            res_ = st.session_state.get(f"res_{rk}")
            if res_ is not None:
                res_.update(topic=topic.strip(), alts=alts.strip(), days=days, created=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    res = st.session_state.get(f"res_{rk}") or {}
    if not res.get("topic"):
        return
    st.markdown(f"#### 📌 {res['topic']}" + (f" — خلال آخر {res.get('days', '?')} يوم" if res.get("days") else ""))
    lab = lambda d: about_plain(re.sub(r"<[^>]+>", "", html.unescape(src_label(d, with_domain=False))).split("·")[0])
    items = [dossiers_mod.from_app_item(a, lab, source_country, "تتبّع موضوع") for a in res.get("items") or []
             if isinstance(a, dict) and a.get("url") and (a.get("title") or a.get("title_ar"))]
    words = [res["topic"]] + [t.strip() for t in TERM_SPLIT.split(res.get("alts", "")) if t.strip()]
    if st.checkbox("💬 ضمّ منشوراتي (فيس/تويتر) اللي فيها كلمات الموضوع", value=True, key=f"{pk}_posts"):
        pats = [dossiers_mod.make_pattern([w]) for w in words]
        for p_ in S().get("posts", []):
            if (p_.get("scope") or "pol") == P and any(pt is not None and pt.search(dossiers_mod.normalize(p_.get("text", ""))) for pt in pats):
                items.append(dossiers_mod.from_post(p_))
    if not items:
        st.info("مفيش نتائج للموضوع ده في الفترة دي. جرّب كلمات بديلة أو فترة أطول أو مصادر أكتر.")
    else:
        r = dossiers_mod.run(items, [], 3, 2, res.get("days"), topic=res["topic"])
        if r["dossiers"]:
            _dos_group(r["dossiers"][0], "الموضوع", pk)
        if r["threads"]:
            st.markdown(f"**🧵 الخيوط اللي طلعت جوا الموضوع ({r['n_threads']})**")
            labels = [f"{n}. {t['name']} — {len(t['items'])} عنصر · {t['first']} → {t['last']}" for n, t in enumerate(r["threads"][:8], 1)]
            pick_thr = st.selectbox("اختار خيط تشوفه", labels, key=f"{pk}_thread")
            n = labels.index(pick_thr) + 1
            _dos_group(r["threads"][n - 1], "الخيط", f"{pk}_t{n}")
    st.markdown("**💾 خلّيه ملف دائم**")
    st.caption("بيتحفظ في «📁 الملفات» بتاعتك، وأي خبر جديد فيه الكلمات دي (من أي بحث بتعمله بعد كده) يدخله لوحده.")
    d1, d2, d3 = st.columns([3, 3, 1])
    fname = d1.text_input("اسم الملف", value=res["topic"][:60], key=f"{pk}_fname")
    fwords = d2.text_input("كلمات الملف (بفاصلة، كلمة واحدة منهم تكفي)", value="، ".join(w for w in words[1:]) or res["topic"], key=f"{pk}_fwords")
    fkind = d3.radio("النوع", ["ملف", "ترند"], key=f"{pk}_fkind")
    if st.button("💾 احفظه ملف دائم", key=f"{pk}_save"):
        ws = [w.strip() for w in re.split(r"[,،]", fwords) if w.strip()]
        if fname.strip() and ws:
            _dos_save_cfg(dossiers_mod.add_dossier(_dos_cfg_text(P), fname.strip(), ws, fkind), P)
            st.success(f"✅ اتحفظ ملف «{fname.strip()}». روح «🔗 اربط واعرض» عشان يظهر في الملفات.")
        else:
            st.warning("اكتب اسم الملف وكلمة واحدة على الأقل.")
    if st.toggle("📄 اعرض كروت نتائج البحث (الأصل والترجمة)", key=f"{pk}_cards"):
        render_results(rk)


def render_dossiers_cfg(P="pol"):
    sx = PROFS[P]["sx"]
    egp = P == "eg"
    with st.expander("⚙️ الملفات اللي بيدور عليها (تقدر تضيف وتعدل)"):
        txt = _dos_cfg_text(P)
        dos, err = dossiers_mod.parse_config(txt)
        if dos:
            st.markdown("**الملفات الحالية:** " + "، ".join(("🇺🇸 " if d["lens"] else "📈 " if d["type"] == "ترند" else "📁 ") + d["name"] for d in dos))
        if st.button(("🆕 ضيف الملفات الجاهزة للشأن المصري (السيسي 2030، الإخوان، الاقتصاد والأسعار، قوانين، جرائم...)" if egp else "🆕 ضيف الملفات الجاهزة الجديدة (غزة وفلسطين، رفح، حدود السودان، اقتصاد مصر، قوانين، جرائم...)"), key=f"dos_merge_btn{sx}", use_container_width=True):
            try:
                new_txt, added = dossiers_mod.merge_defaults(txt, egypt=egp)
                if added:
                    _dos_save_cfg(new_txt, P)
                    st.session_state["dos_msg"] = "✅ اتضاف: " + "، ".join(added) + ". دوس «اربط» عشان تظهر."
                else:
                    st.session_state["dos_msg"] = "كل الملفات الجاهزة موجودة عندك بالفعل."
                st.rerun()
            except Exception as ex:
                st.error(f"مقدرتش أضيف ({type(ex).__name__}).")
        st.markdown("**➕ ملف أو ترند جديد بسرعة**")
        c1, c2 = st.columns(2)
        nm = c1.text_input("اسم الملف (مثال: ترند الطماطم في تونس)", key=f"dos_new_name{sx}")
        kind = c2.radio("النوع", ["ملف", "ترند"], horizontal=True, key=f"dos_new_kind{sx}")
        g1 = st.text_input("كلمات المجموعة الأولى مفصولة بفاصلة (مثال: طماطم، tomato)", key=f"dos_new_g1{sx}")
        g2 = st.text_input("كلمات مجموعة تانية لازم تتذكر معاها (اختياري، مثال: تونس، tunisia)", key=f"dos_new_g2{sx}")
        if st.button("➕ ضيف الملف", key=f"dos_new_btn{sx}"):
            groups = [[w.strip() for w in re.split(r"[,،]", g) if w.strip()] for g in (g1, g2)]
            groups = [g for g in groups if g]
            if nm.strip() and groups:
                raw = json.loads(txt)
                raw.append({"name": nm.strip(), "type": kind, "all_of": groups})
                _dos_save_cfg(json.dumps(raw, ensure_ascii=False, indent=1), P)
                st.session_state["dos_msg"] = f"✅ اتضاف ملف «{nm.strip()}». دوس «اربط» عشان يظهر."
                st.rerun()
            else:
                st.warning("اكتب اسم الملف وكلمة واحدة على الأقل.")
        if IS_ADMIN:
            st.markdown("**تعديل متقدم (JSON)**: كل ملف ليه اسم، ونوع، و all_of = مجموعات كلمات، والخبر لازم يلمس كلمة من كل مجموعة.")
            new = st.text_area("تعريف الملفات", value=txt, height=300, key=f"dos_cfg_edit{sx}")
            c1, c2 = st.columns(2)
            if c1.button("💾 احفظ التعديل", key=f"dos_cfg_save{sx}"):
                ok, e2 = dossiers_mod.parse_config(new)
                if ok:
                    _dos_save_cfg(new, P)
                    st.session_state["dos_msg"] = "✅ اتحفظت الملفات."
                    st.rerun()
                else:
                    st.error(f"فيه غلطة في الكتابة: {e2}")
            if c2.button("↩️ رجّع الملفات الأصلية", key=f"dos_cfg_reset{sx}"):
                _dos_save_cfg((dossiers_mod.egypt_config_text() if egp else dossiers_mod.default_config_text()), P)
                st.session_state.pop(f"dos_cfg_edit{sx}", None)
                st.rerun()
        if err:
            st.error(f"تعريف الملفات فيه مشكلة: {err}")


SEARCH_CFG, SEARCH_STATUS = "marsad_search_cfg.json", "marsad_search_job.json"
SEARCH_SCOPES = {"il": "🇮🇱 المصادر الإسرائيلية", "us": "🇺🇸 المصادر الأمريكية", "uk": "🇬🇧 المصادر البريطانية",
                 "rg": "🌍 تركيا وإيران وإثيوبيا", "eg": "🇪🇬 الشأن المصري", "wr": "✍️ الكتّاب الأجانب", "wa": "🇸🇦 الكتّاب العرب"}
PERIOD_OPTS = {"آخر 6 ساعات": 0.25, "آخر 12 ساعة": 0.5, "آخر 24 ساعة": 1, "آخر يومين": 2, "آخر 3 أيام": 3, "آخر 5 أيام": 5, "آخر 7 أيام": 7, "آخر 14 يوماً": 14, "آخر 30 يوماً": 30}


def _period_label(d):
    if d is None:
        return ""
    d = float(d)
    if d < 1:
        return f"آخر {int(round(d * 24))} ساعة"
    return "آخر 24 ساعة" if d == 1 else f"آخر {int(d)} يوم"


def _sa_load(force=False):
    ss = st.session_state
    if force or "sa_cfg" not in ss:
        try:
            ss["sa_cfg"] = store.load_file(GH_TOKEN, GH_GIST, SEARCH_CFG, {}) or {}
            ss["sa_status"] = store.load_file(GH_TOKEN, GH_GIST, SEARCH_STATUS, {}) or {}
        except Exception:
            ss.setdefault("sa_cfg", {})
            ss.setdefault("sa_status", {})
    return ss["sa_cfg"], ss["sa_status"]


def render_search_all():
    """زر واحد: بحث في كل المصادر على GitHub، والنتيجة تظهر في تاباتها وتدخل في الربط وتفضل لحد ما تبحث تاني"""
    with st.expander("🚀 بحث شامل في كل المصادر مرة واحدة (بيشتغل على GitHub)", expanded=False):
        if not (GH_TOKEN and GH_GIST):
            st.info("محتاج التخزين الدائم (GITHUB_TOKEN وGIST_ID).")
            return
        ss = st.session_state
        cfg, stt = _sa_load()
        tok, repo, branch = _sec("ACTIONS_TOKEN"), _sec("GH_REPO") or gh_actions.DEFAULT_REPO, _sec("GH_BRANCH") or "main"
        st.caption("اكتب كلماتك مرة واحدة ودوس الزرار، وسيب GitHub يدور في **كل** المصادر (إسرائيلية وأمريكية وبريطانية وتركيا وإيران وإثيوبيا والكتّاب) "
                   "بنفس طريقة بحث كل تاب. لما يخلص، كل تاب هتلاقي فيه نتيجته زي ما هي، وكلها بتدخل في الربط، وبتفضل محفوظة لحد ما تدوس بحث جديد. "
                   "مش لازم تفضل فاتح التطبيق.")
        terms_txt = st.text_area("كلمات البحث (كلمة أو أكتر، افصل بفاصلة أو سطر جديد). سيبها فاضية لو عايز كل ما نُشر من غير كلمات",
                                 value=cfg.get("terms", ""), height=90, key="sa_terms", placeholder="مثال: سد النهضة، إثيوبيا، الدعم السريع")
        c1, c2 = st.columns(2)
        plabels = list(PERIOD_OPTS)
        cur_p = next((k for k, v in PERIOD_OPTS.items() if v == cfg.get("days")), "آخر 3 أيام")
        period = c1.selectbox("الفترة", plabels, index=plabels.index(cur_p), key="sa_period")
        joiner_lbl = c2.radio("لو كتبت أكتر من كلمة", ["أي كلمة منهم (OR)", "كل الكلمات مع بعض (AND)"], index=0 if cfg.get("joiner", "OR") == "OR" else 1,
                              key="sa_join")
        st.caption("💡 اقتراح: لو بتتابع حدث ساخن النهاردة اختار 12 أو 24 ساعة. للقصة الشغالة اختار 3 أيام. للصورة الأوسع 7 أيام. كل ما كبّرت الفترة، البحث بياخد وقت أطول.")
        keys_sel = st.multiselect("ادور في إيه؟", list(SEARCH_SCOPES), default=[k for k in (cfg.get("scopes") or list(SEARCH_SCOPES)) if k in SEARCH_SCOPES],
                                  format_func=lambda k: SEARCH_SCOPES[k], key="sa_scopes")
        use_body = st.checkbox("🔬 ابحث كمان جوه نص المقالات (أبطأ بكتير بس بيلقط اللي كلمتك في وسطه)", value=bool(cfg.get("use_body")), key="sa_body")
        lr = None
        if tok:
            t0, v0 = ss.get("sa_lr", (0, None))
            if time.time() - t0 > 45:
                try:
                    v0 = gh_actions.last_run(tok, repo, "search.yml")
                except Exception as ex:
                    v0 = None
                    st.caption(f"تعذّر قراءة حالة التشغيل ({type(ex).__name__}). اتأكد إنك رفعت ملف search.yml.")
                ss["sa_lr"] = (time.time(), v0)
            lr = v0
        else:
            st.warning("زرار التشغيل محتاج ACTIONS_TOKEN في Secrets (نفس اللي عملناه للتقرير اليومي).")
        busy = bool(lr and lr["status"] in ("queued", "in_progress", "waiting", "requested"))
        if lr:
            ico = {"success": "✅ خلص", "failure": "❌ فشل", "cancelled": "⚪ اتلغى"}.get(lr["conclusion"] or "", "⏳ شغال دلوقتي" if busy else "—")
            when = keys_mod.parse(lr["created"])
            wt = when.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if when else ""
            st.markdown(f"آخر تشغيل: **{ico}** — بدأ {wt} (القاهرة) · [افتح التفاصيل على GitHub]({lr['url']})")
        if stt.get("done") is not None:
            parts = [f"{SEARCH_SCOPES.get(k, k).split(' ', 1)[-1]}: {n}" for k, n in (stt.get("counts") or {}).items()]
            fin = keys_mod.parse(stt.get("finished") or stt.get("updated"))
            ft = fin.astimezone(core.TZ).strftime("%Y-%m-%d %H:%M") if fin else ""
            state = "✅ خلص" if stt.get("state") == "done" else "⏳ شغال (خلّص " + str(len(stt.get("done") or [])) + " قسم)"
            st.markdown(f"آخر بحث شامل: **{state}** · {ft} (القاهرة) · الكلمات: {'، '.join(stt.get('terms') or []) or 'من غير كلمات (كل ما نُشر)'} · {_period_label(stt.get('days'))}"
                        + (f"  \nعدد النتايج: {' · '.join(parts)}" if parts else ""))
            for k, e in (stt.get("errors") or {}).items():
                st.warning(f"{SEARCH_SCOPES.get(k, k)}: فشل ({e[:120]})")
        if ss.get("sa_msg"):
            st.success(ss["sa_msg"])
        b1, b2 = st.columns(2)
        if b1.button("▶️ ابحث في كل المصادر دلوقتي", type="primary", disabled=busy or not tok, key="sa_go", use_container_width=True):
            if not keys_sel:
                st.warning("اختار قسم واحد على الأقل.")
            else:
                new_cfg = {"terms": terms_txt, "days": PERIOD_OPTS[period], "joiner": "OR" if joiner_lbl.startswith("أي") else "AND",
                           "scopes": keys_sel, "use_body": use_body}
                try:
                    store.save_file(GH_TOKEN, GH_GIST, SEARCH_CFG, new_cfg)
                    ss["sa_cfg"] = new_cfg
                    ok, msg = dispatch_tracked("search.yml", "البحث الشامل", gh_actions.dispatch, tok, repo, branch, "search.yml")
                    if ok:
                        time.sleep(4)
                        ss.pop("sa_lr", None)
                        ss["sa_msg"] = f"✅ اتبعت الأمر لـ GitHub الساعة {datetime.now(core.TZ).strftime('%H:%M')}. " + msg + " ولما يخلص دوس «حدّث وحمّل النتايج»."
                        st.rerun()
                    st.error(msg)
                except Exception as ex:
                    st.error(f"مقدرتش أبدأ ({type(ex).__name__}).")
        if b2.button("🔄 حدّث وحمّل النتايج في التابات", key="sa_refresh", use_container_width=True):
            ss.pop("sa_msg", None)
            ss.pop("sa_lr", None)
            _sa_load(force=True)
            try:
                n = reload_results()
                ss["sa_msg"] = f"✅ اتحمّل {n} قسم من آخر نتايج محفوظة. افتح أي تاب هتلاقي نتيجته، ودوس «اربط» تحت عشان تدخل في الخيوط."
            except Exception as ex:
                ss["sa_msg"] = f"تعذّر تحميل النتايج ({type(ex).__name__})."
            st.rerun()


@_fragment
def render_custom_collections(P="pol"):
    """إنشاء ملفات بحث يدوية وخيوط قصص يختار المستخدم عناصرها بنفسه."""
    st.markdown("### ✍️ ملفاتك وخيوطك الخاصة")
    st.caption("الملف موضوع ثابت له كلمات متابعة، أما الخيط فهو مجموعة أخبار تختارها أنت يدوياً حتى لو لم يلتقطها الربط الآلي.")
    left, right = st.columns(2)
    with left:
        with st.expander("➕ إنشاء ملف متابعة جديد", expanded=False):
            with st.form(f"custom_dossier_form_{P}"):
                nm = st.text_input("اسم الملف", placeholder="مثال: المفاوضات المصرية حول غزة")
                words = st.text_area("كلمات وأسماء وأطراف الملف، افصل بينها بفاصلة", placeholder="مصر، غزة، رفح، المفاوضات")
                desc = st.text_area("وصف الملف / سؤال البحث (اختياري)", height=70)
                if st.form_submit_button("إنشاء الملف", use_container_width=True):
                    terms = [x.strip() for x in re.split(r"[,،\n]+", words) if x.strip()]
                    if not nm.strip() or not terms:
                        st.error("اكتب اسم الملف وكلمة متابعة واحدة على الأقل.")
                    else:
                        try:
                            cfg = dossiers_mod.add_dossier(_dos_cfg_text(P), nm.strip(), terms, "ملف")
                            _dos_save_cfg(cfg, P)
                            rec = analysis_lab_mod.new_record(nm, desc, terms, "ملف")
                            S().setdefault("custom_dossiers", []).append({**rec, "scope": P})
                            persist()
                            st.success("اتعمل الملف واتضاف لمحرك الربط. اضغط «اربط» لتجميع الأخبار الموجودة.")
                        except Exception as e:
                            st.error(f"تعذر إنشاء الملف: {type(e).__name__}: {e}")
    with right:
        pool = list(_pool_for(P))
        by_url = {a.get("url"): a for a in pool if a.get("url")}
        labels = {f"{(a.get('title_ar') or a.get('title') or '')[:105]} · {a.get('domain','')} · {str(a.get('seendate',''))[:8]}": u for u, a in by_url.items()}
        with st.expander("🧵 إنشاء خيط يدوي من أخبار تختارها", expanded=False):
            with st.form(f"custom_thread_form_{P}"):
                tname = st.text_input("اسم الخيط", placeholder="مثال: تحركات واشنطن قبل القمة")
                chosen = st.multiselect("اختار الأخبار التي تنتمي للخيط", list(labels))
                tdesc = st.text_area("ما الرابط أو الفرضية التي تريد اختبارها؟", height=70)
                if st.form_submit_button("إنشاء الخيط", use_container_width=True):
                    urls = [labels[x] for x in chosen]
                    if not tname.strip() or len(urls) < 2:
                        st.error("اكتب اسم الخيط واختر خبرين على الأقل.")
                    else:
                        rec = analysis_lab_mod.new_record(tname, tdesc, [], "خيط", urls)
                        rec["scope"] = P
                        S().setdefault("custom_threads", []).insert(0, rec)
                        persist()
                        st.success(f"اتحفظ الخيط وفيه {len(urls)} خبر.")
    custom_files = [x for x in S().get("custom_dossiers", []) if x.get("scope", "pol") == P]
    custom_threads = [x for x in S().get("custom_threads", []) if x.get("scope", "pol") == P]
    if custom_files or custom_threads:
        with st.expander(f"📚 مجموعاتك الخاصة ({len(custom_files)} ملف · {len(custom_threads)} خيط)", expanded=False):
            for typ, records in (("ملف", custom_files), ("خيط", custom_threads)):
                if records:
                    st.markdown(f"**{typ}**")
                    for rec in records:
                        c1, c2 = st.columns([6, 1])
                        c1.markdown(f"**{rec.get('name')}** · {len(rec.get('tags', [])) if typ == 'ملف' else len(rec.get('articles', []))} {'كلمة' if typ == 'ملف' else 'خبر'}")
                        if rec.get("description"):
                            c1.caption(rec["description"])
                        if c2.button("حذف", key=f"del_custom_{typ}_{rec['id']}_{P}"):
                            key = "custom_dossiers" if typ == "ملف" else "custom_threads"
                            S()[key] = [x for x in S().get(key, []) if x.get("id") != rec.get("id")]
                            persist()
                            st.rerun()
                        if typ == "خيط":
                            _thread_articles = [by_url[u] for u in rec.get("articles", []) if u in by_url]
                            if _thread_articles and st.button("🧠 جهّز تحليل الخيط", key=f"analyse_thread_{rec['id']}"):
                                _prompt = analysis_lab_mod.make_prompt("تحليل ملف مقالات متراكم", _thread_articles,
                                    case_name=rec.get("name", "خيط يدوي"), author_profile="راجع بطاقات الكُتّاب المحفوظة، ولا تفترض ميولاً غير موثقة.",
                                    custom_outlets=S().get("outlet_profiles", {}),
                                    custom_writers=S().get("writer_profiles", {}))
                                st.session_state["analysis_lab_prompt"] = _prompt
                                st.session_state["analysis_lab_articles"] = _thread_articles
                                st.success("البرومبت جاهز في تبويب ورشة التحليل.")


def render_analysis_lab():
    """ورشة تحليل مقال منفرد أو مجموعة مقالات، مع توصيف المنبر والكاتب وبرومبتات مقارنة."""
    st.markdown("### 🧠 ورشة تحليل المقالات والرأي")
    st.caption("حلّل مقالاً منفرداً، أو قارن مقالات رأي، أو اجمع سلسلة مقالات داخل ملف واحد. البرومبتات تفصل بين الوقائع والرأي والاستنتاج، ولا تفترض توجه الكاتب من اسم الصحيفة.")
    pool = list(_dos_pool().values())
    saved = list(S().get("saved", []))
    combined = []
    seen = set()
    for a in saved + pool:
        u = a.get("url")
        if u and u not in seen:
            seen.add(u)
            combined.append(a)
    labels = {}
    for i, a in enumerate(combined):
        label = f"{(a.get('title_ar') or a.get('title') or 'بدون عنوان')[:115]} · {a.get('domain') or a.get('outlet') or ''} · {str(a.get('seendate') or '')[:8]} · {i+1}"
        labels[label] = a
    with st.expander("🏛️ توصيف الصحف والمنصات", expanded=False):
        domain = st.text_input("دومين المنبر", placeholder="مثال: nytimes.com", key="lab_domain")
        current = analysis_lab_mod.outlet_profile(domain, S().get("outlet_profiles", {})) if domain else {}
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم المنبر", value=current.get("name", ""), key="lab_out_name")
        country = c2.text_input("الدولة", value=current.get("country", ""), key="lab_out_country")
        ownership = c1.text_input("الملكية / التمويل المعلن", value=current.get("ownership", ""), key="lab_out_ownership")
        orientation = c2.text_input("التوجه التحريري التقريبي", value=current.get("orientation", ""), key="lab_out_orientation")
        outlet_type = st.text_input("نوع المنبر", value=current.get("type", ""), key="lab_out_type")
        caveat = st.text_area("ملاحظات وحدود التوصيف", value=current.get("caveat", ""), key="lab_out_caveat", height=65)
        if st.button("حفظ بطاقة المنبر", key="lab_save_outlet"):
            if domain.strip():
                S().setdefault("outlet_profiles", {})[domain.strip().lower().replace("www.", "")] = {
                    "name": name, "country": country, "ownership": ownership, "orientation": orientation,
                    "type": outlet_type, "caveat": caveat, "confidence": "إدخال المستخدم / يحتاج توثيق"}
                persist()
                st.success("تم حفظ بطاقة المنبر.")
            else:
                st.warning("اكتب الدومين أولاً.")
    with st.expander("✍️ بطاقات الكُتّاب والمحللين", expanded=False):
        allw = current_writers()
        writer_labels = {f"{w.get('name_ar')} · {w.get('outlet')} · {w.get('kind')}": w for w in allw}
        picked_writer = st.selectbox("اختار كاتباً", ["إضافة بطاقة يدوية"] + list(writer_labels), key="lab_writer_pick")
        base_w = writer_labels.get(picked_writer, {})
        wid = base_w.get("id") or st.text_input("معرّف الكاتب", key="lab_writer_id")
        wname = st.text_input("اسم الكاتب", value=base_w.get("name_ar", ""), key="lab_writer_name")
        woutlet = st.text_input("المنبر المعتاد", value=base_w.get("outlet", ""), key="lab_writer_outlet")
        wbio = st.text_area("سيرة مهنية ومجالات تخصص ومواقف موثقة (مع روابط إن أمكن)",
                            value=S().get("writer_profiles", {}).get(wid, ""), height=100, key="lab_writer_bio")
        if st.button("حفظ بطاقة الكاتب", key="lab_save_writer"):
            if wid and wname:
                S().setdefault("writer_profiles", {})[wid] = {"name": wname, "outlet": woutlet, "profile": wbio}
                persist()
                st.success("تم حفظ بطاقة الكاتب. لن تُعرض الميول كحقيقة إلا إذا دعمتها مصادر موثقة.")
            else:
                st.warning("حدد كاتباً أو اكتب معرّفاً واسماً.")
    st.divider()
    with st.form("analysis_lab_form"):
        kind = st.selectbox("نوع التحليل", ["تحليل مقال واحد", "مقارنة مقالات رأي", "تحليل ملف مقالات متراكم", "تحليل التناقضات بين المصادر", "ملف صحفي عن كاتب أو صحيفة"])
        case_name = st.text_input("اسم الملف / القضية", placeholder="مثال: اتجاهات الصحافة الأمريكية تجاه إيران")
        chosen_labels = st.multiselect("اختار مقالات من أرشيف البحث والمحفوظات", list(labels))
        title = st.text_input("عنوان مقال إضافي (اختياري)")
        article_url = st.text_input("رابط المقال الإضافي")
        article_author = st.text_input("اسم الكاتب")
        article_outlet = st.text_input("اسم الصحيفة / المنبر")
        article_date = st.text_input("تاريخ النشر")
        article_domain = st.text_input("دومين المنبر (اختياري)")
        article_text = st.text_area("الصق نص المقال أو مقتطفاً كبيراً هنا (مهم للتحليل الدقيق)", height=220)
        author_profile = st.text_area("ملاحظات عن الكاتب (اختياري، مع مصادرها)", height=75)
        save_case = st.checkbox("احفظ هذه المجموعة كملف تحليلي للرجوع إليها", value=True)
        submitted = st.form_submit_button("🧠 جهّز برومبت التحليل", type="primary", use_container_width=True)
    if submitted:
        articles = [dict(labels[x]) for x in chosen_labels]
        if title.strip() or article_text.strip() or article_url.strip():
            articles.insert(0, {"title": title, "title_ar": title, "url": article_url, "writer": article_author,
                                "outlet": article_outlet, "date": article_date, "domain": article_domain,
                                "text": article_text, "summary": article_text[:1200]})
        if not articles:
            st.warning("اختار مقالاً من الأرشيف أو أضف مقالاً يدوياً.")
        elif kind == "تحليل مقال واحد" and len(articles) > 1:
            articles = articles[:1]
            st.info("نوع التحليل مقال واحد، لذلك استخدمت أول مقال فقط.")
        if articles:
            custom_profiles = S().get("outlet_profiles", {})
            inferred_author = article_author or (articles[0].get("writer") if articles else "") or "غير محدد"
            inferred_profile = author_profile
            if not inferred_profile and inferred_author:
                for _wid, _wp in S().get("writer_profiles", {}).items():
                    if _wp.get("name") == inferred_author or _wid == inferred_author:
                        inferred_profile = _wp.get("profile", "")
                        break
            prompt = analysis_lab_mod.make_prompt(kind, articles, case_name or "ملف بحثي", author=inferred_author,
                outlet=article_outlet or (articles[0].get("outlet") if articles else "") or "غير محدد",
                author_profile=inferred_profile, custom_outlets=custom_profiles, custom_writers=S().get("writer_profiles", {}))
            st.session_state["analysis_lab_prompt"] = prompt
            st.session_state["analysis_lab_articles"] = articles
            if save_case:
                rec = analysis_lab_mod.new_record(case_name or (articles[0].get("title") or "مجموعة تحليل"),
                    f"{kind} · {len(articles)} مادة", [], "تحليل", [a.get("url") for a in articles if a.get("url")])
                rec.update({"prompt": prompt, "analysis_type": kind, "articles": articles})
                S().setdefault("analysis_cases", []).insert(0, rec)
                persist()
                st.success("اتحفظ الملف التحليلي في ورشة التحليل.")
    if st.session_state.get("analysis_lab_prompt"):
        st.markdown("#### البرومبت الجاهز")
        st.caption("انسخه إلى نموذج الذكاء الاصطناعي. لو المقال خلف اشتراك أو الأرشيف لا يحتوي نصه الكامل، الصق النص بنفسك قبل طلب تحليل تفصيلي.")
        st.code(st.session_state["analysis_lab_prompt"], language=None)
    cases = S().get("analysis_cases", [])
    if cases:
        with st.expander(f"📚 ملفات التحليل المحفوظة ({len(cases)})", expanded=False):
            for rec in cases[:30]:
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.markdown(f"**{rec.get('name')}** · {rec.get('analysis_type','')} · {len(rec.get('articles', []))} مادة")
                if c2.button("فتح", key=f"lab_open_{rec['id']}"):
                    st.session_state["analysis_lab_prompt"] = rec.get("prompt", "")
                    st.rerun()
                if c3.button("حذف", key=f"lab_del_{rec['id']}"):
                    S()["analysis_cases"] = [x for x in cases if x.get("id") != rec.get("id")]
                    persist()
                    st.rerun()


    st.divider()
    render_research_casebook()


def render_research_casebook():
    """مركز ملف القضية: مواد متعددة، سجل ادعاءات، خط زمني، وموجّه بحثي موحد."""
    st.markdown("### 🗃️ مركز الملفات البحثية")
    st.caption("اجمع داخل ملف واحد الأخبار والتصريحات ومقالات الرأي والوثائق، ثم ابنِ خطاً زمنياً وسجل ادعاءات وخريطة خلاف قابلة للتحليل.")
    cases = S().setdefault("research_cases", [])
    S().setdefault("case_links", [])

    with st.expander("➕ إنشاء ملف بحثي جديد", expanded=not bool(cases)):
        with st.form("research_case_create_form"):
            c_title = st.text_input("عنوان القضية", placeholder="مثال: مسارات التفاوض الأمريكي الإيراني")
            c_desc = st.text_area("نطاق الملف والسؤال البحثي", placeholder="ما القضية؟ وما الأسئلة التي تريد الإجابة عنها؟", height=85)
            c_tags = st.text_input("وسوم مفصولة بفواصل", placeholder="إيران، الولايات المتحدة، مفاوضات")
            create_case = st.form_submit_button("إنشاء الملف البحثي", type="primary")
        if create_case:
            if not c_title.strip():
                st.warning("اكتب عنواناً للملف أولاً.")
            else:
                rec = casebook_mod.new_case(c_title, c_desc, [x.strip() for x in re.split(r"[,،]", c_tags) if x.strip()])
                cases.insert(0, rec)
                st.session_state["research_case_active"] = rec["id"]
                persist()
                st.success("تم إنشاء الملف البحثي.")
                st.rerun()

    if len(cases) >= 2:
        render_case_relationship_center(cases)

    if not cases:
        st.info("أنشئ أول ملف بحثي لتبدأ تجميع المواد وبناء سجل الأدلة.")
        return

    case_labels = {f"{x.get('title','ملف بلا عنوان')} · {len(x.get('materials', []))} مادة · {str(x.get('updated_at',''))[:10]}": x for x in cases}
    active_id = st.session_state.get("research_case_active")
    default_label = next((k for k, v in case_labels.items() if v.get("id") == active_id), next(iter(case_labels)))
    picked_label = st.selectbox("الملف النشط", list(case_labels), index=list(case_labels).index(default_label), key="research_case_select")
    case = case_labels[picked_label]
    st.session_state["research_case_active"] = case["id"]

    # تحديث وصف الملف والوسوم
    with st.expander("⚙️ إعدادات الملف", expanded=False):
        with st.form(f"research_case_meta_{case['id']}"):
            new_title = st.text_input("اسم الملف", value=case.get("title", ""))
            new_desc = st.text_area("وصف القضية", value=case.get("description", ""), height=75)
            new_tags = st.text_input("الوسوم", value="، ".join(case.get("tags", [])))
            new_notes = st.text_area("ملاحظات الباحث / أسئلة مفتوحة", value=case.get("research_notes", ""), height=90)
            save_meta = st.form_submit_button("حفظ بيانات الملف")
        if save_meta:
            case.update({"title": new_title.strip(), "description": new_desc.strip(),
                         "tags": [x.strip() for x in re.split(r"[,،]", new_tags) if x.strip()],
                         "research_notes": new_notes.strip(), "updated_at": casebook_mod.now_iso()})
            persist(); st.success("تم تحديث الملف."); st.rerun()

    materials = case.get("materials", [])
    claims = case.get("claims", [])
    events = case.get("events", [])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("المواد", len(materials))
    m2.metric("الادعاءات", len(claims))
    m3.metric("الأحداث", len(events))
    m4.metric("المصادر", len({x.get('domain') or x.get('outlet') for x in materials if x.get('domain') or x.get('outlet')}))

    st.markdown("#### ⚡ استيراد نتائج البحث تلقائياً إلى ملف القضية")
    st.caption("اختر مجموعة نتائج محفوظة من جلسة البحث الحالية. سيُضاف الجديد فقط، مع الاحتفاظ بالرابط والمصدر والتاريخ، ويمكن تجهيز دفعات بحث منها دون استدعاء أي نموذج مدفوع.")
    recent_result_sets = {}
    for state_key, state_value in list(st.session_state.items()):
        if str(state_key).startswith("res_") and isinstance(state_value, dict) and isinstance(state_value.get("items"), list) and state_value.get("items"):
            result_label = f"{str(state_key)[4:]} · {len(state_value['items'])} نتيجة"
            recent_result_sets[result_label] = state_value
    if recent_result_sets:
        chosen_result_label = st.selectbox("مجموعة نتائج البحث", list(recent_result_sets), key=f"case_intake_results_{case['id']}")
        selected_result_data = recent_result_sets[chosen_result_label]
        selected_result_items = selected_result_data.get("items", [])
        st.caption(f"المتاح للاستيراد: {len(selected_result_items)} نتيجة. التجميع لا يعني التحقق من صحة الأخبار أو اكتمال المقالات.")
        intake_col1, intake_col2 = st.columns([1, 1])
        intake_type = intake_col1.selectbox("تصنيف المواد المستوردة", casebook_mod.MATERIAL_TYPES, key=f"case_intake_type_{case['id']}")
        intake_limit = intake_col2.selectbox("الحد الأقصى للاستيراد", [25, 50, 100, 200, 300], index=2, key=f"case_intake_limit_{case['id']}")
        if st.button("📥 استيراد النتائج وإنشاء دفعات البحث", type="primary", key=f"case_intake_run_{case['id']}", use_container_width=True):
            try:
                intake_result = case_intake_mod.import_search_results(case, selected_result_items, material_type=intake_type, max_items=intake_limit)
                new_materials = intake_result["added"]
                created_batch = case_intake_mod.batch_from_materials(case, new_materials, batch_size=8) if new_materials else None
                if created_batch:
                    S().setdefault("research_batches", []).insert(0, created_batch)
                    S()["research_batches"] = S()["research_batches"][:30]
                if new_materials:
                    persist()
                st.success(f"تمت إضافة {len(new_materials)} مادة جديدة، وتجاوز {intake_result['skipped']} مكررة." + (f" وتم تجهيز {len(created_batch['chunks'])} دفعة بحث." if created_batch else " لا توجد مواد جديدة لتقسيمها."))
                st.rerun()
            except Exception as exc:
                st.error(f"تعذر استيراد النتائج: {type(exc).__name__}: {exc}")
    else:
        st.info("نفّذ بحثاً أولاً، وستظهر مجموعات النتائج هنا لاستيرادها مباشرة إلى ملف القضية.")

    st.markdown("#### 📥 إضافة مواد إلى الملف")
    pool = list(_dos_pool().values())
    pool += list(S().get("saved", []))
    # إزالة التكرار بحسب الرابط
    unique_pool, seen_urls = [], set()
    for a in pool:
        u = a.get("url") or a.get("link")
        if u and u not in seen_urls:
            seen_urls.add(u); unique_pool.append(a)
    labels = {}
    for i, a in enumerate(unique_pool):
        title = a.get("title_ar") or a.get("title") or "بدون عنوان"
        outlet = a.get("outlet") or a.get("source") or a.get("domain") or "مصدر غير محدد"
        labels[f"{str(title)[:105]} · {outlet} · {str(a.get('date') or a.get('seendate') or '')[:10]} · {i+1}"] = a
    with st.form(f"research_add_existing_{case['id']}"):
        chosen = st.multiselect("اختر من نتائج البحث والمحفوظات", list(labels), help="يمكنك ضم عدة مواد دفعة واحدة.")
        material_type = st.selectbox("نوع المواد المختارة", casebook_mod.MATERIAL_TYPES)
        stance = st.text_input("زاوية / موقف مبدئي (اختياري)", placeholder="مثال: يدعم استمرار التفاوض، يعارض الاتفاق...")
        add_selected = st.form_submit_button("إضافة المواد المختارة")
    if add_selected:
        added = 0
        for label in chosen:
            added += bool(casebook_mod.add_material(case, labels[label], material_type, stance))
        persist()
        st.success(f"تمت إضافة {added} مادة جديدة. المواد المكررة تم تجاوزها.")
        st.rerun()

    with st.expander("إضافة مادة يدوياً: تصريح أو مقال أو وثيقة", expanded=False):
        with st.form(f"research_manual_material_{case['id']}"):
            mm_title = st.text_input("العنوان أو نص التصريح المختصر")
            mm_type = st.selectbox("نوع المادة", casebook_mod.MATERIAL_TYPES, key=f"manual_type_{case['id']}")
            mm_author = st.text_input("الكاتب / المتحدث / الجهة")
            mm_outlet = st.text_input("الصحيفة / المؤسسة / المصدر")
            mm_date = st.text_input("تاريخ النشر أو التصريح", placeholder="2026-11-22")
            mm_url = st.text_input("الرابط الأصلي")
            mm_text = st.text_area("النص أو المقتطف المتاح", height=140)
            mm_stance = st.text_input("الموقف أو الزاوية (اختياري)")
            mm_actor = st.text_input("الطرف / المتحدث صاحب الموقف (مهم لمقارنة التحولات)", placeholder="مثال: وزارة الخارجية الإيرانية")
            mm_position = st.text_input("الموقف المحدد المنسوب للطرف (اختياري)", placeholder="مثال: يرفض وقف التخصيب")
            mm_save = st.form_submit_button("إضافة المادة إلى الملف")
        if mm_save:
            manual = {"title": mm_title, "title_ar": mm_title, "writer": mm_author, "outlet": mm_outlet,
                      "date": mm_date, "url": mm_url, "domain": casebook_mod.domain(mm_url), "text": mm_text,
                      "speaker": mm_actor, "actor": mm_actor, "position": mm_position}
            if not (mm_title.strip() or mm_text.strip() or mm_url.strip()):
                st.warning("أدخل عنواناً أو نصاً أو رابطاً للمادة.")
            else:
                casebook_mod.add_material(case, manual, mm_type, mm_stance)
                persist(); st.success("تمت إضافة المادة."); st.rerun()

    st.markdown("#### ⚖️ مختبر مقارنة الروايات ومصفوفة الأدلة")
    st.caption("يقارن المواد المحفوظة في هذا الملف، ويعرض نقاط التقارب والاختلاف المرشحة. لا يقرر آلياً أي رواية صحيحة.")
    if len(materials) < 2:
        st.info("أضف مادتين على الأقل، ويفضل أن يتوفر نص أو مقتطف لكل مادة، لبدء المقارنة.")
    else:
        if st.button("⚖️ بناء خريطة الروايات ومقارنة المصادر", key=f"narrative_compare_{case['id']}", type="primary"):
            try:
                report = narrative_analysis_mod.compare_narratives(materials, claims)
                st.session_state[f"narrative_report_{case['id']}"] = report
                st.success("تم بناء خريطة المقارنة من المواد المحفوظة. راجع المرشحات قبل اعتماد أي استنتاج.")
            except Exception as exc:
                st.error(f"تعذرت المقارنة: {type(exc).__name__}: {exc}")
        narrative_report = st.session_state.get(f"narrative_report_{case['id']}")
        if narrative_report:
            n1, n2, n3 = st.columns(3)
            n1.metric("المصادر/مجموعات النطاق", narrative_report.get("source_count", 0))
            n2.metric("النطاقات المختلفة", narrative_report.get("distinct_domains", 0))
            n3.metric("مرشحات المقارنة", len(narrative_report.get("comparison_candidates", [])))
            st.caption(f"مواد الملف: {narrative_report.get('material_count', 0)} · مواد لها نص قابل للمقارنة: {narrative_report.get('usable_text_count', 0)}")
            with st.expander("🗞️ خريطة المصادر", expanded=False):
                for src in narrative_report.get("sources", []):
                    st.markdown(f"**{src.get('source')}** · {src.get('domain') or 'النطاق غير متاح'} · {len(src.get('items', []))} مادة")
                    st.caption(src.get("independence_note", ""))
            candidates = narrative_report.get("comparison_candidates", [])
            if not candidates:
                st.info("لم تظهر مرشحات مقارنة نصية كافية. هذا لا يثبت اتفاق المصادر أو غياب الاختلافات.")
            for idx, item in enumerate(candidates[:40], 1):
                with st.expander(f"{idx}. {item.get('kind')} · تشابه مفردات {item.get('overlap', 0):.0%} · {item.get('source_a')} / {item.get('source_b')}", expanded=False):
                    st.markdown(f"**المادة الأولى:** {item.get('title_a')} · {item.get('date_a')}  \n{item.get('text_a','')[:1000]}")
                    if item.get("url_a"): st.markdown(f"[فتح المصدر الأول]({item['url_a']})")
                    st.markdown(f"**المادة الثانية:** {item.get('title_b')} · {item.get('date_b')}  \n{item.get('text_b','')[:1000]}")
                    if item.get("url_b"): st.markdown(f"[فتح المصدر الثاني]({item['url_b']})")
                    st.caption(f"مؤشر لغوي: {item.get('polarity_a')} مقابل {item.get('polarity_b')} · مفردات مشتركة: {', '.join(item.get('shared_terms', []))}")
                    st.warning(item.get("caveat", "مرشح يحتاج مراجعة بشرية."))
                    for question in item.get("review_questions", []): st.write("• " + question)
            for limitation in narrative_report.get("limitations", []): st.caption("حدود التحليل: " + limitation)
            comparison_prompt = narrative_analysis_mod.build_comparison_prompt(case, narrative_report)
            dl1, dl2 = st.columns(2)
            dl1.download_button("⬇️ تنزيل تقرير المقارنة JSON", json.dumps(narrative_report, ensure_ascii=False, indent=2), file_name=f"narrative_comparison_{case['id']}.json", mime="application/json", key=f"narrative_json_{case['id']}")
            dl2.download_button("⬇️ تنزيل برومبت التحليل", comparison_prompt, file_name=f"narrative_analysis_{case['id']}.txt", key=f"narrative_prompt_{case['id']}")

    st.markdown("#### 🧾 سجل الادعاءات والأدلة")
    st.caption("سجّل ما تريد اختباره، وحدد هل هو واقعة أم ادعاء منسوب أم تفسير أو توقع، ثم دوّن حالة الدليل. هذا السجل لا يتحقق آلياً من صحة الادعاء.")
    with st.form(f"research_claim_form_{case['id']}"):
        claim_text = st.text_area("الادعاء / المعلومة المراد فحصها", height=75)
        cc1, cc2 = st.columns(2)
        claim_type = cc1.selectbox("طبيعة العبارة", casebook_mod.CLAIM_TYPES)
        claim_status = cc2.selectbox("حالة الدليل الحالية", casebook_mod.EVIDENCE_STATUSES)
        claim_source = st.text_input("رابط المصدر أو الوثيقة")
        claim_note = st.text_input("ملاحظات / ما المطلوب للتحقق؟")
        add_claim_btn = st.form_submit_button("إضافة إلى سجل الادعاءات")
    if add_claim_btn:
        try:
            casebook_mod.add_claim(case, claim_text, claim_type, claim_status, claim_source, claim_note)
            persist(); st.success("تم تسجيل الادعاء."); st.rerun()
        except ValueError as exc:
            st.warning(str(exc))

    st.markdown("#### 🕒 الخط الزمني للقضية")
    with st.form(f"research_event_form_{case['id']}"):
        ec1, ec2 = st.columns([1, 3])
        event_date = ec1.text_input("تاريخ الحدث", placeholder="2026-11-22")
        event_title = ec2.text_input("عنوان الحدث")
        event_detail = st.text_input("تفاصيل مختصرة")
        event_source = st.text_input("مصدر / رابط الحدث")
        add_event_btn = st.form_submit_button("إضافة حدث للخط الزمني")
    if add_event_btn:
        try:
            casebook_mod.add_event(case, event_date, event_title, event_detail, event_source)
            persist(); st.success("تمت إضافة الحدث."); st.rerun()
        except ValueError as exc:
            st.warning(str(exc))

    # عرض السجلات وإتاحة الحذف المنفصل
    if materials:
        with st.expander(f"📰 المواد المرفقة ({len(materials)})", expanded=True):
            for item in materials:
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{item.get('title')}**  \n{item.get('type')} · {item.get('author')} · {item.get('outlet')} · {item.get('date')}")
                if item.get("url"):
                    c1.markdown(f"[فتح المصدر الأصلي]({item['url']})")
                if item.get("text"):
                    c1.caption(item.get("text", "")[:350])
                if c2.button("حذف", key=f"rm_mat_{item['id']}"):
                    casebook_mod.remove_item(case, "materials", item["id"]); persist(); st.rerun()
    if claims:
        with st.expander(f"🔎 الادعاءات المسجلة ({len(claims)})", expanded=False):
            for item in claims:
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{item.get('statement')}**  \n{item.get('type')} · الحالة: **{item.get('status')}**")
                if item.get("source"):
                    c1.markdown(f"[رابط الدليل]({item['source']})")
                if item.get("note"):
                    c1.caption(item["note"])
                if c2.button("حذف", key=f"rm_claim_{item['id']}"):
                    casebook_mod.remove_item(case, "claims", item["id"]); persist(); st.rerun()
    if events:
        with st.expander(f"📅 أحداث الخط الزمني ({len(events)})", expanded=False):
            for item in sorted(events, key=lambda x: x.get("date") or "9999"):
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{item.get('date')} · {item.get('title')}**  \n{item.get('detail')}")
                if item.get("source"):
                    c1.markdown(f"[مصدر الحدث]({item['source']})")
                if c2.button("حذف", key=f"rm_event_{item['id']}"):
                    casebook_mod.remove_item(case, "events", item["id"]); persist(); st.rerun()

    # الملف الاستخباراتي التراكمي: لا يُحدّث إلا بطلب صريح من الباحث.
    st.divider()
    st.markdown("### 🧠 الملف الاستخباراتي التراكمي")
    st.caption("يسجل لقطات متتابعة للمواد والادعاءات والأحداث، ويرصد الإضافات والتعديلات وتغير حالة الدليل. لا يستدعي أي نموذج أو API مدفوع.")
    cumulative_files = S().setdefault("intel_case_files", [])
    cumulative_record = next((x for x in cumulative_files if x.get("case_id") == case.get("id")), None)
    cumulative_summary = case_intel_mod.summarize(cumulative_record or {})
    ci1, ci2, ci3, ci4 = st.columns(4)
    ci1.metric("لقطات محفوظة", cumulative_summary["snapshots"])
    ci2.metric("تغييرات مسجلة", cumulative_summary["changes"])
    ci3.metric("مواد متتبعة", cumulative_summary["materials_tracked"])
    ci4.metric("ادعاءات متتبعة", cumulative_summary["claims_tracked"])
    if st.button("🔄 تحديث الملف التراكمي الآن", type="primary", key=f"update_cumulative_case_{case['id']}", use_container_width=True):
        updated_record, update_result = case_intel_mod.update_case_file(
            cumulative_record, case, S().get("intel_dossiers", []))
        if cumulative_record is None:
            cumulative_files.insert(0, updated_record)
        else:
            cumulative_files[:] = [updated_record if x.get("case_id") == case.get("id") else x for x in cumulative_files]
        persist()
        if update_result["changed"]:
            st.success(f"تم حفظ لقطة جديدة وتسجيل {len(update_result['events'])} تغييراً.")
        else:
            st.info("لا توجد تغييرات جديدة منذ آخر لقطة. لم يتم إنشاء نسخة مكررة.")
        st.rerun()
    if cumulative_record:
        with st.expander("📜 سجل تطور القضية", expanded=True):
            for snap in reversed(cumulative_record.get("snapshots", [])[-10:]):
                st.markdown(f"**{snap.get('captured_at', '')}** · {snap.get('change_count', 0)} تغيير · `{snap.get('id', '')}`")
            recent_changes = list(reversed(cumulative_record.get("change_log", [])[-30:]))
            if recent_changes:
                st.markdown("**آخر التغييرات**")
                for change in recent_changes:
                    summary_text = change.get("summary") or change.get("after", {}).get("statement") or change.get("after", {}).get("title") or ""
                    st.markdown(f"- **{change.get('label', change.get('type'))}** · {change.get('at', '')} · {summary_text}")
                    if change.get("type") == "updated_claims":
                        before_status = change.get("before", {}).get("status", "غير محدد")
                        after_status = change.get("after", {}).get("status", "غير محدد")
                        st.caption(f"حالة الدليل: {before_status} ← {after_status}")
            else:
                st.info("تم حفظ لقطة تأسيسية. ستظهر التغييرات هنا بعد التحديثات التالية.")
        prompt_col, json_col = st.columns(2)
        if prompt_col.button("🧠 إنشاء برومبت التحديث التراكمي", key=f"cumulative_prompt_{case['id']}", use_container_width=True):
            st.session_state["cumulative_case_prompt"] = case_intel_mod.build_cumulative_prompt(case, cumulative_record)
            st.session_state["cumulative_case_prompt_case_id"] = case["id"]
        json_col.download_button("⬇️ تنزيل سجل القضية JSON",
            json.dumps(cumulative_record, ensure_ascii=False, indent=2),
            file_name=f"marsad-cumulative-case-{case['id']}.json", mime="application/json",
            key=f"download_cumulative_case_{case['id']}", use_container_width=True)
        if st.session_state.get("cumulative_case_prompt_case_id") == case.get("id"):
            st.text_area("برومبت التحديث التراكمي", value=st.session_state["cumulative_case_prompt"],
                         height=320, key=f"cumulative_case_prompt_display_{case['id']}")
            st.download_button("⬇️ تنزيل برومبت التحديث TXT", st.session_state["cumulative_case_prompt"],
                file_name=f"marsad-cumulative-update-{case['id']}.txt", mime="text/plain",
                key=f"download_cumulative_prompt_{case['id']}")
    else:
        st.info("احفظ أول لقطة تأسيسية الآن. بعد ذلك، كل تحديث سيقارن الملف الحالي باللقطة السابقة ويكشف ما استجد.")

    st.markdown("#### 🧠 بناء التقرير التحليلي الشامل")
    st.caption("ينتج برومبتاً مبنياً على محتويات الملف الفعلية: المواد، الادعاءات، والأحداث. انسخه إلى نموذج الذكاء الاصطناعي لتحليلها مع إظهار الفجوات وحدود الثقة.")
    if st.button("إنشاء برومبت الملف البحثي", type="primary", key=f"build_case_prompt_{case['id']}", use_container_width=True):
        st.session_state["research_case_prompt"] = casebook_mod.build_prompt(case)
        st.session_state["research_case_prompt_name"] = case.get("title", "research_case")
    if st.session_state.get("research_case_prompt"):
        st.text_area("البرومبت الناتج", value=st.session_state["research_case_prompt"], height=360, key="research_case_prompt_display")
        st.download_button("⬇️ تنزيل البرومبت TXT", data=st.session_state["research_case_prompt"],
                           file_name="marsad_research_prompt.txt", mime="text/plain", key="download_research_prompt")

    st.divider()
    st.markdown("#### 🧰 مكتبة البرومبتات وإصداراتها")
    st.caption("احفظ برومبتاتك الخاصة، عدّلها بإصدارات جديدة، وارجع لأي إصدار سابق من غير ما نخسر النسخ القديمة. المكتبة محفوظة مع بيانات المرصد في التخزين الدائم.")
    prompt_records = S().setdefault("prompt_library", [])
    if IS_ADMIN:
        with st.expander("➕ إنشاء برومبت جديد", expanded=False):
            with st.form(f"prompt_create_form_{case['id']}"):
                new_prompt_name = st.text_input("اسم البرومبت", placeholder="مثال: تحليل تحركات واشنطن في البحر الأحمر")
                new_prompt_category = st.selectbox("تصنيف البرومبت", prompt_workbench_mod.CATEGORIES)
                new_prompt_description = st.text_input("وصف مختصر", placeholder="متى تستخدم هذا البرومبت؟")
                new_prompt_body = st.text_area("نص البرومبت الكامل", height=220, placeholder="اكتب التعليمات التي تريد إرسالها للمحادثة...")
                create_prompt_clicked = st.form_submit_button("حفظ البرومبت في المكتبة", type="primary", use_container_width=True)
            if create_prompt_clicked:
                try:
                    prompt_workbench_mod.create_prompt(prompt_records, new_prompt_name, new_prompt_body,
                        new_prompt_category, new_prompt_description)
                    persist(); st.success("تم حفظ البرومبت كإصدار أول."); st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    active_prompt_records = prompt_workbench_mod.active_prompts(prompt_records)
    if active_prompt_records:
        prompt_record_labels = {f"{x.get('name')} · الإصدار {x.get('current_version', 1)}": x for x in active_prompt_records}
        selected_prompt_record_label = st.selectbox("استعراض برومبتاتك المحفوظة", list(prompt_record_labels), key=f"prompt_library_pick_{case['id']}")
        selected_prompt_record = prompt_record_labels[selected_prompt_record_label]
        selected_prompt_version = prompt_workbench_mod.current_version(selected_prompt_record) or {}
        st.caption(f"{selected_prompt_record.get('category', 'عام')} · {selected_prompt_record.get('description', '')} · {len(selected_prompt_record.get('versions', []))} إصدار محفوظ")
        st.download_button("⬇️ تنزيل البرومبت الحالي TXT", selected_prompt_version.get("body", ""),
            file_name=f"marsad_prompt_{selected_prompt_record.get('id')}_v{selected_prompt_version.get('version', 1)}.txt",
            mime="text/plain", key=f"prompt_download_{case['id']}_{selected_prompt_record['id']}")
        with st.expander("📜 سجل الإصدارات", expanded=False):
            for version_record in reversed(selected_prompt_record.get("versions", [])):
                st.markdown(f"**الإصدار {version_record.get('version')}** · {version_record.get('created_at', '')[:16]} · `{version_record.get('sha256', '')[:12]}`")
                if version_record.get("note"):
                    st.caption(version_record.get("note"))
                if version_record.get("version") != selected_prompt_record.get("current_version"):
                    if st.button(f"استعادة الإصدار {version_record.get('version')} كإصدار جديد", key=f"prompt_rollback_{selected_prompt_record['id']}_{version_record.get('version')}"):
                        try:
                            prompt_workbench_mod.rollback_as_new_version(prompt_records, selected_prompt_record["id"], version_record["version"])
                            persist(); st.success("تم إنشاء إصدار جديد من النسخة المختارة."); st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
        if IS_ADMIN:
            with st.expander("✏️ تعديل البرومبت وإنشاء إصدار جديد", expanded=False):
                with st.form(f"prompt_edit_form_{case['id']}_{selected_prompt_record['id']}_{selected_prompt_record.get('current_version', 1)}"):
                    edited_prompt_body = st.text_area("محتوى الإصدار الجديد", value=selected_prompt_version.get("body", ""), height=260)
                    edited_prompt_note = st.text_input("ملاحظة الإصدار", placeholder="مثال: إضافة فصل بين الوقائع والتحليل")
                    save_prompt_version_clicked = st.form_submit_button("حفظ كإصدار جديد", type="primary", use_container_width=True)
                if save_prompt_version_clicked:
                    try:
                        prompt_workbench_mod.save_version(prompt_records, selected_prompt_record["id"], edited_prompt_body, edited_prompt_note)
                        persist(); st.success("تم حفظ إصدار جديد مع الاحتفاظ بكل الإصدارات السابقة."); st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if st.button("🗄️ أرشفة البرومبت", key=f"prompt_archive_{case['id']}_{selected_prompt_record['id']}"):
                prompt_workbench_mod.archive_prompt(prompt_records, selected_prompt_record["id"])
                persist(); st.success("تمت أرشفة البرومبت، ويمكن استعادته لاحقاً."); st.rerun()
    else:
        st.info("مكتبة البرومبتات لسه فاضية. ابدأ بإنشاء أول برومبت خاص بك.")

    archived_prompt_records = [x for x in prompt_records if x.get("status") == "archived"]
    if IS_ADMIN and archived_prompt_records:
        with st.expander(f"🗃️ الأرشيف ({len(archived_prompt_records)})", expanded=False):
            archived_labels = {f"{x.get('name')} · {x.get('id')}" : x for x in archived_prompt_records}
            archived_label = st.selectbox("البرومبتات المؤرشفة", list(archived_labels), key=f"archived_prompt_pick_{case['id']}")
            archived_record = archived_labels[archived_label]
            if st.button("استعادة البرومبت", key=f"prompt_restore_{case['id']}_{archived_record['id']}"):
                prompt_workbench_mod.restore_prompt(prompt_records, archived_record["id"])
                persist(); st.success("تمت استعادة البرومبت."); st.rerun()

    st.divider()
    st.markdown("#### 🧠 Prompt Workbench Pro | المتغيرات والسلاسل البحثية")
    st.caption("حوّل البرومبت الثابت إلى قالب متغير، واجمع عدة ملفات مع إزالة تكرار المواد وحفظ مصدر كل مادة، ثم نفّذ سلسلة مراحل يدوياً داخل أي محادثة ذكاء اصطناعي. لا توجد طلبات API تلقائية هنا.")

    # Variable-aware prompt preview
    with st.expander("🧩 تشغيل برومبت محفوظ بمتغيرات القضية", expanded=False):
        variable_prompt_choices = {f"{x.get('name')} · v{x.get('current_version', 1)}": x for x in active_prompt_records}
        if variable_prompt_choices:
            vp_label = st.selectbox("اختر قالب البرومبت", list(variable_prompt_choices), key=f"pro_var_prompt_{case['id']}")
            vp_record = variable_prompt_choices[vp_label]
            vp_version = prompt_workbench_mod.current_version(vp_record) or {}
            vp_body = vp_version.get("body", "")
            st.caption("المتغيرات المتاحة: " + "، ".join("{{" + k + "}}" for k in prompt_workbench_mod.VARIABLES))
            with st.form(f"pro_var_form_{case['id']}_{vp_record['id']}"):
                vv1, vv2 = st.columns(2)
                v_case_title = vv1.text_input("اسم القضية", value=case.get("title", ""))
                v_date_from = vv1.text_input("بداية الفترة", placeholder="2026-11-01")
                v_date_to = vv2.text_input("نهاية الفترة", placeholder="2026-11-23")
                v_parties = vv2.text_input("الأطراف", placeholder="مصر، الولايات المتحدة، ...")
                v_threads = st.text_input("الخيوط", placeholder="البحر الأحمر؛ القرن الإفريقي؛ ...")
                v_sources = st.text_input("المصادر المفضلة", placeholder="وكالات أنباء، مراكز أبحاث، وثائق رسمية...")
                v_output = st.selectbox("نوع المخرج", ["تحليل استخباراتي", "تحليل + سكريبت", "سكريبت فقط", "تقرير زمني"])
                v_dialect = st.text_input("اللهجة", value="مصرية مبسطة")
                v_duration = st.text_input("مدة المحتوى", value="3 إلى 5 دقائق")
                v_audience = st.text_input("الجمهور المستهدف", value="الجمهور العام")
                v_question = st.text_input("سؤال البحث", placeholder="ما الذي نريد تفسيره أو اختباره؟")
                v_extra = st.text_area("تعليمات إضافية", height=70)
                render_vars_clicked = st.form_submit_button("⚙️ تجهيز نسخة البرومبت بالمتغيرات", use_container_width=True)
            if render_vars_clicked:
                values = {"case_title": v_case_title, "date_from": v_date_from, "date_to": v_date_to, "parties": v_parties,
                    "threads": v_threads, "sources": v_sources, "output_type": v_output, "dialect": v_dialect,
                    "duration": v_duration, "audience": v_audience, "research_question": v_question, "extra_instructions": v_extra}
                rendered = prompt_workbench_mod.render_template(vp_body, values)
                st.session_state[f"pro_rendered_{case['id']}"] = rendered
            rendered = st.session_state.get(f"pro_rendered_{case['id']}")
            if rendered:
                if rendered["missing"]:
                    st.warning("متغيرات لم يتم ملؤها: " + "، ".join("{{" + x + "}}" for x in rendered["missing"]))
                if rendered["unknown"]:
                    st.warning("أسماء متغيرات غير معروفة: " + "، ".join(rendered["unknown"]))
                st.text_area("البرومبت الناتج", value=rendered["text"], height=280, key=f"pro_var_preview_{case['id']}")
                st.download_button("⬇️ تنزيل البرومبت الناتج TXT", rendered["text"], file_name="marsad_prompt_filled.txt", mime="text/plain", key=f"pro_var_download_{case['id']}")
        else:
            st.info("احفظ برومبتاً في المكتبة أولاً، واستخدم الأقواس المزدوجة للمتغيرات مثل {{case_title}}.")

    # Multi-case bundle builder
    with st.expander("📚 تجميع عدة ملفات في حزمة بحثية واحدة", expanded=False):
        all_research_cases = S().get("research_cases", [])
        if all_research_cases:
            case_choice_map = {f"{x.get('title', 'ملف بلا عنوان')} · {x.get('id')}": x for x in all_research_cases}
            with st.form(f"pro_bundle_form_{case['id']}"):
                bundle_title = st.text_input("اسم الحزمة", value=f"تجميع: {case.get('title', 'ملف بحثي')}")
                bundle_case_labels = st.multiselect("اختر الملفات المراد تجميعها", list(case_choice_map), default=[k for k,v in case_choice_map.items() if v.get('id') == case.get('id')])
                make_bundle_clicked = st.form_submit_button("📦 إنشاء وحفظ لقطة الحزمة", type="primary", use_container_width=True)
            if make_bundle_clicked:
                try:
                    bundle = prompt_workbench_mod.create_bundle(all_research_cases, [case_choice_map[x]["id"] for x in bundle_case_labels], bundle_title)
                    S().setdefault("prompt_bundles", []).insert(0, bundle)
                    persist(); st.success(f"تم حفظ الحزمة: {bundle['source_case_count']} ملفات، {bundle['material_count']} مواد بعد إزالة التكرار، {bundle['deduplicated_count']} تكرارات مدمجة."); st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("لا توجد ملفات بحثية يمكن تجميعها حالياً.")
        saved_bundles = S().get("prompt_bundles", [])
        if saved_bundles:
            bundle_labels = {f"{b.get('title')} · {b.get('source_case_count')} ملفات · {b.get('material_count')} مواد · {b.get('created_at','')[:16]}": b for b in saved_bundles}
            chosen_bundle_label = st.selectbox("الحزم المحفوظة", list(bundle_labels), key=f"pro_bundle_pick_{case['id']}")
            chosen_bundle = bundle_labels[chosen_bundle_label]
            bundle_markdown = prompt_workbench_mod.render_bundle(chosen_bundle)
            st.caption(f"بصمة الحزمة SHA-256: {chosen_bundle.get('sha256','')}")
            st.download_button("⬇️ تنزيل الحزمة البحثية Markdown", bundle_markdown, file_name=f"marsad_bundle_{chosen_bundle['id']}.md", mime="text/markdown", key=f"pro_bundle_download_{case['id']}")

    # Human-operated multi-stage prompt chain
    with st.expander("🔗 إنشاء وإدارة سلسلة بحثية من 6 مراحل", expanded=False):
        saved_bundles = S().get("prompt_bundles", [])
        if saved_bundles:
            chain_bundle_labels = {f"{b.get('title')} · {b.get('id')}": b for b in saved_bundles}
            with st.form(f"pro_chain_create_{case['id']}"):
                chain_title = st.text_input("اسم السلسلة", value=f"سلسلة: {case.get('title', 'بحث جديد')}")
                chain_bundle_label = st.selectbox("الحزمة التي ستعمل عليها", list(chain_bundle_labels))
                chain_research_question = st.text_input("سؤال البحث الرئيسي")
                chain_parties = st.text_input("الأطراف الرئيسية")
                chain_date_range = st.text_input("الفترة الزمنية", placeholder="من 2026-11-01 إلى 2026-11-23")
                chain_dialect = st.text_input("لهجة المخرج النهائي", value="مصرية مبسطة")
                chain_duration = st.text_input("مدة السكريبت", value="3 إلى 5 دقائق")
                create_chain_clicked = st.form_submit_button("🚀 إنشاء السلسلة وحفظها", type="primary", use_container_width=True)
            if create_chain_clicked:
                b = chain_bundle_labels[chain_bundle_label]
                vars_ = {"case_title": chain_title, "research_question": chain_research_question, "parties": chain_parties,
                         "date_from": chain_date_range, "dialect": chain_dialect, "duration": chain_duration}
                chain = prompt_workbench_mod.new_chain(chain_title, b, vars_)
                S().setdefault("prompt_chains", []).insert(0, chain)
                persist(); st.success("تم إنشاء السلسلة. كل مرحلة ستُرسل يدوياً إلى المحادثة التي تختارها، ثم تلصق نتيجتها هنا."); st.rerun()
        else:
            st.info("أنشئ حزمة بحثية واحدة على الأقل قبل بدء السلسلة.")
        saved_chains = S().get("prompt_chains", [])
        if saved_chains:
            chain_label_map = {f"{x.get('title')} · {x.get('id')}": x for x in saved_chains}
            active_chain_label = st.selectbox("السلاسل المحفوظة", list(chain_label_map), key=f"pro_chain_pick_{case['id']}")
            active_chain = chain_label_map[active_chain_label]
            linked_bundle = next((x for x in S().get("prompt_bundles", []) if x.get("id") == active_chain.get("bundle_id")), None)
            if linked_bundle:
                chain_bundle_text = prompt_workbench_mod.render_bundle(linked_bundle)
                stage_labels = [f"{i+1}. {x.get('title')} · {'مكتملة' if x.get('status') == 'completed' else 'مسودة' if x.get('status') == 'draft' else 'بانتظار التنفيذ'}" for i,x in enumerate(active_chain.get('stages', []))]
                stage_label = st.selectbox("المرحلة الحالية", stage_labels, key=f"pro_chain_stage_{active_chain['id']}")
                stage_index = stage_labels.index(stage_label)
                stage_payload = prompt_workbench_mod.chain_stage_prompt(active_chain, stage_index, chain_bundle_text)
                if stage_payload["missing_prior"]:
                    st.warning("تنبيه: توجد مراحل سابقة غير مكتملة: " + "، ".join(stage_payload["missing_prior"]) + ". يمكنك تجهيز البرومبت، لكن لا تعتمد على نتائج لم تُدخل بعد.")
                st.text_area("برومبت المرحلة الجاهز للإرسال في ChatGPT أو أي محادثة خارجية", value=stage_payload["prompt"], height=300, key=f"pro_chain_prompt_{active_chain['id']}_{stage_index}")
                st.download_button("⬇️ تنزيل برومبت المرحلة TXT", stage_payload["prompt"], file_name=f"marsad_{active_chain['id']}_{active_chain['stages'][stage_index]['key']}.txt", mime="text/plain", key=f"pro_chain_prompt_dl_{active_chain['id']}_{stage_index}")
                with st.form(f"pro_chain_output_form_{active_chain['id']}_{stage_index}"):
                    stage_output_text = st.text_area("الصق هنا نتيجة المرحلة بعد تنفيذها في المحادثة الخارجية", value=active_chain['stages'][stage_index].get('output',''), height=240)
                    mark_stage_done = st.checkbox("اعتماد هذه المرحلة كمكتملة وإتاحتها للمرحلة التالية", value=True)
                    save_stage_clicked = st.form_submit_button("💾 حفظ نتيجة المرحلة", type="primary", use_container_width=True)
                if save_stage_clicked:
                    try:
                        prompt_workbench_mod.save_stage_output(active_chain, stage_index, stage_output_text, mark_stage_done)
                        persist(); st.success("تم حفظ نتيجة المرحلة وتحديث حالة السلسلة."); st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                completed_count = sum(1 for x in active_chain.get("stages", []) if x.get("status") == "completed")
                st.progress(completed_count / max(1, len(active_chain.get("stages", []))))
                st.caption(f"إنجاز السلسلة: {completed_count} من {len(active_chain.get('stages', []))} مراحل")
                with st.expander("🧾 مخرجات السلسلة للمراجعة النهائية", expanded=False):
                    for stage in active_chain.get("stages", []):
                        st.markdown(f"**{stage.get('title')}** · {stage.get('status')}")
                        if stage.get("output"):
                            st.text_area(f"نتيجة: {stage.get('title')}", value=stage.get("output"), height=140, key=f"pro_chain_review_{active_chain['id']}_{stage['key']}", disabled=True)
                    final_draft = st.text_area("النسخة النهائية بعد المراجعة والتحرير", value=active_chain.get("approval", {}).get("final_output", ""), height=220, key=f"pro_chain_final_{active_chain['id']}")
                    if st.button("✅ اعتماد المخرج النهائي", key=f"pro_chain_approve_{active_chain['id']}", use_container_width=True):
                        try:
                            prompt_workbench_mod.approve_chain(active_chain, final_draft)
                            persist(); st.success("تم اعتماد النسخة النهائية وحفظ بصمتها."); st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                    if active_chain.get("approval", {}).get("status") == "approved":
                        st.success("السلسلة معتمدة · " + active_chain.get("approval", {}).get("approved_at", ""))
                        st.download_button("⬇️ تنزيل المخرج النهائي TXT", active_chain["approval"].get("final_output", ""), file_name=f"marsad_final_{active_chain['id']}.txt", mime="text/plain", key=f"pro_chain_final_dl_{active_chain['id']}")
            else:
                st.error("الحزمة المرتبطة بهذه السلسلة غير موجودة. لا تحذف الحزم التي تستخدمها سلاسل محفوظة.")

        # Compare outputs from the same stage across chains
        if len(S().get("prompt_chains", [])) >= 2:
            st.markdown("**مقارنة نتائج أكثر من سلسلة لنفس المرحلة**")
            compare_stage_options = {f"{x.get('title')} · {x.get('id')}": x for x in S().get("prompt_chains", [])}
            compare_labels = st.multiselect("اختر سلاسل للمقارنة", list(compare_stage_options), key=f"pro_compare_chains_{case['id']}")
            if compare_labels:
                compare_key = st.selectbox("المرحلة المراد مقارنة نتائجها", [x[0] for x in prompt_workbench_mod.CHAIN_STAGES], key=f"pro_compare_stage_{case['id']}")
                compare_items = []
                for label in compare_labels:
                    c_rec = compare_stage_options[label]
                    st_rec = next((z for z in c_rec.get("stages", []) if z.get("key") == compare_key), None)
                    if st_rec and st_rec.get("output"):
                        compare_items.append({"label": c_rec.get("title"), "text": st_rec["output"]})
                if len(compare_items) >= 2:
                    comparison_prompt = prompt_workbench_mod.compare_outputs(compare_items)
                    st.text_area("برومبت المقارنة", value=comparison_prompt, height=240, key=f"pro_compare_prompt_{case['id']}")
                    st.download_button("⬇️ تنزيل برومبت المقارنة", comparison_prompt, file_name="marsad_compare_outputs.txt", mime="text/plain", key=f"pro_compare_dl_{case['id']}")
                else:
                    st.info("لا توجد نتيجتان محفوظتان على الأقل لنفس المرحلة ضمن السلاسل المختارة.")

    st.divider()
    st.markdown("#### 🧩 محرك الأبحاث الضخمة وتقسيم المواد")
    st.caption("يقسم مواد القضية إلى دفعات قابلة للاستكمال. تجهيز البرومبتات وحفظ النتائج لا يرسل أي طلب مدفوع تلقائياً.")
    batch_rows = S().setdefault("research_batches", [])
    case_batches = [x for x in batch_rows if x.get("case_id") == case.get("id")]
    with st.expander("إنشاء أو استكمال بحث متعدد الدفعات", expanded=not bool(case_batches)):
        case_materials = [dict(x) for x in case.get("materials", []) if isinstance(x, dict)]
        st.caption(f"المواد المتاحة في ملف القضية: {len(case_materials)} مادة. يُفضّل أن تتضمن المواد نصوصاً أو مقتطفات، وليس العناوين والروابط فقط.")
        with st.form(f"research_batch_create_{case['id']}"):
            rb_title = st.text_input("اسم البحث", value=case.get("title", "بحث جديد"))
            rb_size = st.selectbox("عدد المواد في كل دفعة", [4, 6, 8, 10, 12], index=2,
                                   help="الدفعات الأصغر أسهل في المراجعة وتقلل احتمال تجاوز حدود سياق النموذج.")
            rb_note = st.text_area("تعليمات موحدة لكل الدفعات (اختياري)", height=65,
                                   placeholder="مثال: ركّز على الموقف الأمريكي والإسرائيلي وانعكاساته على مصر.")
            rb_create = st.form_submit_button("🧩 تقسيم مواد القضية إلى دفعات", type="primary",
                                              disabled=not bool(case_materials), use_container_width=True)
        if rb_create:
            try:
                new_batch = research_batches_mod.create_batch(rb_title, case_materials,
                    batch_size=rb_size, instructions=rb_note)
                new_batch["case_id"] = case.get("id")
                new_batch["case_title"] = case.get("title", "")
                batch_rows.insert(0, new_batch)
                S()["research_batches"] = batch_rows[:30]
                if persist():
                    st.success(f"تم تجهيز {len(new_batch['chunks'])} دفعة من {new_batch['material_count']} مادة. لم يتم إرسال أي طلب لنموذج.")
                st.rerun()
            except Exception as exc:
                st.error(f"تعذر تجهيز الدفعات: {type(exc).__name__}: {exc}")
        if case_batches:
            rb_labels = {f"{x.get('title')} · {x.get('created_at','')[:16]} · {x.get('material_count',0)} مادة": x for x in case_batches}
            selected_rb_label = st.selectbox("الأبحاث المحفوظة", list(rb_labels), key=f"rb_select_{case['id']}")
            active_rb = rb_labels[selected_rb_label]
            rb_sum = research_batches_mod.summary(active_rb)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("المواد", rb_sum["materials"])
            m2.metric("الدفعات", rb_sum["chunks"])
            m3.metric("المكتمل", rb_sum["completed"])
            m4.metric("التقدم", f"{rb_sum['progress_percent']}%")
            st.progress(rb_sum["progress_percent"] / 100)
            st.caption("كل دفعة لها برومبت مستقل. انسخه إلى المحادثة أو النموذج الذي تختاره، ثم الصق النتيجة هنا. الدفعات المكتملة لا تحتاج لإعادة التنفيذ.")
            chunk_labels = {
                f"الدفعة {x.get('index')} · {len(x.get('materials', []))} مادة · "
                f"{'مكتملة' if x.get('state') == 'completed' else 'فاشلة' if x.get('state') == 'failed' else 'في الانتظار'}": x
                for x in active_rb.get("chunks", [])
            }
            chosen_chunk_label = st.selectbox("اختر الدفعة", list(chunk_labels),
                                              key=f"rb_chunk_{active_rb['id']}")
            active_chunk = chunk_labels[chosen_chunk_label]
            chunk_prompt_text = research_batches_mod.chunk_prompt(active_rb, active_chunk)
            st.download_button("⬇️ تنزيل برومبت الدفعة TXT", chunk_prompt_text,
                file_name=f"marsad_{active_rb['id'][:8]}_batch_{active_chunk['index']}.txt",
                mime="text/plain", key=f"rb_prompt_dl_{active_chunk['id']}")
            st.text_area("برومبت الدفعة للنسخ", value=chunk_prompt_text, height=220,
                         key=f"rb_prompt_view_{active_chunk['id']}")
            with st.form(f"rb_output_form_{active_chunk['id']}"):
                rb_output = st.text_area("الصق نتيجة تحليل الدفعة هنا", value=active_chunk.get("output", ""),
                    height=220, placeholder="الصق المخرج الذي حصلت عليه من النموذج...")
                rb_error = st.text_input("ملاحظة أو سبب فشل (اختياري)", value=active_chunk.get("error", ""))
                rb_status = st.selectbox("حالة الدفعة بعد الحفظ", ["completed", "failed", "pending"],
                    index=["completed", "failed", "pending"].index(active_chunk.get("state", "pending")),
                    format_func=lambda x: {"completed": "مكتملة", "failed": "فشلت وتحتاج إعادة", "pending": "لم تُنفذ بعد"}[x])
                rb_save = st.form_submit_button("💾 حفظ نتيجة الدفعة", type="primary", use_container_width=True)
            if rb_save:
                try:
                    research_batches_mod.set_chunk_output(active_rb, active_chunk["id"], rb_output,
                                                          state=rb_status, error=rb_error)
                    persist()
                    st.success("تم حفظ نتيجة الدفعة وتحديث سجل البحث.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"تعذر حفظ النتيجة: {type(exc).__name__}")
            if active_chunk.get("state") == "failed":
                if st.button("↻ إعادة تجهيز هذه الدفعة", key=f"rb_retry_{active_chunk['id']}"):
                    research_batches_mod.retry_chunk(active_rb, active_chunk["id"])
                    persist()
                    st.rerun()
            if rb_sum["completed"] == rb_sum["chunks"] and rb_sum["chunks"]:
                try:
                    merge_text = research_batches_mod.merge_prompt(active_rb)
                    st.success("اكتملت كل الدفعات. يمكنك الآن تجهيز برومبت الدمج النهائي.")
                    st.download_button("⬇️ تنزيل برومبت دمج البحث الكامل", merge_text,
                        file_name=f"marsad_{active_rb['id'][:8]}_merge.txt", mime="text/plain",
                        key=f"rb_merge_dl_{active_rb['id']}")
                    st.text_area("برومبت الدمج النهائي", value=merge_text, height=260,
                                 key=f"rb_merge_view_{active_rb['id']}")
                except ValueError as exc:
                    st.info(str(exc))
            elif rb_sum["failed"]:
                st.warning(f"هناك {rb_sum['failed']} دفعة فاشلة. أعد تجهيزها قبل الدمج النهائي.")
            st.caption("ملاحظة: المحرك يحفظ المواد والمخرجات في بيانات التطبيق. لا يقرأ الروابط بنفسه ولا يضمن أن النص الكامل متاح؛ جودة التحليل مرتبطة بما جُمع فعلياً.")

    st.divider()
    st.markdown("#### 🎬 محرك إنتاج الفيديو المصري | Phase 8.27")
    st.caption("حوّل ملف التحليل النهائي إلى ورقة قراءة، وسكريبت مصري، وخطة مشاهد ومقاطع قصيرة. كل شيء هنا يعمل بالبرومبتات اليدوية ولا يرسل طلباً مدفوعاً.")
    video_rows = S().setdefault("video_projects", [])
    case_video_projects = [x for x in video_rows if x.get("case_id") == case.get("id")]
    with st.expander("إنشاء مشروع فيديو أو فتح مشروع محفوظ", expanded=not bool(case_video_projects)):
        with st.form(f"video_project_create_{case['id']}"):
            vp_title = st.text_input("عنوان مشروع الفيديو", value=case.get("title", "تحليل سياسي"))
            vp_type_label = st.selectbox("نوع الفيديو", list(video_storyteller_mod.VIDEO_TYPES),
                format_func=lambda x: video_storyteller_mod.VIDEO_TYPES[x], index=0)
            vp_duration = st.selectbox("مدة الفيديو بالدقائق", list(video_storyteller_mod.DURATIONS), index=3)
            vp_tone = st.selectbox("أسلوب التقديم", list(video_storyteller_mod.TONES),
                format_func=lambda x: video_storyteller_mod.TONES[x], index=0)
            vp_scenes = st.checkbox("إنشاء خطة المشاهد والإنتاج", value=True)
            vp_shorts = st.checkbox("إنشاء مقاطع Shorts / Reels", value=True)
            vp_dossier = st.text_area("الصق هنا ملف التحليل النهائي أو نتيجة الدمج", height=220,
                placeholder="الصق التقرير النهائي الذي جمعته من دفعات البحث، مع معرّفات المصادر...")
            vp_create = st.form_submit_button("🎬 إنشاء مشروع الفيديو وحفظ ملف البحث", type="primary", use_container_width=True)
        if vp_create:
            try:
                cfg = {"video_type": vp_type_label, "duration_minutes": vp_duration, "tone": vp_tone,
                       "scene_plan_enabled": vp_scenes, "short_clips_enabled": vp_shorts}
                project = video_storyteller_mod.create_project(case.get("id"), vp_title, vp_dossier, cfg,
                    dossier_id=f"case:{case.get('id')}")
                video_rows.insert(0, project)
                S()["video_projects"] = video_rows[:50]
                persist(); st.success("اتحفظ مشروع الفيديو وملف البحث المرجعي. مفيش أي استدعاء لنموذج أو تكلفة."); st.rerun()
            except Exception as exc:
                st.error(f"تعذر إنشاء المشروع: {type(exc).__name__}: {exc}")
        if case_video_projects:
            vp_labels = {f"{x.get('case_title') or x.get('case_id')} · {x.get('created_at','')[:16]} · {len(x.get('artifacts', []))} مخرج": x for x in case_video_projects}
            selected_vp_label = st.selectbox("مشروعات الفيديو المحفوظة", list(vp_labels), key=f"vp_select_{case['id']}")
            active_vp = vp_labels[selected_vp_label]
            cfg = video_storyteller_mod.validate_settings(active_vp.get("settings"))
            st.caption(f"الإعدادات الحالية: {video_storyteller_mod.VIDEO_TYPES[cfg['video_type']]} · {cfg['duration_minutes']} دقائق · {video_storyteller_mod.TONES[cfg['tone']]}")
            with st.form(f"vp_edit_settings_{active_vp['id']}"):
                edit_type = st.selectbox("تعديل نوع الفيديو", list(video_storyteller_mod.VIDEO_TYPES), index=list(video_storyteller_mod.VIDEO_TYPES).index(cfg['video_type']), format_func=lambda x: video_storyteller_mod.VIDEO_TYPES[x])
                edit_duration = st.selectbox("تعديل المدة", list(video_storyteller_mod.DURATIONS), index=list(video_storyteller_mod.DURATIONS).index(cfg['duration_minutes']))
                edit_tone = st.selectbox("تعديل أسلوب التقديم", list(video_storyteller_mod.TONES), index=list(video_storyteller_mod.TONES).index(cfg['tone']), format_func=lambda x: video_storyteller_mod.TONES[x])
                edit_scenes = st.checkbox("خطة المشاهد مفعلة", value=cfg['scene_plan_enabled'])
                edit_shorts = st.checkbox("المقاطع القصيرة مفعلة", value=cfg['short_clips_enabled'])
                edit_save = st.form_submit_button("حفظ إعدادات هذا الفيديو")
            if edit_save:
                active_vp["settings"] = video_storyteller_mod.validate_settings({"video_type": edit_type, "duration_minutes": edit_duration, "tone": edit_tone, "scene_plan_enabled": edit_scenes, "short_clips_enabled": edit_shorts})
                active_vp["updated_at"] = video_storyteller_mod._now(); persist(); st.rerun()

            st.markdown("##### 1. ورقة القراءة التحليلية")
            read_prompt = video_storyteller_mod.reading_prompt(active_vp)
            st.download_button("⬇️ تنزيل برومبت ورقة القراءة", read_prompt, file_name=f"marsad_video_reading_{active_vp['id'][:8]}.txt", mime="text/plain", key=f"vp_read_dl_{active_vp['id']}")
            st.text_area("برومبت ورقة القراءة للنسخ", value=read_prompt, height=180, key=f"vp_read_prompt_{active_vp['id']}")
            with st.form(f"vp_read_save_{active_vp['id']}"):
                read_output = st.text_area("الصق نتيجة ورقة القراءة هنا", height=160, key=f"vp_read_output_{active_vp['id']}")
                read_submit = st.form_submit_button("حفظ ورقة القراءة كإصدار")
            if read_submit:
                try:
                    video_storyteller_mod.save_artifact(active_vp, "reading_sheet", read_output, title="ورقة القراءة التحليلية")
                    persist(); st.success("اتحفظت ورقة القراءة."); st.rerun()
                except Exception as exc: st.error(str(exc))

            st.markdown("##### 2. السكريبت المصري وخطة الإنتاج")
            saved_reading = video_storyteller_mod.latest_artifact(active_vp, "reading_sheet")
            script_prompt_text = video_storyteller_mod.script_prompt(active_vp, saved_reading.get("content", "") if saved_reading else "")
            st.download_button("⬇️ تنزيل برومبت السكريبت والإنتاج", script_prompt_text, file_name=f"marsad_video_script_{active_vp['id'][:8]}.txt", mime="text/plain", key=f"vp_script_dl_{active_vp['id']}")
            st.text_area("برومبت السكريبت للنسخ", value=script_prompt_text, height=220, key=f"vp_script_prompt_{active_vp['id']}")
            with st.form(f"vp_script_save_{active_vp['id']}"):
                script_output = st.text_area("السكريبت المنطوق", height=220, key=f"vp_script_output_{active_vp['id']}")
                plan_output = st.text_area("خطة المشاهد والإنتاج", height=160, key=f"vp_plan_output_{active_vp['id']}") if cfg['scene_plan_enabled'] else ""
                shorts_output = st.text_area("مقاطع Shorts / Reels", height=140, key=f"vp_shorts_output_{active_vp['id']}") if cfg['short_clips_enabled'] else ""
                kit_output = st.text_area("عناوين ووصف وغلاف وكلمات مفتاحية", height=120, key=f"vp_kit_output_{active_vp['id']}")
                script_submit = st.form_submit_button("حفظ المخرجات كلٌ في إصدار مستقل", type="primary")
            if script_submit:
                try:
                    saved_count = 0
                    for kind, content, title in (("script", script_output, "السكريبت المصري"), ("production_plan", plan_output, "خطة المشاهد والإنتاج"), ("short_clips", shorts_output, "مقاطع Shorts / Reels"), ("publishing_kit", kit_output, "حزمة النشر")):
                        if content.strip():
                            video_storyteller_mod.save_artifact(active_vp, kind, content, title=title); saved_count += 1
                    if not saved_count: raise ValueError("الصق مخرجاً واحداً على الأقل قبل الحفظ")
                    persist(); st.success(f"اتحفظ {saved_count} مخرج/مخرجات بإصدارات مستقلة."); st.rerun()
                except Exception as exc: st.error(str(exc))

            st.markdown("##### 3. إعادة كتابة السكريبت من غير إعادة البحث")
            previous_script = video_storyteller_mod.latest_artifact(active_vp, "script")
            if previous_script:
                with st.form(f"vp_revision_{active_vp['id']}"):
                    revision_note = st.text_area("إيه اللي عايز تغيره؟", placeholder="مثال: خلي المقدمة أقوى، قلل التكرار، زوّد شرح أثر الموضوع على مصر...")
                    revision_go = st.form_submit_button("إنشاء برومبت إعادة الكتابة")
                if revision_go:
                    try:
                        rev_prompt = video_storyteller_mod.revision_prompt(active_vp, previous_script.get("content", ""), revision_note)
                        st.session_state[f"vp_revision_prompt_{active_vp['id']}"] = rev_prompt
                    except Exception as exc: st.error(str(exc))
                if st.session_state.get(f"vp_revision_prompt_{active_vp['id']}"):
                    st.text_area("برومبت إعادة الكتابة", value=st.session_state[f"vp_revision_prompt_{active_vp['id']}"], height=180, key=f"vp_revision_view_{active_vp['id']}")
                    st.download_button("⬇️ تنزيل برومبت إعادة الكتابة", st.session_state[f"vp_revision_prompt_{active_vp['id']}"], file_name="marsad_script_revision.txt", mime="text/plain", key=f"vp_revision_dl_{active_vp['id']}")
            else:
                st.info("احفظ أول نسخة من السكريبت حتى يظهر مسار إعادة الكتابة.")

            st.markdown("##### سجل المخرجات والإصدارات")
            if active_vp.get("artifacts"):
                for artifact in reversed(active_vp["artifacts"][-20:]):
                    with st.expander(f"{artifact.get('title')} · إصدار {artifact.get('version')} · {artifact.get('created_at','')[:16]}"):
                        st.text_area("المحتوى المحفوظ", value=artifact.get("content", ""), height=180, key=f"vp_artifact_{artifact['id']}")
                        st.download_button("تنزيل هذا الإصدار", artifact.get("content", ""), file_name=f"{artifact.get('kind')}_v{artifact.get('version')}.txt", mime="text/plain", key=f"vp_artifact_dl_{artifact['id']}")
            else:
                st.info("لسه مفيش مخرجات محفوظة للمشروع.")
            st.caption("ملاحظة: المحرك ينشئ البرومبتات ويحفظ المخرجات التي تلصقها. لا يولّد الفيديو أو الصور تلقائياً، ولا يفتح روابط المصادر من تلقاء نفسه.")

    st.markdown("#### 📦 ملفات القضايا والتجميعات الذكية")
    st.caption("جهّز حزمة مستقلة من لقطة مواد القضية الحالية، واختر الخيوط والبرومبت والنموذج المستهدف. إنشاء الحزمة لا يرسل أي طلب مدفوع تلقائياً.")
    thread_options = list(links_mod.THREADS.keys()) + [x.get("name", "") for x in S().get("custom_threads", []) if x.get("name")]
    custom_prompt_records = prompt_workbench_mod.active_prompts(S().get("prompt_library", []))
    custom_prompt_choices = {f"📚 {x.get('name')} · إصدار {x.get('current_version', 1)}": x for x in custom_prompt_records}
    prompt_options = ["تحليل ملف القضية الشامل"] + list(analysis_lab_mod.PROMPT_TEMPLATES.keys()) + list(custom_prompt_choices)
    model_options = ["Gemini API (مدفوع)", "Gemini (خطة مجانية إن توفرت)", "OpenRouter (مجاني/مدفوع حسب النموذج)",
                     "Ollama (محلي)", "Hugging Face (حسب نقطة التشغيل)", "Google Colab (معالجة مساعدة)", "نسخ يدوي إلى نموذج خارجي"]
    with st.form(f"analysis_package_form_{case['id']}"):
        selected_threads = st.multiselect("الخيوط المرتبطة بالقضية", thread_options,
                                          help="اختيار الخيوط يثبت سياقها داخل الحزمة. المواد المضافة يدوياً للملف تظل موجودة كلها.")
        selected_prompt = st.selectbox("البرومبت المستخدم", prompt_options)
        selected_model = st.selectbox("النموذج المستهدف", model_options)
        output_mode = st.selectbox("شكل المخرج المطلوب", ["تحليل + سكريبت مصري", "تحليل استخباراتي فقط", "سكريبت مصري فقط"],
                                   help="حدد هل تريد التحليل، أو سكريبت جاهز للإلقاء، أو الاثنين معاً.")
        audience = st.selectbox("الجمهور المستهدف", ["الجمهور العام", "متابع مهتم بالسياسة", "صانع محتوى متخصص", "تقرير مهني لصانع قرار"])
        script_duration = st.selectbox("مدة السكريبت", ["60 إلى 90 ثانية", "3 إلى 5 دقائق", "8 إلى 12 دقيقة"], index=1)
        package_note = st.text_area("تعليمات إضافية لهذه الحزمة (اختياري)", height=70,
                                    placeholder="مثال: ركّز على أثر التطورات على مصر، وقارن الروايات الإسرائيلية والأمريكية.")
        make_package = st.form_submit_button("📦 تجهيز حزمة التحليل وحفظ إصدار", type="primary", use_container_width=True)
    if make_package:
        if selected_prompt == "تحليل ملف القضية الشامل":
            package_prompt = casebook_mod.build_prompt(case)
            prompt_label = selected_prompt
        elif selected_prompt in custom_prompt_choices:
            chosen_custom_prompt = custom_prompt_choices[selected_prompt]
            chosen_custom_version = prompt_workbench_mod.current_version(chosen_custom_prompt) or {}
            package_prompt = (chosen_custom_version.get("body", "") + "\n\n## سياق القضية البحثي\n" +
                              casebook_mod.build_prompt(case))
            prompt_label = f"{chosen_custom_prompt.get('name')} · v{chosen_custom_version.get('version')}"
        else:
            package_articles = [dict(x) for x in case.get("materials", [])]
            package_prompt = analysis_lab_mod.make_prompt(selected_prompt, package_articles,
                case_name=case.get("title", "ملف بحثي"), custom_outlets=S().get("outlet_profiles", {}),
                custom_writers=S().get("writer_profiles", {}))
            prompt_label = selected_prompt
        output_instructions = {
            "تحليل استخباراتي فقط": "أخرج تحليلاً بحثياً منظماً فقط، ولا تكتب سكريبتاً إعلامياً.",
            "سكريبت مصري فقط": "أخرج سكريبتاً مصرياً جاهزاً للإلقاء فقط، مع قائمة تحقق ومصادر في نهاية منفصلة.",
            "تحليل + سكريبت مصري": "أخرج أولاً التحليل البحثي المنظم، ثم سكريبتاً مصرياً مستقلاً مبنياً حصراً على نتائج التحليل والأدلة.",
        }
        package_prompt += "\n\n## مواصفات المخرج التحريري\n" + output_instructions[output_mode]
        package_prompt += f"\nالجمهور المستهدف: {audience}."
        if output_mode != "تحليل استخباراتي فقط":
            package_prompt += f"\nمدة السكريبت المستهدفة: {script_duration}."
            package_prompt += "\nاكتب بلهجة مصرية طبيعية مبسطة، بجمل قصيرة صالحة للإلقاء الصوتي. افتتح بخطاف قوي غير مضلل، ثم اشرح الحكاية وسياقها ومصالح الأطراف، واختم بخلاصة وسؤال ذكي للجمهور. تجنب التهويل والشتائم والادعاءات غير المثبتة. لا تضع معلومة غير مؤكدة بصيغة الجزم. أضف توجيهات أداء خفيفة بين أقواس عند الحاجة. افصل قائمة المصادر والروابط عن نص الإلقاء حتى لا تُقرأ ضمن الفيديو."
        package_prompt += "\n\n## معيار الدقة الإلزامي\nصنّف كل نقطة إلى: واقعة موثقة، ادعاء منسوب لمصدر، تحليل/استنتاج، أو سيناريو محتمل. اربط الاستنتاج بمصدره، واذكر التناقضات والفجوات ودرجة الثقة. لا تعتبر تكرار الخبر في مواقع تنقل عن وكالة واحدة تأكيداً مستقلاً. لا تخترع تواريخ أو أرقاماً أو اقتباسات أو روابط. إذا لم تتوفر مادة كافية، قل ذلك بوضوح."
        if package_note.strip():
            package_prompt += "\n\nتعليمات إضافية من الباحث:\n" + package_note.strip()
        # ضم مواد الأرشيف المطابقة للخيوط المختارة إلى لقطة الحزمة دون تعديل الملف الأصلي.
        thread_pool = list(_dos_pool().values()) + list(S().get("saved", []))
        thread_pool = links_mod.tag_pool(thread_pool)
        selected_articles = []
        seen_package_urls = {x.get("url") for x in case.get("materials", []) if x.get("url")}
        custom_by_name = {x.get("name"): x for x in S().get("custom_threads", []) if x.get("name")}
        for thread_name in selected_threads:
            if thread_name in links_mod.THREADS:
                candidates = links_mod.thread_items(thread_pool, thread_name)
            else:
                custom_rec = custom_by_name.get(thread_name, {})
                wanted_urls = set(custom_rec.get("articles", []))
                candidates = [a for a in thread_pool if (a.get("url") or a.get("link")) in wanted_urls]
            for article in candidates:
                article_url = article.get("url") or article.get("link") or ""
                if article_url and article_url not in seen_package_urls:
                    selected_articles.append(article)
                    seen_package_urls.add(article_url)
        package_materials = list(case.get("materials", [])) + selected_articles
        if selected_threads:
            package_prompt += "\n\nالخيوط المختارة لإثراء الحزمة (سياق بحثي لا يثبت علاقة سببية):\n- " + "\n- ".join(selected_threads)
            package_prompt += f"\nتم ضم {len(selected_articles)} مادة إضافية من الأرشيف بناءً على مطابقة الخيوط المختارة."
        history = S().setdefault("analysis_packages", [])
        package = analysis_packages_mod.build_package(case, package_prompt, prompt_label, selected_model,
                                                       selected_threads, source_materials=package_materials,
                                                       package_history=history, output_mode=output_mode,
                                                       audience=audience, script_duration=script_duration)
        history.insert(0, package)
        persist()
        st.session_state[f"active_analysis_package_{case['id']}"] = package["id"]
        st.success(f"تم تجهيز الحزمة وحفظ الإصدار رقم {package['version']} بنجاح. لم يتم استهلاك أي توكنز أو إرسال طلب إلى Gemini.")

    saved_packages = [x for x in S().get("analysis_packages", []) if x.get("case_id") == case.get("id")]
    if saved_packages:
        package_labels = {f"إصدار {x.get('version')} · {x.get('created_at','')[:16]} · {x.get('prompt_name','')} · {x.get('model','')}": x for x in saved_packages}
        active_pkg_id = st.session_state.get(f"active_analysis_package_{case['id']}")
        default_pkg = next((k for k, v in package_labels.items() if v.get("id") == active_pkg_id), next(iter(package_labels)))
        picked_pkg_label = st.selectbox("الحزم المحفوظة لهذه القضية", list(package_labels),
                                        index=list(package_labels).index(default_pkg), key=f"analysis_pkg_select_{case['id']}")
        active_pkg = package_labels[picked_pkg_label]
        st.caption(f"{active_pkg.get('material_count', 0)} مادة · {active_pkg.get('source_count', 0)} مصدر · SHA-256: {active_pkg.get('sha256','')[:16]}…")
        pkg_md = analysis_packages_mod.render_markdown(active_pkg)
        pkg_json = analysis_packages_mod.render_json(active_pkg)
        p1, p2, p3 = st.columns(3)
        p1.download_button("⬇️ Markdown", pkg_md, file_name=f"marsad_case_v{active_pkg.get('version')}.md", mime="text/markdown", key=f"pkg_md_{active_pkg['id']}", use_container_width=True)
        p2.download_button("⬇️ TXT", analysis_packages_mod.render_text(active_pkg), file_name=f"marsad_case_v{active_pkg.get('version')}.txt", mime="text/plain", key=f"pkg_txt_{active_pkg['id']}", use_container_width=True)
        p3.download_button("⬇️ JSON", pkg_json, file_name=f"marsad_case_v{active_pkg.get('version')}.json", mime="application/json", key=f"pkg_json_{active_pkg['id']}", use_container_width=True)
        st.text_area("البرومبت والحزمة الجاهزة للنسخ", value=pkg_md, height=300, key=f"pkg_preview_{active_pkg['id']}")
        st.info("الحزمة محفوظة. لن يتم إرسالها لأي نموذج إلا بعد ضغط زر الإرسال صراحةً. المفاتيح لا تُحفظ داخل ملف القضية أو GitHub Gist.")

        with st.expander("🚀 مركز النماذج AI Hub · اقتراح وموافقة وتشغيل", expanded=False):
            st.caption("المرصد يقترح فقط. أنت تختار وتوافق قبل أي إرسال، ولا يوجد تشغيل تلقائي للنماذج.")
            task_type = st.selectbox("نوع المهمة التي تريد تنفيذها", list(ai_router_mod.TASKS), key=f"router_task_{case['id']}")
            task_extra = st.text_area("تعليماتك الإضافية للمهمة (اختياري)", height=80,
                placeholder="مثال: ركّز على تأثير التطورات على مصر، واعرض الروايات المتعارضة.", key=f"router_extra_{case['id']}")
            provider_labels = ai_providers_mod.provider_options()
            configured_candidates = []
            for _pid, _cfg in ai_providers_mod.PROVIDERS.items():
                if _pid == "custom_openai":
                    if st.session_state.get(f"custom_ai_key_{case['id']}"):
                        configured_candidates.append(_pid)
                elif _cfg.get("secret_name") and _secret(_cfg["secret_name"]):
                    configured_candidates.append(_pid)
            suggested_provider = ai_router_mod.recommend_provider(task_type, configured_candidates)
            if suggested_provider:
                suggested_label = ai_providers_mod.PROVIDERS[suggested_provider]["label"]
                st.info(f"**اقتراح المرصد:** {suggested_label}. الاقتراح مبني على نوع المهمة والمزودات التي ظهر لها إعداد متاح، وليس ضماناً للجودة أو التوافر أو المجانية. راجع نوع الفوترة والتكلفة قبل الموافقة.")
            else:
                st.warning("لم يجد المرصد مزوداً بإعدادات متاحة في هذه الجلسة. يمكنك تجهيز البرومبت ونسخه إلى أي محادثة خارجية دون إرسال API.")
            provider_label = st.selectbox("اختر المزود بنفسك أو خالف اقتراح المرصد", list(provider_labels),
                index=list(provider_labels).index(ai_providers_mod.PROVIDERS[suggested_provider]["label"]) if suggested_provider else 0,
                key=f"ai_provider_{case['id']}")
            provider_id = provider_labels[provider_label]
            provider_cfg = ai_providers_mod.PROVIDERS[provider_id]
            st.caption(provider_cfg.get("note", ""))
            if provider_id == "custom_openai":
                model = st.text_input("اسم النموذج عند المزود", placeholder="مثال: provider/model-name", key=f"custom_ai_model_{case['id']}")
            elif provider_id == "gemini":
                model = st.text_input("اسم نموذج Gemini", value=provider_cfg["default_model"], help="اكتب أي model ID متاح لمفتاحك في Google AI Studio.", key=f"gemini_model_{case['id']}")
            else:
                model = st.selectbox("النموذج", provider_cfg["models"], index=provider_cfg["models"].index(provider_cfg["default_model"]), key=f"ai_model_{case['id']}")

            billing_profile = ai_billing_mod.get_profile(S().get("ai_settings", {}), provider_id, model)
            billing_widget_suffix = ai_billing_mod.profile_key(provider_id, model)
            api_key = ""
            account_id = ""
            base_url = ""
            free_confirmed = False
            gemini_mode = ""
            input_price = output_price = 0.0
            monthly_budget = 0.0
            price_reviewed = False
            if provider_id == "custom_openai":
                base_url = st.text_input("عنوان API الأساسي (HTTPS)", placeholder="https://api.example.com/v1", key=f"custom_ai_url_{case['id']}")
                api_key = st.text_input("مفتاح API للمزود", type="password", key=f"custom_ai_key_{case['id']}", placeholder="يظل في الجلسة الحالية فقط")
            elif provider_cfg.get("secret_name"):
                saved_key = _secret(provider_cfg["secret_name"])
                api_key = saved_key or st.text_input("مفتاح API (يظل في الجلسة الحالية فقط)", type="password", key=f"ai_key_{provider_id}_{case['id']}", placeholder="الصق المفتاح هنا أو أضفه إلى Secrets")
                if saved_key:
                    st.caption(f"تم العثور على {provider_cfg['secret_name']} في أسرار التطبيق.")
            if provider_id == "custom_openai":
                custom_billing = st.radio("نوع حساب المزود المخصص", ["مجاني مؤكد", "مدفوع بسقف إنفاق"], horizontal=True, key=f"custom_ai_billing_{case['id']}")
                if custom_billing == "مجاني مؤكد":
                    free_confirmed = st.checkbox("أؤكد أن استخدام هذا المفتاح لا يترتب عليه رسوم أو فوترة مدفوعة.", key=f"custom_ai_free_{case['id']}")
                else:
                    q1, q2 = st.columns(2)
                    input_price = q1.number_input("سعر مليون توكن إدخال بالدولار", min_value=0.0, value=float(billing_profile.get("input_price_per_million", 0.0)), step=0.05, key=f"custom_ai_in_price_{billing_widget_suffix}")
                    output_price = q2.number_input("سعر مليون توكن إخراج بالدولار", min_value=0.0, value=float(billing_profile.get("output_price_per_million", 0.0)), step=0.05, key=f"custom_ai_out_price_{billing_widget_suffix}")
                    monthly_budget = st.number_input("أقصى إنفاق شهري بالدولار", min_value=0.0, value=float(billing_profile.get("monthly_budget_usd", 0.0)), step=1.0, key=f"custom_ai_budget_{billing_widget_suffix}")
                    pricing_source = st.text_input("رابط صفحة الأسعار الرسمية (اختياري)", value=billing_profile.get("pricing_source_url", ""), key=f"custom_ai_price_source_{billing_widget_suffix}")
                    if st.button("💾 حفظ أسعار وسقف هذا النموذج", key=f"save_custom_billing_{billing_widget_suffix}"):
                        try:
                            ai_billing_mod.save_profile(S().setdefault("ai_settings", {}), provider_id, model, input_price, output_price, monthly_budget, pricing_source)
                            persist(); st.success("تم حفظ إعدادات الفوترة لهذا النموذج.")
                        except ValueError as exc:
                            st.error(str(exc))
                    price_reviewed = st.checkbox("راجعت الأسعار الرسمية لهذا النموذج وأدخلت السعر الصحيح.", key=f"custom_ai_price_review_{billing_widget_suffix}")
            if provider_id == "cloudflare":
                account_id = _secret("CLOUDFLARE_ACCOUNT_ID") or st.text_input("Cloudflare Account ID", key=f"cf_account_{case['id']}")
            if provider_id == "ollama":
                base_url = st.text_input("عنوان Ollama المحلي", value="http://127.0.0.1:11434", key=f"ollama_url_{case['id']}")

            if provider_id in ("openrouter_free", "groq", "cloudflare"):
                free_confirmed = st.checkbox("أؤكد أن حسابي على الخطة المجانية، ولم أفعل فوترة مدفوعة قد تسبب رسوماً إضافية.", key=f"ai_free_confirm_{provider_id}_{case['id']}")
            elif provider_id == "gemini":
                gemini_mode = st.radio("نوع فوترة مشروع Gemini", ["غير محدد · إيقاف الإرسال", "خطة مجانية مؤكدة", "خطة مدفوعة"], horizontal=True, key=f"gemini_mode_{case['id']}")
                if gemini_mode == "خطة مجانية مؤكدة":
                    free_confirmed = st.checkbox("أؤكد أن مفتاح API تابع لمشروع على الخطة المجانية في Google AI Studio.", key=f"gemini_free_confirm_{case['id']}")
                    st.warning("في الخطة المجانية قد تستخدم Google محتوى الطلبات لتحسين منتجاتها. لا ترسل معلومات حساسة أو سرية.")
                elif gemini_mode == "خطة مدفوعة":
                    st.warning("الإرسال المدفوع يحتاج تأكيدك وسقف إنفاق. أدخل أسعار النموذج المحدد من صفحة الأسعار الرسمية، لأن الأسعار تختلف بين نماذج Gemini وقد تتغير.")
                    q1, q2 = st.columns(2)
                    input_price = q1.number_input("سعر مليون توكن إدخال بالدولار", min_value=0.0, value=float(billing_profile.get("input_price_per_million", 0.0)), step=0.05, key=f"gemini_in_price_{billing_widget_suffix}")
                    output_price = q2.number_input("سعر مليون توكن إخراج بالدولار", min_value=0.0, value=float(billing_profile.get("output_price_per_million", 0.0)), step=0.05, key=f"gemini_out_price_{billing_widget_suffix}")
                    monthly_budget = st.number_input("أقصى إنفاق شهري بالدولار", min_value=0.0, value=float(billing_profile.get("monthly_budget_usd", 0.0)), step=1.0, key=f"gemini_budget_{billing_widget_suffix}")
                    pricing_source = st.text_input("رابط صفحة الأسعار الرسمية (اختياري)", value=billing_profile.get("pricing_source_url", ""), key=f"gemini_price_source_{billing_widget_suffix}")
                    if st.button("💾 حفظ أسعار وسقف هذا النموذج", key=f"save_gemini_billing_{billing_widget_suffix}"):
                        try:
                            ai_billing_mod.save_profile(S().setdefault("ai_settings", {}), provider_id, model, input_price, output_price, monthly_budget, pricing_source)
                            persist(); st.success("تم حفظ إعدادات الفوترة لهذا النموذج.")
                        except ValueError as exc:
                            st.error(str(exc))
                    price_reviewed = st.checkbox("راجعت أن الأسعار المدخلة تخص Model ID المحدد حالياً.", key=f"gemini_price_review_{billing_widget_suffix}")

            max_output = pick(st, "أقصى طول للإجابة (توكنز)", [1024, 2048, 4096, 6144, 8192], 4096, f"ai_max_output_{case['id']}")
            task_prompt = ai_router_mod.build_task_prompt(pkg_md, task_type, task_extra)
            st.caption("البرومبت النهائي يجمع لقطة القضية والمواد والخيوط والبرومبت الأساسي مع تكليف المهمة الإضافي.")
            st.download_button("⬇️ تنزيل برومبت المحادثة الكامل", task_prompt,
                file_name=f"marsad_prompt_{active_pkg.get('version')}.txt", mime="text/plain",
                key=f"router_prompt_download_{active_pkg['id']}", use_container_width=True)
            with st.expander("معاينة البرومبت النهائي قبل الإرسال أو النسخ"):
                st.text_area("البرومبت الكامل", value=task_prompt, height=280, key=f"router_prompt_preview_{active_pkg['id']}")
            month_key = datetime.now(timezone.utc).strftime("%Y-%m")
            usage_rows = [x for x in S().get("ai_usage", []) if x.get("month") == month_key]
            month_spend = sum(float(x.get("cost_usd") or 0) for x in usage_rows)
            selected_provider_spend = sum(float(x.get("cost_usd") or 0) for x in usage_rows if x.get("provider") == provider_id)
            selected_model_committed = ai_billing_mod.month_spend(usage_rows, month_key, provider_id, model)
            selected_model_reserved = ai_billing_mod.reserved_spend(S().get("ai_settings", {}), provider_id, model, month_key)
            selected_model_spend = selected_model_committed + selected_model_reserved
            u1, u2, u3 = st.columns(3)
            u1.metric("طلبات هذا الشهر", len(usage_rows))
            u2.metric("توكنز مسجلة", sum(int(x.get("total_tokens") or 0) for x in usage_rows))
            u3.metric("إنفاق مسجل", f"${month_spend:.4f}")

            can_send = bool(IS_ADMIN)
            if provider_id in ("openrouter_free", "groq", "cloudflare") and not free_confirmed:
                can_send = False
            if provider_id == "custom_openai":
                if custom_billing == "مجاني مؤكد":
                    can_send = bool(IS_ADMIN and free_confirmed)
                else:
                    can_send = bool(IS_ADMIN and input_price > 0 and output_price > 0 and monthly_budget > 0 and price_reviewed and selected_model_spend < monthly_budget)
                can_send = can_send and bool(base_url and model and model != "اكتب اسم النموذج")
            if provider_id == "gemini":
                if gemini_mode == "خطة مجانية مؤكدة":
                    can_send = bool(IS_ADMIN and free_confirmed)
                elif gemini_mode == "خطة مدفوعة":
                    can_send = bool(IS_ADMIN and input_price > 0 and output_price > 0 and monthly_budget > 0 and (selected_model_spend < monthly_budget) and price_reviewed)
                else:
                    can_send = False
            if provider_id != "ollama" and not api_key:
                can_send = False
            if provider_id == "cloudflare" and not account_id:
                can_send = False
            projected_input_tokens = ai_router_mod.estimate_input_tokens(task_prompt)
            paid_mode = ((provider_id == "gemini" and gemini_mode == "خطة مدفوعة") or
                         (provider_id == "custom_openai" and custom_billing == "مدفوع بسقف إنفاق"))
            projected_cost = ai_providers_mod.estimate_cost(projected_input_tokens, max_output, input_price, output_price) if paid_mode else (0.0 if free_confirmed or provider_id == "ollama" else None)
            budget_check = ai_billing_mod.preflight(selected_model_spend, projected_cost, monthly_budget) if paid_mode and projected_cost is not None else None
            if paid_mode and budget_check and not budget_check["allowed"]:
                can_send = False
            st.markdown("**تقدير التكلفة قبل الموافقة**")
            c1, c2, c3 = st.columns(3)
            c1.metric("توكنز الإدخال المتوقعة", f"~{projected_input_tokens:,}")
            c2.metric("توكنز الإخراج القصوى", f"{max_output:,}")
            if projected_cost is None:
                c3.metric("التكلفة المتوقعة", "غير معروفة")
                st.warning("لا يمكن تأكيد تكلفة هذا المسار من البيانات الحالية. لن نعرضه على أنه مجاني. راجع خطة المزود وأسعاره قبل الإرسال.")
            else:
                c3.metric("التكلفة التقديرية", f"${projected_cost:.5f}")
                st.caption("التقدير تقريبي وليس عرض سعر نهائياً. التكلفة الفعلية تعتمد على عداد المزود والتوكنز الفعلية وأي رسوم إضافية.")
            if paid_mode and projected_cost is not None:
                st.caption(f"الإنفاق المسجل والحجوزات النشطة لهذا النموذج: ${selected_model_spend:.4f} (منها حجوزات ${selected_model_reserved:.4f}) · المتبقي من سقف النموذج: ${max(0, monthly_budget-selected_model_spend):.4f} · بعد الطلب المتوقع: ${selected_model_spend+projected_cost:.4f}")
            approval = st.checkbox("أوافق على إرسال هذه الحزمة إلى المزود والنموذج المحددين، بعد مراجعة التكلفة المعروضة.", key=f"router_approval_{active_pkg['id']}_{provider_id}_{model}")
            if not IS_ADMIN:
                st.warning("إرسال الحزم للنماذج متاح لحساب المالك فقط، لحماية مفاتيح API ومنع استهلاك الحصة من حسابات الضيوف.")
            if provider_id in ("openrouter_free", "groq", "cloudflare") or (provider_id == "gemini" and gemini_mode == "خطة مجانية مؤكدة") or (provider_id == "custom_openai" and custom_billing == "مجاني مؤكد"):
                st.caption("تجنب إرسال بيانات شخصية أو سرية إلى مزود خارجي، وراجع شروط الخصوصية لكل مزود.")

            if st.button("📨 إرسال الحزمة للنموذج الآن", type="primary", disabled=(not can_send or not approval or projected_cost is None), key=f"send_ai_package_{active_pkg['id']}", use_container_width=True):
                try:
                    estimated_input = projected_input_tokens
                    if paid_mode and not ai_billing_mod.preflight(selected_model_spend, projected_cost, monthly_budget)["allowed"]:
                        st.error(f"تم منع الطلب: التقدير المعروض ${projected_cost:.5f} يتجاوز المتبقي من سقف هذا النموذج ${max(0, monthly_budget-selected_model_spend):.5f}.")
                        st.stop()
                    reservation_id = f"ai_{uuid.uuid4().hex}"
                    if paid_mode:
                        ai_billing_mod.reserve(S().setdefault("ai_settings", {}), provider_id, model,
                            month_key, projected_cost, reservation_id)
                        if PERSIST and not persist():
                            ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), reservation_id, status="released")
                            raise RuntimeError("لم نتمكن من حفظ حجز الإنفاق في التخزين الدائم؛ تم إيقاف الطلب قبل الاتصال بالمزود")
                        if paid_mode:
                            merged_guard = ai_billing_mod.budget_preflight(S().get("ai_usage", []), S().get("ai_settings", {}), month_key, provider_id, model, 0.0, monthly_budget)
                            if not merged_guard["allowed"]:
                                ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), reservation_id, status="released")
                                persist()
                                raise RuntimeError("تجاوزت الحجوزات المدمجة سقف النموذج؛ تم إيقاف الطلب قبل الاتصال بالمزود")
                    with st.spinner(f"جارٍ إرسال الحزمة إلى {provider_label}..."):
                        result = ai_providers_mod.call_model(provider_id, model, task_prompt, api_key=api_key,
                            account_id=account_id, base_url=base_url, max_output_tokens=max_output)
                    usage = result.get("usage", {})
                    if (provider_id == "gemini" and gemini_mode == "خطة مدفوعة") or (provider_id == "custom_openai" and custom_billing == "مدفوع بسقف إنفاق"):
                        actual_cost = ai_providers_mod.estimate_cost(usage.get("input_tokens"), usage.get("output_tokens"), input_price, output_price)
                        if actual_cost is None:
                            actual_cost = ai_providers_mod.estimate_cost(estimated_input, max_output, input_price, output_price)
                    else:
                        actual_cost = 0.0
                    if paid_mode:
                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), reservation_id, actual_cost, "settled")
                    log = {"id": f"usage_{int(time.time()*1000)}", "month": month_key, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "provider": provider_id, "model": result.get("model", model), "case_id": case.get("id"), "package_id": active_pkg.get("id"),
                        "task": task_type, "prompt_chars": len(task_prompt), "estimated_cost_usd": projected_cost,
                        "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                        "total_tokens": usage.get("total_tokens"), "cost_usd": actual_cost, "billing_mode": (gemini_mode or custom_billing) if provider_id in ("gemini", "custom_openai") else ("free_confirmed" if free_confirmed else "local")}
                    S().setdefault("ai_usage", []).insert(0, log)
                    S()["ai_usage"] = S()["ai_usage"][:500]
                    saved_result = {"id": log["id"], "case_id": case.get("id"), "package_id": active_pkg.get("id"),
                        "provider": provider_id, "model": result.get("model", model), "created_at": log["created_at"],
                        "task": task_type, "text": result.get("text", ""), "usage": usage, "cost_usd": actual_cost}
                    S().setdefault("ai_results", []).insert(0, saved_result)
                    S()["ai_results"] = S()["ai_results"][:100]
                    persist()
                    st.session_state[f"ai_last_result_{case['id']}"] = saved_result
                    st.success("وصل رد النموذج واتحفظ في سجل التحليلات. راجع حدود الثقة والمصادر قبل اعتماد أي استنتاج.")
                    st.rerun()
                except Exception as exc:
                    if "reservation_id" in locals() and paid_mode:
                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), reservation_id, status="failed")
                        persist()
                    st.error(f"تعذر تنفيذ الطلب: {type(exc).__name__}: {str(exc)[:500]}")

            last_result = st.session_state.get(f"ai_last_result_{case['id']}")
            if last_result and last_result.get("package_id") == active_pkg.get("id"):
                st.markdown("##### 🧠 نتيجة التحليل")
                st.caption(f"{last_result.get('provider')} · {last_result.get('model')} · {last_result.get('usage', {}).get('total_tokens') or 'توكنز غير متاحة'} توكن · التكلفة المسجلة ${float(last_result.get('cost_usd') or 0):.4f}")
                st.text_area("مخرجات النموذج", value=last_result.get("text", ""), height=420, key=f"ai_result_text_{last_result['id']}")
                st.download_button("⬇️ تنزيل نتيجة التحليل TXT", last_result.get("text", ""), file_name=f"marsad_ai_result_{active_pkg.get('version')}.txt", mime="text/plain", key=f"ai_result_download_{last_result['id']}")

            # استرجاع النتائج المحفوظة من التخزين الدائم، حتى بعد فتح جلسة جديدة.
            saved_case_results = [x for x in S().get("ai_results", [])
                                  if x.get("case_id") == case.get("id")]
            if saved_case_results:
                st.markdown("##### 🗂️ أرشيف نتائج التحليل المحفوظة")
                result_labels = {
                    f"{x.get('created_at', '')[:16]} · {x.get('provider', '')} · {x.get('model', '')} · {(x.get('package_id') or '')[-8:]} · {(x.get('id') or '')[-6:]}": x
                    for x in saved_case_results
                }
                selected_result_label = st.selectbox(
                    "استرجاع نتيجة سابقة من هذه القضية",
                    list(result_labels),
                    key=f"ai_saved_result_select_{case['id']}"
                )
                selected_result = result_labels[selected_result_label]
                selected_usage = selected_result.get("usage") or {}
                st.caption(
                    f"{selected_result.get('provider', '')} · {selected_result.get('model', '')} · "
                    f"{selected_usage.get('total_tokens') or 'توكنز غير متاحة'} توكن · "
                    f"التكلفة التقديرية ${float(selected_result.get('cost_usd') or 0):.4f}"
                )
                st.text_area(
                    "النص المحفوظ",
                    value=selected_result.get("text", ""),
                    height=360,
                    key=f"ai_saved_result_text_{selected_result.get('id', 'unknown')}"
                )
                st.download_button(
                    "⬇️ تنزيل النتيجة المحفوظة",
                    selected_result.get("text", ""),
                    file_name=f"marsad_saved_analysis_{selected_result.get('id', 'result')}.txt",
                    mime="text/plain",
                    key=f"ai_saved_result_download_{selected_result.get('id', 'unknown')}"
                )

            # استوديو الإنتاج: يحول نتيجة محفوظة إلى تكليف تحريري مستقل قابل للإرسال أو النسخ.
            if saved_case_results:
                st.divider()
                st.markdown("##### 🎬 استوديو إنتاج المحتوى")
                st.caption("اختار نتيجة تحليل محفوظة، وجهّز لها تكليف إنتاج متعدد المنصات. تجهيز التكليف لا يرسل طلباً جديداً ولا يستهلك توكنز.")
                production_labels = {
                    f"{x.get('created_at', '')[:16]} · {x.get('provider', '')} · {(x.get('id') or '')[-8:]}": x
                    for x in saved_case_results if x.get("text")
                }
                if production_labels:
                    production_label = st.selectbox("نتيجة التحليل التي هنبني عليها المحتوى", list(production_labels), key=f"content_source_{case['id']}")
                    production_result = production_labels[production_label]
                    with st.form(f"content_factory_form_{case['id']}"):
                        c1, c2 = st.columns(2)
                        content_type = c1.selectbox("نوع الإنتاج", list(content_factory_mod.OUTPUTS), key=f"content_type_{case['id']}")
                        content_audience = c2.selectbox("الجمهور", ["الجمهور العام", "متابع مهتم بالسياسة", "صانع محتوى متخصص"], key=f"content_audience_{case['id']}")
                        c3, c4 = st.columns(2)
                        content_platform = c3.selectbox("المنصات", ["فيسبوك ويوتيوب وتيك توك", "فيسبوك Reels", "YouTube Shorts", "TikTok", "يوتيوب فيديو طويل"], key=f"content_platform_{case['id']}")
                        content_duration = c4.selectbox("مدة الفيديو الرئيسي", ["60 إلى 90 ثانية", "3 إلى 5 دقائق", "8 إلى 12 دقيقة"], index=1, key=f"content_duration_{case['id']}")
                        content_dialect = st.selectbox("أسلوب اللغة", ["عامية مصرية مبسطة", "عامية قاهرية حوارية", "عربية مبسطة"], key=f"content_dialect_{case['id']}")
                        make_content_job = st.form_submit_button("🧰 تجهيز غرفة الإنتاج وحفظ التكليف", type="primary", use_container_width=True)
                    if make_content_job:
                        job = content_factory_mod.create_job(case.get("id"), case.get("title"), production_result.get("id"),
                            production_result.get("text", ""), content_type, content_audience, content_dialect, content_duration, content_platform)
                        S().setdefault("content_jobs", []).insert(0, job)
                        S()["content_jobs"] = S()["content_jobs"][:100]
                        persist()
                        st.session_state[f"active_content_job_{case['id']}"] = job["id"]
                        st.success("تم تجهيز تكليف الإنتاج وحفظه. لم يتم إرسال أي طلب إلى نموذج ذكاء اصطناعي.")
                    case_jobs = [x for x in S().get("content_jobs", []) if x.get("case_id") == case.get("id")]
                    if case_jobs:
                        job_labels = {f"{x.get('created_at', '')[:16]} · {x.get('output_type', '')} · {x.get('platform', '')}": x for x in case_jobs}
                        active_job_id = st.session_state.get(f"active_content_job_{case['id']}")
                        default_job_label = next((k for k, v in job_labels.items() if v.get("id") == active_job_id), next(iter(job_labels)))
                        active_job = job_labels[st.selectbox("تكليفات الإنتاج المحفوظة", list(job_labels), index=list(job_labels).index(default_job_label), key=f"content_job_select_{case['id']}")]
                        st.caption(f"بصمة التكليف SHA-256: {active_job.get('sha256', '')[:20]}… · المصدر: {(active_job.get('result_id') or '')[-10:]}")
                        st.text_area("تكليف جاهز للإرسال إلى النموذج", value=active_job.get("prompt", ""), height=360, key=f"content_job_prompt_{active_job['id']}")
                        d1, d2 = st.columns(2)
                        d1.download_button("⬇️ تنزيل تكليف الإنتاج TXT", active_job.get("prompt", ""), file_name=f"marsad_content_{active_job['id']}.txt", mime="text/plain", key=f"content_job_txt_{active_job['id']}", use_container_width=True)
                        d2.download_button("⬇️ تنزيل بيانات التكليف JSON", content_factory_mod.render_json(active_job), file_name=f"marsad_content_{active_job['id']}.json", mime="application/json", key=f"content_job_json_{active_job['id']}", use_container_width=True)
                        st.caption("يمكن تشغيل التكليف على نفس مزود الذكاء الاصطناعي المختار بالأعلى. هذا طلب مستقل عن تحليل القضية، ولذلك له تقدير وموافقة منفصلان.")
                        content_prompt = active_job.get("prompt", "")
                        estimated_content_input = ai_router_mod.estimate_input_tokens(content_prompt)
                        content_paid_mode = ((provider_id == "gemini" and gemini_mode == "خطة مدفوعة") or
                                             (provider_id == "custom_openai" and custom_billing == "مدفوع بسقف إنفاق"))
                        projected_content_cost = ai_providers_mod.estimate_cost(estimated_content_input, max_output, input_price, output_price) if content_paid_mode else (0.0 if free_confirmed or provider_id == "ollama" else None)
                        pc1, pc2, pc3 = st.columns(3)
                        pc1.metric("توكنز الإدخال المتوقعة", f"~{estimated_content_input:,}")
                        pc2.metric("حد الإخراج", f"{max_output:,}")
                        pc3.metric("تكلفة الطلب", f"${projected_content_cost:.5f}" if projected_content_cost is not None else "غير معروفة")
                        if projected_content_cost is not None:
                            st.caption("التكلفة تقديرية، وليست فاتورة نهائية. الطلب المدفوع سيُمنع إذا تخطى سقف المزود.")
                        else:
                            st.warning("لا يمكن تأكيد تكلفة طلب إنتاج المحتوى. لن يتم تفعيله قبل تحديد مسار فوترة واضح.")
                        content_approval = st.checkbox("أوافق على إرسال تكليف الإنتاج هذا بشكل مستقل بعد مراجعة تكلفته.", key=f"content_approval_{active_job['id']}_{provider_id}_{model}")
                        if st.button("🚀 إنتاج المحتوى الآن باستخدام النموذج المختار", type="primary", disabled=(not can_send or not content_approval or projected_content_cost is None), key=f"run_content_job_{active_job['id']}", use_container_width=True):
                            try:
                                if content_paid_mode and selected_model_spend + projected_content_cost > monthly_budget:
                                    st.error(f"تم منع الطلب: التقدير ${projected_content_cost:.4f} يتجاوز المتبقي من سقف هذا المزود ${max(0, monthly_budget-selected_provider_spend):.4f}.")
                                    st.stop()
                                content_reservation_id = f"content_{uuid.uuid4().hex}"
                                if content_paid_mode:
                                    ai_billing_mod.reserve(S().setdefault("ai_settings", {}), provider_id, model,
                                        month_key, projected_content_cost, content_reservation_id)
                                    if PERSIST and not persist():
                                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), content_reservation_id, status="released")
                                        raise RuntimeError("تعذر حفظ حجز الإنفاق؛ أوقفنا طلب إنتاج المحتوى قبل الاتصال بالمزود")
                                    merged_guard = ai_billing_mod.budget_preflight(S().get("ai_usage", []), S().get("ai_settings", {}), month_key, provider_id, model, 0.0, monthly_budget)
                                    if not merged_guard["allowed"]:
                                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), content_reservation_id, status="released")
                                        persist()
                                        raise RuntimeError("تجاوزت الحجوزات المدمجة سقف النموذج؛ أوقفنا طلب الإنتاج قبل الاتصال بالمزود")
                                with st.spinner(f"جارٍ إنتاج المحتوى عبر {provider_label}..."):
                                    content_response = ai_providers_mod.call_model(provider_id, model, content_prompt, api_key=api_key,
                                        account_id=account_id, base_url=base_url, max_output_tokens=max_output)
                                content_usage = content_response.get("usage", {})
                                if (provider_id == "gemini" and gemini_mode == "خطة مدفوعة") or (provider_id == "custom_openai" and custom_billing == "مدفوع بسقف إنفاق"):
                                    content_cost = ai_providers_mod.estimate_cost(content_usage.get("input_tokens"), content_usage.get("output_tokens"), input_price, output_price)
                                    if content_cost is None:
                                        content_cost = ai_providers_mod.estimate_cost(estimated_content_input, max_output, input_price, output_price)
                                else:
                                    content_cost = 0.0
                                if content_paid_mode:
                                    ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), content_reservation_id, content_cost, "settled")
                                content_log = {"id": f"content_usage_{int(time.time()*1000)}", "month": month_key,
                                    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "provider": provider_id,
                                    "model": content_response.get("model", model), "case_id": case.get("id"),
                                    "content_job_id": active_job.get("id"), "input_tokens": content_usage.get("input_tokens"),
                                    "output_tokens": content_usage.get("output_tokens"), "total_tokens": content_usage.get("total_tokens"),
                                    "cost_usd": content_cost, "billing_mode": (gemini_mode or custom_billing) if provider_id in ("gemini", "custom_openai") else ("free_confirmed" if free_confirmed else "local"),
                                    "task": "content_generation"}
                                S().setdefault("ai_usage", []).insert(0, content_log)
                                S()["ai_usage"] = S()["ai_usage"][:500]
                                content_saved = {"id": content_log["id"], "case_id": case.get("id"), "content_job_id": active_job.get("id"),
                                    "provider": provider_id, "model": content_response.get("model", model), "created_at": content_log["created_at"],
                                    "text": content_response.get("text", ""), "usage": content_usage, "cost_usd": content_cost}
                                S().setdefault("content_results", []).insert(0, content_saved)
                                S()["content_results"] = S()["content_results"][:100]
                                persist()
                                st.success("تم إنتاج المحتوى وحفظه في الأرشيف الدائم.")
                                st.rerun()
                            except Exception as exc:
                                if "content_reservation_id" in locals() and content_paid_mode:
                                    ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), content_reservation_id, status="failed")
                                    persist()
                                st.error(f"تعذر إنتاج المحتوى: {type(exc).__name__}: {str(exc)[:500]}")
                        job_results = [x for x in S().get("content_results", []) if x.get("content_job_id") == active_job.get("id")]
                        if job_results:
                            latest_content = job_results[0]
                            st.markdown("###### 📝 المخرجات المنتجة")
                            st.caption(f"{latest_content.get('provider')} · {latest_content.get('model')} · {latest_content.get('usage', {}).get('total_tokens') or 'توكنز غير متاحة'} توكن · التكلفة المسجلة ${float(latest_content.get('cost_usd') or 0):.4f}")
                            st.text_area("المحتوى الجاهز للمراجعة", value=latest_content.get("text", ""), height=480, key=f"content_result_text_{latest_content['id']}")
                            st.download_button("⬇️ تنزيل المحتوى المنتج TXT", latest_content.get("text", ""), file_name=f"marsad_content_output_{latest_content['id']}.txt", mime="text/plain", key=f"content_result_download_{latest_content['id']}")

                            # استوديو توليد الصور الفعلي: الصور تحفظ في الجلسة وتدخل حزمة ZIP عند تنزيلها.
                            st.divider()
                            st.markdown("###### 🖼️ استوديو توليد صور المشاهد")
                            st.caption("توليد فعلي عبر OpenAI Images API. كل صورة ترتبط بمعرّف مشهد، ويمكن معاينتها وتنزيلها وإعادة توليد نسخة أخرى. الصور لا تُحفظ في Gist حتى لا يتحول مخزن البيانات إلى مستودع ملفات ضخم؛ نزّل حزمة الإنتاج للاحتفاظ الدائم بها. استخدام API وفوترته منفصلان عن اشتراك ChatGPT، وقد يتطلب تفعيل نماذج الصور تحققاً لحساب المؤسسة.")
                            image_key = f"marsad_generated_images_{active_job['id']}"
                            generated_images = st.session_state.setdefault(image_key, [])
                            openai_image_key = _secret("OPENAI_API_KEY")
                            if not openai_image_key:
                                openai_image_key = st.text_input("مفتاح OpenAI API لتوليد الصور (لن يُحفظ في الأرشيف)", type="password", key=f"image_api_key_{active_job['id']}")
                                st.caption("الأفضل إضافته في Streamlit Secrets باسم OPENAI_API_KEY. مفتاح النماذج النصية الحالي لا يُستخدم تلقائياً هنا.")
                            image_model = st.selectbox("نموذج الصور", image_generation_mod.MODELS, index=0,
                                key=f"image_model_{active_job['id']}")
                            if image_model == "gpt-image-1.5":
                                st.warning("نموذج GPT Image 1.5 مقرر إيقافه في 1 ديسمبر 2026. يفضّل استخدام GPT Image 2.6 أو 2.5.")
                            image_sizes = image_generation_mod.sizes_for_model(image_model)
                            default_size_label = "رأسي 9:16" if "رأسي 9:16" in image_sizes else "رأسي 2:3"
                            image_size_label = st.selectbox("نسبة وأبعاد الصورة", list(image_sizes),
                                index=list(image_sizes).index(default_size_label), key=f"image_size_{active_job['id']}")
                            image_quality = st.selectbox("الجودة", image_generation_mod.QUALITIES, index=1, key=f"image_quality_{active_job['id']}")
                            st.markdown("**مراجعة تكلفة الصورة قبل التوليد**")
                            st.caption("أسعار الصور تختلف حسب النموذج والجودة والمقاس وقد تتغير. لن نخمن سعراً من عندنا.")
                            image_unit_price = st.number_input("السعر الرسمي للصورة الواحدة بالدولار", min_value=0.0, value=0.0, step=0.01, key=f"image_unit_price_{active_job['id']}")
                            image_price_reviewed = st.checkbox("راجعت السعر الرسمي الحالي لهذا النموذج والجودة والمقاس.", key=f"image_price_review_{active_job['id']}")
                            image_monthly_budget = st.number_input("سقف إنفاق الصور الشهري بالدولار", min_value=0.0, value=0.0, step=1.0, key=f"image_monthly_budget_{active_job['id']}")
                            image_month_spend = ai_billing_mod.month_spend(S().get("ai_usage", []), month_key, "openai_images", image_model)
                            image_budget_check = ai_billing_mod.budget_preflight(S().get("ai_usage", []), S().get("ai_settings", {}), month_key, "openai_images", image_model, image_unit_price, image_monthly_budget)
                            st.metric("التكلفة المتوقعة لهذه الصورة", f"${image_unit_price:.4f}" if image_unit_price > 0 and image_price_reviewed else "غير محددة")
                            if image_monthly_budget > 0:
                                st.caption(f"إنفاق الصور المسجل: ${image_month_spend:.4f} · حجوزات نشطة: ${image_budget_check['reserved_usd']:.4f} · المتبقي قبل الطلب: ${max(0, image_monthly_budget-image_budget_check['committed_usd']-image_budget_check['reserved_usd']):.4f}")
                            else:
                                st.warning("أدخل سقفاً شهرياً للصور. لا يمكن تنفيذ توليد مدفوع دون سقف محدد.")
                            with st.form(f"image_generation_form_{active_job['id']}"):
                                scene_id = st.text_input("معرّف المشهد", value="SH001", help="مثال: SH001 أو SH002")
                                image_prompt = st.text_area("البرومبت البصري للمشهد", height=150,
                                    placeholder="اكتب وصفاً بصرياً واضحاً. لا تطلب كتابة عناوين أو نصوص داخل الصورة.",
                                    help="استخدم برومبت المشهد من مخرجات استوديو الإخراج البصري، مع وصف اللقطة والإضاءة والتكوين.")
                                image_approval = st.checkbox("أوافق على تكلفة توليد صورة واحدة الموضحة أعلاه.", key=f"image_approval_{active_job['id']}")
                                generate_scene_image = st.form_submit_button("🎨 توليد الصورة الآن", type="primary", disabled=not (image_unit_price > 0 and image_price_reviewed and image_monthly_budget > 0 and image_budget_check["allowed"] and image_approval), use_container_width=True)
                            if generate_scene_image:
                                try:
                                    if not openai_image_key:
                                        raise ValueError("أضف OPENAI_API_KEY في Secrets أو أدخل المفتاح للجلسة الحالية")
                                    if not image_budget_check["allowed"]:
                                        raise RuntimeError("تم منع التوليد: الطلب يتجاوز سقف الصور الشهري بعد احتساب الإنفاق والحجوزات النشطة")
                                    image_reservation_id = f"image_{uuid.uuid4().hex}"
                                    ai_billing_mod.reserve(S().setdefault("ai_settings", {}), "openai_images", image_model,
                                        month_key, image_unit_price, image_reservation_id)
                                    if PERSIST and not persist():
                                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), image_reservation_id, status="released")
                                        raise RuntimeError("تعذر حفظ حجز تكلفة الصورة؛ تم إيقاف التوليد قبل الاتصال بالمزود")
                                    merged_guard = ai_billing_mod.budget_preflight(S().get("ai_usage", []), S().get("ai_settings", {}), month_key, "openai_images", image_model, 0.0, image_monthly_budget)
                                    if not merged_guard["allowed"]:
                                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), image_reservation_id, status="released")
                                        persist()
                                        raise RuntimeError("تجاوزت حجوزات الصور المدمجة سقف الشهر؛ تم إيقاف التوليد قبل الاتصال بالمزود")
                                    normalized_scene = re.sub(r"[^A-Za-z0-9_-]+", "_", (scene_id or "SH001").strip()).strip("_")[:24] or "SH001"
                                    with st.spinner("جاري توليد الصورة. قد تستغرق العملية حتى دقيقتين..."):
                                        image_response = image_generation_mod.generate_image(
                                            image_prompt, openai_image_key, model=image_model,
                                            size=image_sizes[image_size_label], quality=image_quality)
                                    scene_versions = [x for x in generated_images if x.get("scene_id") == normalized_scene]
                                    version = len(scene_versions) + 1
                                    image_record = {
                                        "id": f"{normalized_scene}_{version}_{int(time.time())}",
                                        "scene_id": normalized_scene, "version": version,
                                        "filename": f"{normalized_scene}_v{version:02d}.png",
                                        "prompt": image_prompt, "provider": "openai",
                                        "model": image_response["model"], "size": image_response["size"],
                                        "quality": image_response["quality"], "request_id": image_response.get("request_id", ""),
                                        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                        "image_bytes": image_response["image_bytes"],
                                    }
                                    generated_images.append(image_record)
                                    ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), image_reservation_id, image_unit_price, "settled")
                                    image_log = {"id": f"image_usage_{int(time.time()*1000)}", "month": month_key,
                                        "created_at": image_record["created_at"], "provider": "openai_images", "model": image_model,
                                        "case_id": case.get("id"), "content_job_id": active_job.get("id"),
                                        "task": "image_generation", "input_tokens": None, "output_tokens": None,
                                        "total_tokens": None, "cost_usd": float(image_unit_price),
                                        "estimated_cost_usd": float(image_unit_price), "billing_mode": "user_price_confirmed",
                                        "size": image_sizes[image_size_label], "quality": image_quality}
                                    S().setdefault("ai_usage", []).insert(0, image_log)
                                    S()["ai_usage"] = S()["ai_usage"][:500]
                                    persist()
                                    st.success(f"تم توليد {normalized_scene} بنجاح. النسخة رقم {version} جاهزة للمعاينة، وتم تسجيل التكلفة التي أدخلتها.")
                                except Exception as image_exc:
                                    if "image_reservation_id" in locals():
                                        ai_billing_mod.finish_reservation(S().setdefault("ai_settings", {}), image_reservation_id, status="failed")
                                        persist()
                                    st.error(f"تعذر توليد الصورة: {type(image_exc).__name__}: {str(image_exc)[:450]}")
                            if generated_images:
                                st.markdown(f"**الصور الجاهزة في هذه الجلسة: {len(generated_images)}**")
                                for image_record in reversed(generated_images):
                                    with st.container(border=True):
                                        st.markdown(f"**{image_record['scene_id']} · النسخة {image_record['version']}**")
                                        st.image(image_record["image_bytes"], use_container_width=True)
                                        st.caption(f"{image_record['model']} · {image_record['size']} · {image_record['quality']} · {image_record.get('created_at', '')}")
                                        st.text_area("البرومبت المستخدم", value=image_record.get("prompt", ""), height=75,
                                            key=f"image_prompt_view_{image_record['id']}", disabled=True)
                                        idownload, idelete = st.columns(2)
                                        idownload.download_button("⬇️ تنزيل الصورة PNG", image_record["image_bytes"],
                                            file_name=image_record["filename"], mime="image/png", key=f"image_download_{image_record['id']}", use_container_width=True)
                                        if idelete.button("حذف من الجلسة", key=f"image_delete_{image_record['id']}", use_container_width=True):
                                            generated_images[:] = [x for x in generated_images if x.get("id") != image_record["id"]]
                                            st.rerun()
                            try:
                                production_zip = production_bundle_mod.build_production_bundle(active_job, latest_content, generated_images)
                                st.download_button("📦 تنزيل حزمة الإنتاج الكاملة ZIP", production_zip,
                                    file_name=f"marsad_production_{active_job['id']}.zip", mime="application/zip",
                                    key=f"content_bundle_download_{latest_content['id']}", use_container_width=True)
                                st.caption(f"الحزمة تجمع النص ولوحة المشاهد والبرومبتات وسجل الأصول وقالب المونتاج، وتضم {len(generated_images)} صورة مولدة من الجلسة الحالية إن وجدت. الفيديوهات غير مولدة داخل التطبيق حتى الآن.")
                            except Exception as bundle_exc:
                                st.warning(f"تعذر تجهيز حزمة الإنتاج: {type(bundle_exc).__name__}: {str(bundle_exc)[:250]}")

    with st.expander("🧹 حذف الملف البحثي بالكامل", expanded=False):
        st.warning("سيؤدي ذلك إلى حذف سجل هذا الملف ومواده وادعاءاته وأحداثه من التخزين الدائم.")
        if st.button("حذف هذا الملف", key=f"delete_research_case_{case['id']}"):
            S()["research_cases"] = [x for x in cases if x.get("id") != case.get("id")]
            S()["case_links"] = [x for x in S().get("case_links", [])
                                 if case.get("id") not in {x.get("case_a"), x.get("case_b")}]
            S()["intel_case_files"] = [x for x in S().get("intel_case_files", [])
                                       if x.get("case_id") != case.get("id")]
            S()["research_batches"] = [x for x in S().get("research_batches", [])
                                       if x.get("case_id") != case.get("id")]
            S()["video_projects"] = [x for x in S().get("video_projects", [])
                                      if x.get("case_id") != case.get("id")]
            persist(); st.session_state.pop("research_case_active", None); st.success("تم حذف الملف وروابطه."); st.rerun()



def render_case_relationship_center(cases):
    """اقتراح ومراجعة الروابط بين الملفات البحثية مع إظهار أسباب كل رابط."""
    st.markdown("#### 🕸️ شبكة العلاقات بين الملفات")
    st.caption("يبحث عن كيانات ووسوم ومفردات مشتركة بين ملفاتك. كل نتيجة اقتراح قابل للمراجعة، وليست إثباتاً لعلاقة سببية أو تنسيق بين الأطراف.")
    saved_links = S().setdefault("case_links", [])
    accepted = [x for x in saved_links if x.get("status") == "accepted"]
    suggested = [x for x in saved_links if x.get("status") == "suggested"]
    rejected = [x for x in saved_links if x.get("status") == "rejected"]
    a, b, c = st.columns(3)
    a.metric("روابط معتمدة", len(accepted))
    b.metric("اقتراحات للمراجعة", len(suggested))
    c.metric("مرفوضة", len(rejected))
    controls = st.columns([3, 1])
    threshold = pick(controls[0], "حساسية اكتشاف التقاطعات", [12, 18, 25, 35, 45], 18, "case_link_threshold",
        fmt=lambda x: {12: "مرتفعة جداً", 18: "مرتفعة", 25: "متوازنة", 35: "متحفظة", 45: "صارمة"}[x])
    if controls[1].button("🔍 حلّل التقاطعات", type="primary", use_container_width=True, key="run_case_link_scan"):
        fresh = case_links_mod.suggest_links(cases, min_score=threshold)
        S()["case_links"] = case_links_mod.merge_suggestions(saved_links, fresh)
        persist()
        st.success(f"انتهى الفحص. تم تحديث {len(fresh)} اقتراحاً.")
        st.rerun()

    # إنشاء رابط يدوي مفيد عندما يعرف الباحث صلة لا تلتقطها الكلمات.
    with st.expander("➕ اربط ملفين يدوياً", expanded=False):
        labels = {f"{x.get('title', 'ملف')} · {len(x.get('materials', []))} مادة · {x.get('id', '')[-6:]}": x for x in cases}
        with st.form("manual_case_link_form"):
            left = st.selectbox("الملف الأول", list(labels), key="manual_case_link_a")
            right = st.selectbox("الملف الثاني", list(labels), index=min(1, len(labels)-1), key="manual_case_link_b")
            note = st.text_area("سبب الربط أو الفرضية التي تريد اختبارها", height=70)
            submit = st.form_submit_button("حفظ العلاقة")
        if submit:
            try:
                rec = case_links_mod.create_manual_link(labels[left], labels[right], note)
                existing = S().setdefault("case_links", [])
                key = {rec["case_a"], rec["case_b"]}
                existing[:] = [x for x in existing if {x.get("case_a"), x.get("case_b")} != key]
                existing.append(rec)
                persist(); st.success("تم حفظ العلاقة اليدوية."); st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

    links = S().get("case_links", [])
    accepted = [x for x in links if x.get("status") == "accepted"]
    suggested = [x for x in links if x.get("status") == "suggested"]
    show_suggestions = st.checkbox("إظهار الاقتراحات غير المعتمدة على الرسم", value=False, key="case_graph_suggestions")
    graph = case_links_mod.graph_data(cases, links, include_suggested=show_suggestions)
    if graph["edges"]:
        def _dot_escape(value):
            return str(value or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        dot = ["graph Marsad {", "rankdir=LR;", "overlap=false;", "splines=true;", "node [shape=box, style=rounded];"]
        for node in graph["nodes"]:
            dot.append(f'"{_dot_escape(node["id"])}" [label="{_dot_escape(node["label"])}\n{node["materials"]} مادة"];')
        for edge in graph["edges"]:
            style = "dashed" if edge.get("status") == "suggested" else "solid"
            dot.append(f'"{_dot_escape(edge["source"])}" -- "{_dot_escape(edge["target"])}" [label="{_dot_escape(edge["label"])}", style={style}];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
    if accepted or suggested:
        prompt_link_options = {f"{x.get('title_a')} ↔ {x.get('title_b')} · {x.get('id')[-8:]}": x for x in accepted + suggested}
        chosen_link_label = st.selectbox("جهّز برومبت لفحص علاقة بين ملفين", list(prompt_link_options), key="case_link_prompt_select")
        if st.button("🧠 إنشاء برومبت فحص العلاقة", key="build_case_link_prompt", use_container_width=True):
            selected_link = prompt_link_options[chosen_link_label]
            by_id = {x.get("id"): x for x in cases}
            st.session_state["case_link_prompt"] = case_links_mod.build_link_prompt(
                by_id.get(selected_link.get("case_a"), {}), by_id.get(selected_link.get("case_b"), {}), selected_link)
        if st.session_state.get("case_link_prompt"):
            st.text_area("برومبت فحص العلاقة بين الملفين", value=st.session_state["case_link_prompt"], height=300, key="case_link_prompt_display")
            st.download_button("⬇️ تنزيل برومبت فحص العلاقة", data=st.session_state["case_link_prompt"],
                file_name="marsad_case_link_analysis.txt", mime="text/plain", key="download_case_link_prompt")
    if accepted:
        with st.expander(f"🧩 شبكة الروابط المعتمدة ({len(accepted)})", expanded=True):
            for link in accepted:
                st.markdown(f"**{link.get('title_a')}**  ↔  **{link.get('title_b')}**")
                st.caption(f"قوة التشابه الإرشادية: {link.get('level')} · الدرجة {link.get('score')}/100")
                if link.get("user_note"):
                    st.write("ملاحظة الباحث: " + link["user_note"])
                for reason in link.get("reasons", []):
                    st.write("• " + reason)
                if link.get("evidence_examples"):
                    with st.container(border=True):
                        for ex in link["evidence_examples"]:
                            st.markdown(f"**{ex.get('entity')}**")
                            st.write("الملف الأول: " + ("؛ ".join(ex.get("case_a_materials", [])) or "لا توجد مادة بعنوان مطابق"))
                            st.write("الملف الثاني: " + ("؛ ".join(ex.get("case_b_materials", [])) or "لا توجد مادة بعنوان مطابق"))
                st.caption(link.get("caveat", ""))
                if st.button("إلغاء اعتماد الرابط", key=f"unlink_case_{link.get('id')}"):
                    case_links_mod.set_status(S()["case_links"], link.get("id"), "suggested")
                    persist(); st.rerun()
                st.divider()
    if suggested:
        with st.expander(f"💡 اقتراحات الربط للمراجعة ({len(suggested)})", expanded=True):
            for link in suggested[:30]:
                st.markdown(f"**{link.get('title_a')}**  ↔  **{link.get('title_b')}**")
                st.caption(f"التشابه: {link.get('level')} · الدرجة الإرشادية {link.get('score')}/100")
                for reason in link.get("reasons", []):
                    st.write("• " + reason)
                if link.get("evidence_examples"):
                    with st.container(border=True):
                        for ex in link["evidence_examples"]:
                            st.markdown(f"**{ex.get('entity')}**")
                            st.write("الملف الأول: " + ("؛ ".join(ex.get("case_a_materials", [])) or "لا توجد مادة بعنوان مطابق"))
                            st.write("الملف الثاني: " + ("؛ ".join(ex.get("case_b_materials", [])) or "لا توجد مادة بعنوان مطابق"))
                st.caption(link.get("caveat", ""))
                x1, x2 = st.columns(2)
                if x1.button("اعتماد العلاقة", key=f"accept_case_link_{link.get('id')}", use_container_width=True):
                    case_links_mod.set_status(S()["case_links"], link.get("id"), "accepted")
                    persist(); st.rerun()
                if x2.button("رفض الاقتراح", key=f"reject_case_link_{link.get('id')}", use_container_width=True):
                    case_links_mod.set_status(S()["case_links"], link.get("id"), "rejected")
                    persist(); st.rerun()
                st.divider()
    if not accepted and not suggested:
        st.info("لم تُحلل العلاقات بعد. اضغط «حلّل التقاطعات» لاكتشاف الروابط المحتملة بين ملفاتك.")

    render_early_warning_center()
    render_stance_scenario_center(case)


def render_stance_scenario_center(case):
    """مقارنة المواقف وبناء سيناريوهات داخل الملف البحثي نفسه."""
    st.divider()
    st.markdown("### 🧭 محلل تحولات المواقف والسيناريوهات")
    st.caption("يعتمد على المواقف التي أدخلها الباحث في كل مادة. لا يستنتج موقفاً تلقائياً من العنوان ولا يحوّل الاختلاف وحده إلى تحول سياسي.")
    comparisons = stance_scenarios_mod.compare_stances(case)
    if comparisons:
        st.markdown("#### مقارنة المواقف عبر الزمن")
        for item in comparisons:
            with st.expander(f"{item['actor']} · {'اختلاف يحتاج فحصاً' if item['changed'] else 'لا اختلاف ظاهر'}", expanded=item["changed"]):
                a, b = st.columns(2)
                a.markdown("**أقدم موقف مدخل**")
                a.write(item["first"]["date"] + " · " + item["first"]["stance"])
                a.caption(item["first"]["title"])
                b.markdown("**أحدث موقف مدخل**")
                b.write(item["latest"]["date"] + " · " + item["latest"]["stance"])
                b.caption(item["latest"]["title"])
                for entry, col in ((item["first"], a), (item["latest"], b)):
                    if entry.get("url"):
                        col.markdown(f"[المصدر الأصلي]({entry['url']})")
                st.caption("ملاحظة آلية: " + item["assessment"] + "، وليست حكماً بأن الموقف تغير فعلاً.")
        compare_prompt = stance_scenarios_mod.build_comparison_prompt(case, comparisons)
        st.download_button("⬇️ تنزيل برومبت فحص تحولات المواقف", compare_prompt, file_name="marsad_stance_comparison.txt", key=f"stance_prompt_{case['id']}")
    else:
        st.info("لإظهار المقارنة، أضف مادتين على الأقل للكاتب أو الجهة نفسها، مع تاريخ وموقف/زاوية في خانة الموقف.")
    st.markdown("#### بناء سيناريوهات مشروطة")
    with st.form(f"scenario_form_{case['id']}"):
        drivers_text = st.text_area("المحركات والعوامل التي تريد مراقبتها (كل عامل في سطر)", placeholder="مثال: مسار المفاوضات\nتحركات عسكرية معلنة\nمواقف الحلفاء\nالضغوط الاقتصادية", height=110)
        horizon = st.selectbox("الأفق الزمني للتحليل", ["7 أيام", "30 يوماً", "90 يوماً", "6 أشهر", "12 شهراً"], index=1, key=f"scenario_horizon_{case['id']}")
        make_scenarios = st.form_submit_button("إنشاء ورقة السيناريوهات", type="primary")
    if make_scenarios:
        record = stance_scenarios_mod.build_scenarios(case, drivers_text.splitlines(), horizon)
        S().setdefault("scenario_worksheets", []).insert(0, record)
        S()["scenario_worksheets"] = S()["scenario_worksheets"][:100]
        persist()
        st.session_state[f"active_scenario_{case['id']}"] = record["id"]
        st.rerun()
    records = [x for x in S().get("scenario_worksheets", []) if x.get("case_id") == case.get("id")]
    if records:
        selected = st.selectbox("ورقة السيناريوهات", records, format_func=lambda x: f"{x.get('created_at','')[:16]} · {x.get('horizon','')}", key=f"scenario_select_{case['id']}")
        for scenario in selected.get("scenarios", []):
            st.markdown(f"**{scenario['name']}**")
            st.write(scenario["question"])
            st.caption("مؤشرات المتابعة: " + ("، ".join(scenario.get("indicators", [])) or "لم تحدد"))
        st.warning(selected.get("caveat", ""))
        scenario_prompt = stance_scenarios_mod.build_scenario_prompt(selected, case)
        st.download_button("⬇️ تنزيل برومبت التحليل بالسيناريوهات", scenario_prompt, file_name="marsad_scenario_analysis.txt", key=f"scenario_prompt_{case['id']}")


def render_early_warning_center():
    """مركز الإنذار المبكر: مقارنة تراكمية للتغيرات في ملفات القضايا."""
    st.divider()
    st.markdown("### 🚨 مركز الإنذار المبكر والتحليل الاستراتيجي")
    auto_note("warning")
    st.caption("يقارن المواد والادعاءات والأحداث والمواقف المسجلة بخط الأساس السابق. درجات المتابعة أداة فرز وليست حكماً استخباراتياً أو إثباتاً لوقوع حدث.")
    cases = S().get("research_cases", [])
    state = S().setdefault("early_warning", {"baselines": {}, "reports": [], "last_scan": ""})
    c1, c2 = st.columns([2, 1])
    c1.caption("أول فحص ينشئ خط أساس فقط. بعد إضافة مواد أو تعديل سجل الادعاءات والأحداث، أعد الفحص لرصد الفروق.")
    if c2.button("🔍 افحص التغييرات الآن", key="early_warning_scan", type="primary", use_container_width=True):
        updated, alerts, initialized = early_warning_mod.scan_cases(cases, state)
        S()["early_warning"] = updated
        persist()
        st.session_state["early_warning_last_alerts"] = alerts
        st.session_state["early_warning_initialized"] = initialized
        st.rerun()
    initialized = st.session_state.get("early_warning_initialized", [])
    if initialized:
        st.info("تم إنشاء خط أساس لأول مرة للملفات: " + "، ".join(initialized) + ". لن يصدر إنذار عن مواد قديمة قبل خط الأساس.")
    alerts = st.session_state.get("early_warning_last_alerts", [])
    if alerts:
        st.success(f"تم رصد تغييرات في {len(alerts)} ملف/ملفات.")
        for alert in alerts:
            sev = alert.get("severity", "متابعة")
            with st.expander(f"🚨 {sev} · {alert.get('case_title')} · {len(alert.get('new_materials', []))} مادة جديدة", expanded=True):
                if alert.get("urgent_terms"):
                    st.warning("كلمات تستدعي مراجعة عاجلة للمصدر، ولا تثبت وقوع الحدث: " + "، ".join(alert["urgent_terms"]))
                if alert.get("new_entities"):
                    st.write("**كيانات ظهرت لأول مرة:** " + "، ".join(alert["new_entities"]))
                for item in alert.get("new_materials", []):
                    st.markdown(f"**مادة جديدة: {item.get('title')}**")
                    st.caption(f"{item.get('type')} · {item.get('outlet')} · {item.get('date')} · الكاتب: {item.get('author')}")
                    if item.get("url"): st.markdown(f"[فتح المصدر الأصلي]({item['url']})")
                    for group, terms in item.get("signals", {}).items(): st.warning(f"إشارة لغوية محتملة ({group}): " + "، ".join(terms))
                    if not item.get("text_available"): st.caption("المادة بلا نص محفوظ؛ لا يمكن استنتاج موقف أو حدث من العنوان وحده.")
                for item in alert.get("changed_materials", []):
                    st.info(f"**تغيرت مادة محفوظة:** {item.get('title')} · الحقول: {', '.join(item.get('changed_fields', []))}")
                    if item.get("url"): st.markdown(f"[فتح المصدر]({item['url']})")
                for item in alert.get("changed_claims", []):
                    before, after = item.get("before") or {}, item.get("after") or {}
                    st.write(f"**تغير سجل ادعاء:** {before.get('statement') or after.get('statement')}")
                    st.caption(f"حالة الدليل: {before.get('status', 'جديد')} ← {after.get('status', 'غير محدد')} · المصدر: {after.get('source', '')}")
                for item in alert.get("changed_events", []):
                    before, after = item.get("before") or {}, item.get("after") or {}
                    st.write(f"**تغير حدث:** {before.get('title') or after.get('title')} · {before.get('date', '')} ← {after.get('date', '')}")
                for item in alert.get("stance_changes", []):
                    st.warning(f"**تغير موقف/زاوية مسجل يحتاج تحققاً:** {item.get('actor')} · {' / '.join(item.get('previous_positions', []))} ← {item.get('new_position')}")
                    if item.get("url"): st.markdown(f"[المصدر الأصلي]({item['url']})")
                st.caption(alert.get("note", ""))
        daily_md = early_warning_mod.build_daily_brief(alerts)
        st.download_button("⬇️ تنزيل موجز التغييرات", daily_md, file_name="marsad_early_warning.md", key="early_warning_download")
        prompt = early_warning_mod.build_analysis_prompt(alerts)
        with st.expander("🧠 برومبت التحليل الاستراتيجي للتغييرات"):
            st.code(prompt, language=None)
            st.download_button("تنزيل البرومبت", prompt, file_name="early_warning_analysis_prompt.txt", key="early_warning_prompt_download")
    else:
        st.info("لا توجد تغييرات جديدة في آخر فحص. لو ده أول فحص، تم إنشاء خط الأساس فقط.")
    history = (S().get("early_warning") or {}).get("reports", [])
    if history:
        with st.expander(f"📚 سجل الإنذارات السابقة ({len(history)})"):
            for item in reversed(history[-30:]):
                st.write(f"**{item.get('severity', 'متابعة')} · {item.get('case_title')}** · {item.get('created_at')} · {len(item.get('new_materials', []))} مادة جديدة · {len(item.get('changed_claims', []))} ادعاء متغير")


def render_dossiers(P="pol"):

    ss = st.session_state
    sx, egp = PROFS[P]["sx"], P == "eg"
    if egp:
        st.caption("ملفات وخيوط الشأن المصري **لوحدها**: بتاخد بس نتايج تاب «الشأن المصري» وتتبّع المواضيع، ومبتتخلطش بسياسة المنطقة. "
                   "فيها ملفات جاهزة (نهاية حكم السيسي 2030 ومن بعده، الإخوان، الاقتصاد والأسعار…) وتقدر تعمل ملف جديد على أي موضوع أو ترند. "
                   "دوس «اربط» وهتطلعلك الملفات والخيوط، وجوه كل ملف برومبت تحليل.")
    else:
        st.caption("بيجمع الأخبار اللي عندك في ملفات (مواضيع ثابتة) وخيوط (قصص بتتكون لوحدها من الأخبار اللي فيها نفس الأطراف في أيام قريبة). "
                   "عدّ وربط بس من غير ذكاء اصطناعي، فمش بيصرف رصيد. والتحليل بيتعمل بالبرومبت الجاهز لأهم الملفات.")
    if ss.get("dos_msg"):
        st.success(ss.pop("dos_msg"))
    if not egp:
        with st.expander("📖 ازاي تستخدم التبويب ده؟ (خطوة بخطوة)", expanded=_dos_result(P) is None):
            st.markdown(DOS_HELP)
        render_search_all()
    if auto_pull_jobs():
        st.success("✅ لقيت بحث جديد خلص على GitHub، وحمّلت نتايجه لوحدي.")
    pool = {a["url"]: a for a in _pool_for(P)}
    tabs_n = Counter(t_ for a in pool.values() for t_ in (a.get("tabs") or [a.get("tab", "")]) if (t_ in EG_TABS) == egp)
    st.markdown(f"🔎 **أرشيف البحث" + (" (الشأن المصري)" if egp else " (السياسة والمنطقة)") + f":** {len(pool)} خبر (آخر 21 يوم)"
                + (f" — منهم {', '.join(f'{TAB_LABELS.get(k, k)} ({n})' for k, n in tabs_n.most_common(6))}" if pool else
                   " — لسه مفيش. أي بحث تعمله في تاب الشأن المصري أو تتبّع موضوع هيتسجل هنا لوحده." if egp else
                   " — لسه مفيش. أي بحث تعمله في أي تاب هيتسجل هنا لوحده."))
    if pool and st.button("🗑️ امسح أرشيف البحث ده", key=f"dos_pool_clear{sx}"):
        gone = set(pool)
        ss["dos_pool"] = {u: a for u, a in _dos_pool().items() if u not in gone}
        if PERSIST:
            try:
                store.save_file(GH_TOKEN, GH_GIST, DOS_POOL_FILE, ss["dos_pool"])
            except Exception:
                pass
        st.rerun()
    with st.expander("💬 منشورات فيس وتويتر (الخلاط التحليلي)", expanded=False):
        render_posts(P)
    render_dossiers_cfg(P)
    if not egp:
        if st.toggle("🔎 ترند أو موضوع طارئ (وقف الطيران، عطل مايكروسوفت…)؟ تتبّعه من كل المصادر واعمله ملف", key="trd_open"):
            render_topic_track("pol")

    st.markdown("### 🔗 اربط الأخبار")
    opts = {"بحث": "نتايج البحث اللي في التابات", "يومي": "التقرير اليومي (آخر 7 أيام)", "مخصص": "التقرير المخصص",
            "محفوظات": "المحفوظات", "أمريكا": "تحركات أمريكا وتصريحات ترامب (ملف جاهز بالروابط)"}
    if egp:
        opts = {"بحث": "نتايج البحث بتاعة الشأن المصري (التاب وتتبّع المواضيع)"}
    use = st.multiselect("هات الأخبار منين؟", list(opts), default=list(opts), format_func=lambda k: opts[k], key=f"dos_use{sx}")
    ups = st.file_uploader("ملفات أخبار إضافية CSV (اختياري) — الأعمدة: date, source, country, title, url, summary",
                           type=["csv"], accept_multiple_files=True, key=f"dos_up{sx}")
    DAYS_OPTS = {"آخر 6 ساعات": 0.25, "آخر 12 ساعة": 0.5, "آخر 24 ساعة": 1, "آخر يومين": 2, "آخر 3 أيام": 3, "آخر 5 أيام": 5,
                 "آخر 7 أيام": 7, "آخر 14 يوم": 14, "آخر 30 يوم": 30}
    pp = _dos_prefs().get(P) or {}
    lk_opts = ["🌐 الصفحة الأصلية (للتصوير والمرجع)", "📖 صفحة الترجمة"]
    dl = pick(st, "📅 الأخبار بتاعة أنهي فترة؟ (أي حاجة أقدم من كده بتتشال)", list(DAYS_OPTS),
              pp.get("days") if pp.get("days") in DAYS_OPTS else "آخر 7 أيام", f"dos_days2{sx}")
    max_days = DAYS_OPTS[dl]
    st.caption("💡 اقتراح: **6 أو 12 ساعة** لو بتتابع حدث ساخن لسه حاصل. **24 ساعة أو 3 أيام** لقصة شغالة. **7 أيام** للصورة العامة (الافتراضي). **14 أو 30 يوم** للخلفية بس. "
               "الأخبار اللي مفيهاش ساعة (زي ملف أمريكا والمنشورات) بتتحسب باليوم.")
    lk = st.radio("🔗 لما أدوس على عنوان خبر يفتح إيه؟", lk_opts, index=1 if pp.get("link") == "tr" else 0, horizontal=True, key=f"dos_link_r{sx}")
    st.session_state["dos_link"] = "tr" if lk.startswith("📖") else "orig"
    st.caption("وجنب كل خبر لينك صغير تاني للتاني، فتقدر تفتح الاتنين.")
    c1, c2 = st.columns(2)
    window = pick(c1, "أقصى فرق بالأيام بين خبرين في نفس الخيط", range(1, 8), int(pp.get("win") or 3), f"dos_win{sx}")
    mins = pick(c2, "أقل عدد أطراف مشتركة (زي مصر + إثيوبيا = 2)", [1, 2, 3], int(pp.get("min") or 2), f"dos_min{sx}")
    _dos_save_prefs(P, {"days": dl, "link": "tr" if lk.startswith("📖") else "orig", "win": window, "min": mins})
    cur_params = {"max_days": max_days, "window": window, "mins": mins, "use": sorted(use)}
    old_res = _dos_result(P)
    auto = False
    if old_res:
        old_params = old_res.get("params") or {**cur_params, "max_days": old_res.get("max_days")}
        auto = old_params != cur_params  # غيّرت الفترة أو الإعدادات: نربط تاني لوحدنا بدل ما نعرض القديم
        made = keys_mod.parse(old_res.get("created"))
        if made and max_days:
            if made.tzinfo is None:
                made = made.replace(tzinfo=timezone.utc)  # السيرفر بيكتب الوقت بتوقيت UTC
            if datetime.now(timezone.utc) - made > timedelta(days=float(max_days)):
                auto = True  # الربط المحفوظ أقدم من الفترة نفسها (زي ربط آخر 24 ساعة اتعمل من 3 أيام): نحدّثه
    clicked = st.button("🔗 اربط واعرض الملفات والخيوط", type="primary", use_container_width=True, key=f"dos_run{sx}")
    if clicked or auto:
        dos, err = dossiers_mod.parse_config(_dos_cfg_text(P))
        if err:
            st.error(f"تعريف الملفات فيه مشكلة: {err}")
        else:
            with st.spinner("⏳ غيّرت الفترة، فبيربط تاني على الفترة الجديدة…" if auto and not clicked else "⏳ بيجمع ويربط…"):
                items, counts = _dos_collect(use, ups, P)
                if not items:
                    st.warning("مفيش أخبار. اعمل بحث في أي تاب، أو استنى التقرير اليومي، أو ضيف منشورات.")
                else:
                    res = dossiers_mod.run(items, dos, window, mins, max_days)
                    res["counts"] = counts
                    res["params"] = cur_params
                    res["newest"] = max((str(it.get("date") or "") for it in items), default="")
                    ss[PROFS[P]["res_key"]] = res
                    if PERSIST:
                        try:
                            store.save_file(GH_TOKEN, GH_GIST, PROFS[P]["res_file"], res)
                        except Exception as e:
                            st.caption(f"النتيجة ما اتحفظتش في التخزين الدائم ({type(e).__name__})")

    res = _dos_result(P)
    if not res:
        st.info("دوس «اربط» عشان يطلعلك الملفات والخيوط. النتيجة بتفضل محفوظة لحد ما تربط تاني.")
        return
    st.divider()
    cr = keys_mod.parse(res.get("created"))
    ct = cr.strftime("%Y-%m-%d %H:%M") if cr else "؟"
    if res.get("max_days"):
        st.caption(f"📅 أخبار {_period_label(res['max_days'])} بس" + (f" · اتشال {res['dropped_old']} خبر أقدم" if res.get("dropped_old") else "") + f" · الربط اتعمل {ct}")
    else:
        st.warning(f"⚠️ النتيجة دي اتعملت {ct} من غير فلتر فترة، فممكن فيها أخبار قديمة. دوس «اربط واعرض» تاني فوق عشان تتنضف.")
    try:
        if res.get("first") and res.get("max_days") and str(res["first"])[:10] < (datetime.now(timezone.utc) - timedelta(days=float(res["max_days"]) + 1)).strftime("%Y-%m-%d"):
            st.warning("⚠️ النتيجة المعروضة قديمة (فيها أخبار أقدم من الفترة المختارة). دوس «اربط واعرض» تاني عشان تتحدّث.")
    except Exception:
        pass
    if not res.get("total"):
        nw = res.get("newest") or ""
        st.warning("مفيش أخبار في الفترة دي." + (f" أحدث خبر عندك في الأرشيف بتاريخ **{nw[:10]}**، يعني مفيش بحث جديد اتعمل من ساعتها." if nw else "")
                   + " اعمل بحث جديد (أو «🚀 بحث شامل في كل المصادر» فوق ودوس «حدّث وحمّل النتايج») عشان تيجي أخبار النهارده، أو كبّر الفترة.")
        return
    nw = res.get("newest") or ""
    try:
        if nw and res.get("max_days") and nw[:10] < (datetime.now(timezone.utc) - timedelta(days=float(res["max_days"]) + 1)).strftime("%Y-%m-%d"):
            st.info(f"ℹ️ أحدث خبر عندك في الأرشيف بتاريخ {nw[:10]}. عشان تجيب أخبار النهارده اعمل بحث جديد أو «🚀 بحث شامل».")
    except Exception:
        pass
    st.caption(f"آخر ربط: {res.get('created', '').replace('T', ' ')} · الأخبار جت من: "
               + "، ".join(f"{k} ({v})" for k, v in (res.get("counts") or {}).items() if v))
    m = st.columns(4)
    for col, (lbl, val) in zip(m, [("عنصر", res["total"]), ("ملف فيه أخبار", len(res["dossiers"])),
                                   ("خيط", res["n_threads"]), ("منشور", res["posts"])]):
        col.markdown(f"<div class='hm-stat'><b>{val}</b>{lbl}</div>", unsafe_allow_html=True)
    view = st.radio("اعرض", ["📁 الملفات", "🧵 خيوط القصص", "💡 اقتراحات ملفات جديدة"], horizontal=True, key=f"dos_view{sx}")
    if view.startswith("📁"):
        names = [g["name"] for g in res["dossiers"]]
        if names:
            def _dlabel(nm):
                g_ = res["dossiers"][names.index(nm)]
                ico_ = "🇺🇸" if g_.get("lens") else "📈" if g_["type"] == "ترند" else "📁"
                return f"{ico_} {nm} — {len(g_['items'])} عنصر"
            st.caption("بنعرض ملف واحد في المرة عشان الصفحة تفضل خفيفة. اختار الملف من القايمة.")
            pick_d = st.selectbox(f"اختار ملف ({len(names)} ملف فيه أخبار)", names, format_func=_dlabel, key=f"dos_pick{sx}")
            _dos_group(res["dossiers"][names.index(pick_d)], "الملف", f"{sx}d{names.index(pick_d)}")
        if not res["dossiers"]:
            st.info("مفيش ولا خبر دخل أي ملف. جرّب تجيب أخبار أكتر أو ضيف كلمات للملفات.")
    elif view.startswith("🧵"):
        st.caption("الخيط = أخبار فيها نفس الأطراف في أيام قريبة. مرتبة من الأهم (أخبار ومصادر وتصريحات أكتر).")
        if res["threads"]:
            tl_ = [f"{n}. {t['name']} — {len(t['items'])} عنصر · الملف: {t['dossier']}" for n, t in enumerate(res["threads"], 1)]
            pick_t = st.selectbox(f"اختار خيط ({len(tl_)} خيط)", tl_, key=f"dos_tpick{sx}")
            n_t = tl_.index(pick_t) + 1
            _dos_group(res["threads"][n_t - 1], "الخيط", f"{sx}t{n_t}")
        if not res["threads"]:
            st.info("مفيش خيوط. جرّب تكبّر عدد الأيام أو تقلل الأطراف المشتركة لـ 1.")
    else:
        st.caption("كلمات وأطراف بتتكرر في أخبار مش داخلة أي ملف. لو حاجة منها مهمة، دوس «اعمله ملف».")
        for i, sgg in enumerate(res["suggested_words"]):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{sgg['word']}** — في {sgg['news']} خبر و{sgg['posts']} منشور")
            if c2.button("➕ اعمله ملف", key=f"dos_sg{sx}_{i}"):
                _dos_save_cfg(dossiers_mod.add_dossier(_dos_cfg_text(P), f"مقترح: {sgg['word']}", [sgg["word"]]), P)
                ss["dos_msg"] = f"✅ اتعمل ملف «{sgg['word']}». دوس «اربط» تاني عشان يتملى."
                st.rerun()
        if res.get("suggested_entities"):
            st.markdown("**أطراف بتظهر كتير من غير ملف:** " + "، ".join(f"{e['entity']} ({e['count']})" for e in res["suggested_entities"]))
        if not res["suggested_words"]:
            st.info("مفيش كلمات متكررة كفاية.")
    if st.toggle("⬇️ جهّز التقرير الكامل للتنزيل (ملف نصي)", key=f"dos_dlt{sx}"):
        st.download_button("⬇️ نزّل التقرير", dossiers_mod.briefing_md(res), file_name="dossiers_report.md", key=f"dos_dl{sx}")


EG_PRESETS = {
    "🚨 جرائم وحوادث": "جريمة، مقتل، القبض على، النيابة العامة، حادث",
    "⚖️ قوانين وقرارات": "قانون، مجلس النواب، قرار جمهوري، الجريدة الرسمية، تعديل تشريعي",
    "💰 اقتصاد وأسعار": "الدولار، الجنيه، التضخم، الأسعار، الدعم، البنك المركزي",
    "🇸🇩 الحدود مع السودان": "السودان، الحدود، لاجئين، أرقين، حلايب",
    "🇵🇸 غزة ورفح": "غزة، رفح، معبر رفح، فلسطين، المساعدات",
    "💍 مجتمع وأحوال شخصية": "زواج، طلاق، أسرة، قضية رأي عام",
    "🏥 صحة وتعليم": "المستشفيات، التأمين الصحي، الثانوية العامة، الجامعات، التعليم",
    "⛽ خدمات وطاقة": "الكهرباء، انقطاع الكهرباء، الوقود، البنزين، المياه",
}

if _on("search", "eg"):
    with tab_eg:
        use_filters("eg", "full")
        st.caption("أخبار الشأن الداخلي المصري من صحف ومواقع مصرية بس: جرائم وحوادث، ومجتمع، واقتصاد وأسعار، وقوانين وقرارات، والحدود، والخدمات. "
                   "اختار موضوع جاهز تحت أو اكتب كلماتك في الخانة فوق. وللشرح (القانون ده بيعمل إيه ولزمته إيه) روح تاب «🧵 الملفات والخيوط» واختار «📜 شرح للمواطن».")
        pre = st.multiselect("🎯 مواضيع جاهزة (بتدور على كلماتها كلها)", list(EG_PRESETS), key="eg_pre")
        if pre:
            if query.strip():
                st.caption("كلماتك اللي فوق هي اللي بتتستخدم (المواضيع الجاهزة بتشتغل لما الخانة تبقى فاضية).")
            else:
                query = "، ".join(EG_PRESETS[p] for p in pre)
                joiner = "OR"
                st.caption(f"هيدور على: {query}")
        eg_view = st.radio("عايز إيه؟", ["🔎 تتبّع موضوع كامل (أسعار الطماطم، جريمة معينة…) من كل المصادر", "📰 بحث عادي في المصادر", "🧵 ملفات وخيوط الشأن المصري (منفصلة عن السياسة)"], key="eg_view")
        if eg_view.startswith("🔎"):
            render_topic_track("eg")
        elif eg_view.startswith("🧵"):
            render_dossiers("eg")
        else:
            curated_tab("eg", EGYPT, "EG", "EG", "ابحث في المصادر المصرية")


if _on("ops"):
    with tab_dr:
        if IS_ADMIN:
            render_workflow_overview()
            render_auto_intel_panel()
            render_watch()
            with st.expander("🔗 مزامنة إصدار المرصد إلى GitHub", expanded=False):
                sync_repo = _sec("GH_REPO") or gh_actions.DEFAULT_REPO
                sync_branch = _sec("GH_BRANCH") or "main"
                sync_token = _sec("GH_SYNC_TOKEN")
                st.caption(f"المستودع: {sync_repo} · الفرع: {sync_branch}. بعد نجاح Commit سيبدأ GitHub Actions بالتحقق، وإذا كان Streamlit Cloud مربوطاً بهذا الفرع فسيبدأ النشر تلقائياً حسب إعداداته.")
                auto_sync_value = _sec("GH_SYNC_AUTO")
                auto_sync = auto_sync_value is True or str(auto_sync_value).strip().lower() in ("1", "true", "yes", "on")
                if not sync_token:
                    st.warning("للتفعيل مرة واحدة: أضف GH_SYNC_TOKEN في Streamlit Secrets بتوكن Fine-grained يملك Contents: Read and write على المستودع. أضف GH_REPO وGH_BRANCH إذا كنت تستخدم مستودعاً/فرعاً مختلفاً. لا تضع التوكن في المحادثة.")
                elif auto_sync:
                    st.success("وضع المزامنة التلقائية مفعّل: رفع حزمة إصدار جديدة بعد فحصها ينشئ Commit تلقائياً مرة واحدة لكل ملف.")
                release_zip = st.file_uploader("حزمة الإصدار ZIP", type=["zip"], key="github_release_zip")
                if release_zip is not None:
                    try:
                        release_bytes = release_zip.getvalue()
                        release_files = github_sync_mod.inspect_release_zip(release_bytes)
                        release_digest = hashlib.sha256(release_bytes).hexdigest()
                        st.success(f"الحزمة سليمة: {len(release_files)} ملفاً قابلاً للمزامنة، بإجمالي {sum(len(v) for v in release_files.values()):,} بايت.")
                        with st.expander("معاينة الملفات التي ستُرفع"):
                            st.code("\n".join(sorted(release_files)), language="text")
                        do_push = False
                        if auto_sync and sync_token:
                            do_push = st.session_state.get("github_last_sync_digest") != release_digest
                        elif st.button("⬆️ أنشئ Commit وادفع الإصدار إلى GitHub", type="primary", disabled=not sync_token, key="push_marsad_release"):
                            do_push = True
                        if do_push:
                            with st.spinner("جارٍ رفع الملفات وإنشاء Commit دون Force Push…"):
                                pushed = github_sync_mod.push_release_zip(sync_token, sync_repo, sync_branch, release_bytes,
                                                                          message=f"Marsad News release sync: {len(release_files)} files")
                            st.session_state["github_last_sync_digest"] = release_digest
                            st.success(f"تم إنشاء Commit: {pushed['commit_sha'][:12]} · {pushed['files']} ملفاً")
                            if pushed.get("commit_url"):
                                st.markdown(f"[فتح Commit على GitHub]({pushed['commit_url']})")
                            st.info("تم تحديث الفرع. راقب GitHub Actions للتحقق، ثم حالة نشر Streamlit Cloud.")
                    except Exception as exc:
                        st.error(f"الحزمة لم تجتز الفحص أو فشل الاتصال: {type(exc).__name__}: {str(exc)[:220]}")
                st.caption("المزامنة لا تحذف ملفات من المستودع ولا تستخدم Force Push، وتستبعد الأسرار والنسخ الاحتياطية. GH_SYNC_AUTO=true يجعل الرفع التلقائي بعد رفع ZIP جديد. هذا يختصر خطوات النشر داخل التطبيق، لكنه لا يربط جلسة ChatGPT مباشرة بمستودعك؛ لذلك لا ندّعي مزامنة تعديلات هذه المحادثة قبل وصولها للمستودع.")
        render_daily()

if _on("library", "dos"):
    with tab_dos:
        render_dossiers()
        render_custom_collections("pol")

if _on("library", "sv"):
    with tab_sv:
        render_saved()
if _on("library", "lab"):
    with tab_lab:
        render_analysis_lab()

if _on("guide"):
    with tab_guide:
        user_guide_mod.render(st)

if _on("settings"):
    with tab_ms:
        with st.expander("🎧 إعدادات القراءة الصوتية (للمترو والسماعات)"):
            tts_settings("tts")
            st.radio("ما الذي يُقرأ عند الضغط على «🎧 استمع»؟", TTS_MODES, key="tts_mode")
            for _k in ("tts_voice", "tts_rate", "tts_mode"):
                tts_get(_k, None)  # احفظ نسخة
            st.caption("تُجهَّز القراءة بصوت عربي عصبي، ويمكن تنزيلها MP3 قبل نزول المترو للاستماع بلا إنترنت.")
        if IS_ADMIN:
            render_manage()
            st.divider()
            render_keys_admin()
        else:
            st.info("إدارة المصادر والشفرات غير متاحة في النسخة التجريبية.")

save_results()
show_footer()
