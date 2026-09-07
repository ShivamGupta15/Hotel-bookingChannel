"""Generate test dates in the hotel's dd-mm-yyyy format."""

import argparse
import json
from datetime import date, timedelta

DATE_FORMAT = "%d-%m-%Y"


def generate_dates(start_date: date, end_date: date) -> list[str]:
    """Return every date from start_date through end_date, inclusively."""
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date")

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime(DATE_FORMAT))
        current_date += timedelta(days=1)
    return dates


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate dates for bulk inventory API testing."
    )
    parser.add_argument(
        "--start",
        default=date.today().isoformat(),
        help="Start date in yyyy-mm-dd format (default: today)",
    )
    parser.add_argument(
        "--end",
        help="End date in yyyy-mm-dd format (default: same as start)",
    )
    args = parser.parse_args()

    start_date = parse_date(args.start)
    end_date = parse_date(args.end) if args.end else start_date
    print(json.dumps(generate_dates(start_date, end_date)))


if __name__ == "__main__":
    main()
