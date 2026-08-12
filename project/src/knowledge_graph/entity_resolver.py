"""Conservative deterministic identity keys for graph entity de-duplication."""

from __future__ import annotations

import re

from .graph_models import GraphNodeType


class EntityResolver:
    """Normalizes explicitly parsed entity labels; it never invents an identity."""

    @staticmethod
    def identity_key(node_type: GraphNodeType, label: str) -> str:
        normalized = re.sub(r"[^a-z0-9]", "", label.casefold())
        if node_type == GraphNodeType.VEHICLE:
            return f"vehicle:{normalized}"
        if node_type == GraphNodeType.LOCATION:
            return f"location:{normalized}"
        if node_type == GraphNodeType.PERSON:
            return f"person:{normalized}"
        return f"{node_type.value}:{normalized}"

    @staticmethod
    def person_matches(left: str, right: str) -> bool:
        """Match name abbreviations only when their explicit tokens are compatible."""

        left_tokens = re.findall(r"[a-z0-9]+", left.casefold())
        right_tokens = re.findall(r"[a-z0-9]+", right.casefold())
        if not left_tokens or not right_tokens or left_tokens[0] != right_tokens[0]:
            return False
        if len(left_tokens) == 1 or len(right_tokens) == 1:
            return True
        return all(
            a == b or len(a) == 1 and b.startswith(a) or len(b) == 1 and a.startswith(b)
            for a, b in zip(left_tokens, right_tokens)
        ) and len(left_tokens) == len(right_tokens)

