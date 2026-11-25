"""Unit tests for Gemini multi-key rotation pool and failover resilience."""
import os
import unittest
from unittest.mock import MagicMock, patch

from src.gemini_runtime import (
    EvaluationUnavailable,
    GeminiClientPool,
    GeminiPool,
    init_gemini_client_pool,
    load_gemini_api_keys,
    mask_api_key,
)


class DummyResponse:
    def __init__(self, text):
        self.text = text


class TestGeminiKeyRotation(unittest.TestCase):
    def test_mask_api_key(self):
        self.assertEqual(mask_api_key("AIzaSy1234567890abcd"), "AIza...abcd")
        self.assertEqual(mask_api_key("short"), "***")
        self.assertEqual(mask_api_key(""), "<empty>")
        self.assertEqual(mask_api_key(None), "<empty>")

    def test_load_gemini_api_keys_single(self):
        env = {"GEMINI_API_KEY": "key_primary"}
        with patch.dict(os.environ, env, clear=True):
            keys = load_gemini_api_keys()
            self.assertEqual(keys, ["key_primary"])

    def test_load_gemini_api_keys_comma_separated(self):
        env = {
            "GEMINI_API_KEYS": "key_alpha, key_beta, key_gamma",
            "GEMINI_API_KEY": "key_alpha",  # duplicate should be skipped
        }
        with patch.dict(os.environ, env, clear=True):
            keys = load_gemini_api_keys()
            self.assertEqual(keys, ["key_alpha", "key_beta", "key_gamma"])

    def test_load_gemini_api_keys_numbered(self):
        env = {
            "GEMINI_API_KEY": "key_1",
            "GEMINI_API_KEY_2": "key_2",
            "GEMINI_API_KEY_3": "key_3",
            "GEMINI_API_KEY_5": "key_5",  # non-contiguous
        }
        with patch.dict(os.environ, env, clear=True):
            keys = load_gemini_api_keys()
            self.assertEqual(keys, ["key_1", "key_2", "key_3", "key_5"])

    def test_gemini_client_pool_rotation(self):
        mock_factory = MagicMock()
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_factory.side_effect = [mock_client1, mock_client2]

        pool = GeminiClientPool(["key_first", "key_second"], client_factory=mock_factory)
        self.assertEqual(pool.total_key_count(), 2)
        self.assertEqual(pool.active_key_count(), 2)

        # Initial active client is key 1
        entry1 = pool.get_current_entry()
        self.assertIsNotNone(entry1)
        self.assertEqual(entry1.key, "key_first")
        self.assertEqual(pool.get_current_client(), mock_client1)

        # Rotate on daily_quota trips key 1 and activates key 2
        rotated = pool.rotate_on_error("daily_quota")
        self.assertTrue(rotated)
        self.assertEqual(pool.active_key_count(), 1)
        entry2 = pool.get_current_entry()
        self.assertEqual(entry2.key, "key_second")
        self.assertEqual(pool.get_current_client(), mock_client2)

        # Rotate key 2 on daily_quota trips key 2 -> all exhausted
        rotated2 = pool.rotate_on_error("daily_quota")
        self.assertFalse(rotated2)
        self.assertEqual(pool.active_key_count(), 0)
        self.assertTrue(pool.is_all_exhausted())

    def test_init_gemini_client_pool_none_when_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            pool = init_gemini_client_pool()
            self.assertIsNone(pool)

    def test_gemini_pool_failover_to_second_key_on_daily_quota(self):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()

        # Client 1 raises 429 daily quota
        error_429 = Exception("Resource has been exhausted: quota exceeded per day")
        mock_client1.models.generate_content.side_effect = error_429

        # Client 2 succeeds with valid JSON evaluation
        valid_json = (
            '{"status": "QUALIFIED", "technical_role": true, "match_score": 85, '
            '"concrete_matches_count": 3, "reasoning": "Strong match", '
            '"sector_key": "solar", "location": "Tel Aviv"}'
        )
        mock_client2.models.generate_content.return_value = DummyResponse(valid_json)

        mock_factory = MagicMock(side_effect=[mock_client1, mock_client2])
        key_pool = GeminiClientPool(["key_a", "key_b"], client_factory=mock_factory)

        pool = GeminiPool(models=["mock-model"], max_attempts=1)
        result = pool.evaluate(key_pool, "Evaluate this job", None)

        self.assertEqual(result["status"], "QUALIFIED")
        self.assertEqual(result["match_score"], 85)
        # Client 1 was called once, hit quota; Client 2 was called once and succeeded
        self.assertEqual(mock_client1.models.generate_content.call_count, 1)
        self.assertEqual(mock_client2.models.generate_content.call_count, 1)
        # Model circuit breaker is NOT tripped
        self.assertFalse(pool.is_exhausted())

    def test_gemini_pool_exhausts_when_all_keys_fail(self):
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()

        error_429 = Exception("Resource has been exhausted: quota exceeded per day")
        mock_client1.models.generate_content.side_effect = error_429
        mock_client2.models.generate_content.side_effect = error_429

        mock_factory = MagicMock(side_effect=[mock_client1, mock_client2])
        key_pool = GeminiClientPool(["key_a", "key_b"], client_factory=mock_factory)

        pool = GeminiPool(models=["mock-model"], max_attempts=1)
        with self.assertRaises(EvaluationUnavailable):
            pool.evaluate(key_pool, "Evaluate this job", None)

        self.assertTrue(key_pool.is_all_exhausted())


if __name__ == "__main__":
    unittest.main()
