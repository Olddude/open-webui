"""
Schema router for serving UI Agent Form Schema
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()


@router.get("/api/v1/schema/ui-agent-form")
async def get_ui_agent_form_schema() -> Dict[str, Any]:
    """
    Serve the UI Agent Form Schema from the root schema.json file
    """
    try:
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "schema.json"

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        return schema
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schema file not found")
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON in schema file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading schema: {str(e)}")


@router.get("/api/v1/schema/validate")
async def validate_ui_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a UI form against the schema
    """
    try:
        import jsonschema

        # Load schema
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Validate
        jsonschema.validate(instance=form_data, schema=schema)

        return {"valid": True, "message": "Form data is valid"}
    except jsonschema.ValidationError as e:
        return {"valid": False, "message": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
