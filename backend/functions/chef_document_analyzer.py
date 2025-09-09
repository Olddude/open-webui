"""
title: Chef's Document Analyzer
author: Open WebUI
description: Your personal chef that analyzes uploaded documents for culinary insights, recipes, and food-related content
requirements: openai, python-magic, pypdf2, python-docx, openpyxl, pyyaml
"""

from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import json
import yaml
import os
import logging
import io
import base64
from pydantic import BaseModel
from openai import AsyncOpenAI
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        openai_api_key: str = ""
        openai_api_base: str = "https://api.openai.com/v1"
        openai_model: str = "gpt-4o-mini"
        temperature: float = 0.7
        max_file_size: int = 10 * 1024 * 1024  # 10MB
        supported_extensions: List[str] = [
            ".txt",
            ".pdf",
            ".doc",
            ".docx",
            ".json",
            ".csv",
            ".md",
            ".html",
            ".htm",
        ]

    def __init__(self):
        self.name = "Chef's Document Analyzer"
        self.valves = self.Valves()
        self.openai_client: Optional[AsyncOpenAI] = None

    async def on_startup(self):
        """Initialize the chef function"""
        logger.info(f"👨‍🍳 Welcome to {self.name}!")

        # Initialize OpenAI client
        try:
            api_key = os.getenv("OPENAI_API_KEY", self.valves.openai_api_key)
            if api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=api_key, base_url=self.valves.openai_api_base
                )
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("No OpenAI API key found - using mock mode")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        logger.info(f"👨‍🍳 Chef is closing the kitchen - {self.name}")

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> AsyncGenerator[str, None]:
        """Main chef function that analyzes documents"""

        messages = body.get("messages", [])
        if not messages:
            yield (
                "👨‍🍳 **Chef here!** I don't see any messages. "
                "What would you like me to analyze?"
            )
            return

        last_message = messages[-1]
        user_input = last_message.get("content", "")

        # Check for file attachments
        files = last_message.get("files", [])

        if not files:
            # No files uploaded, provide instructions with upload controls
            yield await self.provide_upload_instructions_with_controls(
                user_input, __event_emitter__
            )
            return

        # Process uploaded files with progress tracking
        try:
            # Emit UI form with progress component
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "ui:agent_form",
                        "data": {
                            "version": "1.0.0",
                            "type": "ui-agent-form",
                            "metadata": {
                                "title": "Document Analysis Progress",
                                "agent": "chef_document_analyzer",
                                "timestamp": datetime.now().isoformat(),
                                "sessionId": "chef_analysis",
                            },
                            "components": [
                                {
                                    "id": "progress_container",
                                    "type": "container",
                                    "layout": "vertical",
                                    "children": [
                                        {
                                            "id": "progress_title",
                                            "type": "text",
                                            "content": "👨‍🍳 Analyzing your documents...",
                                            "variant": "h3",
                                        },
                                        {
                                            "id": "progress_bar",
                                            "type": "progress",
                                            "value": 0,
                                            "label": "Initializing analysis",
                                            "variant": "linear",
                                            "color": "primary",
                                            "showPercentage": True,
                                        },
                                    ],
                                }
                            ],
                        },
                    }
                )

            yield (
                "👨‍🍳 **Excellent!** I see you've uploaded some documents. "
                "Let me put on my chef's hat and analyze them...\n\n"
            )

            # Emit progress update UI form
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "ui:update_form",
                        "data": {
                            "sessionId": "chef_analysis",
                            "updates": [
                                {
                                    "id": "progress_bar",
                                    "properties": {
                                        "value": 25,
                                        "label": "Processing uploaded files",
                                    },
                                }
                            ],
                        },
                    }
                )

            document_contents = []

            for i, file_info in enumerate(files):
                # Update progress for each file
                if __event_emitter__:
                    progress = 25 + (50 * (i + 1)) // len(files)
                    await __event_emitter__(
                        {
                            "type": "ui:update_form",
                            "data": {
                                "sessionId": "chef_analysis",
                                "updates": [
                                    {
                                        "id": "progress_bar",
                                        "properties": {
                                            "value": progress,
                                            "label": f"Processing file: {file_info.get('name', 'unknown')}",
                                        },
                                    }
                                ],
                            },
                        }
                    )

                file_content = await self.process_file(file_info)
                if file_content:
                    document_contents.append(file_content)

            if not document_contents:
                # Emit task failure
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "task:error",
                            "data": {
                                "task_id": "chef_analysis",
                                "error": (
                                    "No extractable content found in " "uploaded files"
                                ),
                            },
                        }
                    )
                yield (
                    "😅 **Chef's note:** I couldn't extract content from the "
                    "uploaded files. Please make sure they're in a supported "
                    "format (txt, pdf, doc, docx, json, csv, md)."
                )
                return

            # Update progress for analysis phase
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "ui:update_form",
                        "data": {
                            "sessionId": "chef_analysis",
                            "updates": [
                                {
                                    "id": "progress_bar",
                                    "properties": {
                                        "value": 75,
                                        "label": "Analyzing content with culinary expertise",
                                    },
                                }
                            ],
                        },
                    }
                )

            # Analyze documents with culinary expertise
            analysis = await self.analyze_documents_as_chef(
                document_contents, user_input
            )

            # Emit task completion with success alert
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "ui:agent_form",
                        "data": {
                            "version": "1.0.0",
                            "type": "ui-agent-form",
                            "metadata": {
                                "title": "Analysis Complete",
                                "agent": "chef_document_analyzer",
                                "timestamp": datetime.now().isoformat(),
                                "sessionId": "chef_analysis_complete",
                            },
                            "components": [
                                {
                                    "id": "success_alert",
                                    "type": "alert",
                                    "message": "Analysis complete! Your culinary document analysis is ready below.",
                                    "variant": "success",
                                    "title": "👨‍🍳 Chef's Analysis Ready",
                                    "icon": True,
                                }
                            ],
                        },
                    }
                )

            yield analysis

        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            # Emit task error
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "task:error",
                        "data": {"task_id": "chef_analysis", "error": str(e)},
                    }
                )
            yield (
                f"🍳 **Chef's apology:** I encountered an issue while "
                f"analyzing your documents: {str(e)}"
            )

    async def provide_upload_instructions(self, user_input: str) -> str:
        """Provide instructions for document upload"""

        instructions = """
👨‍🍳 **Greetings from your Personal Chef!**

I'm here to analyze your documents with a culinary perspective! I can help with:

🍳 **What I can analyze:**
- Recipe collections and cookbooks
- Ingredient lists and nutrition data
- Menu planning documents
- Food safety guidelines
- Restaurant reviews and food blogs
- Cooking technique guides
- Dietary requirement documents

📁 **Supported file formats:**
- Text files (.txt, .md)
- HTML files (.html, .htm)
- PDFs (.pdf)
- Word documents (.doc, .docx)
- JSON data (.json)
- CSV spreadsheets (.csv)

📤 **To get started:**
1. Click the attachment/upload button in the chat
2. Select your document(s) - up to 10MB each
3. Tell me what you'd like me to focus on (optional)

🎯 **Example requests:**
- "Find all the dessert recipes in this cookbook"
- "Analyze the nutritional content of this menu"
- "Extract cooking times from these recipes"
- "Help me organize these ingredients by cuisine type"

**Ready when you are!** Upload your documents and I'll give you my 
chef's analysis! 👨‍🍳✨
"""

        # If user provided specific input, acknowledge it
        if user_input and user_input.strip():
            instructions += (
                f'\n\n*I noticed you mentioned: "{user_input}"* - I\'ll keep '
                f"that in mind when analyzing your documents!"
            )

        return instructions

    async def provide_upload_instructions_with_controls(
        self, user_input: str, event_emitter=None
    ) -> str:
        """Provide instructions for document upload with interactive controls"""

        # Emit UI agent form event matching the schema
        if event_emitter:
            await event_emitter(
                {
                    "type": "ui:agent_form",
                    "data": {
                        "version": "1.0.0",
                        "type": "ui-agent-form",
                        "metadata": {
                            "title": "Chef Document Analyzer",
                            "description": "Upload and analyze culinary documents",
                            "agent": "chef_document_analyzer",
                            "timestamp": datetime.now().isoformat(),
                            "capabilities": [
                                "file_upload",
                                "document_analysis",
                                "recipe_extraction",
                            ],
                        },
                        "layout": {"type": "single", "responsive": True},
                        "components": [
                            {
                                "id": "chef_header",
                                "type": "container",
                                "layout": "vertical",
                                "className": "chef-header",
                                "children": [
                                    {
                                        "id": "title",
                                        "type": "text",
                                        "content": "👨‍🍳 **Greetings from your Personal Chef!**",
                                        "variant": "h2",
                                    },
                                    {
                                        "id": "subtitle",
                                        "type": "text",
                                        "content": "I'm here to analyze your documents with a culinary perspective!",
                                        "variant": "body",
                                    },
                                ],
                            },
                            {
                                "id": "capabilities_section",
                                "type": "container",
                                "layout": "columns",
                                "columns": 2,
                                "gap": "1rem",
                                "children": [
                                    {
                                        "id": "what_i_analyze",
                                        "type": "container",
                                        "layout": "vertical",
                                        "children": [
                                            {
                                                "id": "analyze_title",
                                                "type": "text",
                                                "content": "🍳 **What I can analyze:**",
                                                "variant": "h4",
                                            },
                                            {
                                                "id": "analyze_list",
                                                "type": "markdown",
                                                "content": "- Recipe collections and cookbooks\\n- Ingredient lists and nutrition data\\n- Menu planning documents\\n- Food safety guidelines\\n- Restaurant reviews and food blogs\\n- Cooking technique guides\\n- Dietary requirement documents",
                                            },
                                        ],
                                    },
                                    {
                                        "id": "file_formats",
                                        "type": "container",
                                        "layout": "vertical",
                                        "children": [
                                            {
                                                "id": "formats_title",
                                                "type": "text",
                                                "content": "📁 **Supported file formats:**",
                                                "variant": "h4",
                                            },
                                            {
                                                "id": "formats_list",
                                                "type": "markdown",
                                                "content": "- Text files (.txt, .md)\\n- HTML files (.html, .htm)\\n- PDFs (.pdf)\\n- Word documents (.doc, .docx)\\n- JSON data (.json)\\n- CSV spreadsheets (.csv)",
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "id": "upload_section",
                                "type": "container",
                                "layout": "vertical",
                                "className": "upload-section",
                                "style": {"marginTop": "2rem"},
                                "children": [
                                    {
                                        "id": "upload_title",
                                        "type": "text",
                                        "content": "📤 **Upload Your Documents**",
                                        "variant": "h3",
                                    },
                                    {
                                        "id": "file_uploader",
                                        "type": "fileUpload",
                                        "label": "Drop your culinary documents here or click to browse",
                                        "accept": ".txt,.pdf,.doc,.docx,.json,.csv,.md,.html,.htm",
                                        "multiple": True,
                                        "maxSize": "10MB",
                                        "dragDrop": True,
                                        "showPreview": True,
                                    },
                                ],
                            },
                            {
                                "id": "examples_section",
                                "type": "container",
                                "layout": "vertical",
                                "className": "examples-section",
                                "style": {"marginTop": "1.5rem"},
                                "children": [
                                    {
                                        "id": "examples_title",
                                        "type": "text",
                                        "content": "🎯 **Example requests:**",
                                        "variant": "h4",
                                    },
                                    {
                                        "id": "examples_grid",
                                        "type": "container",
                                        "layout": "grid",
                                        "columns": 2,
                                        "gap": "0.5rem",
                                        "children": [
                                            {
                                                "id": "example_1",
                                                "type": "badge",
                                                "label": "Find all dessert recipes",
                                                "variant": "info",
                                            },
                                            {
                                                "id": "example_2",
                                                "type": "badge",
                                                "label": "Analyze nutritional content",
                                                "variant": "success",
                                            },
                                            {
                                                "id": "example_3",
                                                "type": "badge",
                                                "label": "Extract cooking times",
                                                "variant": "warning",
                                            },
                                            {
                                                "id": "example_4",
                                                "type": "badge",
                                                "label": "Organize by cuisine type",
                                                "variant": "primary",
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "id": "footer_message",
                                "type": "alert",
                                "message": "Ready when you are! Upload your documents and I'll give you my chef's analysis! 👨‍🍳✨",
                                "variant": "info",
                                "icon": True,
                            },
                        ],
                        "state": {"uploadedFiles": []},
                        "actions": {
                            "onFileUpload": {
                                "type": "emit",
                                "handler": "handleFileUpload",
                                "params": {"eventName": "files:uploaded"},
                            }
                        },
                    },
                }
            )

        # Return a simple text message for fallback
        return "Please upload your culinary documents using the interface above. I'm ready to analyze them with my chef's expertise! 👨‍🍳"

    async def process_file(self, file_info: dict) -> Optional[Dict[str, Any]]:
        """Process uploaded file and extract content"""

        try:
            filename = file_info.get("name", "unknown")
            file_content = file_info.get("content", "")

            # Basic file info
            file_data = {"filename": filename, "content": "", "type": "unknown"}

            # Handle base64 encoded content
            if file_content.startswith("data:"):
                # Extract base64 content
                base64_data = (
                    file_content.split(",", 1)[1]
                    if "," in file_content
                    else file_content
                )
                try:
                    decoded_content = base64.b64decode(base64_data).decode("utf-8")
                    file_data["content"] = decoded_content
                    file_data["type"] = self._detect_content_type(
                        filename, decoded_content
                    )
                except Exception:
                    # If it's not text, treat as binary
                    file_data["content"] = f"[Binary file: {filename}]"
                    file_data["type"] = "binary"
            else:
                # Assume it's already text content
                file_data["content"] = file_content
                file_data["type"] = self._detect_content_type(filename, file_content)

            # Process content based on type
            file_data["processed_content"] = self._process_content_by_type(
                file_data["content"], file_data["type"]
            )

            return file_data

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return None

    def _detect_content_type(self, filename: str, content: str) -> str:
        """Detect content type based on filename and content"""

        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension in ["html", "htm"]:
            return "html"
        elif extension == "md":
            return "markdown"
        elif extension == "json":
            return "json"
        elif extension == "csv":
            return "csv"
        elif content.strip().startswith(("<html", "<!DOCTYPE", "<HTML")):
            return "html"
        elif content.strip().startswith("#") or "##" in content:
            return "markdown"
        elif content.strip().startswith(("{", "[")):
            return "json"
        else:
            return "text"

    def _process_content_by_type(self, content: str, content_type: str) -> str:
        """Process content based on its detected type"""

        if content_type == "html":
            # Strip HTML tags for analysis but keep structure
            import re

            # Remove HTML tags but preserve line breaks and structure
            text = re.sub(
                r"<script[^>]*>.*?</script>",
                "",
                content,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(
                r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE
            )
            text = re.sub(r"<[^>]+>", " ", text)
            # Convert HTML entities
            text = (
                text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
            )
            return " ".join(text.split())  # Clean up whitespace

        elif content_type == "markdown":
            # Clean markdown formatting for analysis while preserving meaning
            import re

            text = re.sub(r"#+\s*", "", content)  # Remove heading markers
            text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)  # Remove bold/italic
            text = re.sub(r"`([^`]+)`", r"\1", text)  # Remove inline code
            text = re.sub(
                r"\[([^\]]+)\]\([^)]+\)", r"\1", text
            )  # Remove links, keep text
            return text

        elif content_type == "json":
            # Pretty format JSON for better analysis
            try:
                import json as json_module

                parsed = json_module.loads(content)
                return json_module.dumps(parsed, indent=2, ensure_ascii=False)
            except:
                return content

        else:
            return content

    async def analyze_documents_as_chef(
        self, documents: List[Dict[str, Any]], user_query: str = ""
    ) -> str:
        """Analyze documents from a chef's perspective"""

        if self.openai_client:
            return await self.analyze_with_openai(documents, user_query)
        else:
            return await self.analyze_with_mock(documents, user_query)

    async def analyze_with_openai(
        self, documents: List[Dict[str, Any]], user_query: str
    ) -> str:
        """Use OpenAI to analyze documents as a chef"""

        # Prepare document content for analysis
        doc_summary = []
        for i, doc in enumerate(documents, 1):
            doc_summary.append(f"**Document {i}: {doc['filename']}**")
            content_to_analyze = doc.get("processed_content", doc["content"])
            content_preview = (
                content_to_analyze[:1000] + "..."
                if len(content_to_analyze) > 1000
                else content_to_analyze
            )
            doc_type = doc.get("type", "text")
            doc_summary.append(f"Content type: {doc_type}")
            doc_summary.append(f"Content preview: {content_preview}\n")

        combined_docs = "\n".join(doc_summary)

        chef_prompt = f"""
You are a highly experienced and passionate chef with expertise in cuisine 
from around the world. You have been asked to analyze the following 
documents with your culinary expertise.

Please provide a comprehensive analysis from a chef's perspective, focusing on:
1. Recipe identification and analysis
2. Ingredient insights and substitutions
3. Cooking techniques and methods
4. Nutritional considerations
5. Cuisine types and cultural context
6. Practical cooking tips and improvements

User's specific request: {user_query if user_query else "General analysis"}

Documents to analyze:
{combined_docs}

Please respond as an enthusiastic, knowledgeable chef who loves to share 
culinary wisdom. Use chef emojis and terminology appropriately. Structure 
your response with clear sections and actionable insights.
"""

        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=self.valves.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a world-class chef and culinary "
                                "expert. Respond with enthusiasm, expertise, "
                                "and practical cooking advice."
                            ),
                        },
                        {"role": "user", "content": chef_prompt},
                    ],
                    temperature=self.valves.temperature,
                ),
                timeout=60.0,
            )

            chef_analysis = response.choices[0].message.content.strip()

            # Add chef header and footer with enhanced formatting
            final_response = f"""
<div class="chef-analysis-report">

## 👨‍🍳 **Chef's Document Analysis**

{chef_analysis}

---

### 📊 **Analysis Summary**
- **Documents processed:** {len(documents)}
- **Files analyzed:** {', '.join([doc['filename'] for doc in documents])}
- **Content types:** {', '.join(set([doc.get('type', 'text') for doc in documents]))}
- **Analysis completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 🍳 **Chef's Note**
Feel free to ask follow-up questions about any of the culinary insights I've shared! I can provide more specific guidance on recipes, techniques, or ingredients.

</div>
"""

            return final_response

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return await self.analyze_with_mock(documents, user_query)

    async def analyze_with_mock(
        self, documents: List[Dict[str, Any]], user_query: str
    ) -> str:
        """Provide mock analysis when OpenAI is not available"""

        total_content_length = sum(len(doc["content"]) for doc in documents)
        file_types = set()

        # Basic content analysis
        recipe_keywords = [
            "recipe",
            "ingredient",
            "cook",
            "bake",
            "fry",
            "boil",
            "simmer",
            "season",
        ]
        nutrition_keywords = [
            "calorie",
            "protein",
            "fat",
            "carb",
            "vitamin",
            "mineral",
            "nutrition",
        ]
        technique_keywords = [
            "sauté",
            "braise",
            "grill",
            "roast",
            "steam",
            "poach",
            "blanch",
        ]

        found_recipes = 0
        found_nutrition = 0
        found_techniques = 0

        for doc in documents:
            content_to_analyze = doc.get("processed_content", doc["content"])
            content_lower = content_to_analyze.lower()
            file_ext = (
                doc["filename"].split(".")[-1] if "." in doc["filename"] else "unknown"
            )
            file_types.add(file_ext)

            found_recipes += sum(
                1 for keyword in recipe_keywords if keyword in content_lower
            )
            found_nutrition += sum(
                1 for keyword in nutrition_keywords if keyword in content_lower
            )
            found_techniques += sum(
                1 for keyword in technique_keywords if keyword in content_lower
            )

        analysis = f"""
<div class="chef-mock-analysis">

## 👨‍🍳 **Chef's Document Analysis** (Mock Mode)

### **Documents Overview**
- **Files processed:** {len(documents)}
- **File types:** {', '.join(file_types)}
- **Content types:** {', '.join(set([doc.get('type', 'text') for doc in documents]))}
- **Total content:** {total_content_length:,} characters

### 🔍 **Culinary Content Detection**
- **Recipe-related content:** {found_recipes} references found
- **Nutrition information:** {found_nutrition} references found
- **Cooking techniques:** {found_techniques} references found

### 📋 **Files Analyzed**
{chr(10).join([
    f"• **{doc['filename']}** ({len(doc['content'])} chars) - *{doc.get('type', 'text')}*" 
    for doc in documents
])}

### 🍳 **Chef's Mock Insights**
Based on my analysis, your documents appear to contain 
{"recipe" if found_recipes > 5 else "food-related"} content. 
Here are my culinary observations:

**📝 Recipe Analysis:**
- I've identified potential recipe content with cooking instructions 
  and ingredient lists
- The documents seem to focus on 
  {"international cuisine" if len(documents) > 2 else "specific methods"}

**👨‍🍳 Cooking Techniques:**
- Various cooking methods are mentioned throughout the documents
- Temperature and timing information appears to be present

**🥬 Ingredient Insights:**
- Multiple ingredients are referenced across the documents
- Seasonal and fresh ingredient usage seems to be emphasized

### **Chef's Recommendations:**
1. 🥗 Focus on fresh, seasonal ingredients when possible
2. 🔥 Pay attention to cooking temperatures and timing
3. 🧂 Taste and adjust seasonings throughout the cooking process
4. 📖 Keep these documents as reference for future culinary adventures

---
> ⚠️ **Note:** This is a mock analysis. For detailed culinary insights, 
> please configure an OpenAI API key in the settings.

### 🍳 **Chef's Final Note**
Even without AI analysis, I can see you're passionate about cooking! 
Feel free to ask specific questions about any recipes or techniques 
you'd like to discuss!

</div>"""

        if user_query:
            analysis += (
                f'\n\n**Regarding your specific request:** "{user_query}"\n'
                f"I would love to provide more detailed insights with full "
                f"AI analysis capabilities!"
            )

        return analysis


async def main():
    """Main handler for testing the chef document function"""

    # Example file data for testing
    example_files = [
        {
            "name": "sample_recipe.txt",
            "content": """
Chocolate Chip Cookies Recipe

Ingredients:
- 2 1/4 cups all-purpose flour  
- 1 tsp baking soda
- 1 tsp salt
- 1 cup butter, softened
- 3/4 cup granulated sugar
- 3/4 cup packed brown sugar  
- 2 large eggs
- 2 tsp vanilla extract
- 2 cups chocolate chips

Instructions:
1. Preheat oven to 375°F (190°C)
2. Mix flour, baking soda and salt in bowl
3. Beat butter, sugars, eggs and vanilla until creamy
4. Gradually beat in flour mixture
5. Stir in chocolate chips
6. Drop rounded tablespoons onto ungreased cookie sheets  
7. Bake 9-11 minutes or until golden brown
8. Cool on baking sheet for 2 minutes

Serves: 48 cookies
Prep time: 15 minutes
Bake time: 9-11 minutes
""",
        },
        {
            "name": "nutrition_info.json",
            "content": """
{
  "nutrition_per_serving": {
    "calories": 142,
    "total_fat": "7g",
    "saturated_fat": "4g", 
    "cholesterol": "18mg",
    "sodium": "95mg",
    "total_carbs": "19g",
    "dietary_fiber": "1g",
    "sugars": "11g",
    "protein": "2g"
  },
  "allergens": ["wheat", "eggs", "dairy", "soy"],
  "dietary_notes": "Contains gluten. Not suitable for vegans."
}
""",
        },
    ]

    # Example body structure
    example_body = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please analyze these recipe documents and give me "
                    "your chef's perspective"
                ),
                "files": example_files,
            }
        ]
    }

    # Example user metadata
    example_user = {"id": "test_user", "name": "Test Chef"}

    # Example metadata
    example_metadata = {
        "request_id": "chef_test_123",
        "timestamp": datetime.now().isoformat(),
    }

    print("👨‍🍳 Chef's Document Analyzer Test")
    print("=" * 60)
    print("Testing document analysis with sample recipe and nutrition files...")
    print("=" * 60)

    # Initialize the Pipe class
    pipe_instance = Pipe()

    # Call startup
    await pipe_instance.on_startup()

    print("\n🔍 Processing documents...")
    print("=" * 60)

    # Process the documents using the pipe function
    result_chunks = []
    async for chunk in pipe_instance.pipe(
        body=example_body, __user__=example_user, __metadata__=example_metadata
    ):
        result_chunks.append(chunk)

    # Print the complete result
    full_result = "".join(result_chunks)
    print(full_result)

    print("\n" + "=" * 60)
    print("👨‍🍳 Chef's analysis completed successfully! ✅")

    # Call shutdown
    await pipe_instance.on_shutdown()


if __name__ == "__main__":
    """Entry point when running the script directly"""
    print("Starting Chef's Document Analyzer Test...")
    asyncio.run(main())
