"""FPL rank evolution visualization module."""

import csv
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter
import numpy as np

plt.style.use(["petroff10", Path(__file__).parent / "fplot.mplstyle"])
save_dpi = 300


def load_fpl_data(csv_path):
    """Load and parse FPL data from CSV file.

    Handles both 2425 format (sequential GW1->GW38) and 2526 format
    (reverse order with GW prefix).

    Args:
        csv_path: Path to CSV file

    Returns:
        dict with keys: gw, or_vals, gwr, tc, gwp, pb (lists of values)
    """
    data = {
        "gw": [],
        "or_vals": [],  # Overall Rank values
        "gwr": [],  # Gameweek Rank values (may have None for missing)
        "tc": [],  # Transfer Cost
        "gwp": [],  # Gameweek Points
        "pb": [],  # Points on Bench
        "chips": [],  # Chips played (WC, BB, TC, FH or empty string)
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

            # Extract Gameweek Points
            gwp_val = 0
            if "GWP" in row:
                try:
                    gwp_val = int(row["GWP"])
                except (ValueError, TypeError):
                    gwp_val = 0

            # Extract Points on Bench
            pb_val = 0
            if "PB" in row:
                try:
                    pb_val = int(row["PB"])
                except (ValueError, TypeError):
                    pb_val = 0

            # Extract Chip (backward compatible - handle missing column)
            chip_val = ""
            if "Chip" in row:
                chip_val = row["Chip"].strip()

            data["gw"].append(gw)
            data["or_vals"].append(or_val)
            data["gwr"].append(gwr_val)
            data["tc"].append(tc_val)
            data["gwp"].append(gwp_val)
            data["pb"].append(pb_val)
            data["chips"].append(chip_val)

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


def load_bootstrap_averages(json_path=None):
    """Load average points per gameweek from bootstrap.json.

    Args:
        json_path: Path to bootstrap.json file. Defaults to data/bootstrap.json

    Returns:
        dict mapping gameweek number (int) to average points (int)
    """
    import json

    if json_path is None:
        json_path = Path(__file__).parent / "data" / "bootstrap.json"

    try:
        with open(json_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}

    averages = {}
    for event in data.get("events", []):
        gw = event.get("id")
        avg = event.get("average_entry_score")
        if gw is not None and avg is not None:
            averages[gw] = avg

    return averages


def plot_hits_and_chips(ax, data):
    """Plot hits and chips as vertical bars on the given axis.

    Chip labels are positioned at 95% of the y-axis span using axes transform,
    so this function works regardless of y-axis limits or scale.

    Args:
        ax: Matplotlib axis to plot on
        data: FPL data dict with 'gw', 'tc', and 'chips' keys
    """
    # Plot hits as vertical bars (TC > 0)
    for i, (gw, tc) in enumerate(zip(data["gw"], data["tc"], strict=False)):
        if tc > 0:
            ax.axvspan(
                gw - 0.1,
                gw + 0.1,
                color="C2",
                alpha=0.3,
                label="Hits" if i == 0 or data["tc"][i - 1] == 0 else "",
                lw=0,
                ec=None,
                zorder=9,
            )

    # Plot chips as vertical bars with labels
    chip_label_added = False
    for gw, chip in zip(data["gw"], data["chips"], strict=False):
        if chip:
            ax.axvspan(
                gw - 0.25,
                gw + 0.25,
                color="C4",
                alpha=0.4,
                label="Chips" if not chip_label_added else "",
                lw=0,
                ec=None,
                zorder=9,
            )
            # Use blended transform: x in data coords, y in axes coords (0-1)
            ax.text(
                gw,
                0.95,
                chip,
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=6,
                color="white",
                rotation=90,
                fontweight="bold",
                zorder=10,
            )
            chip_label_added = True


def plot_points_evolution(csv_path, ax=None):
    """Generate FPL points per gameweek visualization.

    Creates a plot showing Gameweek Points, Points on Bench, and
    league average points over the season, with hits highlighted.

    Args:
        csv_path: Path to CSV file (e.g., "data/2526.csv")
        ax: Optional matplotlib axis. If None, creates a new figure and saves PNG.

    Output:
        Saves PNG to imgs/ directory with _points suffix (only when ax is None)
    """
    # Load data
    data = load_fpl_data(csv_path)
    averages = load_bootstrap_averages()

    if not data["gw"]:
        print(f"No valid data found in {csv_path}")
        return

    # Create figure if no axis provided
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(10, 6))

    # 1. Plot hits and chips
    plot_hits_and_chips(ax, data)

    # 2. Plot Gameweek Points line
    ax.plot(
        data["gw"],
        data["gwp"],
        color="C0",
        linewidth=2,
        marker="o",
        markersize=8,
        label="GWP",
        mec="w",
        mew=1,
        zorder=14,
    )

    # 3. Plot Points on Bench line
    ax.plot(
        data["gw"],
        data["pb"],
        color="C3",
        linewidth=2,
        marker="s",
        markersize=7,
        label="PB",
        mec="w",
        mew=1,
        zorder=13,
    )

    # 4. Plot league average line (if available)
    if averages:
        avg_gws = [gw for gw in data["gw"] if gw in averages]
        avg_vals = [averages[gw] for gw in avg_gws]
        if avg_gws:
            ax.plot(
                avg_gws,
                avg_vals,
                color="C1",
                linewidth=2,
                linestyle="--",
                label="Average",
                zorder=12,
            )

    # Set y-axis (linear scale for points)
    ax.set_ylim(bottom=0)

    # Set x-axis limits and ticks
    ax.set_xlim(0.5, 38.5)

    # X-axis: major ticks on even GWs, minor ticks on odd GWs
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    # Labels
    if standalone:
        ax.set_xlabel("GW", fontsize=12)
    ax.set_ylabel("Points", fontsize=12)

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
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        borderaxespad=0,
        fontsize=11,
        frameon=False,
    )

    if standalone:
        plt.tight_layout()
        csv_path_obj = Path(csv_path)
        script_dir = Path(__file__).parent
        output_path = script_dir / "imgs" / f"{csv_path_obj.stem}_points.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=save_dpi, bbox_inches="tight")
        print(f"Saved visualization to {output_path}")
        plt.close()


