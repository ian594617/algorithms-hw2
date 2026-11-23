"""Measure separate-chaining lookup costs and compare them with theory."""

import argparse
import csv
import random
from pathlib import Path

from src.hash_table import ChainingHashTable, LinearProbingHashTable


DEFAULT_CHAINING_CAPACITY = 4093
DEFAULT_RANDOM_SEED = 2026


def _random_urls(
    count: int, generator: random.Random, host_prefix: str = ""
) -> list[str]:
    identifiers = generator.sample(range(1 << 32), count)
    return [
        f"https://{host_prefix}{identifier:08x}.example.com/"
        f"{generator.getrandbits(64):016x}"
        for identifier in identifiers
    ]


def chaining_theory(alpha: float) -> tuple[float, float]:
    if alpha < 0:
        raise ValueError("load factor must be non-negative")
    return 1 + alpha / 2, alpha


def run_chaining_experiment(
    load_factors: tuple[float, ...] | None = None,
    capacity: int = DEFAULT_CHAINING_CAPACITY,
    failed_queries: int = 1000,
    seed: int = DEFAULT_RANDOM_SEED,
) -> list[tuple[float, float, float, float, float]]:
    if capacity <= 0 or failed_queries <= 0:
        raise ValueError("capacity and failed_queries must be positive")
    if load_factors is None:
        load_factors = tuple(step / 4 for step in range(1, 17))

    generator = random.Random(seed)
    results = []
    for requested_alpha in load_factors:
        if requested_alpha <= 0:
            raise ValueError("load factors must be positive")
        key_count = max(1, round(requested_alpha * capacity))
        table = ChainingHashTable(
            initial_capacity=capacity,
            max_load_factor=1.0,
            auto_resize=False,
        )
        keys = _random_urls(key_count, generator)
        for index, key in enumerate(keys):
            table.put(key, index)

        successful_probes = 0
        for key in keys:
            table.get(key)
            successful_probes += table.last_probes

        failed_probes = 0
        for key in _random_urls(failed_queries, generator, "missing-"):
            table.get(key)
            failed_probes += table.last_probes

        alpha = round(table.load_factor, 6)
        successful_theory, failed_theory = chaining_theory(alpha)
        results.append(
            (
                alpha,
                successful_probes / key_count,
                successful_theory,
                failed_probes / failed_queries,
                failed_theory,
            )
        )
    return results


def linear_probing_theory(alpha: float) -> tuple[float, float]:
    if not 0 <= alpha < 1:
        raise ValueError("linear-probing load factor must be in [0, 1)")
    return 0.5 * (1 + 1 / (1 - alpha)), 0.5 * (1 + 1 / (1 - alpha) ** 2)


def run_comparison_experiment(
    load_factors: tuple[float, ...] | None = None,
    capacity: int = 503,
    failed_queries: int = 1000,
) -> list[tuple[float, float, float, float, float, float, float, float, float]]:
    if capacity <= 0 or failed_queries <= 0:
        raise ValueError("capacity and failed_queries must be positive")
    if load_factors is None:
        load_factors = tuple(step / 10 for step in range(1, 10))

    results = []
    for requested_alpha in load_factors:
        if not 0 < requested_alpha < 1:
            raise ValueError("comparison load factors must be in (0, 1)")
        key_count = max(1, round(requested_alpha * capacity))
        tables = (
            ChainingHashTable(
                initial_capacity=capacity,
                max_load_factor=1.0,
                auto_resize=False,
            ),
            LinearProbingHashTable(
                initial_capacity=capacity,
                max_load_factor=1.0,
                auto_resize=False,
            ),
        )
        keys = [f"key-{index:06d}" for index in range(key_count)]
        for index, key in enumerate(keys):
            for table in tables:
                table.put(key, index)

        successful_probes = [0, 0]
        for key in keys:
            for index, table in enumerate(tables):
                table.get(key)
                successful_probes[index] += table.last_probes

        failed_probes = [0, 0]
        for query_index in range(failed_queries):
            key = f"missing-{query_index:06d}"
            for index, table in enumerate(tables):
                table.get(key)
                failed_probes[index] += table.last_probes

        alpha = round(tables[0].load_factor, 6)
        chaining_success, chaining_failure = chaining_theory(alpha)
        linear_success, linear_failure = linear_probing_theory(alpha)
        results.append(
            (
                alpha,
                successful_probes[0] / key_count,
                chaining_success,
                failed_probes[0] / failed_queries,
                chaining_failure,
                successful_probes[1] / key_count,
                linear_success,
                failed_probes[1] / failed_queries,
                linear_failure,
            )
        )
    return results


