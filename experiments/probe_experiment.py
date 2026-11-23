"""Measure separate-chaining lookup costs and compare them with theory."""

import csv
from pathlib import Path

from src.hash_table import ChainingHashTable


def chaining_theory(alpha: float) -> tuple[float, float]:
    if alpha < 0:
        raise ValueError("load factor must be non-negative")
    return 1 + alpha / 2, alpha


def run_chaining_experiment(
    load_factors: tuple[float, ...] | None = None,
    capacity: int = 503,
    failed_queries: int = 1000,
) -> list[tuple[float, float, float, float, float]]:
    if capacity <= 0 or failed_queries <= 0:
        raise ValueError("capacity and failed_queries must be positive")
    if load_factors is None:
        load_factors = tuple(step / 4 for step in range(1, 17))

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
        keys = [f"key-{index:06d}" for index in range(key_count)]
        for index, key in enumerate(keys):
            table.put(key, index)

        successful_probes = 0
        for key in keys:
            table.get(key)
            successful_probes += table.last_probes

        failed_probes = 0
        for index in range(failed_queries):
            table.get(f"missing-{index:06d}")
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


def write_chaining_outputs(
    results: list[tuple[float, float, float, float, float]],
    output_directory: Path | None = None,
) -> tuple[Path, Path]:
    directory = output_directory or Path(__file__).parent
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "probe_results.csv"
    svg_path = directory / "probe_results.svg"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
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
    results = run_chaining_experiment()
    write_chaining_outputs(results)
    print("alpha,success_measured,success_theory,failure_measured,failure_theory")
    for row in results:
        print(",".join(f"{value:.4f}" for value in row))
    print("Wrote experiments/probe_results.csv and experiments/probe_results.svg")


if __name__ == "__main__":
    main()
