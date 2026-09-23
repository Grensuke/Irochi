"""
Export the OpenAPI schema to openapi.json.

Usage: python scripts/export_openapi.py

This file is the contract for the Phase 1 frontend's api.ts client.
Commit openapi.json to git. Re-run after any schema change.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import the app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2, default=str))

    paths = schema.get("paths", {})
    schemas = schema.get("components", {}).get("schemas", {})

    print(f"OpenAPI schema written to: {output_path}")
    print(f"  Title:   {schema.get('info', {}).get('title')}")
    print(f"  Version: {schema.get('info', {}).get('version')}")
    print(f"  Paths:   {len(paths)}")
    print(f"  Schemas: {len(schemas)}")
    print()
    print("Endpoints:")
    for path, methods in sorted(paths.items()):
        for method in sorted(methods.keys()):
            if method == "options":
                continue
            summary = methods[method].get("summary", "")
            print(f"  {method.upper():7s} {path:40s} {summary}")


if __name__ == "__main__":
    main()
