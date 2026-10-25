import unittest
from scripts.evaluate_dataset import compute_metrics, evaluate_dataset_file


class TestBenchmarkMetrics(unittest.TestCase):
    def test_compute_metrics_all_positive(self):
        results = [
            {"predicted": "relevant", "expected": "relevant"},
            {"predicted": "relevant", "expected": "relevant"}
        ]
        m = compute_metrics(results)
        self.assertEqual(m["tp"], 2)
        self.assertEqual(m["fp"], 0)
        self.assertEqual(m["precision"], 1.0)
        self.assertEqual(m["recall"], 1.0)
        self.assertEqual(m["f1"], 1.0)
        self.assertEqual(m["false_negatives"], [])

    def test_compute_metrics_division_by_zero_returns_none(self):
        results = []
        m = compute_metrics(results)
        self.assertIsNone(m["precision"])
        self.assertIsNone(m["recall"])
        self.assertIsNone(m["f1"])

    def test_evaluate_dataset_file_runs(self):
        m = evaluate_dataset_file("data/evaluation_benchmark_template.json", include_borderline=False)
        self.assertGreater(m["total_samples"], 0)
        self.assertIn("tp", m)
        self.assertIn("fp", m)


if __name__ == "__main__":
    unittest.main()
