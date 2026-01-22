# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`fplot` is a Python tool for analyzing and visualizing Fantasy Premier League (FPL) data. The project is in early development stages.

## Development Setup

This project uses `uv` for Python package management (similar to `pip` but faster).

- Python version: 3.12 (specified in `.python-version`)
- Project configuration: `pyproject.toml`
- Main entry point: `main.py`
- Dependencies: matplotlib (≥3.8.0), numpy (≥1.26.0), requests (≥2.32.0)
  - Note: Uses matplotlib's `petroff10` style (available in matplotlib ≥3.10)

### Common Commands

```bash
# Install dependencies
uv sync

# Fetch latest data from FPL API (updates CSV and bootstrap.json)
uv run python fetch_data.py

# Generate visualizations for current season
uv run python main.py

# Generate visualization for specific season
uv run python -c "from visualize import plot_rank_evolution, plot_points_evolution; plot_rank_evolution('data/2425.csv'); plot_points_evolution('data/2425.csv')"
```

## Code Architecture

The codebase has a three-module structure:

- **`main.py`**: Entry point that calls visualization functions for the current season (2526.csv)
- **`fetch_data.py`**: FPL API data fetching
  - `get_team_history()`: Fetches manager's season history from FPL API
  - `get_bootstrap_static()`: Fetches league-wide data (includes GW averages)
  - `history_to_csv_rows()`: Converts API response to CSV format, including chips
  - `fetch_and_save_season()`: Fetches and saves data for a season
  - `fetch_current_season()`: Fetches data for the most recent season in id.json
- **`visualize.py`**: Core visualization logic
  - `load_fpl_data()`: Parses CSV and handles both format variations
  - `load_bootstrap_averages()`: Loads average points per GW from bootstrap.json
  - `plot_hits_and_chips()`: Helper to plot hits and chips bars on any axis
  - `plot_rank_evolution()`: Generates rank evolution plot (saves to `*_rank.png`)
  - `plot_points_evolution()`: Generates points per GW plot (saves to `*_points.png`)
  - `format_rank()`: Formats rank values for display (e.g., "1M", "100k")

## Data Structure

FPL data is stored as CSV files in the `data/` directory:

- `data/2425.csv` - Season 2024/25 data (complete, GW1→GW38 sequential)
- `data/2526.csv` - Season 2025/26 data (ongoing, reverse order GW21→GW1)

### CSV Format

**Columns:**
- `GW` - Gameweek number (format: "1" or "GW21")
- `OR` - Overall Rank
- `#` - Empty column (format compatibility)
- `OP` - Overall Points (cumulative)
- `GWR` - Gameweek Rank (may be "-" for missing data)
- `GWP` - Gameweek Points
- `PB` - Points on Bench
- `TM` - Transfers Made
- `TC` - Transfer Cost (>0 indicates "hits" taken)
- `£` - Team Value
- `Chip` - Chip played: WC (Wildcard), BB (Bench Boost), TC (Triple Captain), FH (Free Hit), or empty

**Format notes:**
- Gameweeks may be in reverse order (automatically sorted by `load_fpl_data()`)
- GWR values may be missing ("-") in ongoing seasons
- Chip column is optional for backward compatibility with older CSV files

## Directory Structure

```
fplot/
├── main.py              # Entry point script
├── fetch_data.py        # FPL API data fetching module
├── visualize.py         # Visualization module
├── fplot.mplstyle     # Custom matplotlib style
├── pyproject.toml       # Project dependencies and metadata
├── .python-version      # Python version specification
├── data/                # FPL data files
│   ├── id.json          # Manager ID mapping (season -> FPL ID)
│   ├── bootstrap.json   # League-wide data (GW averages, etc.)
│   ├── 2425.csv         # Season 2024/25 data
│   └── 2526.csv         # Season 2025/26 data
└── imgs/                # Generated visualization outputs (auto-created)
    ├── 2425_rank.png
    ├── 2425_points.png
    ├── 2526_rank.png
    └── 2526_points.png
```

## Visualization Details

### Rank Evolution Plot (`plot_rank_evolution`)

**Visual elements:**
- **Overall Rank (OR)**: Blue line with circle markers showing rank progression
- **Gameweek Rank (GWR)**: Orange diamond markers for individual gameweek performance
- **Reference lines**:
  - Blue dashed line: Final rank (complete seasons) or current rank (ongoing)
  - Orange dashed line: Mean GWR across all gameweeks
- **Hits**: Narrow vertical bars (color C2) highlighting gameweeks where TC > 0
- **Chips**: Wide vertical bars (color C4) with white text labels (WC, BB, TC, FH)
- **Log scale**: Y-axis uses inverted logarithmic scale (better ranks appear higher)
  - Limits auto-determined by data
  - Tick labels formatted as "1M", "100k", etc.

### Points Evolution Plot (`plot_points_evolution`)

**Visual elements:**
- **Gameweek Points (GWP)**: Blue line with circle markers
- **Points on Bench (PB)**: Pink line with square markers
- **Average**: Orange dashed line showing league-wide average (from bootstrap.json)
- **Hits**: Narrow vertical bars (color C2) highlighting gameweeks where TC > 0
- **Chips**: Wide vertical bars (color C4) with white text labels
- **Linear scale**: Y-axis starts at 0, upper limit auto-determined by data

### Common Features

- Automatically sorts gameweeks chronologically (handles reversed CSV order)
- Skips missing GWR values (common in ongoing seasons)
- Creates `imgs/` directory if it doesn't exist
- Output filenames: `{season}_rank.png` and `{season}_points.png`
- Chip labels positioned at 95% of y-axis using axes transform
