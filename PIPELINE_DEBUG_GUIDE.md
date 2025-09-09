# How to Debug the Recipe RAG Pipeline

## Breakpoint Location

Your breakpoint is at line 72 in `workspace/pipelines/recipe_rag_pipeline.py`:

```python
self.recipe_data_cache: Dict[str, List[Dict]] = {}  # Line 72
```

This line is in the `__init__` method of the Pipeline class, which gets called when the pipeline is instantiated.

## Steps to Hit the Breakpoint

### 1. Start Backend in Debug Mode

First, you need to start the backend server with debugging enabled:

```bash
# Navigate to backend directory
cd backend

# Start with Python debugger (using VS Code's debugger or pdb)
# Option A: Using VS Code's Python debugger
# Create or update .vscode/launch.json:
```

Create `.vscode/launch.json` if it doesn't exist:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Open WebUI Backend",
            "type": "python",
            "request": "launch",
            "module": "open_webui.main",
            "cwd": "${workspaceFolder}/backend",
            "env": {
                "LOG_LEVEL": "DEBUG",
                "OPENAI_API_KEY": "your-api-key-here"  // Optional: for OpenAI enhancement
            },
            "justMyCode": false,
            "console": "integratedTerminal"
        }
    ]
}
```

### 2. Register the Pipeline in Open WebUI

The pipeline needs to be registered with Open WebUI. There are two ways:

#### Method A: Through the UI (Recommended)

**IMPORTANT**: Use the **Pipelines** section, NOT the Functions section!

1. **Navigate to the Admin Panel**
   - Open <http://localhost:5173>
   - Log in as admin
   - Go to **Admin Settings** (gear icon in sidebar)
   - Navigate to **Pipelines** tab (NOT Functions!)

2. **Add the Pipeline**
   - Click **"+ Add Pipeline"** button
   - You have two options:
     a. **Copy-paste the code**: Open `workspace/pipelines/recipe_rag_pipeline.py` and paste the entire content
     b. **Upload the file**: Click upload and select `workspace/pipelines/recipe_rag_pipeline.py`
   - Click **"Save"** or **"Create"**
   - The pipeline will be registered and **instantiated** (hitting your breakpoint)

**Common Mistake**: If you see "No Function class found in the module" error, you're in the wrong section. Pipelines require a `Pipeline` class, Functions require a `Function` class.

#### Method B: Auto-load from Directory

Ensure the pipeline is in the correct directory:

```bash
# The pipeline should be in:
workspace/pipelines/recipe_rag_pipeline.py

# Open WebUI auto-loads pipelines from this directory on startup
```

### 3. Trigger the Pipeline Through Chat

Once the pipeline is registered, you can trigger it in chat:

1. **Open a New Chat**
   - Go to <http://localhost:5173>
   - Start a new conversation

2. **Trigger the Pipeline with Keywords**

   Type one of these trigger phrases:

   ```
   - "Process recipe Excel file"
   - "Convert recipe data to JSON"
   - "Parse recipe from Excel"
   - "I have a bulk recipe Excel file"
   - "Recipe schema validation"
   - "Excel to JSON for recipes"
   ```

3. **Attach Files (Optional)**
   - Click the paperclip icon (📎)
   - Upload an Excel file with recipe data
   - Or just type the trigger phrase without files for testing

### 4. Pipeline Execution Flow

When triggered, the pipeline follows this flow:

1. **Initialization** (`__init__` - Line 72) ← **YOUR BREAKPOINT**
   - Creates pipeline instance
   - Initializes `recipe_data_cache`
   - Sets up OpenAI client

2. **Startup** (`on_startup`)
   - Called after initialization
   - Sets up temp directory
   - Configures OpenAI client

3. **Message Processing** (`inlet`)
   - Detects recipe triggers in message
   - Creates processing session
   - Adds agentic messages

4. **Background Processing**
   - Validates files
   - Analyzes schema
   - Extracts data
   - RAG processing
   - Generates JSON

## Debug Tips

### Setting Additional Breakpoints

Key methods to set breakpoints for debugging:

```python
# Line 74: on_startup - Pipeline initialization
async def on_startup(self):

# Line 96: inlet - Message processing entry point
async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:

# Line 377: extract_data - Where sample recipes are created
async def extract_data(self, session: RecipeProcessingSession, step: RecipeProcessingStep):

# Line 424: rag_processing - OpenAI enhancement
async def rag_processing(self, session: RecipeProcessingSession, step: RecipeProcessingStep):

# Line 458: enhance_recipe_with_openai - Individual recipe enhancement
async def enhance_recipe_with_openai(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
```

### Monitoring Pipeline State

Add logging to track execution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug statements
logger.debug(f"Pipeline initialized with session: {self.sessions}")
logger.debug(f"Recipe cache state: {self.recipe_data_cache}")
```

### Testing Without Excel Files

The pipeline includes sample data for testing:

- Lines 386-406: Three sample recipes (Spaghetti Carbonara, Chicken Stir Fry, Chocolate Chip Cookies)
- You can trigger processing without actual Excel files

### Environment Variables

Set these for full functionality:

```bash
export OPENAI_API_KEY="your-api-key"  # For recipe enhancement
export LOG_LEVEL="DEBUG"              # For detailed logging
```

## Quick Test Command

To quickly test the pipeline after setup:

```bash
# Using curl to send a test message
curl -X POST http://localhost:8080/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Process recipe Excel file and convert to JSON with schema validation"
      }
    ]
  }'
```

## Troubleshooting

### Breakpoint Not Hit?

1. **Check Pipeline Registration**
   - Verify in Admin → Pipelines that your pipeline is listed
   - Check logs for pipeline loading errors

2. **Verify Debug Mode**
   - Ensure VS Code debugger is attached
   - Check that breakpoints are enabled (not grayed out)

3. **Check Trigger Words**
   - Message must contain one of the trigger phrases
   - Case-insensitive matching is used

4. **Backend Restart**
   - After adding breakpoints, restart the backend
   - Pipelines are loaded on startup

### Common Issues

- **Pipeline not loading**: Check file permissions and Python syntax
- **Breakpoint skipped**: Ensure you're running in debug mode, not normal mode
- **No OpenAI enhancement**: Set OPENAI_API_KEY environment variable

## Pipeline Data Flow for Debugging

```
User Message → inlet() → Create Session → Background Processing
                ↓                              ↓
          Detect Triggers              Process Steps 1-6
                ↓                              ↓
          Create Agentic UI            Generate JSON Output
                ↓                              ↓
            outlet()                    Store in cache
```

Each step can be debugged independently by setting breakpoints in the corresponding methods.
