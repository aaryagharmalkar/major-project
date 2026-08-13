"""Load incident narrative data from case JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class CaseSourceKind(StrEnum):
    CASE_CONTEXT = "case_context"
    MASTER_CASE = "master_case"


@dataclass(frozen=True)
class IncidentFacts:
    """Normalized incident facts for prompt building."""

    source_kind: CaseSourceKind
    source_path: str
    case_id: str | None
    location: str | None
    datetime: str | None
    weather: str | None
    lighting: str | None
    primary_narrative: str | None
    timeline_events: tuple[str, ...] = ()
    full_timeline: tuple[str, ...] = ()
    people_summary: tuple[str, ...] = ()
    vehicle_summary: tuple[str, ...] = ()
    scene_observations: str | None = None
    location_details: str | None = None


def _fact_value(item: dict[str, Any]) -> str | None:
    value = item.get("value")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _field_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict) and "value" in value:
        return _fact_value(value)
    text = str(value).strip()
    return text or None


def _load_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    # Some project fixtures include a leading // comment line.
    lines = [line for line in raw.splitlines() if not line.lstrip().startswith("//")]
    data = json.loads("\n".join(lines))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _detect_kind(data: dict[str, Any]) -> CaseSourceKind:
    if "occurrence_details" in data or "relevant_timeline" in data:
        return CaseSourceKind.CASE_CONTEXT
    if "case_information" in data or "incident_details" in data:
        return CaseSourceKind.MASTER_CASE
    raise ValueError("Unrecognized case JSON format (expected case_context or master_case)")


def _parse_case_context(data: dict[str, Any], path: Path) -> IncidentFacts:
    occurrence = data.get("occurrence_details") or []
    timeline = data.get("relevant_timeline") or []
    fir_details = data.get("fir_details") or []

    location = None
    datetime = None
    for fact in fir_details:
        path_key = str(fact.get("source_path", "")).casefold()
        value = _fact_value(fact)
        if value is None:
            continue
        if "location" in path_key or "place" in path_key:
            location = location or value
        if "datetime" in path_key or "occurrence" in path_key or "date" in path_key:
            datetime = datetime or value

    police_station = data.get("police_station")
    if location is None and isinstance(police_station, dict):
        location = _fact_value(police_station)
    elif location is None and police_station:
        location = str(police_station)

    narratives: list[str] = []
    for event in occurrence:
        if not isinstance(event, dict):
            continue
        description = event.get("description")
        if isinstance(description, dict):
            text = _fact_value(description)
        else:
            text = str(description).strip() if description else None
        if text:
            narratives.append(text)

    timeline_events: list[str] = []
    for event in timeline[:5]:
        if not isinstance(event, dict):
            continue
        description = event.get("description")
        if isinstance(description, dict):
            text = _fact_value(description)
        else:
            text = str(description).strip() if description else None
        if text and text not in narratives:
            timeline_events.append(text)

    people: list[str] = []
    for key, label in (("victims", "victim"), ("accused", "accused"), ("witnesses", "witness")):
        for person in data.get(key) or []:
            if not isinstance(person, dict):
                continue
            name = person.get("full_name") or person.get("name")
            if isinstance(name, dict):
                name = _fact_value(name)
            if name:
                people.append(f"{label}: {name}")

    vehicles: list[str] = []
    for vehicle in data.get("vehicles") or []:
        if not isinstance(vehicle, dict):
            continue
        parts = [
            _field_text(vehicle.get("registration_number") or vehicle.get("registration")),
            _field_text(vehicle.get("make_model") or vehicle.get("vehicle_type")),
            _field_text(vehicle.get("color")),
        ]
        summary = ", ".join(part for part in parts if part)
        if summary:
            vehicles.append(summary)

    return IncidentFacts(
        source_kind=CaseSourceKind.CASE_CONTEXT,
        source_path=str(path),
        case_id=str(data.get("case_id")) if data.get("case_id") else None,
        location=location,
        datetime=datetime,
        weather=None,
        lighting=None,
        primary_narrative=narratives[0] if narratives else (timeline_events[0] if timeline_events else None),
        timeline_events=tuple(narratives[1:] or timeline_events[:4]),
        people_summary=tuple(people[:4]),
        vehicle_summary=tuple(vehicles[:2]),
    )


def _parse_master_case(data: dict[str, Any], path: Path) -> IncidentFacts:
    case_info = data.get("case_information") or {}
    incident = data.get("incident_details") or {}

    location_obj = incident.get("location") or {}
    location = None
    if isinstance(location_obj, dict):
        parts = [
            location_obj.get("address"),
            location_obj.get("area"),
            location_obj.get("city"),
        ]
        location = ", ".join(str(part).strip() for part in parts if part) or case_info.get("location")
    else:
        location = case_info.get("location") or (str(location_obj) if location_obj else None)

    datetime_parts = [incident.get("date"), incident.get("time")]
    datetime = " ".join(str(part).strip() for part in datetime_parts if part) or None
    if not datetime:
        datetime = " ".join(
            str(part).strip()
            for part in (case_info.get("incident_date"), case_info.get("incident_time"))
            if part
        ) or None

    primary = case_info.get("offence_description")
    timeline_events: list[str] = []
    for event in data.get("timeline") or data.get("timeline_key_events") or []:
        if not isinstance(event, dict):
            continue
        text = event.get("description") or event.get("event")
        time_label = event.get("time") or event.get("timestamp")
        if text and time_label:
            timeline_events.append(f"{time_label} - {text}")
        elif text:
            timeline_events.append(str(text).strip())

    location_details = None
    if isinstance(location_obj, dict):
        detail_parts = [
            f"{location_obj.get('road_type')}" if location_obj.get("road_type") else None,
            f"landmark: {location_obj.get('landmark')}" if location_obj.get("landmark") else None,
            f"traffic signal {location_obj.get('traffic_signal')}" if location_obj.get("traffic_signal") else None,
        ]
        location_details = ", ".join(part for part in detail_parts if part) or None

    vehicles: list[str] = []
    for vehicle in data.get("vehicles") or []:
        if not isinstance(vehicle, dict):
            continue
        summary = ", ".join(
            str(vehicle.get(key, "")).strip()
            for key in ("color", "make_model", "registration", "position_after_accident")
            if vehicle.get(key)
        )
        if summary:
            vehicles.append(summary)

    spot = data.get("spot_panchanama") or {}
    scene = spot.get("observation_summary") if isinstance(spot, dict) else None

    people: list[str] = []
    persons = data.get("persons_involved") or {}
    if isinstance(persons, dict):
        for label in ("victim", "accused", "complainant"):
            person = persons.get(label)
            if isinstance(person, dict) and person.get("full_name"):
                people.append(f"{label}: {person['full_name']}")
        for witness in persons.get("witnesses") or []:
            if isinstance(witness, dict) and witness.get("full_name"):
                people.append(f"witness: {witness['full_name']}")

    case_id = case_info.get("case_id")
    if not case_id:
        identifier = data.get("case_identifier") or {}
        case_id = identifier.get("fir_number") if isinstance(identifier, dict) else None

    return IncidentFacts(
        source_kind=CaseSourceKind.MASTER_CASE,
        source_path=str(path),
        case_id=str(case_id) if case_id else None,
        location=location,
        datetime=datetime,
        weather=incident.get("weather"),
        lighting=incident.get("lighting"),
        primary_narrative=str(primary).strip() if primary else (timeline_events[0] if timeline_events else None),
        timeline_events=tuple(timeline_events[:4]),
        full_timeline=tuple(timeline_events),
        people_summary=tuple(people[:4]),
        vehicle_summary=tuple(vehicles[:2]),
        scene_observations=str(scene).strip() if scene else None,
        location_details=location_details,
    )


def load_incident_facts(path: Path) -> IncidentFacts:
    """Load and normalize incident facts from a case JSON file."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Case file not found: {resolved}")
    data = _load_json(resolved)
    kind = _detect_kind(data)
    if kind is CaseSourceKind.CASE_CONTEXT:
        return _parse_case_context(data, resolved)
    return _parse_master_case(data, resolved)
