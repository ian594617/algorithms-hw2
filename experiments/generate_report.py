"""Generate a compact, single-page PDF report from experiment CSV files."""

import argparse
import csv
from pathlib import Path


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"experiment results are empty: {path}")
    return rows


def _pdf_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_single_page_pdf(path: Path, lines: list[tuple[str, str, int]]) -> None:
    commands = []
    y = 755
    for text, font, size in lines:
        commands.append(
            f"BT /{font} {size} Tf 50 {y} Td ({_pdf_literal(text)}) Tj ET"
        )
        y -= 18 if size >= 10 else 14
    stream = "\n".join(commands).encode("ascii")
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    )

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)


def write_report(
    comparison_csv: Path,
    output_pdf: Path,
    chaining_csv: Path | None = None,
) -> Path:
    comparison_rows = _read_rows(comparison_csv)
    lines: list[tuple[str, str, int]] = [
        ("Hash Table Probe Costs - Algorithms HW2", "F1", 16),
        ("Goal: compare measured probes with uniform-hashing expectations.", "F1", 9),
        ("Capacity 503; same deterministic keys and insertion order for both tables.", "F1", 9),
        ("Theory: chaining success 1+alpha/2, failure alpha.", "F1", 9),
        ("Linear probing success 0.5*(1+1/(1-alpha)); failure 0.5*(1+1/(1-alpha)^2).", "F1", 9),
        ("Measured / theoretical averages (C=chaining, L=linear probing):", "F1", 9),
        (" alpha       C success       L success       C failure       L failure", "F2", 8),
    ]

    sample_count = min(6, len(comparison_rows))
    sample_indices = sorted(
        {round(index * (len(comparison_rows) - 1) / max(1, sample_count - 1)) for index in range(sample_count)}
    )
    for index in sample_indices:
        row = comparison_rows[index]
        lines.append(
            (
                f" {float(row['load_factor']):.2f}     "
                f"{float(row['chaining_success_measured']):.1f}/{float(row['chaining_success_theory']):.1f}"
                f"          {float(row['linear_success_measured']):.1f}/{float(row['linear_success_theory']):.1f}"
                f"          {float(row['chaining_failure_measured']):.1f}/{float(row['chaining_failure_theory']):.1f}"
                f"          {float(row['linear_failure_measured']):.1f}/{float(row['linear_failure_theory']):.1f}",
                "F2",
                7,
            )
        )

    lines.extend(
        (
            ("", "F1", 8),
            ("Interpretation", "F1", 11),
            ("At alpha <= 0.4, both measured successful searches need about one probe.", "F1", 9),
        )
    )
    high_load = comparison_rows[-1]
    lines.append(
        (
            f"At alpha={float(high_load['load_factor']):.2f}, linear success is "
            f"{float(high_load['linear_success_measured']):.1f} vs "
            f"{float(high_load['linear_success_theory']):.1f} theory; failure is "
            f"{float(high_load['linear_failure_measured']):.1f} vs "
            f"{float(high_load['linear_failure_theory']):.1f}.",
            "F1",
            9,
        )
    )
    lines.extend(
        (
            ("The formulas are expected costs under uniform hashing, not guarantees.", "F1", 9),
            ("Sequential keys with deterministic Horner hashing form primary clusters;", "F1", 9),
            ("this workload greatly increases linear-probing costs at high load.", "F1", 9),
        )
    )

    if chaining_csv is not None and chaining_csv.exists():
        chaining_rows = _read_rows(chaining_csv)
        lines.append(("", "F1", 8))
        lines.append(("Separate-chaining load range (alpha 0.25 to 4.0)", "F1", 11))
        for target in (0.25, 4.0):
            row = min(
                chaining_rows,
                key=lambda item: abs(float(item["load_factor"]) - target),
            )
            lines.append(
                (
                    f"alpha={float(row['load_factor']):.2f}: success "
                    f"{float(row['successful_measured']):.2f}/{float(row['successful_theory']):.2f}; "
                    f"failure {float(row['unsuccessful_measured']):.2f}/{float(row['unsuccessful_theory']):.2f} "
                    "(measured/theory).",
                    "F1",
                    9,
                )
            )
    lines.append(("One-page report; see the CSV and SVG files for full results.", "F1", 9))
    _write_single_page_pdf(output_pdf, lines)
    return output_pdf


def main() -> None:
    directory = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--comparison-csv", type=Path, default=directory / "comparison_results.csv"
    )
    parser.add_argument("--chaining-csv", type=Path, default=directory / "probe_results.csv")
    parser.add_argument("--output", type=Path, default=directory / "report.pdf")
    args = parser.parse_args()
    result = write_report(args.comparison_csv, args.output, args.chaining_csv)
    print(f"Wrote {result}")


if __name__ == "__main__":
    main()
