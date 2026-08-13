"""Convert ComfyUI UI workflows to API prompts and inject generation params."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

WIDGET_INPUTS: dict[str, tuple[str, ...]] = {
    "CLIPTextEncode": ("text",),
    "KSampler": (
        "seed",
        "control_after_generate",
        "steps",
        "cfg",
        "sampler_name",
        "scheduler",
        "denoise",
    ),
    "EmptyHunyuanLatentVideo": ("width", "height", "length", "batch_size"),
    "EmptyLatentImage": ("width", "height", "batch_size"),
    "LoaderGGUF": ("gguf_name",),
    "ClipLoaderGGUF": ("clip_name", "type"),
    "VaeGGUF": ("vae_name",),
    "CheckpointLoaderSimple": ("ckpt_name",),
    "LoadImage": ("image", "upload"),
    "WanVaceToVideo": ("width", "height", "length", "batch_size", "strength"),
    "ModelSamplingSD3": ("shift",),
    "TrimVideoLatent": ("trim_amount",),
    "SaveAnimatedWEBP": ("filename_prefix", "fps", "lossless", "quality", "method"),
    "SaveWEBM": ("filename_prefix", "codec", "fps", "crf"),
    "SaveImage": ("filename_prefix",),
    "VAEDecode": (),
}

T2V_NODE_POSITIVE = 6
T2V_NODE_NEGATIVE = 7
T2V_NODE_SAMPLER = 3
T2V_NODE_LATENT_VIDEO = 40
T2V_NODE_MODEL_LOADER = 49

I2V_NODE_POSITIVE = 5
I2V_NODE_NEGATIVE = 6
I2V_NODE_SAMPLER = 9
I2V_NODE_VACE = 7
I2V_NODE_LOAD_IMAGE = 4
I2V_NODE_MODEL_LOADER = 1
I2V_NODE_SAVE = 12

KEYFRAME_NODE_POSITIVE = 2
KEYFRAME_NODE_NEGATIVE = 3
KEYFRAME_NODE_SAMPLER = 5
KEYFRAME_NODE_LATENT = 4

DEFAULT_T2V_MODEL = "wan2.1_t2v_1.3b-q4_0.gguf"
DEFAULT_I2V_MODEL = "wan2.1-vace-1.3b-q4_0.gguf"
DEFAULT_CLIP_FILE = "umt5-xxl-encoder-q4_k_m.gguf"
DEFAULT_VAE_FILE = "pig_wan_vae_fp32-f16.gguf"
DEFAULT_SD15_CHECKPOINT = "v1-5-pruned-emaonly.safetensors"


class WorkflowKind(str, Enum):
    T2V = "t2v"
    I2V = "i2v"
    KEYFRAME = "keyframe"


@dataclass(frozen=True)
class GenerationParams:
    positive_prompt: str
    negative_prompt: str
    seed: int
    width: int = 480
    height: int = 480
    frame_count: int = 30
    steps: int = 30
    cfg: float = 6.0
    model_file: str = DEFAULT_T2V_MODEL
    input_image: str | None = None
    fps: int = 15


@dataclass(frozen=True)
class KeyframeParams:
    positive_prompt: str
    negative_prompt: str
    seed: int
    width: int = 512
    height: int = 512
    steps: int = 25
    cfg: float = 7.0
    checkpoint: str = DEFAULT_SD15_CHECKPOINT


def detect_workflow_kind(path: Path) -> WorkflowKind:
    name = path.name.lower()
    if "keyframe" in name or "sd15" in name:
        return WorkflowKind.KEYFRAME
    if "i2v" in name or "vace" in name:
        return WorkflowKind.I2V
    return WorkflowKind.T2V


def load_ui_workflow(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        workflow = json.load(handle)
    if "nodes" not in workflow:
        raise ValueError(f"Invalid ComfyUI workflow (missing nodes): {path}")
    return workflow


def patch_t2v_workflow(workflow: dict[str, Any], params: GenerationParams) -> dict[str, Any]:
    patched = copy.deepcopy(workflow)
    for node in patched["nodes"]:
        node_id = node["id"]
        if node_id == T2V_NODE_POSITIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.positive_prompt
        elif node_id == T2V_NODE_NEGATIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.negative_prompt
        elif node_id == T2V_NODE_SAMPLER and node["type"] == "KSampler":
            widgets = list(node["widgets_values"])
            widgets[0] = params.seed
            widgets[1] = "fixed"
            widgets[2] = params.steps
            widgets[3] = params.cfg
            node["widgets_values"] = widgets
        elif node_id == T2V_NODE_LATENT_VIDEO and node["type"] == "EmptyHunyuanLatentVideo":
            node["widgets_values"] = [params.width, params.height, params.frame_count, 1]
        elif node_id == T2V_NODE_MODEL_LOADER and node["type"] == "LoaderGGUF":
            node["widgets_values"][0] = params.model_file
    return patched


def patch_i2v_workflow(workflow: dict[str, Any], params: GenerationParams) -> dict[str, Any]:
    if not params.input_image:
        raise ValueError("I2V workflow requires input_image (uploaded keyframe filename)")

    patched = copy.deepcopy(workflow)
    for node in patched["nodes"]:
        node_id = node["id"]
        if node_id == I2V_NODE_POSITIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.positive_prompt
        elif node_id == I2V_NODE_NEGATIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.negative_prompt
        elif node_id == I2V_NODE_SAMPLER and node["type"] == "KSampler":
            widgets = list(node["widgets_values"])
            widgets[0] = params.seed
            widgets[1] = "fixed"
            widgets[2] = params.steps
            widgets[3] = params.cfg
            node["widgets_values"] = widgets
        elif node_id == I2V_NODE_VACE and node["type"] == "WanVaceToVideo":
            node["widgets_values"] = [params.width, params.height, params.frame_count, 1, 1.0]
        elif node_id == I2V_NODE_LOAD_IMAGE and node["type"] == "LoadImage":
            node["widgets_values"][0] = params.input_image
        elif node_id == I2V_NODE_MODEL_LOADER and node["type"] == "LoaderGGUF":
            node["widgets_values"][0] = params.model_file
        elif node_id == I2V_NODE_SAVE and node["type"] == "SaveAnimatedWEBP":
            widgets = list(node["widgets_values"])
            if widgets:
                widgets[0] = "ComfyUI"
            if len(widgets) > 1:
                widgets[1] = float(params.fps)
            node["widgets_values"] = widgets
    return patched


def patch_keyframe_workflow(workflow: dict[str, Any], params: KeyframeParams) -> dict[str, Any]:
    patched = copy.deepcopy(workflow)
    for node in patched["nodes"]:
        node_id = node["id"]
        if node_id == KEYFRAME_NODE_POSITIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.positive_prompt
        elif node_id == KEYFRAME_NODE_NEGATIVE and node["type"] == "CLIPTextEncode":
            node["widgets_values"][0] = params.negative_prompt
        elif node_id == KEYFRAME_NODE_SAMPLER and node["type"] == "KSampler":
            widgets = list(node["widgets_values"])
            widgets[0] = params.seed
            widgets[1] = "fixed"
            widgets[2] = params.steps
            widgets[3] = params.cfg
            node["widgets_values"] = widgets
        elif node_id == KEYFRAME_NODE_LATENT and node["type"] == "EmptyLatentImage":
            node["widgets_values"] = [params.width, params.height, 1]
        elif node["type"] == "CheckpointLoaderSimple":
            node["widgets_values"][0] = params.checkpoint
    return patched


def ui_workflow_to_api_prompt(workflow: dict[str, Any]) -> dict[str, Any]:
    links_by_target: dict[int, dict[int, list[Any]]] = {}
    for link in workflow.get("links", []):
        _, origin_id, origin_slot, target_id, target_slot, _ = link
        links_by_target.setdefault(target_id, {})[target_slot] = [str(origin_id), origin_slot]

    prompt: dict[str, Any] = {}
    for node in workflow["nodes"]:
        if node.get("mode") == 4:
            continue

        node_id = str(node["id"])
        class_type = node["type"]
        inputs: dict[str, Any] = {}

        for slot_index, input_def in enumerate(node.get("inputs", [])):
            if slot_index in links_by_target.get(node["id"], {}):
                inputs[input_def["name"]] = links_by_target[node["id"]][slot_index]

        widget_fields = WIDGET_INPUTS.get(class_type)
        widgets = node.get("widgets_values", [])
        if widget_fields:
            for index, field_name in enumerate(widget_fields):
                if index < len(widgets):
                    inputs[field_name] = widgets[index]

        prompt[node_id] = {"class_type": class_type, "inputs": inputs}

    return prompt


def build_api_prompt(
    workflow_path: Path,
    params: GenerationParams | KeyframeParams,
    *,
    kind: WorkflowKind | None = None,
) -> dict[str, Any]:
    workflow_kind = kind or detect_workflow_kind(workflow_path)
    workflow = load_ui_workflow(workflow_path)

    if workflow_kind == WorkflowKind.KEYFRAME:
        if not isinstance(params, KeyframeParams):
            raise TypeError("Keyframe workflow requires KeyframeParams")
        patched = patch_keyframe_workflow(workflow, params)
    elif workflow_kind == WorkflowKind.I2V:
        if not isinstance(params, GenerationParams):
            raise TypeError("I2V workflow requires GenerationParams")
        i2v_params = GenerationParams(
            **{**params.__dict__, "model_file": params.model_file or DEFAULT_I2V_MODEL}
        )
        patched = patch_i2v_workflow(workflow, i2v_params)
    else:
        if not isinstance(params, GenerationParams):
            raise TypeError("T2V workflow requires GenerationParams")
        patched = patch_t2v_workflow(workflow, params)

    return ui_workflow_to_api_prompt(patched)


patch_ui_workflow = patch_t2v_workflow
NODE_POSITIVE_PROMPT = T2V_NODE_POSITIVE
NODE_NEGATIVE_PROMPT = T2V_NODE_NEGATIVE
NODE_SAMPLER = T2V_NODE_SAMPLER
NODE_LATENT_VIDEO = T2V_NODE_LATENT_VIDEO
NODE_MODEL_LOADER = T2V_NODE_MODEL_LOADER
DEFAULT_MODEL_FILE = DEFAULT_T2V_MODEL

