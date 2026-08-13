"""Build keyframe and motion prompts for I2V multi-scene pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from .case_sources import IncidentFacts

MAX_KEYFRAME_CHARS = 380
MAX_MOTION_CHARS = 280
DEFAULT_NEGATIVE = (
    "cartoon, anime, text overlay, watermark, logo, gore, blood splatter, "
    "identifiable faces, blurry, distorted, low quality, shaky cam, dramatic stylization, "
    "license plate close-up, news banner, timestamp overlay"
)
KEYFRAME_NEGATIVE = (
    "cartoon, anime, text, watermark, logo, gore, blood, identifiable faces, "
    "blurry, distorted, low quality, oversaturated, fisheye, dutch angle"
)

VISUAL_ANCHOR = (
    "Fixed elevated wide CCTV angle, Shankar Road T-point intersection near hospital gate, "
    "New Delhi India, dusk lighting, dry asphalt, muted documentary colors, no text on screen"
)

MASTER_CASE_VISUAL_SCENE_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        "approach_victim",
        "White Honda Activa scooter with office commuter approaching T-point from Shankar Road, moderate speed, autos in background",
        "Activa scooter moves forward toward intersection center, slight camera drift, evening traffic",
    ),
    (
        "approach_accused",
        "Red Bajaj Pulsar 220F motorcycle with delivery bag entering same T-point from cross street, young rider in casual clothes",
        "Red Pulsar motorcycle enters frame and accelerates toward intersection center, dusk street",
    ),
    (
        "collision",
        "Both two-wheelers meet at center of T-point, riders lose balance, scooters skid on dry road, broken traffic signal overhead",
        "Two scooters collide at intersection center, brief skid, riders stumble, debris on asphalt",
    ),
    (
        "immediate_aftermath",
        "White Activa near road divider, red Pulsar stopped mid-intersection, damaged fairing, riders standing beside vehicles, bystanders reacting",
        "Riders stand beside stopped scooters, bystanders step forward slowly, no emergency vehicles yet",
    ),
    (
        "witness_response",
        "Traffic constable in uniform and tea stall owner near hospital gate react, people gathering at safe distance",
        "Constable gestures toward accident scene, small crowd gathers at roadside, evening ambient motion",
    ),
)


@dataclass(frozen=True)
class VideoPrompt:
    positive: str
    negative: str
    facts_summary: str


@dataclass(frozen=True)
class VideoScene:
    scene_id: str
    title: str
    time_label: str
    event_text: str
    positive: str
    negative: str
    keyframe_prompt: str
    motion_prompt: str


def _truncate(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _compact_location(facts: IncidentFacts) -> str:
    if facts.location_details:
        return facts.location_details
    return facts.location or "Indian urban street intersection"


def _weather_line(facts: IncidentFacts) -> str:
    parts: list[str] = []
    if facts.weather:
        parts.append(facts.weather)
    if facts.lighting:
        parts.append(facts.lighting)
    return ", ".join(parts) if parts else "clear dusk conditions"


def build_keyframe_prompt(facts: IncidentFacts, scene_action: str) -> str:
    body = (
        f"{scene_action}. {VISUAL_ANCHOR}. "
        f"Location: {_compact_location(facts)}. {_weather_line(facts)}. "
        "Photorealistic still frame, no faces visible, investigative reconstruction."
    )
    return _truncate(body, MAX_KEYFRAME_CHARS)


def build_motion_prompt(scene_action: str, event_text: str) -> str:
    body = (
        f"{scene_action}. Motion: subtle realistic movement, fixed CCTV camera, documentary style. "
        f"Event: {event_text}. Smooth natural motion, no camera shake."
    )
    return _truncate(body, MAX_MOTION_CHARS)


def build_video_prompt(facts: IncidentFacts) -> VideoPrompt:
    action = facts.primary_narrative or "Traffic incident at urban intersection"
    positive = build_keyframe_prompt(facts, action)
    facts_summary = _truncate(
        " | ".join(filter(None, [facts.primary_narrative, facts.location, facts.datetime])),
        240,
    )
    return VideoPrompt(positive=positive, negative=DEFAULT_NEGATIVE, facts_summary=facts_summary)


def _select_visual_timeline_events(facts: IncidentFacts) -> tuple[str, ...]:
    events = list(facts.full_timeline or facts.timeline_events)
    if not events:
        return ()
    visual: list[str] = []
    skip_keywords = (
        "FIR registered",
        "Spot panchnama",
        "PCR receives",
        "PCR van arrives",
        "Ambulance",
        "admitted",
        "taken to Rajinder Nagar PS",
    )
    for event in events:
        if any(keyword.casefold() in event.casefold() for keyword in skip_keywords):
            continue
        visual.append(event)
        if len(visual) >= len(MASTER_CASE_VISUAL_SCENE_SPECS):
            break
    return tuple(visual)


def _split_timeline_event(event: str) -> tuple[str, str]:
    if " - " in event:
        time_label, event_text = event.split(" - ", 1)
        return time_label.strip(), event_text.strip()
    return "unknown", event


def build_multi_scene_prompts(facts: IncidentFacts) -> tuple[VideoScene, ...]:
    visual_events = _select_visual_timeline_events(facts)
    scenes: list[VideoScene] = []

    for index, (scene_id, still_action, motion_action) in enumerate(MASTER_CASE_VISUAL_SCENE_SPECS):
        if index < len(visual_events):
            time_label, event_text = _split_timeline_event(visual_events[index])
        else:
            time_label, event_text = "unknown", still_action

        keyframe = build_keyframe_prompt(facts, still_action)
        motion = build_motion_prompt(motion_action, event_text)

        scenes.append(
            VideoScene(
                scene_id=scene_id,
                title=scene_id.replace("_", " ").title(),
                time_label=time_label,
                event_text=event_text,
                positive=motion,
                negative=DEFAULT_NEGATIVE,
                keyframe_prompt=keyframe,
                motion_prompt=motion,
            )
        )
    return tuple(scenes)

