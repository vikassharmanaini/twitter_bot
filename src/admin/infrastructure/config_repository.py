"""
Atomic read/write of config.yaml with secret masking and merge-on-save for empty secrets.
"""

from __future__ import annotations

import copy
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from src.config_loader import AppConfig, _is_placeholder, _validate_secrets, load_raw_yaml, merge_defaults
from src.admin.infrastructure.secret_fields import is_secret_key


def _placeholder_config_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent.parent
    return root / "config.example.yaml"


class ConfigRepository:
    def __init__(self, config_path: str | Path | None = None):
        self._path = Path(config_path or os.environ.get("BOT_CONFIG", "config.yaml"))

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.is_file()

    def bootstrap_from_example(self) -> None:
        """Create config.yaml from config.example.yaml if missing."""
        if self.exists():
            return
        example = _placeholder_config_path()
        if not example.is_file():
            raise FileNotFoundError(f"config.example.yaml not found at {example}")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example, self._path)

    def read_raw_dict(self) -> dict[str, Any]:
        if not self.exists():
            self.bootstrap_from_example()
        return merge_defaults(load_raw_yaml(self._path))

    def mask_for_display(self, data: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, bool]]:
        """
        Return a deep copy with secret string values replaced by empty string,
        plus secret_status[path] = True if value looks configured (non-empty, not placeholder).
        """
        if data is None:
            data = self.read_raw_dict()
        secret_status: dict[str, bool] = {}

        def walk(obj: Any, prefix: str) -> Any:
            if isinstance(obj, dict):
                out: dict[str, Any] = {}
                for k, v in obj.items():
                    p = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        out[k] = walk(v, p)
                    elif isinstance(v, list):
                        out[k] = v
                    elif isinstance(v, str) and is_secret_key(k):
                        secret_status[p] = bool(v.strip()) and not _is_placeholder(v)
                        out[k] = ""
                    else:
                        out[k] = v
                return out
            return obj

        return walk(copy.deepcopy(data), ""), secret_status

    def save(
        self,
        body: dict[str, Any],
        *,
        allow_incomplete: bool = False,
        merge_secrets: bool = True,
    ) -> AppConfig:
        """Validate and atomically write YAML. Empty secret strings keep previous file values if merge_secrets."""
        merged = merge_defaults(copy.deepcopy(body))
        if merge_secrets and self.exists():
            prev = merge_defaults(load_raw_yaml(self._path))

            def merge_secrets_walk(new: Any, old: Any) -> Any:
                if isinstance(new, dict) and isinstance(old, dict):
                    for k, nv in list(new.items()):
                        ov = old.get(k)
                        if isinstance(nv, str) and nv.strip() == "" and is_secret_key(k):
                            if isinstance(ov, str) and ov.strip():
                                new[k] = ov
                        elif isinstance(nv, dict) and isinstance(ov, dict):
                            merge_secrets_walk(nv, ov)
                return new

            merge_secrets_walk(merged, prev)

        cfg = AppConfig.model_validate(merged)
        if not allow_incomplete:
            _validate_secrets(cfg)

        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            yaml.safe_dump(merged, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        tmp.replace(self._path)
        return cfg

    def load_app_config(self, *, skip_secret_validation: bool = False) -> AppConfig:
        from src.config_loader import load_config

        return load_config(self._path, skip_secret_validation=skip_secret_validation)
