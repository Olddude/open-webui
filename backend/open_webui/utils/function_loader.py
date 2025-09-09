"""
Function Loader Utility for Development/Debugging

This utility loads functions directly from workspace/functions directory,
allowing debugging breakpoints to work properly. When functions are loaded
through the UI, they use exec() which prevents breakpoints from functioning.

Usage:
    from open_webui.utils.function_loader import FunctionLoader

    # Load all functions
    loader = FunctionLoader()
    functions = loader.load_all_functions()

    # Load specific function
    function_module = loader.load_function('recipe_rag_function')

    # Test a function
    result = await loader.test_function('recipe_rag_function', test_data)
"""

import os
import sys
import re
import subprocess
import importlib.util
import logging
import asyncio
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunctionLoader:
    """Loads functions from workspace/functions for debugging purposes"""

    def __init__(self, functions_dir: Optional[str] = None, app=None):
        """
        Initialize the FunctionLoader

        Args:
            functions_dir: Path to functions directory.
                          Defaults to backend/open_webui/workspace/functions
            app: FastAPI application instance for caching functions
        """
        if functions_dir is None:
            # Get the default functions directory
            try:
                from open_webui.env import OPEN_WEBUI_DIR

                functions_dir = OPEN_WEBUI_DIR / "workspace" / "functions"
            except ImportError:
                # Fallback to relative path
                current_file = Path(__file__)
                backend_dir = current_file.parent.parent  # backend/open_webui
                functions_dir = backend_dir / "workspace" / "functions"

        self.functions_dir = Path(functions_dir)
        self.loaded_modules = {}
        self.loaded_functions = {}
        self.app = app

        # Ensure the functions directory exists
        if not self.functions_dir.exists():
            logger.warning(f"Functions directory does not exist: {self.functions_dir}")
            self.functions_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FunctionLoader initialized with directory: {self.functions_dir}")

    def _get_function_files(self) -> List[Path]:
        """Get all Python files in the functions directory"""
        if not self.functions_dir.exists():
            return []

        return list(self.functions_dir.glob("*.py"))

    def _load_module_from_file(self, filepath: Path) -> Optional[Any]:
        """
        Load a Python module from a file path

        This method loads the module using importlib instead of exec(),
        which allows breakpoints to work properly.
        """
        try:
            # Create module name from filename
            module_name = f"workspace_function_{filepath.stem}"

            # Check if already loaded
            if module_name in self.loaded_modules:
                logger.info(
                    f"Module {module_name} already loaded, returning cached version"
                )
                return self.loaded_modules[module_name]

            # Load the module spec
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create spec for {filepath}")
                return None

            # Create and load the module
            module = importlib.util.module_from_spec(spec)

            # Add to sys.modules to make it importable
            sys.modules[module_name] = module

            # Execute the module
            spec.loader.exec_module(module)

            # Cache the loaded module
            self.loaded_modules[module_name] = module

            logger.info(f"Successfully loaded module {module_name} from {filepath}")
            return module

        except Exception as e:
            logger.error(f"Error loading module from {filepath}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Extract frontmatter from function content
        """
        frontmatter = {}
        frontmatter_started = False
        frontmatter_ended = False
        frontmatter_pattern = re.compile(r"^\s*([a-z_]+):\s*(.*)\s*$", re.IGNORECASE)

        try:
            lines = content.splitlines()
            if len(lines) < 1 or lines[0].strip() != '"""':
                return {}

            frontmatter_started = True

            for line in lines[1:]:
                if '"""' in line:
                    if frontmatter_started:
                        frontmatter_ended = True
                        break

                if frontmatter_started and not frontmatter_ended:
                    match = frontmatter_pattern.match(line)
                    if match:
                        key, value = match.groups()
                        frontmatter[key.strip()] = value.strip()

        except Exception as e:
            logger.error(f"Failed to extract frontmatter: {e}")

        return frontmatter

    def _install_requirements(self, requirements: str):
        """
        Install pip requirements from frontmatter
        """
        if not requirements:
            return

        try:
            from open_webui.env import PIP_OPTIONS, PIP_PACKAGE_INDEX_OPTIONS

            req_list = [req.strip() for req in requirements.split(",")]
            logger.info(f"Installing requirements: {' '.join(req_list)}")

            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"]
                + PIP_OPTIONS
                + req_list
                + PIP_PACKAGE_INDEX_OPTIONS
            )
        except ImportError:
            # Fallback if environment not available
            req_list = [req.strip() for req in requirements.split(",")]
            logger.info(f"Installing requirements: {' '.join(req_list)}")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + req_list)
        except Exception as e:
            logger.error(f"Error installing packages: {e}")

    def _extract_function_info(
        self, module: Any, filepath: Path
    ) -> Optional[Tuple[Any, str, Dict]]:
        """
        Extract function class and metadata from a loaded module

        Returns:
            Tuple of (function_instance, function_type, metadata)
        """
        try:
            # Read file content to extract frontmatter
            metadata = {}
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                metadata = self._extract_frontmatter(content)

            # Install requirements if specified
            if requirements := metadata.get("requirements"):
                self._install_requirements(requirements)

            # Check for function classes
            if hasattr(module, "Pipe"):
                instance = module.Pipe()
                return instance, "pipe", metadata
            elif hasattr(module, "Filter"):
                instance = module.Filter()
                return instance, "filter", metadata
            elif hasattr(module, "Action"):
                instance = module.Action()
                return instance, "action", metadata
            else:
                logger.warning(
                    f"No function class (Pipe/Filter/Action) found in module"
                )
                return None

        except Exception as e:
            logger.error(f"Error extracting function info: {e}")
            return None

    def load_function(self, function_name: str) -> Optional[Any]:
        """
        Load a specific function by name

        Args:
            function_name: Name of the function file (without .py extension)

        Returns:
            Function instance or None if loading failed
        """
        # Check cache first
        if function_name in self.loaded_functions:
            logger.info(f"Returning cached function: {function_name}")
            return self.loaded_functions[function_name]

        # Construct file path
        if not function_name.endswith(".py"):
            function_name = f"{function_name}.py"

        filepath = self.functions_dir / function_name

        if not filepath.exists():
            logger.error(f"Function file not found: {filepath}")
            return None

        # Load the module
        module = self._load_module_from_file(filepath)
        if module is None:
            return None

        # Extract function instance
        result = self._extract_function_info(module, filepath)
        if result is None:
            return None

        function_instance, function_type, metadata = result

        # Cache the function
        cache_key = filepath.stem
        self.loaded_functions[cache_key] = {
            "instance": function_instance,
            "type": function_type,
            "metadata": metadata,
            "module": module,
            "filepath": str(filepath),
        }

        # Also cache in app state if available
        if self.app:
            if not hasattr(self.app.state, "WORKSPACE_FUNCTIONS"):
                self.app.state.WORKSPACE_FUNCTIONS = {}
            self.app.state.WORKSPACE_FUNCTIONS[cache_key] = function_instance
            logger.info(f"Cached {function_type} function in app state: {cache_key}")

        logger.info(f"Loaded {function_type} function: {cache_key}")
        return self.loaded_functions[cache_key]

    def load_all_functions(self) -> Dict[str, Any]:
        """
        Load all functions from the workspace/functions directory

        Returns:
            Dictionary mapping function names to their instances
        """
        function_files = self._get_function_files()

        if not function_files:
            logger.warning("No function files found in workspace/functions")
            return {}

        logger.info(f"Found {len(function_files)} function file(s)")

        for filepath in function_files:
            function_name = filepath.stem
            self.load_function(function_name)

        return self.loaded_functions

    async def test_function(
        self,
        function_name: str,
        body: Dict[str, Any],
        user: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> Any:
        """
        Test a function with sample data

        Args:
            function_name: Name of the function to test
            body: Request body containing messages, model, etc.
            user: Optional user context
            metadata: Optional metadata

        Returns:
            Function result
        """
        # Load the function
        function_data = self.load_function(function_name)
        if not function_data:
            raise ValueError(f"Failed to load function: {function_name}")

        function_instance = function_data["instance"]
        function_type = function_data["type"]

        logger.info(f"Testing {function_type} function: {function_name}")

        # Initialize function if it has startup
        if hasattr(function_instance, "on_startup"):
            if asyncio.iscoroutinefunction(function_instance.on_startup):
                await function_instance.on_startup()
            else:
                function_instance.on_startup()

        # Prepare parameters based on function type
        params = {"body": body, "__user__": user or {}, "__metadata__": metadata or {}}

        try:
            # Call the appropriate method based on function type
            if function_type == "pipe":
                if hasattr(function_instance, "pipe"):
                    result = function_instance.pipe(**params)

                    # Handle async generators
                    if inspect.isasyncgenfunction(function_instance.pipe):
                        result_text = ""
                        async for chunk in result:
                            result_text += str(chunk)
                        return result_text
                    elif asyncio.iscoroutinefunction(function_instance.pipe):
                        return await result
                    else:
                        return result

            elif function_type == "filter":
                if hasattr(function_instance, "inlet"):
                    params = function_instance.inlet(**params)
                return params

            elif function_type == "action":
                if hasattr(function_instance, "action"):
                    return await function_instance.action(**params)

        finally:
            # Cleanup if needed
            if hasattr(function_instance, "on_shutdown"):
                if asyncio.iscoroutinefunction(function_instance.on_shutdown):
                    await function_instance.on_shutdown()
                else:
                    function_instance.on_shutdown()

    def list_functions(self) -> List[Dict[str, Any]]:
        """
        List all available functions with their metadata

        Returns:
            List of function information dictionaries
        """
        self.load_all_functions()

        functions_list = []
        for name, data in self.loaded_functions.items():
            functions_list.append(
                {
                    "name": name,
                    "type": data["type"],
                    "metadata": data["metadata"],
                    "filepath": data["filepath"],
                    "has_valves": hasattr(data["instance"], "valves"),
                    "has_user_valves": hasattr(data["instance"], "UserValves"),
                }
            )

        return functions_list

    def get_function_instance(self, function_name: str) -> Optional[Any]:
        """
        Get the raw function instance for direct access

        Args:
            function_name: Name of the function

        Returns:
            Function instance or None
        """
        function_data = self.load_function(function_name)
        if function_data:
            return function_data["instance"]
        return None

    def reload_function(self, function_name: str) -> Optional[Any]:
        """
        Force reload a function from disk

        Args:
            function_name: Name of the function to reload

        Returns:
            Reloaded function instance or None
        """
        # Clear from caches
        if function_name in self.loaded_functions:
            del self.loaded_functions[function_name]

        # Clear module from sys.modules
        module_name = f"workspace_function_{function_name}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]

        # Clear from app state if available
        if self.app and hasattr(self.app.state, "WORKSPACE_FUNCTIONS"):
            if function_name in self.app.state.WORKSPACE_FUNCTIONS:
                del self.app.state.WORKSPACE_FUNCTIONS[function_name]

        # Reload
        return self.load_function(function_name)

    def install_dependencies_and_load_all(self):
        """
        Install all dependencies from workspace functions and load them.
        This is meant to be called once during app startup.
        """
        logger.info("Installing dependencies for workspace functions...")

        # Collect all requirements
        all_requirements = set()
        function_files = self._get_function_files()

        for filepath in function_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                metadata = self._extract_frontmatter(content)
                if requirements := metadata.get("requirements"):
                    for req in requirements.split(","):
                        all_requirements.add(req.strip())
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")

        # Install all requirements at once
        if all_requirements:
            self._install_requirements(", ".join(all_requirements))

        # Now load all functions
        logger.info("Loading all workspace functions for debugging...")
        loaded = self.load_all_functions()
        logger.info(f"Loaded {len(loaded)} workspace function(s)")

        return loaded


# One-liner function for main.py
def load_workspace_functions_for_debugging(app):
    """
    Load all workspace functions with debug support.
    This is a one-liner function to be called from main.py.

    Args:
        app: FastAPI application instance
    """
    try:
        FunctionLoader(app=app).install_dependencies_and_load_all()
    except Exception as e:
        logger.warning(f"Failed to load workspace functions: {e}")


# Example usage and test script
if __name__ == "__main__":

    async def main():
        """Example usage of FunctionLoader"""

        # Initialize loader
        loader = FunctionLoader()

        # List all available functions
        print("\n=== Available Functions ===")
        functions = loader.list_functions()
        for func in functions:
            print(f"- {func['name']} ({func['type']})")
            if func["metadata"]:
                print(f"  Metadata: {func['metadata']}")

        # Load all functions
        print("\n=== Loading All Functions ===")
        loaded = loader.load_all_functions()
        print(f"Loaded {len(loaded)} function(s)")

        # Test a specific function if available
        if "recipe_rag_function" in loaded:
            print("\n=== Testing recipe_rag_function ===")

            test_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Convert this to JSON: Chocolate Cake - 2 cups flour, 1 cup sugar, bake at 350F for 30 minutes",
                    }
                ],
                "model": "test-model",
            }

            try:
                result = await loader.test_function("recipe_rag_function", test_body)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error testing function: {e}")

        # Example of direct function access for debugging
        if loaded:
            first_func_name = list(loaded.keys())[0]
            print(f"\n=== Direct Access to {first_func_name} ===")
            instance = loader.get_function_instance(first_func_name)
            print(f"Function instance: {instance}")
            print(f"Has valves: {hasattr(instance, 'valves')}")

            # Set a breakpoint here to debug the function
            # breakpoint()  # Uncomment to debug

    # Run the example
    asyncio.run(main())
