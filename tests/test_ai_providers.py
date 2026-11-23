import unittest
from unittest.mock import patch
import ai_providers

class AIProviderTests(unittest.TestCase):
    def test_free_openrouter_route_is_explicit(self):
        cfg = ai_providers.PROVIDERS["openrouter_free"]
        self.assertTrue(cfg["free_only"])
        self.assertEqual(cfg["default_model"], "openrouter/free")

    def test_usage_normalization(self):
        self.assertEqual(ai_providers._usage_openai({"usage":{"prompt_tokens":12,"completion_tokens":8,"total_tokens":20}}),
                         {"input_tokens":12,"output_tokens":8,"total_tokens":20})

    def test_cost_estimate_uses_user_prices(self):
        self.assertAlmostEqual(ai_providers.estimate_cost(1000000, 500000, 0.5, 1.0), 1.0)
        self.assertIsNone(ai_providers.estimate_cost(None, 10, 1, 1))

    def test_no_unknown_provider(self):
        with self.assertRaises(ValueError):
            ai_providers.call_model("bad", "m", "hello")

    @patch("ai_providers._post_json")
    def test_gemini_usage_and_text_are_normalized(self, post):
        post.return_value = ({"candidates":[{"content":{"parts":[{"text":"نتيجة"}]},"finishReason":"STOP"}],
                              "usageMetadata":{"promptTokenCount":10,"candidatesTokenCount":5,"totalTokenCount":15}}, {})
        out = ai_providers.call_model("gemini", "gemini-3.8-flash", "حلل", api_key="secret")
        self.assertEqual(out["text"], "نتيجة")
        self.assertEqual(out["usage"]["total_tokens"], 15)
        self.assertNotIn("secret", str(out))

    @patch("ai_providers._post_json")
    def test_openrouter_free_endpoint_and_response(self, post):
        post.return_value = ({"model":"sample-free", "choices":[{"message":{"content":"تحليل"},"finish_reason":"stop"}],
                              "usage":{"prompt_tokens":20,"completion_tokens":30,"total_tokens":50}}, {})
        out = ai_providers.call_model("openrouter_free", "openrouter/free", "حلل", api_key="secret")
        self.assertEqual(out["text"], "تحليل")
        self.assertEqual(out["usage"]["total_tokens"], 50)
        self.assertIn("/chat/completions", post.call_args.args[0])


    @patch("ai_providers._post_json")
    def test_custom_openai_compatible_provider(self, post):
        post.return_value = ({"model":"vendor/model-x", "choices":[{"message":{"content":"تم"},"finish_reason":"stop"}],
                             "usage":{"prompt_tokens":7,"completion_tokens":4,"total_tokens":11}}, {})
        out = ai_providers.call_model("custom_openai", "vendor/model-x", "حلل", api_key="secret",
                                      base_url="https://api.vendor.example/v1")
        self.assertEqual(out["text"], "تم")
        self.assertEqual(out["usage"]["total_tokens"], 11)
        self.assertEqual(post.call_args.args[0], "https://api.vendor.example/v1/chat/completions")

    def test_custom_provider_rejects_non_https_endpoint(self):
        with self.assertRaises(ValueError):
            ai_providers.call_model("custom_openai", "model-x", "حلل", api_key="secret",
                                    base_url="http://api.vendor.example/v1")

    def test_custom_provider_requires_model_id(self):
        with self.assertRaises(ValueError):
            ai_providers.call_model("custom_openai", "", "حلل", api_key="secret",
                                    base_url="https://api.vendor.example/v1")

if __name__ == '__main__':
    unittest.main()
