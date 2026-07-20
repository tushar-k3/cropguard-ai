import requests
import logging
from datetime import date, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

DATA_GOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


def fetch_from_api(commodity=None, state=None, limit=100):
    """
    Fetches market prices from data.gov.in API.
    Returns list of price records or None on failure.
    """
    api_key = settings.DATA_GOV_API_KEY
    if not api_key:
        logger.warning("DATA_GOV_API_KEY not set. Cannot fetch live prices.")
        return None, "API key not configured."

    params = {
        "api-key": api_key,
        "format":  "json",
        "limit":   limit,
        "offset":  0,
    }

    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state

    try:
        response = requests.get(DATA_GOV_URL, params=params, timeout=15)

        if response.status_code == 401:
            return None, "Invalid data.gov.in API key."

        if response.status_code != 200:
            return None, f"API returned status {response.status_code}."

        data = response.json()
        records = data.get("records", [])
        return records, None

    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as e:
        logger.error(f"Market API error: {e}")
        return None, str(e)


def save_to_cache(records):
    """Saves API records to the database cache."""
    from .models import MarketPrice

    saved = 0
    for record in records:
        try:
            price_date_str = record.get("arrival_date", "")
            if not price_date_str:
                continue

            # Parse date — data.gov.in format is dd/mm/yyyy
            parts = price_date_str.split("/")
            if len(parts) == 3:
                price_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
            else:
                continue

            MarketPrice.objects.update_or_create(
                commodity=record.get("commodity", "").strip(),
                market=record.get("market", "").strip(),
                price_date=price_date,
                defaults={
                    "variety":     record.get("variety", "").strip(),
                    "state":       record.get("state", "").strip(),
                    "district":    record.get("district", "").strip(),
                    "min_price":   float(record.get("min_price", 0) or 0),
                    "max_price":   float(record.get("max_price", 0) or 0),
                    "modal_price": float(record.get("modal_price", 0) or 0),
                },
            )
            saved += 1
        except Exception as e:
            logger.warning(f"Failed to save market record: {e}")

    logger.info(f"Saved {saved} market price records to cache.")
    return saved


def get_market_prices(commodity=None, state=None, limit=50):
    """
    Main function — tries live API first, falls back to cache.
    Always returns data with a source indicator.
    """
    from .models import MarketPrice

    # Try live API
    records, error = fetch_from_api(commodity=commodity, state=state, limit=limit)

    if records is not None and len(records) > 0:
        save_to_cache(records)
        return {
            "source":       "live",
            "source_label": "Live data from data.gov.in",
            "error":        None,
            "records":      records,
            "fetched_at":   timezone.now().isoformat(),
        }

    # Fall back to database cache
    logger.warning(f"API unavailable ({error}). Serving from cache.")

    queryset = MarketPrice.objects.all()
    if commodity:
        queryset = queryset.filter(commodity__icontains=commodity)
    if state:
        queryset = queryset.filter(state__icontains=state)

    queryset = queryset[:limit]

    if not queryset.exists():
        return {
            "source":       "cache",
            "source_label": "Cached data",
            "error":        error or "No data available.",
            "records":      [],
            "fetched_at":   None,
        }

    cache_records = []
    last_updated = None

    for p in queryset:
        cache_records.append({
            "commodity":   p.commodity,
            "variety":     p.variety,
            "market":      p.market,
            "state":       p.state,
            "district":    p.district,
            "min_price":   p.min_price,
            "max_price":   p.max_price,
            "modal_price": p.modal_price,
            "arrival_date": p.price_date.strftime("%d/%m/%Y"),
        })
        if last_updated is None or p.fetched_at > last_updated:
            last_updated = p.fetched_at

    return {
        "source":       "cache",
        "source_label": "Cached data (API unavailable)",
        "error":        error,
        "records":      cache_records,
        "fetched_at":   last_updated.isoformat() if last_updated else None,
        "api_unavailable": True,
    }


def seed_sample_prices():
    """
    Seeds the cache with realistic Maharashtra market prices.
    Called automatically when the cache is empty.
    This ensures the market page always shows something.
    """
    from .models import MarketPrice

    if MarketPrice.objects.exists():
        return

    today = date.today()
    sample_data = [
        ("Tomato",    "Local",   "Nashik",       "Maharashtra", "Nashik",    800,  1200, 1000),
        ("Onion",     "Local",   "Lasalgaon",    "Maharashtra", "Nashik",    600,  900,  750),
        ("Cotton",    "Bt",      "Akola",        "Maharashtra", "Akola",     6200, 6800, 6500),
        ("Soybean",   "Yellow",  "Latur",        "Maharashtra", "Latur",     4200, 4600, 4400),
        ("Wheat",     "Lokwan",  "Pune",         "Maharashtra", "Pune",      2100, 2400, 2250),
        ("Rice",      "Common",  "Kolhapur",     "Maharashtra", "Kolhapur",  1800, 2200, 2000),
        ("Maize",     "Yellow",  "Aurangabad",   "Maharashtra", "Aurangabad",1400, 1700, 1550),
        ("Sugarcane", "Local",   "Solapur",      "Maharashtra", "Solapur",   280,  320,  300),
        ("Banana",    "Robusta", "Jalgaon",      "Maharashtra", "Jalgaon",   1200, 1800, 1500),
        ("Grapes",    "Thom",    "Sangli",       "Maharashtra", "Sangli",    3000, 4500, 3800),
        ("Pomegranate","Bhagwa", "Solapur",      "Maharashtra", "Solapur",   5000, 7000, 6000),
        ("Chilli",    "Dry",     "Nagpur",       "Maharashtra", "Nagpur",    8000, 12000,10000),
        ("Turmeric",  "Local",   "Hingoli",      "Maharashtra", "Hingoli",   6000, 8000, 7000),
        ("Groundnut", "Bold",    "Osmanabad",    "Maharashtra", "Osmanabad", 4500, 5200, 4800),
        ("Chickpea",  "Desi",    "Amravati",     "Maharashtra", "Amravati",  4800, 5400, 5100),
    ]

    for commodity, variety, market, state, district, min_p, max_p, modal_p in sample_data:
        MarketPrice.objects.get_or_create(
            commodity=commodity,
            market=market,
            price_date=today,
            defaults={
                "variety":     variety,
                "state":       state,
                "district":    district,
                "min_price":   min_p,
                "max_price":   max_p,
                "modal_price": modal_p,
            },
        )

    logger.info("Seeded sample market prices.")