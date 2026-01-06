# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`fplplot` is a Python tool for analyzing and visualizing Fantasy Premier League (FPL) data. The project is in early development stages.

## Development Setup

This project uses `uv` for Python package management (similar to `pip` but faster).

- Python version: 3.12 (specified in `.python-version`)
- Project configuration: `pyproject.toml`
- Main entry point: `main.py`
- Dependencies: matplotlib (≥3.8.0), numpy (≥1.26.0)
  - Note: Uses matplotlib's `petroff10` style (available in matplotlib ≥3.10)

### Common Commands

```bash
# Install dependencies
uv sync

# Generate visualization for current season
uv run python main.py

# Generate visualization for specific season
uv run python -c "from visualize import plot_rank_evolution; plot_rank_evolution('data/2425.csv')"
```

## Code Architecture

The codebase has a simple two-module structure:

- **`main.py`**: Entry point that calls `plot_rank_evolution()` for the current season (2526.csv)
- **`visualize.py`**: Core visualization logic
  - `load_fpl_data()`: Parses CSV and handles both format variations
  - `plot_rank_evolution()`: Generates and saves the rank evolution plot
  - `format_rank()`: Formats rank values for display (e.g., "1M", "100k")

## Data Structure

FPL data is stored as CSV files in the `data/` directory:

- `data/2425.csv` - Season 2024/25 data (complete, GW1→GW38 sequential)
- `data/2526.csv` - Season 2025/26 data (ongoing, reverse order GW21→GW1)

### CSV Format

**Common columns:**
- `GW` - Gameweek number (format: "1" or "GW21")
- `OR` - Overall Rank
- `OP` - Overall Points (cumulative)
- `GWR` - Gameweek Rank (may be "-" for missing data)
- `GWP` - Gameweek Points
- `PB` - Points on Bench
- `TM` - Transfers Made
- `TC` - Transfer Cost (>0 indicates "hits" taken)
- `£` - Team Value

**Format variations:**
- 2526.csv has an extra `#` column (ignored by parser)
- 2526.csv has gameweeks in reverse order (automatically sorted by `load_fpl_data()`)
- GWR values may be missing ("-") in ongoing seasons

## Directory Structure

```
fplplot/
├── main.py              # Entry point script
├── visualize.py         # Visualization module
├── pyproject.toml       # Project dependencies and metadata
├── .python-version      # Python version specification
├── data/                # FPL season data CSV files
│   ├── 2425.csv
│   └── 2526.csv
└── imgs/                # Generated visualization outputs (auto-created)
    ├── 2425.png
    └── 2526.png
```

## Visualization Details

The `plot_rank_evolution()` function generates plots with the following features:

**Visual elements:**
- **Overall Rank (OR)**: Blue line with circle markers showing rank progression
- **Gameweek Rank (GWR)**: Orange diamond markers for individual gameweek performance
- **Reference lines**:
  - Blue dashed line: Final rank (complete seasons) or current rank (ongoing)
  - Orange dashed line: Mean GWR across all gameweeks
- **Hits**: Pink vertical bars highlighting gameweeks where TC > 0 (transfer penalties)
- **Log scale**: Y-axis uses inverted logarithmic scale (better ranks appear higher)
  - Range: 10k to 10M
  - Tick labels formatted as "1M", "100k", etc.

**Data handling:**
- Automatically sorts gameweeks chronologically (handles reversed CSV order)
- Skips missing GWR values (common in ongoing seasons)
- Creates `imgs/` directory if it doesn't exist
- Output filename matches input CSV basename (e.g., `data/2425.csv` → `imgs/2425.png`)
