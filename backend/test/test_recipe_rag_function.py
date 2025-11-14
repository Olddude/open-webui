"""
Integration tests for recipe_rag_function.py

Tests the main function and pipe functionality with stdout assertions.
"""

import pytest
import json
import re
import subprocess
import sys
import os
from unittest.mock import patch, AsyncMock

from backend.functions.recipe_rag_function import main


class TestRecipeRagFunction:
    """Integration test class for Recipe RAG Function with stdout assertions"""

    def test_main_function_stdout_comprehensive(self, capsys):
        """Integration test for main function with stdout assertions"""

        # This test runs the main function and captures all stdout output
        import asyncio

        # Mock the OpenAI client to ensure consistent test results
        with patch("recipe_rag_function.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            # Mock the OpenAI API to force fallback to mock mode
            # for consistent testing
            mock_client.chat.completions.create.side_effect = Exception(
                "Test API Error - using mock mode"
            )

            # Run the main function
            asyncio.run(main())

        # Capture all stdout output
        captured = capsys.readouterr()
        stdout_content = captured.out

        # Test 1: Basic function startup messages
        assert (
            "🍪 Recipe RAG Function Test" in stdout_content
        ), "Missing main test header"
        assert (
            "Processing recipe data..." in stdout_content
        ), "Missing processing message"

        # Test 2: Input recipe content is displayed
        assert (
            "Chocolate Chip Cookies" in stdout_content
        ), "Missing recipe name in output"
        assert (
            "all-purpose flour" in stdout_content
        ), "Missing ingredient in displayed input"
        assert (
            "Preheat oven to 375°F" in stdout_content
        ), "Missing instruction in displayed input"

        # Test 3: JSON conversion output structure
        assert (
            "Recipe Data Converted to JSON" in stdout_content
        ), "Missing JSON conversion header"
        assert "```json" in stdout_content, "Missing JSON code block start"
        assert '"recipes":' in stdout_content, "Missing recipes key in JSON output"
        assert '"metadata":' in stdout_content, "Missing metadata key in JSON output"

        # Test 4: Mock mode fallback behavior
        assert (
            '"processing_mode": "mock"' in stdout_content
        ), "Should use mock mode when API fails"

        # Test 5: Download instructions and completion
        assert (
            "Download Instructions:" in stdout_content
        ), "Missing download instructions"
        assert (
            "Copy the JSON content above" in stdout_content
        ), "Missing copy instruction"
        assert (
            "Total items processed: 1" in stdout_content
        ), "Missing processing summary"
        assert (
            "Test completed successfully! ✅" in stdout_content
        ), "Missing success completion message"

        # Test 6: JSON structure validation
        json_match = re.search(r"```json\n(.*?)\n```", stdout_content, re.DOTALL)
        assert json_match is not None, "JSON block not found in output"

        json_data = json.loads(json_match.group(1))
        assert isinstance(json_data, dict), "JSON output should be a dictionary"
        assert "recipes" in json_data, "JSON should have 'recipes' key"
        assert "metadata" in json_data, "JSON should have 'metadata' key"
        assert len(json_data["recipes"]) == 1, "Should process exactly 1 recipe"

        # Test 7: Recipe data extraction
        recipe = json_data["recipes"][0]
        assert "name" in recipe, "Recipe should have a name"
        assert "ingredients" in recipe, "Recipe should have ingredients"
        assert "instructions" in recipe, "Recipe should have instructions"
        assert len(recipe["ingredients"]) > 0, "Should extract ingredients"
        assert len(recipe["instructions"]) > 0, "Should extract instructions"

        # Test 8: Metadata validation
        metadata = json_data["metadata"]
        assert "total_recipes" in metadata, "Metadata should have total count"
        assert "processed_at" in metadata, "Metadata should have timestamp"
        assert "processing_mode" in metadata, "Metadata should indicate processing mode"
        assert metadata["processing_mode"] == "mock", "Should use mock mode"

    def test_script_execution_via_subprocess(self):
        """Test direct script execution via subprocess"""

        # Get the functions directory path
        functions_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "functions")
        )
        script_path = os.path.join(functions_dir, "recipe_rag_function.py")

        # Execute the script as a subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=functions_dir,
            timeout=30,  # 30 second timeout
        )

        # Validate subprocess execution
        assert (
            result.returncode == 0
        ), f"Script failed with exit code {result.returncode}. Error: {result.stderr}"

        stdout_output = result.stdout
        stderr_output = result.stderr

        # Test subprocess stdout assertions
        assert (
            "Starting Recipe RAG Function Test..." in stdout_output
        ), "Missing entry point message in subprocess"
        assert (
            "🍪 Recipe RAG Function Test" in stdout_output
        ), "Missing main header in subprocess"
        assert (
            "Test completed successfully! ✅" in stdout_output
        ), "Missing success message in subprocess"

        # Test that there are no unexpected critical errors in stderr
        if stderr_output:
            # Allow expected OpenAI API errors since we're testing with invalid key
            # Allow INFO and WARNING logs, but check for unexpected errors
            expected_errors = [
                "OpenAI conversion failed",  # Expected when API key fails
                "Error code: 401",  # Expected authentication error
                "Incorrect API key provided",  # Expected API key error
            ]

            # Check if this is just an expected OpenAI API error
            is_expected_error = any(
                expected in stderr_output for expected in expected_errors
            )

            if not is_expected_error:
                assert (
                    "CRITICAL:" not in stderr_output
                ), f"Unexpected CRITICAL error in stderr: {stderr_output}"

    def test_json_extraction_and_validation(self, capsys):
        """Test that we can extract and validate the JSON from stdout"""

        import asyncio

        # Run main with mocked OpenAI to get consistent output
        with patch("recipe_rag_function.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            # Force mock mode
            mock_client.chat.completions.create.side_effect = Exception("Mock mode")

            asyncio.run(main())

        captured = capsys.readouterr()
        stdout_content = captured.out

        # Extract JSON using regex
        json_pattern = r"```json\n(.*?)\n```"
        json_matches = re.findall(json_pattern, stdout_content, re.DOTALL)

        assert (
            len(json_matches) == 1
        ), f"Expected exactly 1 JSON block, found {len(json_matches)}"

        json_content = json_matches[0]

        # Validate JSON can be parsed
        try:
            parsed_json = json.loads(json_content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in stdout: {e}")

        # Comprehensive JSON structure validation
        required_keys = ["recipes", "metadata"]
        for key in required_keys:
            assert key in parsed_json, f"Missing required key '{key}' in JSON"

        # Validate recipe structure
        recipes = parsed_json["recipes"]
        assert isinstance(recipes, list), "Recipes should be a list"
        assert len(recipes) > 0, "Should have at least one recipe"

        recipe = recipes[0]
        recipe_required_keys = [
            "name",
            "ingredients",
            "instructions",
            "servings",
            "prep_time",
            "cook_time",
            "difficulty",
            "cuisine",
        ]

        for key in recipe_required_keys:
            assert key in recipe, f"Missing required recipe key '{key}'"

        # Validate metadata structure
        metadata = parsed_json["metadata"]
        metadata_required_keys = [
            "total_recipes",
            "processed_at",
            "source",
            "processing_mode",
        ]

        for key in metadata_required_keys:
            assert key in metadata, f"Missing required metadata key '{key}'"

        # Validate data types
        assert isinstance(recipe["ingredients"], list), "Ingredients should be a list"
        assert isinstance(recipe["instructions"], list), "Instructions should be a list"
        assert isinstance(recipe["servings"], int), "Servings should be an integer"
        assert isinstance(
            metadata["total_recipes"], int
        ), "Total recipes should be an integer"

        # Validate content extraction worked
        ingredients_text = " ".join(recipe["ingredients"]).lower()
        instructions_text = " ".join(recipe["instructions"]).lower()

        # Check that some key ingredients were extracted
        assert any(
            ingredient in ingredients_text
            for ingredient in ["flour", "sugar", "butter", "chocolate"]
        ), "Should extract key ingredients from input"

        # Check that some instructions were extracted
        assert any(
            instruction in instructions_text
            for instruction in ["preheat", "mix", "bake"]
        ), "Should extract key instructions from input"

    def test_error_handling_and_logging(self, capsys):
        """Test error handling and logging behavior"""

        import asyncio

        # Test with no OpenAI key (should gracefully fall back to mock mode)
        # Remove any existing OpenAI API key to force mock mode
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        try:
            asyncio.run(main())
        finally:
            # Restore original key if it existed
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key

        captured = capsys.readouterr()
        stdout_content = captured.out

        # Should still complete successfully even without API key
        assert (
            "Test completed successfully! ✅" in stdout_content
        ), "Should complete successfully even without API key"
        assert (
            '"processing_mode": "mock"' in stdout_content
        ), "Should use mock mode when no API key available"


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v", "-s"])
