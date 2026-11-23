# -*- coding: utf-8 -*-
"""GitHub Contents sync for a reviewed Marsad release ZIP; token is never persisted by this module."""
from __future__ import annotations
import base64
import io
import re
import zipfile
from pathlib import PurePosixPath
import requests

API = "https://api.github.com"
MAX_FILES = 250
MAX_FILE_BYTES = 5_000_000
MAX_TOTAL_BYTES = 20_000_000
ALLOWED_EXACT = {".gitignore"}
ALLOWED_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".txt", ".json", ".csv", ".toml", ".ipynb", ".html", ".css", ".js"}
BLOCKED_NAMES = {".env", "secrets.toml", "credentials.json", "token.txt"}


def validate_repo(repo):
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", (repo or "").strip()))


def inspect_release_zip(data):
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("ملف ZIP فارغ أو غير صالح")
    files, total = {}, 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = [x for x in archive.infolist() if not x.is_dir()]
        if not infos or len(infos) > MAX_FILES:
            raise ValueError(f"عدد الملفات يجب أن يكون بين 1 و{MAX_FILES}")
        for info in infos:
            raw = info.filename.replace("\\", "/")
            path = PurePosixPath(raw)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"مسار غير آمن داخل ZIP: {raw}")
            parts = [p for p in path.parts if p not in ("", ".")]
            if not parts or parts[0] in (".git", ".venv", "venv", "__pycache__"):
                continue
            name = parts[-1].lower()
            if name in BLOCKED_NAMES or name.endswith((".mrbak", ".zip")) or ".env" in parts:
                continue
            suffix = PurePosixPath(raw).suffix.lower()
            if suffix not in ALLOWED_SUFFIXES and name not in ALLOWED_EXACT:
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"روابط رمزية غير مسموحة: {raw}")
            if info.file_size > MAX_FILE_BYTES:
                raise ValueError(f"ملف أكبر من الحد المسموح: {raw}")
            content = archive.read(info)
            total += len(content)
            if total > MAX_TOTAL_BYTES:
                raise ValueError("إجمالي ملفات الإصدار أكبر من 20 MB")
            rel = "/".join(parts)
            if rel in files:
                raise ValueError(f"ملف مكرر داخل ZIP: {rel}")
            files[rel] = content
    if not files:
        raise ValueError("لم يتم العثور على ملفات كود/توثيق مسموح بمزامنتها")
    return files


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "marsad-news-phase8-19"}


def push_release_zip(token, repo, branch, zip_bytes, message="Marsad News release sync"):
    """Create blobs/tree/commit and fast-forward branch. No force push and no file deletions."""
    if not token:
        raise ValueError("GH_SYNC_TOKEN غير مضبوط")
    if not validate_repo(repo):
        raise ValueError("صيغة المستودع يجب أن تكون owner/repository")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch or "") or branch.startswith("/") or ".." in branch.split("/"):
        raise ValueError("اسم الفرع غير صالح")
    files = inspect_release_zip(zip_bytes)
    base = f"{API}/repos/{repo}"
    headers = _headers(token)
    ref = requests.get(f"{base}/git/ref/heads/{branch}", headers=headers, timeout=25)
    ref.raise_for_status()
    parent_sha = ref.json()["object"]["sha"]
    parent = requests.get(f"{base}/git/commits/{parent_sha}", headers=headers, timeout=25)
    parent.raise_for_status()
    base_tree = parent.json()["tree"]["sha"]
    tree_items = []
    for path, content in files.items():
        blob = requests.post(f"{base}/git/blobs", headers=headers,
                             json={"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"}, timeout=30)
        blob.raise_for_status()
        tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob.json()["sha"]})
    tree = requests.post(f"{base}/git/trees", headers=headers,
                         json={"base_tree": base_tree, "tree": tree_items}, timeout=30)
    tree.raise_for_status()
    commit = requests.post(f"{base}/git/commits", headers=headers,
                           json={"message": (message or "Marsad release sync")[:180], "tree": tree.json()["sha"], "parents": [parent_sha]}, timeout=30)
    commit.raise_for_status()
    new_sha = commit.json()["sha"]
    update = requests.patch(f"{base}/git/refs/heads/{branch}", headers=headers,
                            json={"sha": new_sha, "force": False}, timeout=30)
    update.raise_for_status()
    return {"commit_sha": new_sha, "commit_url": commit.json().get("html_url"), "files": len(files),
            "bytes": sum(len(v) for v in files.values()), "branch": branch, "repo": repo}
