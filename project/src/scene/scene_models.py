"""
Scene Intermediate Representation (IR).

This module defines the domain-neutral representation consumed
by the future Three.js visualization layer.

The scene layer does NOT understand FIRs, chargesheets, medical
reports, etc. It only understands visualizable entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================
# BASIC TYPES
# ============================================================

class Vector3(BaseModel):
    """
    Three-dimensional position.

    Coordinate convention:
        x = left/right
        y = height
        z = forward/backward
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class SourceInfo(BaseModel):
    """
    Provenance information preserved from the investigation layer.
    """

    source: str | None = None
    confidence: float | None = None
    extraction_method: str | None = None


# ============================================================
# ROAD
# ============================================================

class SceneRoad(BaseModel):
    id: str
    name: str
    width_m: float | None = None

    # Direction/orientation in the scene.
    heading_deg: float = 0.0

    # Position of the road's center.
    position: Vector3 = Field(default_factory=Vector3)

    source: SourceInfo = Field(default_factory=SourceInfo)


# ============================================================
# VEHICLE
# ============================================================

class SpeedHypothesis(BaseModel):
    value_kmph: float
    source: str | None = None
    confidence: float | None = None
    description: str | None = None


class FinalPosition(BaseModel):
    position: Vector3
    heading_deg: float | None = None

    raw_description: str | None = None


class SceneVehicle(BaseModel):
    id: str

    registration: str | None = None
    make: str | None = None
    model: str | None = None
    color: str | None = None

    # Used by the asset system.
    asset_query: str | None = None
    asset_path: str | None = None

    position: Vector3 = Field(default_factory=Vector3)
    rotation: Vector3 = Field(default_factory=Vector3)

    speed_hypotheses: list[SpeedHypothesis] = Field(default_factory=list)

    final_position: FinalPosition | None = None

    source: SourceInfo = Field(default_factory=SourceInfo)


# ============================================================
# PERSON
# ============================================================

class ScenePerson(BaseModel):
    id: str

    name: str | None = None
    role: str | None = None

    position: Vector3 = Field(default_factory=Vector3)
    rotation: Vector3 = Field(default_factory=Vector3)

    asset_query: str | None = None
    asset_path: str | None = None

    source: SourceInfo = Field(default_factory=SourceInfo)


# ============================================================
# EVIDENCE
# ============================================================

class SceneEvidence(BaseModel):
    id: str

    type: str
    description: str

    position: Vector3 = Field(default_factory=Vector3)

    # Optional measurements.
    length_m: float | None = None
    width_m: float | None = None

    related_vehicle_ids: list[str] = Field(default_factory=list)

    source: SourceInfo = Field(default_factory=SourceInfo)


# ============================================================
# TIMELINE
# ============================================================

class SceneTimelineEvent(BaseModel):
    id: str

    event_type: str
    description: str

    timestamp: datetime | None = None

    participant_ids: list[str] = Field(default_factory=list)

    location_id: str | None = None

    confidence: float | None = None

    status: Literal[
        "stated",
        "inferred",
        "conflict",
        "review_required"
    ] = "stated"

    source_documents: list[str] = Field(default_factory=list)


# ============================================================
# CONFLICT / HYPOTHESIS
# ============================================================

class SceneHypothesis(BaseModel):
    id: str

    field: str

    value: Any

    source: str | None = None
    confidence: float | None = None

    selected: bool = False


class SceneConflict(BaseModel):
    id: str

    field: str

    hypotheses: list[SceneHypothesis]

    # The renderer can expose this to the investigator.
    active_hypothesis_id: str | None = None


# ============================================================
# SCENE
# ============================================================

class SceneMetadata(BaseModel):
    scene_id: str

    location_name: str | None = None

    scene_type: str = "generic"

    coordinate_system: str = "local_cartesian"

    units: str = "meters"


class SceneIR(BaseModel):
    """
    Complete domain-neutral representation of a reconstruction.

    This is the ONLY object the Three.js layer should eventually
    need to consume.
    """

    metadata: SceneMetadata

    roads: list[SceneRoad] = Field(default_factory=list)

    vehicles: list[SceneVehicle] = Field(default_factory=list)

    people: list[ScenePerson] = Field(default_factory=list)

    evidence: list[SceneEvidence] = Field(default_factory=list)

    timeline: list[SceneTimelineEvent] = Field(default_factory=list)

    conflicts: list[SceneConflict] = Field(default_factory=list)

    hypotheses: list[SceneHypothesis] = Field(default_factory=list)

    # Helpful for debugging / UI.
    warnings: list[str] = Field(default_factory=list)