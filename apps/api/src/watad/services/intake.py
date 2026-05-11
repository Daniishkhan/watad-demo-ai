from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Final

from watad.models import RFQDraft

_CITY_ALIASES: Final[dict[str, str]] = {
    "riyadh": "Riyadh",
    "riyad": "Riyadh",
    "الرياض": "Riyadh",
    "jeddah": "Jeddah",
    "jedda": "Jeddah",
    "جدة": "Jeddah",
    "dammam": "Dammam",
    "الدمام": "Dammam",
}
_DIRECTION_WORDS: Final[dict[str, str]] = {
    "north": "North",
    "south": "South",
    "east": "East",
    "west": "West",
    "central": "Central",
}


def parse_procurement_message(message: str, *, today: date | None = None) -> RFQDraft:
    """Extract deterministic RFQ fields from a contractor message.

    This is the first-slice parser: it handles common demo inputs without making
    external LLM calls or inventing values for fields the user did not provide.
    """

    reference_date = today or date.today()
    normalized_message = " ".join(message.split())
    lower_message = normalized_message.lower()
    extracted: dict[str, object] = {}

    extracted.update(_extract_material(lower_message))
    extracted.update(_extract_quantity(lower_message))
    extracted.update(_extract_location(normalized_message, lower_message))
    extracted.update(_extract_delivery_deadline(lower_message, reference_date))
    extracted.update(_extract_project_name(normalized_message))
    extracted.update(_extract_payment_preference(lower_message))
    extracted.update(_extract_optimization_preference(lower_message))
    extracted.update(_extract_certifications(lower_message))
    extracted.update(_extract_split_delivery(lower_message))

    return RFQDraft.model_validate(extracted)


def _extract_material(lower_message: str) -> dict[str, object]:
    if any(alias in lower_message for alias in ("rebar", "steel bar", "steel bars", "حديد تسليح")):
        material: dict[str, object] = {
            "material_category": "steel",
            "material_name": "rebar",
        }
        diameter_match = re.search(r"\b(?P<diameter>\d+(?:\.\d+)?)\s*mm\b", lower_message)
        if diameter_match:
            material["specification"] = f"{diameter_match.group('diameter')}mm rebar"
        return material

    return {}


def _extract_quantity(lower_message: str) -> dict[str, object]:
    quantity_match = re.search(
        r"\b(?P<quantity>\d+(?:\.\d+)?)\s*(?P<unit>tons?|tonnes?|mt|kg|kilograms?|طن)\b",
        lower_message,
    )
    if quantity_match is None:
        return {}

    unit = quantity_match.group("unit")
    normalized_unit = "tons" if unit in {"ton", "tons", "tonne", "tonnes", "mt", "طن"} else "kg"
    return {
        "quantity": float(quantity_match.group("quantity")),
        "unit": normalized_unit,
    }


def _extract_location(message: str, lower_message: str) -> dict[str, object]:
    location: dict[str, object] = {}
    for alias, city in _CITY_ALIASES.items():
        if alias in lower_message:
            location["delivery_city"] = city
            break

    if not location:
        return location

    city = str(location["delivery_city"])
    city_pattern = re.escape(city.lower())
    direction_pattern = "|".join(_DIRECTION_WORDS)
    district_match = re.search(
        rf"\b(?P<direction>{direction_pattern})\s+{city_pattern}\b",
        lower_message,
    )
    if district_match is not None:
        district = f"{_DIRECTION_WORDS[district_match.group('direction')]} {city}"
        location["delivery_district"] = district
        location["delivery_site"] = district
        return location

    site_match = re.search(
        r"\b(?:site|district|delivery site)\s+(?P<site>[A-Z][A-Za-z0-9 -]+?)(?:,|\.|$)",
        message,
    )
    if site_match is not None:
        location["delivery_site"] = site_match.group("site").strip()

    return location


def _extract_delivery_deadline(lower_message: str, today: date) -> dict[str, object]:
    if "next week" in lower_message:
        return {"delivery_deadline": (today + timedelta(days=7)).isoformat()}
    if "tomorrow" in lower_message:
        return {"delivery_deadline": (today + timedelta(days=1)).isoformat()}

    within_days_match = re.search(r"\bwithin\s+(?P<days>\d+)\s+days?\b", lower_message)
    if within_days_match is not None:
        days = int(within_days_match.group("days"))
        return {"delivery_deadline": (today + timedelta(days=days)).isoformat()}

    iso_date_match = re.search(r"\b(?P<date>\d{4}-\d{2}-\d{2})\b", lower_message)
    if iso_date_match is not None:
        return {"delivery_deadline": iso_date_match.group("date")}

    return {}


def _extract_project_name(message: str) -> dict[str, object]:
    project_match = re.search(
        r"\b[Pp]roject\s+(?P<project>[A-Z][A-Za-z0-9 -]+?)(?:,|\.|$)",
        message,
    )
    if project_match is None:
        return {}

    return {"project_name": project_match.group("project").strip()}


def _extract_payment_preference(lower_message: str) -> dict[str, object]:
    day_terms_match = re.search(r"\b(?P<days>30|45|60|90)[ -]?(?:day|days|d)\b", lower_message)
    if day_terms_match is not None:
        return {"payment_preference": f"{day_terms_match.group('days')}_days"}
    if any(term in lower_message for term in ("pay later", "deferred", "credit")):
        return {"payment_preference": "deferred_payment"}
    if "upfront" in lower_message or "cash" in lower_message:
        return {"payment_preference": "upfront"}

    return {}


def _extract_optimization_preference(lower_message: str) -> dict[str, object]:
    if any(term in lower_message for term in ("cheapest", "lowest price", "lowest-price")):
        return {"optimization_preference": "lowest_price"}
    if any(term in lower_message for term in ("fastest", "urgent", "asap")):
        return {"optimization_preference": "fastest_delivery"}
    if "payment terms" in lower_message:
        return {"optimization_preference": "payment_terms"}
    if "balanced" in lower_message:
        return {"optimization_preference": "balanced"}

    return {}


def _extract_certifications(lower_message: str) -> dict[str, object]:
    if "saudi standard" in lower_message or "saso" in lower_message:
        return {"certification_requirements": ["Saudi standard"]}
    if "approved brand" in lower_message or "approved brands" in lower_message:
        return {"certification_requirements": ["approved brand list required"]}

    return {}


def _extract_split_delivery(lower_message: str) -> dict[str, object]:
    if "split delivery" not in lower_message:
        return {}

    negative_terms = ("no split delivery", "split delivery is not", "split delivery isn't")
    if any(term in lower_message for term in negative_terms):
        return {"split_delivery_acceptable": False}

    positive_terms = ("okay", "ok", "acceptable", "allowed", "fine", "yes")
    if any(term in lower_message for term in positive_terms):
        return {"split_delivery_acceptable": True}

    return {}
