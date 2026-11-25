from unittest import mock

import core


class _Resp:
    status_code = 200
    headers = {"Content-Type": "text/html"}
    encoding = "utf-8"

    def __init__(self, html):
        self._b = html.encode("utf-8")

    def iter_content(self, n):
        yield self._b

    def close(self):
        pass


def test_teaser_reads_public_share_description_and_translates():
    html = ('<html><head><meta property="og:description" content="Egypt and Sudan signed a new border trade deal '
            'on Monday, officials said, opening two crossings."></head><body>paywall</body></html>')
    core._TEASER_CACHE.clear()
    items = [{"url": "https://www.example.com/a", "title": "Deal"}, {"url": "https://www.example.com/b", "title": "x", "snippet": "has"}]
    with mock.patch.object(core.requests, "get", return_value=_Resp(html)), \
         mock.patch.object(core, "is_safe_url", return_value=True), \
         mock.patch.object(core, "_batch_tr", lambda texts, dest: ["مصر والسودان وقعتا اتفاق" for _ in texts]):
        n = core.add_teasers(items)
    assert n == 1
    assert items[0]["summary_status"] == "page_teaser" and "مصر" in items[0]["summary_ar"]
    assert "teaser" not in items[1]  # اللي عنده مقتطف مالمسناهوش


def test_teaser_handles_content_before_property_and_missing_meta():
    core._TEASER_CACHE.clear()
    html = '<meta content="A long enough description written before the property attribute appears here." name="description">'
    with mock.patch.object(core.requests, "get", return_value=_Resp(html)), mock.patch.object(core, "is_safe_url", return_value=True):
        assert core.fetch_teaser("https://e.com/1").startswith("A long enough")
    with mock.patch.object(core.requests, "get", return_value=_Resp("<html></html>")), mock.patch.object(core, "is_safe_url", return_value=True):
        assert core.fetch_teaser("https://e.com/2") == ""
