"""Dataset registry loader.

Loads datasets.yaml and provides lookup helpers for imports_v2.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except Exception:
    yaml = None


@dataclass(frozen=True)
class DatasetSpec:
    dataset_key: str
    description: str
    format: str
    default_sheet: str
    header_row: int
    required_columns_norm: List[str]
    primary_key_norm: List[str]
    loader: Optional[str]
    target_tables: List[str]
    source_files: List[str]
    columns: List[Dict[str, str]]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "DatasetSpec":
        return DatasetSpec(
            dataset_key=d["dataset_key"],
            description=d.get("description", ""),
            format=d.get("format", "xlsx"),
            default_sheet=d.get("default_sheet", 0),
            header_row=int(d.get("header_row", 0)),
            required_columns_norm=list(d.get("required_columns_norm", [])),
            primary_key_norm=list(d.get("primary_key_norm", [])),
            loader=d.get("loader"),
            target_tables=list(d.get("target_tables", [])) if d.get("target_tables") is not None else ([d.get("target_table")] if d.get("target_table") is not None else []),
            source_files=list(d.get("source_files", [])),
            columns=list(d.get("columns", [])),
        )


class DatasetRegistry:
    def __init__(self, specs: List[DatasetSpec]):
        self._specs = specs
        self._by_key = {s.dataset_key: s for s in specs}

    @classmethod
    def load(cls, yaml_path: str | Path) -> "DatasetRegistry":
        p = Path(yaml_path)
        text = p.read_text(encoding="utf-8")
        data = None
        if yaml:
            try:
                data = yaml.safe_load(text) or {}
            except Exception:
                data = None

        if data is None:
            # fallback: try json
            try:
                import json

                data = json.loads(text)
            except Exception:
                # minimal YAML-lite parser for our simple files
                data = {"datasets": []}
                cur = None
                for raw in text.splitlines():
                    line = raw.rstrip("\n")
                    s = line.lstrip()
                    if not s or s.startswith("#"):
                        continue
                    if s.startswith("- "):
                        if cur:
                            data["datasets"].append(cur)
                        cur = {}
                        rest = s[2:]
                        if ":" in rest:
                            k, v = rest.split(":", 1)
                            cur[k.strip()] = v.strip().strip('"\'')
                    elif ":" in s and cur is not None:
                        k, v = s.split(":", 1)
                        cur[k.strip()] = v.strip().strip('"\'')
                if cur:
                    data["datasets"].append(cur)

        specs: List[DatasetSpec] = []
        for x in data.get("datasets", []):
            try:
                if not isinstance(x, dict) or "dataset_key" not in x:
                    continue
                specs.append(DatasetSpec.from_dict(x))
            except Exception:
                # skip malformed entries
                continue
        return cls(specs)

    def keys(self) -> List[str]:
        return sorted(self._by_key.keys())

    def get(self, dataset_key: str) -> Optional[DatasetSpec]:
        return self._by_key.get(dataset_key)

    def all(self) -> List[DatasetSpec]:
        return list(self._specs)
