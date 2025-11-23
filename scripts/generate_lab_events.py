"""Script to scrape Labs events and generate metadata JSON."""

import asyncio
import datetime
import json
import re
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch HTML content from a URL.

    Args:
        session: aiohttp ClientSession to use
        url: URL to fetch

    Returns:
        HTML content as string
    """
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def extract_player_count(html: str) -> int | None:
    """Extract player count from standings page HTML.

    Args:
        html: HTML content from standings page

    Returns:
        Player count as integer, or None if not found
    """
    # Look for pattern like "2117 players"
    match = re.search(r'(\d+)\s+players', html)
    if match:
        return int(match.group(1))
    return None


def extract_labs_list_items(page_html: str) -> tuple[list[str], list[str], list[str]]:
    """Extract tournament IDs, names, and dates from Labs homepage HTML.

    Args:
        page_html: HTML content from Labs homepage

    Returns:
        Tuple of (ids, names, dates)
    """
    soup = BeautifulSoup(page_html, 'html.parser')
    ul = soup.select_one('ul.grid')
    if not ul:
        raise ValueError("No <ul class='grid'> found")

    # Get all immediate <li> children
    lis = ul.find_all('li', recursive=False)

    ids = []
    names = []
    dates = []

    for li in lis:
        a = li.find('a', recursive=False)
        if not a or not a.has_attr('href'):
            continue

        # Extract ID from href
        href_split = a['href'].split('/')
        if len(href_split) < 2:
            continue
        tournament_id = href_split[1]
        ids.append(tournament_id)

        # Extract name and date from divs
        divs_inside_a = a.find_all("div", recursive=False)
        if len(divs_inside_a) >= 1:
            inner_divs = divs_inside_a[0].find_all("div", recursive=False)
            if len(inner_divs) >= 2:
                text1 = inner_divs[0].get_text(strip=True)
                text2 = inner_divs[1].get_text(strip=True)
            else:
                text1 = text2 = None
        else:
            text1 = text2 = None

        names.append(text1 or "Unknown Event")

        # Parse date
        if text2:
            try:
                dash_index = text2.find("–")
                comma_index = text2.find(",")
                date_str = text2[:dash_index] + text2[comma_index:]
                date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y')
                formatted_date = date_obj.strftime('%Y-%m-%d')
                dates.append(formatted_date)
            except (ValueError, AttributeError):
                dates.append(None)
        else:
            dates.append(None)

    return ids, names, dates


def load_existing_events(output_file: str | Path) -> dict[str, dict]:
    """Load existing events from JSON file.

    Args:
        output_file: Path to JSON file

    Returns:
        Dictionary mapping event IDs to event data
    """
    output_path = Path(output_file)
    if not output_path.exists():
        return {}
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # Create lookup dictionary by event ID
        return {event['id']: event for event in events if 'id' in event}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load existing events from {output_path}: {e}")
        return {}


async def fetch_division_player_count(
    session: aiohttp.ClientSession,
    base_url: str,
    tournament_id: str,
    division: str
) -> int | None:
    """Fetch player count for a specific tournament division.

    Args:
        session: aiohttp ClientSession to use
        base_url: Base URL for Labs platform
        tournament_id: Tournament ID
        division: Division code (JR, SR, or MA)

    Returns:
        Player count or None if not found or error occurred
    """
    url = f"{base_url}{tournament_id}/{division}/standings"
    try:
        html = await fetch_html(session, url)
        return extract_player_count(html)
    except Exception as e:
        print(f"  Warning: Could not fetch player count for {tournament_id}/{division}: {e}")
        return None


async def scrape_labs_events(
    base_url: str = "https://labs.limitlesstcg.com/",
    output_file: str | Path = "labs_events.json",
    game: str = "PTCG",
    format: str = None,
) -> list[dict]:
    """Scrape Labs events and generate metadata JSON.

    Args:
        base_url: Base URL for Labs platform
        output_file: Path to output JSON file
        game: Game ID to assign to all events
        format: Format ID to assign to all events (optional)

    Returns:
        List of event metadata dictionaries
    """
    # Ensure base_url ends with /
    if not base_url.endswith('/'):
        base_url += '/'

    # Load existing events
    print("Loading existing events...")
    existing_events = load_existing_events(output_file)
    print(f"Found {len(existing_events)} existing events")

    print(f"\nFetching events from {base_url}...")
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, base_url)

        print("Parsing HTML...")
        ids, names, dates = extract_labs_list_items(html)

        print(f"Found {len(ids)} tournaments")
        print("Fetching player counts for each division...")

        events = []
        divisions = ["JR", "SR", "MA"]
        fetch_count = 0
        cached_count = 0

        for tournament_id, name, date in zip(ids, names, dates):
            print(f"\nProcessing {tournament_id}: {name}")
            
            for division in divisions:
                event_id = f"{tournament_id}_{division}"
                
                # Check if event already exists
                if event_id in existing_events:
                    print(f"  {division}: Using cached data")
                    events.append(existing_events[event_id])
                    cached_count += 1
                    continue
                
                # Event doesn't exist, fetch it
                print(f"  {division}: Fetching player count...")
                fetch_count += 1
                
                player_count = await fetch_division_player_count(
                    session, base_url, tournament_id, division
                )
                
                event = {
                    "id": event_id,
                    "name": f"{name} ({division})",
                    "date": date,
                    "game": game,
                    "division": division,
                }
                
                if player_count is not None:
                    event["player_count"] = player_count
                
                if format:
                    event["format"] = format

                events.append(event)
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)

    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Cached events: {cached_count}")
    print(f"  Newly fetched: {fetch_count}")
    print(f"  Total events: {len(events)}")
    print(f"{'='*50}")

    # Sort by date (newest first), then by division
    events.sort(key=lambda x: (x.get('date') or '', x.get('division') or ''), reverse=True)

    # Write to file
    output_path = Path(output_file)
    print(f"\nWriting {len(events)} events to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print("Done!")
    return events


async def main():
    """Main entry point for scraper script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape Labs events and generate metadata JSON"
    )
    parser.add_argument(
        "--url",
        default="https://labs.limitlesstcg.com/",
        help="Base URL for Labs platform"
    )
    parser.add_argument(
        "--output",
        default="labs_events.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--game",
        default="PTCG",
        help="Game ID to assign to events"
    )
    parser.add_argument(
        "--format",
        help="Format ID to assign to events (optional)"
    )

    args = parser.parse_args()

    await scrape_labs_events(
        base_url=args.url,
        output_file=args.output,
        game=args.game,
        format=args.format,
    )


if __name__ == "__main__":
    asyncio.run(main())
