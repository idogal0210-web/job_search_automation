import unittest

import src.fetchers as fetchers_mod
from src.fetchers import FETCHERS
from src.config import get_search_keywords


class FetchersRegistryTests(unittest.TestCase):
    def test_fetcher_registry_active_sources_only(self):
        expected_sources = {"linkedin", "drushim", "comeet", "greenhouse", "lever"}
        self.assertEqual(set(FETCHERS.keys()), expected_sources)

    def test_config_search_keywords_supported_sources(self):
        keywords = get_search_keywords()
        self.assertNotIn("indeed", keywords)
        self.assertNotIn("glassdoor", keywords)
        self.assertIn("energy", keywords)
        self.assertIn("drones", keywords)
        self.assertIn("drushim", keywords)

    def test_decommissioned_symbols_removed_completely(self):
        self.assertFalse(hasattr(fetchers_mod, "fetch_indeed_jobs"))
        self.assertFalse(hasattr(fetchers_mod, "fetch_glassdoor_jobs"))
        self.assertFalse(hasattr(fetchers_mod, "IndeedFetcher"))
        self.assertFalse(hasattr(fetchers_mod, "GlassdoorFetcher"))


if __name__ == "__main__":
    unittest.main()
