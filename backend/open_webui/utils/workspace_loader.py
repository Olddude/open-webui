"""
Workspace Loader for Functions and Pipelines

This module provides functionality to automatically discover and load
functions and pipelines from the filesystem workspace directory.
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from open_webui.models.functions import Functions, FunctionForm
from open_webui.env import OPEN_WEBUI_DIR
from open_webui.utils.plugin import extract_frontmatter

logger = logging.getLogger(__name__)

# Define workspace directories
WORKSPACE_DIR = OPEN_WEBUI_DIR / "workspace"
FUNCTIONS_DIR = WORKSPACE_DIR / "functions"
PIPELINES_DIR = WORKSPACE_DIR / "pipelines"


class WorkspaceLoader:
    """Handles loading functions and pipelines from filesystem workspace."""

    def __init__(self):
        self.loaded_files = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure workspace directories exist."""
        WORKSPACE_DIR.mkdir(exist_ok=True)
        FUNCTIONS_DIR.mkdir(exist_ok=True)
        PIPELINES_DIR.mkdir(exist_ok=True)

    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content for change detection."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last load."""
        current_hash = self._get_file_hash(file_path)
        file_key = str(file_path)

        if file_key not in self.loaded_files:
            self.loaded_files[file_key] = current_hash
            return True

        if self.loaded_files[file_key] != current_hash:
            self.loaded_files[file_key] = current_hash
            return True

        return False

    def _extract_metadata(self, content: str) -> Tuple[str, str, str]:
        """Extract title, author, and description from content."""
        frontmatter = extract_frontmatter(content)

        title = frontmatter.get("title", "Unnamed")
        author = frontmatter.get("author", "Unknown")
        description = frontmatter.get("description", "")

        return title, author, description

    def _load_function_from_file(self, file_path: Path) -> bool:
        """Load a single function from file into the database."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate function ID from filename
            function_id = file_path.stem

            # Extract metadata
            title, author, description = self._extract_metadata(content)

            # Check if function already exists
            existing_function = Functions.get_function_by_id(function_id)

            if existing_function:
                # Update existing function
                Functions.update_function_by_id(
                    function_id,
                    {
                        "name": title,
                        "content": content,
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                )
                logger.info(f"Updated function: {function_id}")
            else:
                # Create new function
                function_form = FunctionForm(
                    id=function_id,
                    name=title,
                    content=content,
                    meta={
                        "description": description,
                        "author": author,
                        "source": "workspace_file",
                        "file_path": str(file_path),
                    },
                )
                Functions.insert_new_function("system", "pipe", function_form)
                logger.info(f"Created function: {function_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to load function from {file_path}: {e}")
            return False

    def _load_pipeline_from_file(self, file_path: Path) -> bool:
        """Load a single pipeline from file into the database."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate pipeline ID from filename
            pipeline_id = file_path.stem

            # Extract metadata
            title, author, description = self._extract_metadata(content)

            # For pipelines, we need to create the proper pipeline structure
            # This is a simplified approach - adjust based on your format
            logger.info(
                f"Loaded pipeline: {pipeline_id} "
                f"(placeholder - implement pipeline storage)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load pipeline from {file_path}: {e}")
            return False

    def load_functions(self) -> List[str]:
        """Load all functions from the workspace functions directory."""
        loaded = []

        if not FUNCTIONS_DIR.exists():
            logger.warning(f"Functions directory not found: {FUNCTIONS_DIR}")
            return loaded

        for file_path in FUNCTIONS_DIR.glob("*.py"):
            if self._has_file_changed(file_path):
                if self._load_function_from_file(file_path):
                    loaded.append(file_path.stem)

        return loaded

    def load_pipelines(self) -> List[str]:
        """Load all pipelines from the workspace pipelines directory."""
        loaded = []

        if not PIPELINES_DIR.exists():
            logger.warning(f"Pipelines directory not found: {PIPELINES_DIR}")
            return loaded

        for file_path in PIPELINES_DIR.glob("*.py"):
            if self._has_file_changed(file_path):
                if self._load_pipeline_from_file(file_path):
                    loaded.append(file_path.stem)

        return loaded

    def load_all(self) -> Dict[str, List[str]]:
        """Load all functions and pipelines from workspace."""
        result = {
            "functions": self.load_functions(),
            "pipelines": self.load_pipelines(),
        }

        if result["functions"] or result["pipelines"]:
            logger.info(
                f"Workspace loaded - Functions: "
                f"{len(result['functions'])}, "
                f"Pipelines: {len(result['pipelines'])}"
            )

        return result

    def watch_and_reload(self) -> Dict[str, List[str]]:
        """Check for changes and reload if needed."""
        return self.load_all()


# Global workspace loader instance
workspace_loader = WorkspaceLoader()


def initialize_workspace():
    """Initialize workspace loading - called during app startup."""
    try:
        result = workspace_loader.load_all()
        logger.info(f"Workspace initialization complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to initialize workspace: {e}")
        return {"functions": [], "pipelines": []}


def reload_workspace():
    """Reload workspace - can be called via API or periodically."""
    try:
        result = workspace_loader.watch_and_reload()
        logger.info(f"Workspace reload complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to reload workspace: {e}")
        return {"functions": [], "pipelines": []}
