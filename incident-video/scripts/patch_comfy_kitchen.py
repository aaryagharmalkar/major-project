"""Patch comfy_kitchen eager/na.py for torch 2.6 custom_op compatibility."""

from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path("venv/Lib/site-packages/comfy_kitchen/backends/eager/na.py")


def patch_na_py(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "List[int]" in text and "from typing import List" in text:
        print(f"Already patched: {path}")
        return

    if "from typing import List" not in text:
        text = text.replace("import math\n", "import math\nfrom typing import List\n", 1)

    text = text.replace("list[int]", "List[int]")
    text = text.replace("list[bool]", "List[bool]")
    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: python {Path(__file__).name} <comfyui_root>", file=sys.stderr)
        return 2

    comfy_root = Path(sys.argv[1]).expanduser().resolve()
    target = comfy_root / TARGET
    if not target.is_file():
        print(f"Target not found: {target}", file=sys.stderr)
        return 1

    patch_na_py(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
