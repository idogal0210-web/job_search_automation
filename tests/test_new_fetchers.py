import unittest

from src.fetchers import (
    RunHealth,
    fetch_indeed_jobs,
    fetch_glassdoor_jobs,
    FETCHERS,
    IndeedFetcher,
    GlassdoorFetcher,
)
from src.config import get_search_keywords


class FetchersDecommissionedTests(unittest.TestCase):
    def test_fetcher_registry_excludes_decommissioned_sources(self):
        self.assertNotIn("indeed", FETCHERS)
        self.assertNotIn("glassdoor", FETCHERS)
        self.assertIn("linkedin", FETCHERS)
        self.assertIn("drushim", FETCHERS)
        self.assertIn("comeet", FETCHERS)

    def test_config_search_keywords_excludes_decommissioned_sources(self):
        keywords = get_search_keywords()
        self.assertNotIn("indeed", keywords)
        self.assertNotIn("glassdoor", keywords)
        self.assertIn("energy", keywords)
        self.assertIn("drones", keywords)
        self.assertIn("drushim", keywords)

    def test_decommissioned_fetchers_return_empty_safely(self):
        health = RunHealth()
        self.assertEqual(fetch_indeed_jobs(["SCADA"], health), [])
        self.assertEqual(fetch_glassdoor_jobs(["Turbine"], health), [])
        self.assertEqual(IndeedFetcher().fetch(["SCADA"], health), [])
        self.assertEqual(GlassdoorFetcher().fetch(["Turbine"], health), [])


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
