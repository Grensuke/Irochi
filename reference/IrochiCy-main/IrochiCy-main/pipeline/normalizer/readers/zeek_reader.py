"""ZeekLogReader — Parses Zeek TSV log files into Python dicts.

Zeek TSV format:
  Lines starting with # are header/metadata.
  #separator \\x09        → field separator (tab)
  #set_separator ,       → separator for set fields
  #empty_field (empty)   → represents empty value
  #unset_field -         → represents null/missing value
  #path conn             → log type (conn, dns, ssl)
  #fields ts uid ...     → field names
  #types time string ... → field types
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional


class ZeekLogReader:
    """Parses a Zeek TSV log file, yielding typed Python dicts per row.

    Usage:
        reader = ZeekLogReader("conn.log")
        for row in reader:
            print(row["ts"], row["id.orig_h"])
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.separator: str = "\t"
        self.set_separator: str = ","
        self.empty_field: str = "(empty)"
        self.unset_field: str = "-"
        self.log_path: Optional[str] = None  # e.g. "conn", "dns", "ssl"
        self.fields: list[str] = []
        self.types: list[str] = []
        self._parse_header()

    def _parse_header(self) -> None:
        """Parse the Zeek log header lines to extract metadata."""
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.startswith("#"):
                    break

                if line.startswith("#separator"):
                    # Value is the literal separator, e.g. #separator \x09
                    raw = line.split(" ", 1)[1] if " " in line else "\t"
                    self.separator = raw.encode().decode("unicode_escape")
                elif line.startswith("#set_separator"):
                    self.set_separator = line.split(self.separator, 1)[1] if self.separator in line else ","
                elif line.startswith("#empty_field"):
                    self.empty_field = line.split(self.separator, 1)[1] if self.separator in line else "(empty)"
                elif line.startswith("#unset_field"):
                    self.unset_field = line.split(self.separator, 1)[1] if self.separator in line else "-"
                elif line.startswith("#path"):
                    self.log_path = line.split(self.separator, 1)[1] if self.separator in line else None
                elif line.startswith("#fields"):
                    self.fields = line.split(self.separator)[1:]
                elif line.startswith("#types"):
                    self.types = line.split(self.separator)[1:]

    def _coerce_value(self, raw: str, type_hint: str) -> object:
        """Coerce a raw string value to the appropriate Python type.

        Args:
            raw: Raw string value from the TSV field.
            type_hint: Zeek type hint (e.g. "time", "count", "string", "bool").

        Returns:
            Coerced Python value, or None for unset/empty.
        """
        # Handle unset / empty
        if raw == self.unset_field:
            return None
        if raw == self.empty_field:
            if "set" in type_hint or "vector" in type_hint:
                return []
            return None

        # Type coercion
        if type_hint == "time":
            return int(float(raw) * 1_000_000)  # → epoch microseconds
        elif type_hint in ("count", "int"):
            return int(raw)
        elif type_hint in ("interval", "double"):
            return float(raw)
        elif type_hint == "port":
            return int(raw)
        elif type_hint == "bool":
            return raw == "T"
        elif type_hint.startswith("set[") or type_hint.startswith("vector["):
            if not raw:
                return []
            return raw.split(self.set_separator)
        elif type_hint == "addr":
            return raw
        elif type_hint == "string":
            return raw
        else:
            # Unknown type — return as string
            return raw

    def __iter__(self) -> Iterator[dict]:
        """Iterate over data rows, yielding typed dicts."""
        if not self.fields:
            return

        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line.startswith("#") or not line:
                    continue

                parts = line.split(self.separator)
                if len(parts) != len(self.fields):
                    # Skip malformed rows
                    continue

                row: dict = {}
                for i, (field, raw_val) in enumerate(zip(self.fields, parts)):
                    type_hint = self.types[i] if i < len(self.types) else "string"
                    row[field] = self._coerce_value(raw_val, type_hint)

                yield row

    def __len__(self) -> int:
        """Count data rows (non-header, non-empty lines)."""
        count = 0
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.startswith("#") and line.strip():
                    count += 1
        return count
