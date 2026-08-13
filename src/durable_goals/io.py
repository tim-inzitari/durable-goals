from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .errors import IntegrityError, ValidationError


_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def sha256_file(path: Path) -> str:
    return _sha256_bytes(read_bytes(path))


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise IntegrityError(f"referenced file does not exist: {path}") from exc
    except OSError as exc:
        raise IntegrityError(f"cannot read referenced file {path}: {exc}") from exc


def _reject_json_constant(value: str) -> None:
    raise ValidationError(f"JSON contains non-finite number: {value}")


def load_json_bytes(payload: bytes, *, source: str | Path) -> Any:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"JSON is not valid UTF-8 in {source}: {exc}") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {source}: {exc}") from exc


def load_json(path: Path) -> Any:
    return load_json_bytes(read_bytes(path), source=path)


def load_jsonl_bytes(payload: bytes, *, source: str | Path) -> list[Any]:
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValidationError(f"JSONL is not valid UTF-8 in {source}: {exc}") from exc

    records: list[Any] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            records.append(
                json.loads(
                    line,
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_json_constant,
                )
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValidationError(
                f"invalid JSONL record in {source}:{line_number}: {exc}"
            ) from exc
    return records


def load_jsonl(path: Path) -> list[Any]:
    return load_jsonl_bytes(read_bytes(path), source=path)


def resolve_local_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValidationError(f"references must be portable relative paths: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValidationError(f"reference escapes the goal package: {relative}")
    return resolved


def verify_reference(root: Path, reference: dict[str, Any], *, label: str) -> Path:
    path, _ = verify_reference_bytes(root, reference, label=label)
    return path


def verify_reference_bytes(
    root: Path, reference: dict[str, Any], *, label: str
) -> tuple[Path, bytes]:
    path_value = reference.get("path")
    checksum = reference.get("sha256")
    if not isinstance(path_value, str) or not path_value:
        raise ValidationError(f"{label}.path must be a non-empty string")
    if not is_sha256(checksum):
        raise ValidationError(f"{label}.sha256 must use sha256:<hex>")
    path = resolve_local_path(root, path_value)
    payload = read_bytes(path)
    actual = _sha256_bytes(payload)
    if actual != checksum:
        raise IntegrityError(
            f"{label} checksum mismatch: expected {checksum}, observed {actual}"
        )
    return path, payload


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def write_json_lines(records: Iterable[Any]) -> str:
    return "".join(canonical_json(record) + "\n" for record in records)
