import csv
import tempfile
import unittest
from pathlib import Path

from experiments.generate_report import write_report


class ReportTests(unittest.TestCase):
    def test_generates_a_single_page_pdf_from_comparison_csv(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            csv_path = directory / "comparison.csv"
            pdf_path = directory / "report.pdf"
            with csv_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    (
                        "load_factor",
                        "chaining_success_measured",
                        "chaining_success_theory",
                        "chaining_failure_measured",
                        "chaining_failure_theory",
                        "linear_success_measured",
                        "linear_success_theory",
                        "linear_failure_measured",
                        "linear_failure_theory",
                    )
                )
                writer.writerow((0.5, 1.2, 1.25, 0.5, 0.5, 3.0, 1.5, 8.0, 2.5))

            self.assertEqual(write_report(csv_path, pdf_path), pdf_path)
            content = pdf_path.read_bytes()
            self.assertTrue(content.startswith(b"%PDF-1.4"))
            self.assertIn(b"/Count 1", content)
            self.assertIn(b"uniform hashing", content)


if __name__ == "__main__":
    unittest.main()
