import unittest
from unittest.mock import patch

import main


class MainCliTests(unittest.TestCase):
    def test_help_exits_without_running_pipeline(self):
        with patch.object(main, "load_context") as ctx, self.assertRaises(SystemExit) as cm:
            main.main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        ctx.assert_not_called()

    def test_no_argv_means_default_flags(self):
        args = main.parse_args(None)
        self.assertFalse(args.build_only)
        self.assertFalse(args.skip_email)

    def test_build_only_skips_fetch_and_ai(self):
        with patch.object(main, "load_context") as ctx, \
             patch.object(main, "collect_all_jobs") as fetch, \
             patch.object(main, "publish_dashboard", return_value=True) as pub:
            self.assertEqual(main.main(["--build-only"]), 0)
        ctx.assert_not_called()
        fetch.assert_not_called()
        pub.assert_called_once()

    def test_skip_email_never_dispatches(self):
        with patch.object(main, "load_context", return_value=(main.RunHealth(), set(), object(), None)), \
             patch.object(main, "collect_all_jobs", return_value=[]), \
             patch.object(main, "evaluate_all_jobs", return_value=([], {})), \
             patch.object(main, "publish_dashboard", return_value=True), \
             patch.object(main, "dispatch_notifications") as disp, \
             patch.object(main, "persist_state", return_value=True), \
             patch.object(main, "report_results", return_value=0):
            self.assertEqual(main.main(["--skip-email"]), 0)
        disp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
