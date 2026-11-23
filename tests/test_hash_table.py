import unittest

from src.hash_table import ChainingHashTable


class ChainingHashTableTests(unittest.TestCase):
    def test_empty_table_operations(self):
        table = ChainingHashTable()
        self.assertIsNone(table.get("missing"))
        self.assertEqual(table.get("missing", "fallback"), "fallback")
        self.assertFalse(table.contains("missing"))
        self.assertFalse(table.delete("missing"))
        self.assertEqual(len(table), 0)

    def test_collisions_update_and_probe_counts(self):
        table = ChainingHashTable(initial_capacity=4, auto_resize=False)
        table.put("a", 1)
        table.put("e", 2)
        table.put("i", 3)

        self.assertEqual(table.get("e"), 2)
        self.assertEqual(table.last_probes, 2)
        self.assertEqual(table.get("i"), 3)
        self.assertEqual(table.last_probes, 3)
        self.assertEqual(table.get("m"), None)
        self.assertEqual(table.last_probes, 3)

        table.put("e", "updated")
        self.assertEqual(table.get("e"), "updated")
        self.assertEqual(len(table), 3)

    def test_delete_removes_key_and_preserves_other_collisions(self):
        table = ChainingHashTable(initial_capacity=4, auto_resize=False)
        table.put("a", 1)
        table.put("e", 2)
        table.put("i", 3)

        self.assertTrue(table.delete("e"))
        self.assertFalse(table.delete("e"))
        self.assertFalse(table.contains("e"))
        self.assertEqual(table.get("i"), 3)
        self.assertEqual(len(table), 2)

    def test_expands_before_exceeding_maximum_load(self):
        table = ChainingHashTable(initial_capacity=4, max_load_factor=0.5)
        table.put("a", 1)
        table.put("e", 2)
        self.assertEqual(table.capacity, 4)

        table.put("i", 3)
        self.assertEqual(table.capacity, 8)
        for key, value in (("a", 1), ("e", 2), ("i", 3)):
            self.assertEqual(table.get(key), value)

    def test_invalid_key_type_is_rejected(self):
        table = ChainingHashTable()
        with self.assertRaises(TypeError):
            table.put(1, "value")

    def test_invalid_capacity_and_load_factor_are_rejected(self):
        for kwargs in (
            {"initial_capacity": 0},
            {"initial_capacity": -1},
            {"max_load_factor": 0},
            {"max_load_factor": 1.1},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    ChainingHashTable(**kwargs)


if __name__ == "__main__":
    unittest.main()
