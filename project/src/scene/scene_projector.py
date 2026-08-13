"""
Projects investigation data into the domain-neutral Scene IR.

Supported inputs:

1. CanonicalInvestigation
2. Raw fact-ledger dictionaries such as case_summary.json

The renderer should never need to understand the original
investigation schema.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from .asset_registry import AssetRegistry
from .scene_models import (
    FinalPosition,
    SceneConflict,
    SceneEvidence,
    SceneHypothesis,
    SceneIR,
    SceneMetadata,
    ScenePerson,
    SceneRoad,
    SceneTimelineEvent,
    SceneVehicle,
    SourceInfo,
    SpeedHypothesis,
    Vector3,
)


# ============================================================
# CONFIDENCE
# ============================================================

CONFIDENCE_MAP = {
    "high": 0.90,
    "medium": 0.65,
    "low": 0.35,
}


def normalize_confidence(value: Any) -> float | None:

    if value is None:
        return None

    if isinstance(value, (float, int)):
        return float(value)

    return CONFIDENCE_MAP.get(
        str(value).lower()
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def parse_number(value: Any) -> float | None:

    if value is None:
        return None

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        str(value),
    )

    if not match:
        return None

    return float(match.group())


def parse_speed(value: Any) -> float | None:

    if value is None:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*kmph",
        str(value),
        re.IGNORECASE,
    )

    if not match:
        return None

    return float(match.group(1))


def parse_time(value: Any) -> datetime | None:

    if value is None:
        return None

    value = str(value).strip()

    # Handles:
    # 18:20:07.800
    # 18:20:08
    # 18:24:05

    for fmt in (
        "%H:%M:%S.%f",
        "%H:%M:%S",
    ):

        try:

            return datetime.strptime(
                value,
                fmt,
            )

        except ValueError:
            continue

    return None


# ============================================================
# FACT LEDGER
# ============================================================

class FactLedger:

    def __init__(self, facts: list[dict[str, Any]]):

        self.facts = facts

        self.grouped: dict[
            str,
            list[dict[str, Any]]
        ] = defaultdict(list)

        for fact in facts:

            key = fact.get("key")

            if key:
                self.grouped[key].append(fact)

    # --------------------------------------------------------

    def get(
        self,
        key: str,
    ) -> list[dict[str, Any]]:

        return self.grouped.get(
            key,
            [],
        )

    # --------------------------------------------------------

    def first(
        self,
        key: str,
    ) -> dict[str, Any] | None:

        values = self.get(key)

        if not values:
            return None

        return values[0]

    # --------------------------------------------------------

    def all_with_prefix(
        self,
        prefix: str,
    ) -> list[dict[str, Any]]:

        result = []

        for key, facts in self.grouped.items():

            if key.startswith(prefix):

                result.extend(facts)

        return result


# ============================================================
# SCENE PROJECTOR
# ============================================================

class SceneProjector:

    def __init__(
        self,
        asset_registry: AssetRegistry | None = None,
    ):

        self.assets = (
            asset_registry
            or AssetRegistry()
        )

    # ========================================================
    # PUBLIC ENTRY POINT
    # ========================================================

    def project(
        self,
        data: Any,
    ) -> SceneIR:

        # ----------------------------------------------------
        # RAW FACT LEDGER
        # ----------------------------------------------------

        if isinstance(data, dict):

            if "facts" in data:

                return self._project_fact_ledger(
                    data
                )

        # ----------------------------------------------------
        # CANONICAL INVESTIGATION
        # ----------------------------------------------------

        if hasattr(data, "vehicles"):

            return self._project_canonical(
                data
            )

        raise TypeError(
            "SceneProjector expects either "
            "a fact-ledger dictionary or "
            "CanonicalInvestigation."
        )

    # ========================================================
    # RAW FACT LEDGER
    # ========================================================

    def _project_fact_ledger(
        self,
        data: dict[str, Any],
    ) -> SceneIR:

        ledger = FactLedger(
            data.get("facts", [])
        )

        warnings: list[str] = []

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        location_fact = ledger.first(
            "incident_location"
        )

        location_name = (
            str(location_fact["value"])
            if location_fact
            else None
        )

        scene = SceneIR(
            metadata=SceneMetadata(
                scene_id="case_scene",
                location_name=location_name,
                scene_type="road_accident",
            )
        )

        # ----------------------------------------------------
        # ROADS
        # ----------------------------------------------------

        scene.roads = self._build_roads(
            ledger
        )

        # ----------------------------------------------------
        # VEHICLES
        # ----------------------------------------------------

        scene.vehicles = self._build_vehicles(
            ledger
        )

        # ----------------------------------------------------
        # EVIDENCE
        # ----------------------------------------------------

        scene.evidence = self._build_evidence(
            ledger
        )

        # ----------------------------------------------------
        # TIMELINE
        # ----------------------------------------------------

        scene.timeline = self._build_timeline(
            ledger
        )

        # ----------------------------------------------------
        # CONFLICTS
        # ----------------------------------------------------

        scene.conflicts = self._build_conflicts(
            data.get("conflicts", [])
        )

        # ----------------------------------------------------
        # WARNINGS
        # ----------------------------------------------------

        if not scene.roads:
            warnings.append(
                "No road geometry was found."
            )

        if not scene.vehicles:
            warnings.append(
                "No vehicles were found."
            )

        if not scene.timeline:
            warnings.append(
                "No explicit timeline events were found."
            )

        scene.warnings = warnings

        return scene

    # ========================================================
    # ROADS
    # ========================================================

    def _build_roads(
        self,
        ledger: FactLedger,
    ) -> list[SceneRoad]:

        roads: dict[str, SceneRoad] = {}

        pattern = re.compile(
            r"^road_(\d+)_(name|width)$"
        )

        for key, facts in ledger.grouped.items():

            match = pattern.match(key)

            if not match:
                continue

            road_number = match.group(1)
            field = match.group(2)

            road_id = f"road_{road_number}"

            if road_id not in roads:

                roads[road_id] = SceneRoad(
                    id=road_id,
                    name=road_id,
                )

            fact = facts[0]

            if field == "name":

                roads[road_id].name = str(
                    fact["value"]
                )

            elif field == "width":

                roads[road_id].width_m = parse_number(
                    fact["value"]
                )

        return list(roads.values())

    # ========================================================
    # VEHICLES
    # ========================================================

    def _build_vehicles(
        self,
        ledger: FactLedger,
    ) -> list[SceneVehicle]:

        vehicle_numbers = set()

        pattern = re.compile(
            r"^vehicle_(\d+)_"
        )

        for key in ledger.grouped:

            match = pattern.match(key)

            if match:

                vehicle_numbers.add(
                    match.group(1)
                )

        vehicles = []

        for number in sorted(
            vehicle_numbers,
            key=int,
        ):

            prefix = f"vehicle_{number}_"

            reg = ledger.first(
                prefix + "reg"
            )

            make = ledger.first(
                prefix + "make"
            )

            model = ledger.first(
                prefix + "model"
            )

            color = ledger.first(
                prefix + "color"
            )

            vehicle = SceneVehicle(
                id=f"vehicle_{number}",

                registration=(
                    str(reg["value"])
                    if reg
                    else None
                ),

                make=(
                    str(make["value"])
                    if make
                    else None
                ),

                model=(
                    str(model["value"])
                    if model
                    else None
                ),

                color=(
                    str(color["value"])
                    if color
                    else None
                ),
            )

            # ------------------------------------------------
            # ASSET
            # ------------------------------------------------

            asset = self.assets.resolve_vehicle(
                vehicle.make,
                vehicle.model,
            )

            if asset:

                vehicle.asset_query = (
                    f"{vehicle.make or ''} "
                    f"{vehicle.model or ''}"
                ).strip()

                vehicle.asset_path = (
                    self.assets.absolute_path(
                        asset
                    )
                )

            # ------------------------------------------------
            # SPEED HYPOTHESES
            # ------------------------------------------------

            vehicle.speed_hypotheses = (
                self._extract_vehicle_speeds(
                    ledger,
                    vehicle,
                )
            )

            # ------------------------------------------------
            # FINAL POSITION
            # ------------------------------------------------

            final_position = (
                self._extract_final_position(
                    ledger,
                    number,
                    vehicle,
                )
            )

            vehicle.final_position = (
                final_position
            )

            if final_position:

                vehicle.position = (
                    final_position.position
                )

                if (
                    final_position.heading_deg
                    is not None
                ):

                    vehicle.rotation = Vector3(
                        y=final_position.heading_deg
                    )

            vehicles.append(vehicle)

        return vehicles

    # ========================================================
    # SPEEDS
    # ========================================================

    def _extract_vehicle_speeds(
        self,
        ledger: FactLedger,
        vehicle: SceneVehicle,
    ) -> list[SpeedHypothesis]:

        result = []

        # ----------------------------------------------------
        # CCTV keys contain vehicle name + registration.
        # ----------------------------------------------------

        registration = (
            vehicle.registration
            or ""
        )

        model = (
            vehicle.model
            or ""
        )

        for key, facts in ledger.grouped.items():

            if not key.startswith(
                "cctv_speed_"
            ):
                continue

            key_lower = key.lower()

            matches_vehicle = (
                registration.lower()
                in key_lower
                or model.lower()
                in key_lower
            )

            if not matches_vehicle:
                continue

            for fact in facts:

                speed = parse_speed(
                    fact.get("value")
                )

                if speed is None:
                    continue

                result.append(
                    SpeedHypothesis(
                        value_kmph=speed,
                        source=str(
                            fact.get("source")
                            or "unknown"
                        ),
                        confidence=normalize_confidence(
                            fact.get("confidence")
                        ),
                        description=str(
                            fact.get("value")
                        ),
                    )
                )

        # ----------------------------------------------------
        # Remove duplicates.
        # ----------------------------------------------------

        unique = {}

        for item in result:

            unique[
                (
                    item.value_kmph,
                    item.source,
                )
            ] = item

        return list(
            unique.values()
        )

    # ========================================================
    # FINAL POSITION
    # ========================================================

    def _extract_final_position(
        self,
        ledger: FactLedger,
        number: str,
        vehicle: SceneVehicle,
    ) -> FinalPosition | None:

        # Example:
        #
        # final_position_vehicle_1_pulsar

        prefix = (
            f"final_position_vehicle_{number}_"
        )

        facts = ledger.all_with_prefix(
            prefix
        )

        if not facts:
            return None

        description = str(
            facts[0]["value"]
        )

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance_match = re.search(
            r"(\d+(?:\.\d+)?)\s*m\s*from",
            description,
            re.IGNORECASE,
        )

        distance = (
            float(distance_match.group(1))
            if distance_match
            else 0.0
        )

        # ----------------------------------------------------
        # Heading
        # ----------------------------------------------------

        heading_match = re.search(
            r"facing\s+([A-Za-z]+)",
            description,
            re.IGNORECASE,
        )

        heading = (
            heading_match.group(1).lower()
            if heading_match
            else None
        )

        heading_degrees = {
            "north": 0.0,
            "east": 90.0,
            "south": 180.0,
            "west": 270.0,
        }

        heading_deg = (
            heading_degrees.get(
                heading
            )
            if heading
            else None
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # This is a LOCAL visualization approximation.
        #
        # We do NOT pretend the textual panchnama
        # description gives exact GPS coordinates.
        # ----------------------------------------------------

        if heading == "east":

            position = Vector3(
                x=distance,
                y=0,
                z=0,
            )

        elif heading == "west":

            position = Vector3(
                x=-distance,
                y=0,
                z=0,
            )

        elif heading == "north":

            position = Vector3(
                x=0,
                y=0,
                z=distance,
            )

        elif heading == "south":

            position = Vector3(
                x=0,
                y=0,
                z=-distance,
            )

        else:

            position = Vector3(
                x=0,
                y=0,
                z=0,
            )

        return FinalPosition(
            position=position,
            heading_deg=heading_deg,
            raw_description=description,
        )

    # ========================================================
    # EVIDENCE
    # ========================================================

    def _build_evidence(
        self,
        ledger: FactLedger,
    ) -> list[SceneEvidence]:

        evidence = []

        # ----------------------------------------------------
        # Skid mark
        # ----------------------------------------------------

        skid = ledger.first(
            "skid_mark_length"
        )

        if skid:

            evidence.append(
                SceneEvidence(
                    id="evidence_skid_1",
                    type="skid_mark",
                    description=str(
                        skid["value"]
                    ),
                    length_m=parse_number(
                        skid["value"]
                    ),
                    source=SourceInfo(
                        source=str(
                            skid.get("source")
                            or ""
                        ),
                        confidence=normalize_confidence(
                            skid.get("confidence")
                        ),
                    ),
                )
            )

        return evidence

    # ========================================================
    # TIMELINE
    # ========================================================

    def _build_timeline(
        self,
        ledger: FactLedger,
    ) -> list[SceneTimelineEvent]:

        events = []

        # ----------------------------------------------------
        # Impact timestamp hypotheses
        # ----------------------------------------------------

        impact_facts = (
            ledger.get(
                "impact_time"
            )
        )

        if not impact_facts:

            impact_facts = (
                ledger.get(
                    "impact_timestamp_cctv"
                )
            )

        for index, fact in enumerate(
            impact_facts
        ):

            timestamp = parse_time(
                fact.get("value")
            )

            events.append(
                SceneTimelineEvent(
                    id=f"impact_{index + 1}",
                    event_type="collision",
                    description="Vehicle collision",
                    timestamp=timestamp,
                    participant_ids=[
                        "vehicle_1",
                        "vehicle_2",
                    ],
                    confidence=normalize_confidence(
                        fact.get("confidence")
                    ),
                    status=(
                        "conflict"
                        if fact.get("conflict")
                        else "stated"
                    ),
                    source_documents=[
                        str(
                            fact.get("source")
                            or ""
                        )
                    ],
                )
            )

        return sorted(
            events,
            key=lambda event: (
                event.timestamp is None,
                event.timestamp
                or datetime.max,
            ),
        )

    # ========================================================
    # CONFLICTS
    # ========================================================

    def _build_conflicts(
        self,
        conflicts: list[dict[str, Any]],
    ) -> list[SceneConflict]:

        result = []

        for index, conflict in enumerate(
            conflicts
        ):

            key = str(
                conflict.get(
                    "key",
                    f"conflict_{index + 1}",
                )
            )

            hypotheses = []

            for value_index, value in enumerate(
                conflict.get(
                    "values",
                    [],
                )
            ):

                hypotheses.append(
                    SceneHypothesis(
                        id=(
                            f"conflict_{index + 1}_"
                            f"hypothesis_{value_index + 1}"
                        ),
                        field=key,
                        value=value,
                    )
                )

            result.append(
                SceneConflict(
                    id=f"conflict_{index + 1}",
                    field=key,
                    hypotheses=hypotheses,
                )
            )

        return result

    # ========================================================
    # CANONICAL INVESTIGATION
    # ========================================================

    def _project_canonical(
        self,
        case: Any,
    ) -> SceneIR:

        scene = SceneIR(
            metadata=SceneMetadata(
                scene_id=str(
                    case.case_metadata.case_id
                ),
                scene_type="investigation",
            )
        )

        # ----------------------------------------------------
        # Vehicles
        # ----------------------------------------------------

        for vehicle in case.vehicles:

            registration = (
                vehicle.registration_number.value
            )

            asset = self.assets.resolve_vehicle(
                None,
                registration,
            )

            scene_vehicle = SceneVehicle(
                id=str(vehicle.id),
                registration=str(
                    registration
                ),
                asset_path=(
                    self.assets.absolute_path(
                        asset
                    )
                    if asset
                    else None
                ),
                source=SourceInfo(
                    confidence=(
                        vehicle
                        .registration_number
                        .confidence
                    ),
                ),
            )

            scene.vehicles.append(
                scene_vehicle
            )

        # ----------------------------------------------------
        # Locations
        # ----------------------------------------------------

        for location in case.locations:

            scene.roads.append(
                SceneRoad(
                    id=str(location.id),
                    name=str(
                        location.name.value
                    ),
                    source=SourceInfo(
                        confidence=(
                            location
                            .name
                            .confidence
                        ),
                    ),
                )
            )

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        for evidence in case.evidence:

            scene.evidence.append(
                SceneEvidence(
                    id=str(
                        evidence.evidence_id
                    ),
                    type=evidence.type,
                    description=str(
                        evidence
                        .description
                        .value
                    ),
                    source=SourceInfo(
                        confidence=evidence.confidence
                    ),
                )
            )

        # ----------------------------------------------------
        # Timeline
        # ----------------------------------------------------

        for event in case.timeline:

            timestamp = None

            if event.timestamp:

                timestamp = (
                    event.timestamp.value
                )

            scene.timeline.append(
                SceneTimelineEvent(
                    id=str(
                        event.event_id
                    ),
                    event_type="investigation_event",
                    description=str(
                        event.description.value
                    ),
                    timestamp=timestamp,
                    location_id=(
                        str(event.location_id)
                        if event.location_id
                        else None
                    ),
                    participant_ids=[
                        str(identifier)
                        for identifier
                        in event.participant_ids
                    ],
                    confidence=event.confidence,
                    status=(
                        "review_required"
                        if event.status.value
                        == "review_required"
                        else "stated"
                    ),
                    source_documents=[
                        str(identifier)
                        for identifier
                        in event.supporting_documents
                    ],
                )
            )

        # ----------------------------------------------------
        # Conflicts
        # ----------------------------------------------------

        for conflict in case.conflicts:

            hypotheses = []

            for index, fact in enumerate(
                conflict.competing_values
            ):

                hypotheses.append(
                    SceneHypothesis(
                        id=(
                            f"{conflict.conflict_id}_"
                            f"{index}"
                        ),
                        field=conflict.field_path,
                        value=fact.value,
                        confidence=fact.confidence,
                    )
                )

            scene.conflicts.append(
                SceneConflict(
                    id=str(
                        conflict.conflict_id
                    ),
                    field=conflict.field_path,
                    hypotheses=hypotheses,
                )
            )

        return scene