def plot_rank_evolution(csv_path, ax=None):
    """Generate FPL rank evolution visualization.

    Creates a plot showing Overall Rank and Gameweek Rank evolution
    over the season, with hits highlighted.

    Args:
        csv_path: Path to CSV file (e.g., "data/2425.csv")
        ax: Optional matplotlib axis. If None, creates a new figure and saves PNG.

    Output:
        Saves PNG to imgs/ directory with _rank suffix (only when ax is None)
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

    # Create figure if no axis provided
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(10, 6))

    # 1. Plot hits and chips
    plot_hits_and_chips(ax, data)

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
        zorder=14,
    )

    # 3. Plot final/current OR horizontal line
    ax.axhline(
        y=final_or,
        color="C0",
        linestyle="--",
        linewidth=1.5,
        label=or_label,
        zorder=13,
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
            zorder=12,
        )

    # 5. Plot mean GWR horizontal line
    if mean_gwr is not None:
        ax.axhline(
            y=mean_gwr,
            color="C1",
            linestyle="--",
            linewidth=1.5,
            label="(Mean)",
            zorder=11,
        )

    # Set log scale (limits auto-determined by data)
    ax.set_yscale("log")
    ax.invert_yaxis()  # Invert so better ranks (lower values) are at the top

    # Set x-axis limits and ticks
    ax.set_xlim(0.5, 38.5)

    # X-axis: major ticks on even GWs, minor ticks on odd GWs
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    # Y-axis: custom formatter for human-readable ranks
    ax.yaxis.set_major_formatter(FuncFormatter(format_rank))

    # Labels
    if standalone:
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
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        borderaxespad=0,
        fontsize=11,
        frameon=False,
    )

    if standalone:
        plt.tight_layout()
        csv_path_obj = Path(csv_path)
        script_dir = Path(__file__).parent
        output_path = script_dir / "imgs" / f"{csv_path_obj.stem}_rank.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=save_dpi, bbox_inches="tight")
        print(f"Saved visualization to {output_path}")
        plt.close()


def plot_season(csv_path):
    """Generate combined rank + points visualization for a season.

    Creates a single figure with rank evolution on top and points per GW
    on the bottom, sharing the x-axis.

    Args:
        csv_path: Path to CSV file (e.g., "data/2526.csv")

    Output:
        Saves PNG to imgs/ directory with the season stem as filename
    """
    fig, (ax_rank, ax_pts) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    plot_rank_evolution(csv_path, ax=ax_rank)
    plot_points_evolution(csv_path, ax=ax_pts)
    ax_pts.set_xlabel("GW", fontsize=12)
    plt.tight_layout()
    script_dir = Path(__file__).parent
    output_path = script_dir / "imgs" / f"{Path(csv_path).stem}.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=save_dpi, bbox_inches="tight")
    print(f"Saved visualization to {output_path}")
    plt.close()
