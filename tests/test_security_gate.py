import ast
import hashlib
import hmac
import re
import time
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def _funcs(*names, admin_key="secret-123"):
    ns = {"re": re, "time": time, "hmac": hmac, "ADMIN_KEY": admin_key, "ADMIN_TOKEN_DAYS": 14}
    for n in ast.parse(SRC).body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            exec(compile(ast.Module([n], []), "app", "exec"), ns)
    return ns


def test_admin_link_token_is_signed_and_expires():
    ns = _funcs("_adm_sig", "_adm_tok", "_adm_tok_ok")
    tok = ns["_adm_tok"]()
    assert ns["_adm_tok_ok"](tok)
    day = int(time.time() // 86400) - 1
    assert not ns["_adm_tok_ok"](f"a{day}.{ns['_adm_sig'](day)}")  # منتهي
    assert not ns["_adm_tok_ok"](tok[:-1] + ("0" if tok[-1] != "0" else "1"))  # مزوّر
    assert not ns["_adm_tok_ok"](hashlib.sha256(b"marsad-session|secret-123").hexdigest()[:40])  # الرمز القديم الدائم


def test_missing_admin_key_locks_app_instead_of_opening_admin():
    gate = next(n for n in ast.parse(SRC).body if isinstance(n, ast.FunctionDef) and n.name == "gate")
    body = ast.get_source_segment(SRC, gate)
    assert "if OPEN_MODE:" in body and "if not ADMIN_KEY:" in body and "st.stop()" in body
    assert "if not GATE_ON:\n        ss[\"auth\"] = {\"role\": \"admin\"" not in body
    assert 'OPEN_MODE = (not ADMIN_KEY) and' in SRC


def test_invite_links_are_hidden_by_default():
    i = SRC.index("def render_keys_admin")
    seg = SRC[i:SRC.index("\ndef ", i + 10)]
    assert 'f"kshow_{code_}"' in seg and "value=False" in seg
    assert "st.code(link(k[\"code\"])" not in seg
