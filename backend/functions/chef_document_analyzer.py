"""
title: Chef's Document Analyzer
author: Open WebUI
description: Your personal chef that analyzes uploaded documents for culinary insights, recipes, and food-related content
requirements: openai, python-magic, pypdf2, python-docx, openpyxl
"""

from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import json
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
            yield "👨‍🍳 **Chef here!** I don't see any messages. What would you like me to analyze?"
            return

        last_message = messages[-1]
        user_input = last_message.get("content", "")

        # Check for file attachments
        files = last_message.get("files", [])

        if not files:
            # No files uploaded, provide instructions
            yield await self.provide_upload_instructions(user_input)
            return

        # Process uploaded files
        try:
            yield "👨‍🍳 **Excellent!** I see you've uploaded some documents. Let me put on my chef's hat and analyze them...\n\n"

            document_contents = []

            for file_info in files:
                file_content = await self.process_file(file_info)
                if file_content:
                    document_contents.append(file_content)

            if not document_contents:
                yield "😅 **Chef's note:** I couldn't extract content from the uploaded files. Please make sure they're in a supported format (txt, pdf, doc, docx, json, csv, md)."
                return

            # Analyze documents with culinary expertise
            analysis = await self.analyze_documents_as_chef(
                document_contents, user_input
            )
            yield analysis

        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            yield f"🍳 **Chef's apology:** I encountered an issue while analyzing your documents: {str(e)}"

    async def provide_upload_instructions(self, user_input: str) -> str:
        """Provide instructions for document upload"""

        instructions = """
👨‍🍳 **Greetings from your Personal Chef!**

I'm here to analyze your documents with a culinary perspective! I can help you with:

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

**Ready when you are!** Upload your documents and I'll give you my chef's analysis! 👨‍🍳✨
"""

        # If user provided specific input, acknowledge it
        if user_input and user_input.strip():
            instructions += f'\n\n*I noticed you mentioned: "{user_input}"* - I\'ll keep that in mind when analyzing your documents!'

        return instructions

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
                    file_data["type"] = "text"
                except Exception:
                    # If it's not text, treat as binary
                    file_data["content"] = f"[Binary file: {filename}]"
                    file_data["type"] = "binary"
            else:
                # Assume it's already text content
                file_data["content"] = file_content
                file_data["type"] = "text"

            return file_data

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return None

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
            content_preview = (
                doc["content"][:1000] + "..."
                if len(doc["content"]) > 1000
                else doc["content"]
            )
            doc_summary.append(f"Content preview: {content_preview}\n")

        combined_docs = "\n".join(doc_summary)

        chef_prompt = f"""
You are a highly experienced and passionate chef with expertise in cuisine from around the world. You have been asked to analyze the following documents with your culinary expertise.

Please provide a comprehensive analysis from a chef's perspective, focusing on:
1. Recipe identification and analysis
2. Ingredient insights and substitutions
3. Cooking techniques and methods
4. Nutritional considerations
5. Cuisine types and cultural context
6. Practical cooking tips and improvements

User's specific request: {user_query if user_query else "General culinary analysis"}

Documents to analyze:
{combined_docs}

Please respond as an enthusiastic, knowledgeable chef who loves to share culinary wisdom. Use chef emojis and terminology appropriately. Structure your response with clear sections and actionable insights.
"""

        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=self.valves.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a world-class chef and culinary expert. Respond with enthusiasm, expertise, and practical cooking advice.",
                        },
                        {"role": "user", "content": chef_prompt},
                    ],
                    temperature=self.valves.temperature,
                ),
                timeout=60.0,
            )

            chef_analysis = response.choices[0].message.content.strip()

            # Add chef header and footer
            final_response = f"""
👨‍🍳 **Chef's Document Analysis**

{chef_analysis}

---
📊 **Analysis Summary:**
- Documents processed: {len(documents)}
- Files analyzed: {', '.join([doc['filename'] for doc in documents])}
- Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🍳 **Chef's note:** Feel free to ask follow-up questions about any of the culinary insights I've shared!
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
            content_lower = doc["content"].lower()
            file_types.add(
                doc["filename"].split(".")[-1] if "." in doc["filename"] else "unknown"
            )

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
👨‍🍳 **Chef's Document Analysis** (Mock Mode)

**Documents Overview:**
- Files processed: {len(documents)}
- File types: {', '.join(file_types)}
- Total content: {total_content_length:,} characters

🔍 **Culinary Content Detection:**
- Recipe-related content: {found_recipes} references found
- Nutrition information: {found_nutrition} references found  
- Cooking techniques: {found_techniques} references found

📋 **Files Analyzed:**
{chr(10).join([f"• {doc['filename']} ({len(doc['content'])} chars)" for doc in documents])}

🍳 **Chef's Mock Insights:**
Based on my analysis, your documents appear to contain {"recipe" if found_recipes > 5 else "food-related"} content. Here are my culinary observations:

**Recipe Analysis:**
- I've identified potential recipe content with cooking instructions and ingredient lists
- The documents seem to focus on {"international cuisine" if len(documents) > 2 else "specific cooking methods"}

**Cooking Techniques:**
- Various cooking methods are mentioned throughout the documents
- Temperature and timing information appears to be present

**Ingredient Insights:**
- Multiple ingredients are referenced across the documents
- Seasonal and fresh ingredient usage seems to be emphasized

**Chef's Recommendations:**
1. 🥗 Focus on fresh, seasonal ingredients when possible
2. 🔥 Pay attention to cooking temperatures and timing
3. 🧂 Taste and adjust seasonings throughout the cooking process
4. 📖 Keep these documents as reference for future culinary adventures

---
⚠️ **Note:** This is a mock analysis. For detailed culinary insights, please configure an OpenAI API key in the settings.

🍳 **Chef's note:** Even without AI analysis, I can see you're passionate about cooking! Feel free to ask specific questions about any recipes or techniques you'd like to discuss!
"""

        if user_query:
            analysis += f'\n\n**Regarding your specific request:** "{user_query}"\nI would love to provide more detailed insights with full AI analysis capabilities!'

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
                "content": "Please analyze these recipe documents and give me your chef's perspective",
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
