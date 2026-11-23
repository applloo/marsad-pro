import ast
import unittest
from pathlib import Path

import user_guide


class UserGuideTests(unittest.TestCase):
    def test_guide_covers_all_primary_screens(self):
        text = " ".join(title + " " + body for title, body in user_guide.SECTIONS)
        for expected in ("الرئيسية", "البحث والرصد", "التحليل والاستخبارات", "غرفة العمليات", "الملفات والأرشيف", "المصادر والإعدادات", "التكلفة", "نسخة مستقلة"):
            self.assertIn(expected, text)

    def test_guide_is_integrated_as_seventh_main_tab(self):
        source = Path(__file__).resolve().parents[1] / "app.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        app_text = source.read_text(encoding="utf-8")
        self.assertIn("tab_guide", app_text)
        self.assertIn("user_guide_mod.render(st)", app_text)
        self.assertTrue(any(isinstance(n, ast.Import) and any(a.name == "user_guide" for a in n.names) for n in tree.body))


if __name__ == "__main__":
    unittest.main()
