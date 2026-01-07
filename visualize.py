"""FPL rank evolution visualization module."""

import csv
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter
import numpy as np

plt.style.use("petroff10")


def load_fpl_data(csv_path):
    """Load and parse FPL data from CSV file.

    Handles both 2425 format (sequential GW1->GW38) and 2526 format
    (reverse order with GW prefix).

    Args:
        csv_path: Path to CSV file

    Returns:
        dict with keys: gw, or_vals, gwr, tc (lists of values)
    """
    data = {
        "gw": [],
        "or_vals": [],  # Overall Rank values
        "gwr": [],  # Gameweek Rank values (may have None for missing)
        "tc": [],  # Transfer Cost
    }

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        for row in rows:
            # Extract gameweek number (handle "GW21" format)
            gw_str = row["GW"].strip()
            if gw_str.startswith("GW"):
                gw_str = gw_str[2:]

            try:
                gw = int(gw_str)
            except ValueError:
                continue  # Skip invalid rows

            # Extract Overall Rank
            try:
                or_val = int(row["OR"])
            except (ValueError, KeyError):
                continue  # Skip if OR is missing

            # Extract Gameweek Rank (handle missing values)
            gwr_val = None
            if "GWR" in row:
                gwr_str = row["GWR"].strip()
                if gwr_str and gwr_str != "-":
                    try:
                        gwr_val = int(gwr_str)
                    except ValueError:
                        pass  # Keep as None

            # Extract Transfer Cost
            tc_val = 0
            if "TC" in row:
                try:
                    tc_val = int(row["TC"])
                except (ValueError, TypeError):
                    tc_val = 0

            data["gw"].append(gw)
            data["or_vals"].append(or_val)
            data["gwr"].append(gwr_val)
            data["tc"].append(tc_val)

    # Sort by gameweek (handles reversed order in 2526 format)
    sorted_indices = sorted(
        range(len(data["gw"])), key=lambda i: data["gw"][i]
    )
    for key in data:
        data[key] = [data[key][i] for i in sorted_indices]

    return data


def format_rank(value, pos):
    """Format rank values as 10M, 1M, 100k, 10k."""
    if value >= 1e7:
        return f"{int(value / 1e6)}M"
    elif value >= 1e6:
        return f"{int(value / 1e6)}M"
    elif value >= 1e5:
        return f"{int(value / 1e3)}k"
    elif value >= 1e4:
        return f"{int(value / 1e3)}k"
    else:
        return f"{int(value)}"


def plot_rank_evolution(csv_path):
    """Generate FPL rank evolution visualization.

    Creates a plot showing Overall Rank and Gameweek Rank evolution
    over the season, with hits highlighted.

    Args:
        csv_path: Path to CSV file (e.g., "data/2425.csv")

    Output:
        Saves PNG to imgs/ directory with same base name as input CSV
    """
    # Load data
    data = load_fpl_data(csv_path)

    if not data["gw"]:
        print(f"No valid data found in {csv_path}")
        return

    # Calculate statistics
    final_or = data["or_vals"][-1]
    last_gw = data["gw"][-1]

    # Determine if season is complete (GW38) or ongoing
    or_label = "(Final)" if last_gw == 38 else "(Current)"

    # Calculate mean GWR (excluding None values)
    valid_gwr = [g for g in data["gwr"] if g is not None]
    mean_gwr = np.mean(valid_gwr) if valid_gwr else None

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # 1. Plot hits as vertical bars (TC > 0)
    for i, (gw, tc) in enumerate(zip(data["gw"], data["tc"], strict=False)):
        if tc > 0:
            ax.axvspan(
                gw - 0.25,
                gw + 0.25,
                color="C2",
                alpha=0.3,
                label="Hits" if i == 0 or data["tc"][i - 1] == 0 else "",
                lw=0,
                ec=None,
                zorder=0,
            )

    # 2. Plot Overall Rank line
    ax.plot(
        data["gw"],
        data["or_vals"],
        color="C0",
        linewidth=2,
        marker="o",
        markersize=8,
        label="OR",
        mec="w",
        mew=1,
        zorder=4,
    )

    # 3. Plot final/current OR horizontal line
    ax.axhline(
        y=final_or,
        color="C0",
        linestyle="--",
        linewidth=1.5,
        label=or_label,
        zorder=3,
    )

    # 4. Plot Gameweek Ranks (only where data exists)
    gw_with_gwr = [
        gw
        for gw, gwr in zip(data["gw"], data["gwr"], strict=False)
        if gwr is not None
    ]
    gwr_valid = [gwr for gwr in data["gwr"] if gwr is not None]

    if gw_with_gwr:
        ax.plot(
            gw_with_gwr,
            gwr_valid,
            color="C1",
            marker="D",
            markersize=8,
            linestyle="none",
            label="GWR",
            mec="w",
            mew=1,
            zorder=2,
        )

    # 5. Plot mean GWR horizontal line
    if mean_gwr is not None:
        ax.axhline(
            y=mean_gwr,
            color="C1",
            linestyle="--",
            linewidth=1.5,
            label="(Mean)",
            zorder=1,
        )

    # Set log scale and limits
    ax.set_yscale("log")
    ax.set_ylim(1e4, 1e7)
    ax.invert_yaxis()  # Invert so better ranks (lower values) are at the top

    # Set x-axis limits and ticks
    ax.set_xlim(0.5, 38.5)

    # X-axis: major ticks on even GWs, minor ticks on odd GWs
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    # Y-axis: custom formatter for human-readable ranks
    ax.yaxis.set_major_formatter(FuncFormatter(format_rank))

    # Labels
    ax.set_xlabel("GW", fontsize=12)
    ax.set_ylabel("Rank", fontsize=12)

    # Grid
    ax.xaxis.set_ticks_position("both")
    ax.yaxis.set_ticks_position("both")
    ax.grid(True, which="major", alpha=0.75, ls=":", zorder=-1)

    # Legend - remove duplicate 'Hits' labels
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles, strict=False))
    ax.legend(
        by_label.values(),
        by_label.keys(),
        loc="upper right",
        fontsize=11,
        frameon=True,
    )

    # Tight layout
    plt.tight_layout()

    # Save figure
    csv_path_obj = Path(csv_path)
    # Save to imgs/ directory in fplplot
    script_dir = Path(__file__).parent
    output_path = script_dir / "imgs" / f"{csv_path_obj.stem}.png"
    output_path.parent.mkdir(exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved visualization to {output_path}")

    plt.close()
