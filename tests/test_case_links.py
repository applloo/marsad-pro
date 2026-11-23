import unittest
import case_links
import casebook


class CaseLinkTests(unittest.TestCase):
    def make_case(self, title, tags, material_title, text=""):
        c = casebook.new_case(title, "", tags)
        casebook.add_material(c, {"title": material_title, "url": f"https://example.com/{len(title)}", "text": text}, "خبر")
        return c

    def test_detects_shared_named_entities_and_explains_them(self):
        a = self.make_case("إيران والبحر الأحمر", ["إيران", "الملاحة"], "تحركات إيران في البحر الأحمر", "الحوثيون وباب المندب")
        b = self.make_case("أمن باب المندب", ["الملاحة", "اليمن"], "الحوثيون والبحر الأحمر", "إيران واليمن")
        result = case_links.compare_cases(a, b)
        self.assertIn("إيران", result["shared_entities"])
        self.assertIn("البحر الأحمر", result["shared_entities"])
        self.assertTrue(result["reasons"])
        self.assertIn("لا يثبت علاقة سببية", result["caveat"])

    def test_suggestions_skip_weak_pairs(self):
        a = casebook.new_case("ملف أسعار الطماطم", "", ["زراعة"])
        b = casebook.new_case("ملف دوري كرة القدم", "", ["رياضة"])
        self.assertEqual(case_links.suggest_links([a, b]), [])

    def test_user_decision_survives_rescan(self):
        a = self.make_case("إيران", ["إيران"], "إيران")
        b = self.make_case("البحر الأحمر وإيران", ["إيران"], "إيران والبحر الأحمر")
        fresh = case_links.suggest_links([a, b])
        fresh[0]["status"] = "accepted"
        merged = case_links.merge_suggestions(fresh, case_links.suggest_links([a, b]))
        self.assertEqual(merged[0]["status"], "accepted")

    def test_link_prompt_contains_both_original_sources_and_causality_guardrail(self):
        a = self.make_case("ملف إيران", ["إيران"], "خبر عن إيران")
        b = self.make_case("ملف البحر الأحمر", ["البحر الأحمر"], "خبر عن البحر الأحمر")
        link = case_links.create_manual_link(a, b, "اختبار فرضية")
        prompt = case_links.build_link_prompt(a, b, link)
        self.assertIn("https://example.com/", prompt)
        self.assertIn("دون افتراض وجود علاقة سببية", prompt)
        self.assertIn("الملف الأول", prompt)
        self.assertIn("الملف الثاني", prompt)

    def test_manual_link_rejects_same_case(self):
        a = casebook.new_case("ملف")
        with self.assertRaises(ValueError):
            case_links.create_manual_link(a, a)


if __name__ == "__main__":
    unittest.main()
