# Backend Tests

This directory contains unit and integration tests for the backend functions and components.

## Structure

- `test_recipe_rag_function.py` - Integration tests for the recipe RAG function
- `__init__.py` - Makes test directory a proper Python package

## Running Tests

From the backend directory:

```bash
# Run all tests
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_recipe_rag_function.py -v

# Run with coverage
python -m pytest test/ --cov=functions --cov-report=html
```
