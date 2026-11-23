import unittest

from src.hash_table import ChainingHashTable, LinearProbingHashTable


class SharedHashTableTests(unittest.TestCase):
    def test_shared_interface_behaves_consistently(self):
        for table_type in (ChainingHashTable, LinearProbingHashTable):
            with self.subTest(table_type=table_type.__name__):
                table = table_type(initial_capacity=8, auto_resize=False)
                self.assertIsNone(table.get("missing"))
                table.put("one", 1)
                table.put("two", 2)
                table.put("one", "updated")
                self.assertEqual(table.get("one"), "updated")
                self.assertTrue(table.contains("two"))
                self.assertTrue(table.delete("one"))
                self.assertFalse(table.contains("one"))
                self.assertEqual(len(table), 1)


class LinearProbingHashTableTests(unittest.TestCase):
    def test_probe_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(initial_capacity=4, auto_resize=False)
        table.put("c", 1)
        table.put("g", 2)
        table.put("k", 3)

        self.assertEqual(table.get("k"), 3)
        self.assertEqual(table.last_probes, 3)
        self.assertIn("probe path=(3, 0, 1)", table.debug_slots()[1][1][0])

    def test_tombstone_preserves_lookup_and_is_reused(self):
        table = LinearProbingHashTable(initial_capacity=4, auto_resize=False)
        table.put("c", 1)
        table.put("g", 2)
        table.put("k", 3)

        self.assertTrue(table.delete("g"))
        self.assertEqual(table.get("k"), 3)
        self.assertEqual(table.last_probes, 3)
        table.put("o", 4)
        self.assertEqual(table.get("o"), 4)
        self.assertIn("'o' -> 4", table.debug_slots()[0][1][0])

    def test_full_fixed_table_raises_overflow_but_update_succeeds(self):
        table = LinearProbingHashTable(
            initial_capacity=2, max_load_factor=1, auto_resize=False
        )
        table.put("a", 1)
        table.put("b", 2)
        table.put("a", "updated")
        self.assertEqual(table.get("a"), "updated")
        with self.assertRaises(OverflowError):
            table.put("c", 3)

    def test_expands_and_rehashes_before_exceeding_load_factor(self):
        table = LinearProbingHashTable(initial_capacity=4, max_load_factor=0.5)
        table.put("c", 1)
        table.put("g", 2)
        self.assertEqual(table.capacity, 4)

        table.put("k", 3)
        self.assertEqual(table.capacity, 8)
        self.assertEqual([table.get(key) for key in ("c", "g", "k")], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
