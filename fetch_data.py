"""Module to fetch FPL team data from the Fantasy Premier League API."""

import csv
import json
from pathlib import Path

import requests

FPL_API_BASE = "https://fantasy.premierleague.com/api"


def get_bootstrap_static() -> dict:
    """Fetch bootstrap-static data from the FPL API.

    This contains league-wide data including average scores per gameweek.

    Returns:
        dict containing 'events' (gameweek data with averages), 'teams',
        'elements' (players), and game settings

    Raises:
        requests.HTTPError: If the API request fails
    """
    url = f"{FPL_API_BASE}/bootstrap-static/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_team_history(manager_id: int | str) -> dict:
    """Fetch a manager's season history from the FPL API.

    Args:
        manager_id: The FPL team ID

    Returns:
        dict containing 'current' (gameweek data), 'past' (previous seasons),
        and 'chips' (chips used)

    Raises:
        requests.HTTPError: If the API request fails
    """
    url = f"{FPL_API_BASE}/entry/{manager_id}/history/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def history_to_csv_rows(history: dict) -> list[dict]:
    """Convert FPL API history response to CSV row format.

    Maps API fields to CSV columns:
        event -> GW (formatted as "GW{n}")
        overall_rank -> OR
        total_points -> OP
        rank -> GWR (gameweek rank)
        points -> GWP
        points_on_bench -> PB
        event_transfers -> TM
        event_transfers_cost -> TC
        value -> £ (divided by 10, API returns 0.1£ units)

    Args:
        history: Response from get_team_history()

    Returns:
        List of dicts ready for csv.DictWriter, sorted by gameweek descending
    """
    rows = []
    for gw_data in history.get("current", []):
        row = {
            "GW": f"GW{gw_data['event']}",
            "OR": gw_data["overall_rank"],
            "#": "",  # Empty column maintained for format compatibility
            "OP": gw_data["total_points"],
            "GWR": gw_data.get("rank", "-") or "-",
            "GWP": gw_data["points"],
            "PB": gw_data["points_on_bench"],
            "TM": gw_data["event_transfers"],
            "TC": gw_data["event_transfers_cost"],
            "£": gw_data["value"] / 10,  # Convert from 0.1£ to £
        }
        rows.append(row)

    # Sort by gameweek descending (newest first) to match existing format
    rows.sort(key=lambda r: int(r["GW"][2:]), reverse=True)
    return rows


def write_season_csv(rows: list[dict], output_path: Path) -> None:
    """Write FPL data rows to a CSV file.

    Args:
        rows: List of row dicts from history_to_csv_rows()
        output_path: Path to write the CSV file
    """
    fieldnames = ["GW", "OR", "#", "OP", "GWR", "GWP", "PB", "TM", "TC", "£"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_bootstrap_data(output_path: Path | None = None) -> Path:
    """Fetch and save bootstrap-static data (contains average points per GW).

    Args:
        output_path: Path to write JSON file. Defaults to data/bootstrap.json

    Returns:
        Path to the saved JSON file
    """
    if output_path is None:
        output_path = Path(__file__).parent / "data" / "bootstrap.json"

    print("Fetching bootstrap-static data...")
    data = get_bootstrap_static()

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved bootstrap data to {output_path}")

    return output_path


def load_season_ids(json_path: Path | None = None) -> dict[str, str]:
    """Load season -> FPL ID mapping from JSON file.

    Args:
        json_path: Path to id.json file. Defaults to data/id.json

    Returns:
        Dict mapping season code (e.g., "2526") to FPL manager ID
    """
    if json_path is None:
        json_path = Path(__file__).parent / "data" / "id.json"

    with open(json_path) as f:
        return json.load(f)


def fetch_and_save_season(season: str, manager_id: str | None = None) -> Path:
    """Fetch FPL data for a season and save to CSV.

    Args:
        season: Season code (e.g., "2526")
        manager_id: Optional FPL manager ID. If not provided, looks up from
        id.json

    Returns:
        Path to the saved CSV file

    Raises:
        KeyError: If season not found in id.json and manager_id not provided
        requests.HTTPError: If API request fails
    """
    if manager_id is None:
        ids = load_season_ids()
        manager_id = ids[season]

    print(f"Fetching data for season {season} (manager ID: {manager_id})...")
    history = get_team_history(manager_id)

    rows = history_to_csv_rows(history)
    print(f"Retrieved {len(rows)} gameweeks")

    output_path = Path(__file__).parent / "data" / f"{season}.csv"
    write_season_csv(rows, output_path)
    print(f"Saved to {output_path}")

    return output_path


def fetch_current_season() -> Path:
    """Fetch data for the current (most recent) season in id.json.

    Returns:
        Path to the saved CSV file
    """
    ids = load_season_ids()
    # Get the most recent season (highest key when sorted)
    current_season = max(ids.keys())
    return fetch_and_save_season(current_season)


if __name__ == "__main__":
    # When run directly, fetch the current season and bootstrap data
    csv_path = fetch_current_season()
    print(f"\nData saved to {csv_path}")

    bootstrap_path = save_bootstrap_data()
    print(f"Bootstrap data saved to {bootstrap_path}")
