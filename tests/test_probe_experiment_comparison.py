import unittest

from experiments.probe_experiment import (
    linear_probing_theory,
    run_comparison_experiment,
)


class ComparisonExperimentTests(unittest.TestCase):
    def test_linear_probing_theoretical_probe_counts(self):
        success, failure = linear_probing_theory(0.1)
        self.assertAlmostEqual(success, 0.5 * (1 + 1 / 0.9))
        self.assertAlmostEqual(failure, 0.5 * (1 + 1 / (0.9**2)))

        success, failure = linear_probing_theory(0.9)
        self.assertAlmostEqual(success, 5.5)
        self.assertAlmostEqual(failure, 50.5)

    def test_both_tables_measure_the_same_key_set_and_capacity(self):
        rows = run_comparison_experiment(
            load_factors=(0.1, 0.9), capacity=31, failed_queries=20
        )
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0][0], round(3 / 31, 6))
        self.assertAlmostEqual(rows[1][0], round(28 / 31, 6))
        for row in rows:
            self.assertEqual(len(row), 9)
            self.assertTrue(all(value >= 0 for value in row[1:]))


if __name__ == "__main__":
    unittest.main()
