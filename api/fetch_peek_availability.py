import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Default Configuration
PEEK_API_KEY = "6e2f0590-d64d-4e77-b368-a874c585b1d2"
ACTIVITY_ID = "4c19001d-dc02-41c9-a0c2-21069b5035c7"
TICKET_ID = "0d2a5290-6159-48ab-a921-55630701b9f8"

# Headers used for all requests
DEFAULT_HEADERS = {
    "accept": "application/vnd.api+json",
    "accept-language": "en-US,en;q=0.9",
    "dnt": "1",
}


def fetch_availability_single_date(
    date: str,
    api_key: str = PEEK_API_KEY,
    activity_id: str = ACTIVITY_ID,
    booking_refid: str = None,
    ticket_id: str = TICKET_ID,
) -> Optional[Dict[str, Any]]:
    """
    Fetch availability times for a single date from Peek API.
    
    Endpoint: /availability-dates/{date}/availability-times
    
    Args:
        date: Date string in format "YYYY-MM-DD" (e.g., "2025-11-16")
        api_key: Peek API key
        activity_id: Activity ID
        booking_refid: Optional booking reference ID
        ticket_id: Ticket ID
    
    Returns:
        dict: JSON response from Peek API containing availability times
    """
    
    base_url = f"https://book.peek.com/services/api/availability-dates/{date}/availability-times"
    
    params = {
        "activity_id": activity_id,
        "tickets[0][quantity]": 1,
        "tickets[0][ticket_id]": ticket_id,
    }
    
    if booking_refid:
        params["src_booking_refid"] = booking_refid
    
    headers = {**DEFAULT_HEADERS, "authorization": f"Key {api_key}"}
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching availability: {e}")
        return None


def fetch_availability_date_range(
    start_date: str,
    end_date: str,
    api_key: str = PEEK_API_KEY,
    activity_id: str = ACTIVITY_ID,
    ticket_id: str = TICKET_ID,
    booking_refid: str = None,
    namespace: str = None,
    pc_id: str = None,
    use_legacy_api: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Fetch availability dates for a date range from Peek API.
    
    Endpoint: /availability-dates
    
    Args:
        start_date: Start date in format "YYYY-MM-DD"
        end_date: End date in format "YYYY-MM-DD"
        api_key: Peek API key
        activity_id: Activity ID
        ticket_id: Ticket ID
        booking_refid: Optional booking reference ID
        namespace: Optional namespace parameter
        pc_id: Optional product configuration ID
        use_legacy_api: Whether to use legacy API (default: True)
    
    Returns:
        dict: JSON response from Peek API
    """
    
    base_url = "https://book.peek.com/services/api/availability-dates"
    
    params = {
        "activity-id": activity_id,
        "start-date": start_date,
        "end-date": end_date,
        "tickets[0][ticket-id]": ticket_id,
        "tickets[0][quantity]": 1,
        "shouldNotAddTickets": "false",
        "use-legacy-api": "true" if use_legacy_api else "false",
    }
    
    if booking_refid:
        params["src-booking-refid"] = booking_refid
    if namespace:
        params["namespace"] = namespace
    if pc_id:
        params["pc-id"] = pc_id
    
    headers = {**DEFAULT_HEADERS, "authorization": f"Key {api_key}"}
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching availability: {e}")
        return None


def parse_availability(raw_response: Dict[str, Any]) -> list:
    """
    Parse Peek API response to extract only times and availability info.
    
    Args:
        raw_response: Raw JSON response from Peek API
    
    Returns:
        list: Parsed availability data with times and spots
        Example: [
            {
                "time": "7:20PM",
                "date": "2025-11-16",
                "spots": 36,
                "availability_mode": "available"
            },
            ...
        ]
    """
    if not raw_response or "data" not in raw_response:
        return []
    
    parsed = []
    for item in raw_response.get("data", []):
        attributes = item.get("attributes", {})
        
        parsed.append({
            "time": attributes.get("time"),
            "date": attributes.get("date"),
            "spots": attributes.get("spots"),
            "availability_mode": attributes.get("availability-mode"),
            "start_time": attributes.get("datetime-range", "").split(", ")[0].replace("[", ""),
            "end_time": attributes.get("datetime-range", "").split(", ")[1].replace(")", "") if ", " in attributes.get("datetime-range", "") else None,
        })
    
    return parsed


if __name__ == "__main__":
    print("=" * 60)
    print("EXAMPLE 1: Single Date")
    print("=" * 60)
    
    test_date = "2025-11-16"
    print(f"Fetching availability for {test_date}...")
    raw_data = fetch_availability_single_date(
        date=test_date,
        booking_refid="04b33f52-6964-4e1a-ba68-6b49fc55e5ef"
    )
    
    if raw_data:
        parsed = parse_availability(raw_data)
        print(json.dumps(parsed, indent=2))
        print(f"\nTotal times found: {len(parsed)}\n")
    else:
        print("Failed to fetch data\n")
    
    print("=" * 60)
    print("EXAMPLE 2: Date Range (with namespace)")
    print("=" * 60)
    
    print("Fetching availability for Nov 16-23, 2025...")
    raw_data = fetch_availability_date_range(
        start_date="2025-11-16",
        end_date="2025-11-23",
        booking_refid="b90c48f3-1769-40fd-af42-99f25fd1b40b",
        namespace="dd450441-9614-45b8-ed34-88defca23aa4",
        pc_id="p_r45kz8--4c19001d-dc02-41c9-a0c2-21069b5035c7"
    )
    
    if raw_data:
        parsed = parse_availability(raw_data)
        print(json.dumps(parsed, indent=2))
        print(f"\nTotal times found: {len(parsed)}\n")
    else:
        print("Failed to fetch data\n")

