"""
Mock marketplace data generator.
Active when Settings.env_mode != "prod".
Deterministic per event_id — stable across restarts.
Production collection path is never touched.
"""
import random

_MARKETPLACES = ["seatgeek", "stubhub", "tickpick", "gametime", "vividseats", "ticketmaster"]


def generate_mock_listings(event_id: int) -> dict:
    rng = random.Random(event_id * 99991)

    result = {}
    for marketplace in _MARKETPLACES:
        count = rng.randint(5, 120)
        base_price = rng.randint(60, 250)
        min_price = max(20, base_price - rng.randint(5, 40))

        # Simulate thinner inventory on some marketplaces for even-numbered events
        if marketplace in ("gametime", "vividseats", "ticketmaster") and event_id % 2 == 0:
            count = rng.randint(0, 10)

        result[marketplace] = {
            "total": count,
            "real": count,
            "demo": 0,
            "min_price": float(min_price) if count > 0 else None,
        }

    return result
