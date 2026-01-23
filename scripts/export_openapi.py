import json
import sys
from pathlib import Path


# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from project.main import app


def export_openapi() -> None:
    """Exports the OpenAPI schema to a static JSON file."""
    schema = app.openapi()
    output_path = Path("openapi.json")
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"Success! OpenAPI schema exported to {output_path.absolute()}")


if __name__ == "__main__":
    export_openapi()
