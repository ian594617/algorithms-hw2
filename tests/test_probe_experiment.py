import unittest

from experiments.probe_experiment import chaining_theory, run_chaining_experiment


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


if __name__ == "__main__":
    unittest.main()
