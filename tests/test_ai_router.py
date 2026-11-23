import unittest
import ai_router

class AIRouterTests(unittest.TestCase):
    def test_task_prompt_contains_deliverables_and_guardrails(self):
        prompt = ai_router.build_task_prompt("مواد القضية", "التحليل الجيوسياسي", "ركز على البحر الأحمر")
        self.assertIn("خريطة مصالح", prompt)
        self.assertIn("لا تخترع مصادر", prompt)
        self.assertIn("ركز على البحر الأحمر", prompt)

    def test_recommendation_only_uses_available_providers(self):
        self.assertEqual(ai_router.recommend_provider("كتابة سكريبت باللهجة المصرية", ["ollama", "groq"]), "groq")
        self.assertIsNone(ai_router.recommend_provider("إنتاج المحتوى", []))

    def test_unknown_task_rejected(self):
        with self.assertRaises(ValueError):
            ai_router.build_task_prompt("x", "مهمة غير موجودة")

if __name__ == "__main__":
    unittest.main()
