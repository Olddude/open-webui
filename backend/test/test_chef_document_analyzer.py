"""
Integration tests for chef_document_analyzer.py

Tests the chef document analyzer function with stdout assertions.
"""

import pytest
import json
import re
import subprocess
import sys
import os
from unittest.mock import patch, AsyncMock

# Import the function under test from the functions directory
from chef_document_analyzer import main


class TestChefDocumentAnalyzer:
    """Integration test class for Chef Document Analyzer with stdout assertions"""

    def test_main_function_stdout_comprehensive(self, capsys):
        """Integration test for chef main function with stdout assertions"""

        # This test runs the main function and captures all stdout output
        import asyncio

        # Mock the OpenAI client to ensure consistent test results
        with patch("chef_document_analyzer.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            # Mock the OpenAI API to force fallback to mock mode
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
            "👨‍🍳 Chef's Document Analyzer Test" in stdout_content
        ), "Missing chef test header"
        assert "Processing documents..." in stdout_content, "Missing processing message"

        # Test 2: Chef-themed content
        assert "👨‍🍳" in stdout_content, "Missing chef emoji in output"
        assert (
            "Chef's Document Analysis" in stdout_content
        ), "Missing chef analysis header"

        # Test 3: Document processing confirmation
        assert "Files processed: 2" in stdout_content, "Should process 2 test files"
        assert "sample_recipe.txt" in stdout_content, "Should mention recipe file"
        assert "nutrition_info.json" in stdout_content, "Should mention nutrition file"

        # Test 4: Mock mode behavior
        assert "Mock Mode" in stdout_content, "Should indicate mock mode"
        assert (
            "Culinary Content Detection" in stdout_content
        ), "Should show content analysis"

        # Test 5: Chef's insights and recommendations
        assert "Chef's Mock Insights" in stdout_content, "Should provide chef insights"
        assert (
            "Chef's Recommendations" in stdout_content
        ), "Should provide recommendations"

        # Test 6: Success completion
        assert (
            "analysis completed successfully" in stdout_content
        ), "Should complete successfully"

        # Test 7: Culinary analysis content
        assert "Recipe Analysis" in stdout_content, "Should analyze recipes"
        assert (
            "Cooking Techniques" in stdout_content
        ), "Should analyze cooking techniques"
        assert (
            "Ingredient Insights" in stdout_content
        ), "Should provide ingredient insights"

    def test_script_execution_via_subprocess(self):
        """Test direct script execution via subprocess"""

        # Get the functions directory path
        functions_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "functions")
        )
        script_path = os.path.join(functions_dir, "chef_document_analyzer.py")

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
            "Starting Chef's Document Analyzer Test" in stdout_output
        ), "Missing entry point message in subprocess"
        assert (
            "👨‍🍳 Chef's Document Analyzer Test" in stdout_output
        ), "Missing chef header in subprocess"
        assert (
            "analysis completed successfully" in stdout_output
        ), "Missing success message in subprocess"

        # Test that there are no unexpected critical errors in stderr
        if stderr_output:
            # Allow expected OpenAI API errors and INFO logs
            expected_patterns = [
                "OpenAI analysis failed",  # Expected when API key fails
                "Error code: 401",  # Expected authentication error
                "INFO:",  # Allow INFO level logs
                "Welcome to Chef's Document Analyzer",  # Startup message
            ]

            # Check if stderr only contains expected content
            is_expected_error = any(
                pattern in stderr_output for pattern in expected_patterns
            )

            if not is_expected_error:
                assert (
                    "CRITICAL:" not in stderr_output
                ), f"Unexpected CRITICAL error in stderr: {stderr_output}"

    def test_chef_response_formatting(self, capsys):
        """Test that chef responses are properly formatted"""

        import asyncio

        # Run main with mocked OpenAI to get consistent output
        with patch("chef_document_analyzer.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            # Force mock mode
            mock_client.chat.completions.create.side_effect = Exception("Mock mode")

            asyncio.run(main())

        captured = capsys.readouterr()
        stdout_content = captured.out

        # Test chef formatting elements
        chef_elements = [
            "👨‍🍳",  # Chef emoji
            "🔍",  # Analysis emoji
            "🍳",  # Cooking emoji
            "📋",  # Files emoji
            "**Chef's",  # Bold chef text
            "===",  # Section dividers
        ]

        for element in chef_elements:
            assert (
                element in stdout_content
            ), f"Missing chef formatting element: {element}"

        # Test structured sections
        sections = [
            "Documents Overview:",
            "Culinary Content Detection:",
            "Files Analyzed:",
            "Chef's Mock Insights:",
            "Chef's Recommendations:",
        ]

        for section in sections:
            assert section in stdout_content, f"Missing required section: {section}"

    def test_document_content_analysis(self, capsys):
        """Test that the chef analyzes document content correctly"""

        import asyncio

        # Force mock mode for consistent testing
        with patch("chef_document_analyzer.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Mock mode")

            asyncio.run(main())

        captured = capsys.readouterr()
        stdout_content = captured.out

        # Test that it detected content from the sample files
        content_analysis = [
            "Files processed: 2",  # Should process both test files
            "File types: json, txt",  # Should detect file types
            "Recipe-related content:",  # Should find recipe keywords
            "Nutrition information:",  # Should find nutrition keywords
            "sample_recipe.txt",  # Should list the recipe file
            "nutrition_info.json",  # Should list the nutrition file
        ]

        for analysis_item in content_analysis:
            assert (
                analysis_item in stdout_content
            ), f"Missing content analysis: {analysis_item}"


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v", "-s"])
