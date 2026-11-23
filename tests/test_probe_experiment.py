import csv
import random
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from experiments.probe_experiment import (
    _random_urls,
    chaining_theory,
    run_chaining_experiment,
    write_chaining_outputs,
)


class ChainingExperimentTests(unittest.TestCase):
    def test_theoretical_probe_counts(self):
        self.assertEqual(chaining_theory(0.25), (1.125, 0.25))
        self.assertEqual(chaining_theory(4.0), (3.0, 4.0))

    def test_measurement_includes_requested_load_factors_and_probe_counts(self):
        rows = run_chaining_experiment(
            load_factors=(0.25, 4.0), capacity=31, failed_queries=20
        )
        self.assertEqual([row[0] for row in rows], [round(8 / 31, 6), 4.0])
        for row in rows:
            self.assertGreater(row[1], 0)
            self.assertGreaterEqual(row[3], 0)
            self.assertGreaterEqual(row[2], 0)
            self.assertGreaterEqual(row[4], 0)

    def test_default_run_uses_professor_capacity_and_load_range(self):
        rows = run_chaining_experiment(failed_queries=5)

        self.assertEqual(len(rows), 16)
        self.assertEqual(rows[0][0], round(1023 / 4093, 6))
        self.assertEqual(rows[-1][0], 4.0)

    def test_random_urls_are_unique_valid_and_reproducible(self):
        urls = _random_urls(20, random.Random(17))

        self.assertEqual(urls, _random_urls(20, random.Random(17)))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(urlsplit(url).scheme == "https" for url in urls))
        self.assertTrue(
            all(urlsplit(url).hostname.endswith(".example.com") for url in urls)
        )

    def test_writes_results_csv_and_svg(self):
        rows = run_chaining_experiment(
            load_factors=(0.25, 0.5), capacity=31, failed_queries=10
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path, svg_path = write_chaining_outputs(rows, Path(temporary_directory))

            self.assertEqual(csv_path.name, "results.csv")
            self.assertEqual(svg_path.name, "results.svg")
            with csv_path.open(newline="", encoding="utf-8") as file:
                self.assertEqual(len(list(csv.reader(file))), 3)
            self.assertIn("Separate chaining probe counts", svg_path.read_text())


if __name__ == "__main__":
    unittest.main()