def write_comparison_outputs(
    results: list[tuple[float, float, float, float, float, float, float, float, float]],
    output_directory: Path | None = None,
) -> tuple[Path, Path]:
    directory = output_directory or Path(__file__).parent
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "comparison_results.csv"
    svg_path = directory / "comparison_results.svg"

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
        writer.writerows(results)

    width, height = 1040, 700
    left, plot_width = 80, 650
    x_min = min(row[0] for row in results)
    x_max = max(row[0] for row in results)
    panels = (
        (
            "Successful lookup comparisons",
            (1, 2, 5, 6),
            ("Chaining measured", "Chaining theory", "Linear measured", "Linear theory"),
            ("#1565c0", "#64b5f6", "#2e7d32", "#81c784"),
            260,
            50,
        ),
        (
            "Unsuccessful lookup comparisons",
            (3, 4, 7, 8),
            ("Chaining measured", "Chaining theory", "Linear measured", "Linear theory"),
            ("#c62828", "#ef9a9a", "#6a1b9a", "#ce93d8"),
            260,
            390,
        ),
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    for title, columns, labels, colors, plot_height, top in panels:
        y_max = max(row[column] for row in results for column in columns) * 1.08

        def point(alpha: float, value: float) -> tuple[float, float]:
            x = left + (alpha - x_min) / (x_max - x_min) * plot_width
            y = top + plot_height - value / y_max * plot_height
            return x, y

        svg.extend(
            (
                f'<text x="{left + plot_width / 2}" y="{top - 14}" text-anchor="middle" font-family="sans-serif" font-size="16">{title}</text>',
                f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="black"/>',
                f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="black"/>',
            )
        )
        for tick in range(5):
            value = y_max * tick / 4
            y = top + plot_height - value / y_max * plot_height
            svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#ddd"/>')
            svg.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="10">{value:.1f}</text>')
        for series_index, (column, label, color) in enumerate(zip(columns, labels, colors)):
            coordinates = " ".join(
                f"{point(row[0], row[column])[0]:.1f},{point(row[0], row[column])[1]:.1f}"
                for row in results
            )
            svg.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2"/>')
            legend_y = top + 18 + series_index * 18
            svg.append(f'<line x1="{left + plot_width + 25}" y1="{legend_y}" x2="{left + plot_width + 45}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
            svg.append(f'<text x="{left + plot_width + 50}" y="{legend_y + 4}" font-family="sans-serif" font-size="11">{label}</text>')
        for row in results:
            x, y = point(row[0], 0)
            svg.append(f'<text x="{x:.1f}" y="{top + plot_height + 16}" text-anchor="middle" font-family="sans-serif" font-size="10">{row[0]:.1f}</text>')
    svg.extend(
        (
            '<text x="400" y="695" text-anchor="middle" font-family="sans-serif">Load factor (alpha)</text>',
            "</svg>",
        )
    )
    svg_path.write_text("\n".join(svg), encoding="utf-8")
    return csv_path, svg_path


def write_chaining_outputs(
    results: list[tuple[float, float, float, float, float]],
    output_directory: Path | None = None,
) -> tuple[Path, Path]:
    directory = output_directory or Path(__file__).parent
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "results.csv"
    svg_path = directory / "results.svg"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            (
                "load_factor",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        writer.writerows(results)

    width, height = 840, 500
    left, top, plot_width, plot_height = 80, 55, 700, 350
    x_max = max(result[0] for result in results)
    y_max = max(max(result[1], result[2], result[3], result[4]) for result in results)
    y_max = max(1.0, y_max * 1.1)

    def point(alpha: float, value: float) -> tuple[float, float]:
        x = left + alpha / x_max * plot_width
        y = top + plot_height - value / y_max * plot_height
        return x, y

    series = (
        (1, "Success measured", "#1769aa"),
        (2, "Success theory: 1 + alpha/2", "#42a5f5"),
        (3, "Failure measured", "#c62828"),
        (4, "Failure theory: alpha", "#ef5350"),
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="420" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">Separate chaining probe counts</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="black"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="black"/>',
        f'<text x="{left + plot_width / 2}" y="465" text-anchor="middle" font-family="sans-serif">Load factor (alpha)</text>',
        f'<text x="18" y="{top + plot_height / 2}" transform="rotate(-90 18 {top + plot_height / 2})" text-anchor="middle" font-family="sans-serif">Average key comparisons</text>',
    ]

    for tick in range(5):
        value = y_max * tick / 4
        y = top + plot_height - value / y_max * plot_height
        svg.append(f'<line x1="{left - 4}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#ddd"/>')
        svg.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11">{value:.1f}</text>')
        alpha = x_max * tick / 4
        x = left + plot_width * tick / 4
        svg.append(f'<text x="{x:.1f}" y="{top + plot_height + 20}" text-anchor="middle" font-family="sans-serif" font-size="11">{alpha:.2f}</text>')

    for series_index, (column, label, color) in enumerate(series):
        coordinates = " ".join(
            f"{point(result[0], result[column])[0]:.1f},{point(result[0], result[column])[1]:.1f}"
            for result in results
        )
        svg.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2"/>')
        legend_y = top + 18 + series_index * 20
        svg.append(f'<line x1="{left + 20}" y1="{legend_y}" x2="{left + 45}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="{left + 52}" y="{legend_y + 4}" font-family="sans-serif" font-size="12">{label}</text>')

    svg.append("</svg>")
    svg_path.write_text("\n".join(svg), encoding="utf-8")
    return csv_path, svg_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    if args.compare:
        results = run_comparison_experiment()
        write_comparison_outputs(results)
        print("Wrote experiments/comparison_results.csv and experiments/comparison_results.svg")
        for row in results:
            print(",".join(f"{value:.4f}" for value in row))
    else:
        results = run_chaining_experiment()
        write_chaining_outputs(results)
        print("alpha,success_measured,success_theory,failure_measured,failure_theory")
        for row in results:
            print(",".join(f"{value:.4f}" for value in row))
        print("Wrote experiments/results.csv and experiments/results.svg")


if __name__ == "__main__":
    main()
