"""Write the FastAPI app's OpenAPI schema to a file.

This is the contract the frontend's TypeScript types are generated from
(`frontend/src/types/api.generated.ts`). Committing the generated types and
regenerating them in CI is what turns a backend schema change into a
frontend *compile error* rather than a runtime surprise.

Usage:
    uv run python -m scripts.export_openapi            # -> ../openapi.json
    uv run python -m scripts.export_openapi --out x.json
"""

import argparse
import json
import pathlib
import sys

from app.main import app

DEFAULT_OUT = pathlib.Path(__file__).resolve().parents[2] / "openapi.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    schema = app.openapi()
    # Sorted keys and a trailing newline so the file is byte-stable between
    # runs — otherwise CI's "is this up to date?" check would fail on dict
    # ordering rather than on a real contract change.
    args.out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({len(schema.get('paths', {}))} paths)", file=sys.stderr)


if __name__ == "__main__":
    main()
