"""
title: Simple RAG Function
author: Open WebUI
description: A simple RAG (Retrieval-Augmented Generation) function that enhances responses with context
requirements:
"""

import json
import logging
from typing import List, Dict, Any, Optional, Generator, Union, Iterator
from datetime import datetime
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        # Configuration for the RAG function
        enable_rag: bool = True
        context_window_size: int = 3
        enable_context_display: bool = True
        debug_mode: bool = False

    def __init__(self):
        self.name = "Simple RAG Function"
        self.valves = self.Valves()
        # Simple knowledge base for demonstration
        self.knowledge_base = {
            "recipes": [
                {
                    "id": "1",
                    "name": "Spaghetti Carbonara",
                    "ingredients": [
                        "spaghetti",
                        "eggs",
                        "pancetta",
                        "parmesan",
                        "black pepper",
                    ],
                    "time": "30 minutes",
                    "difficulty": "medium",
                    "cuisine": "Italian",
                },
                {
                    "id": "2",
                    "name": "Chicken Stir Fry",
                    "ingredients": [
                        "chicken",
                        "bell peppers",
                        "onion",
                        "soy sauce",
                        "ginger",
                        "garlic",
                    ],
                    "time": "25 minutes",
                    "difficulty": "easy",
                    "cuisine": "Asian",
                },
                {
                    "id": "3",
                    "name": "Greek Salad",
                    "ingredients": [
                        "tomatoes",
                        "cucumber",
                        "feta cheese",
                        "olives",
                        "olive oil",
                        "oregano",
                    ],
                    "time": "15 minutes",
                    "difficulty": "easy",
                    "cuisine": "Greek",
                },
                {
                    "id": "4",
                    "name": "Beef Tacos",
                    "ingredients": [
                        "ground beef",
                        "taco shells",
                        "lettuce",
                        "cheese",
                        "salsa",
                        "sour cream",
                    ],
                    "time": "20 minutes",
                    "difficulty": "easy",
                    "cuisine": "Mexican",
                },
                {
                    "id": "5",
                    "name": "Mushroom Risotto",
                    "ingredients": [
                        "arborio rice",
                        "mushrooms",
                        "white wine",
                        "parmesan",
                        "butter",
                        "onion",
                    ],
                    "time": "45 minutes",
                    "difficulty": "hard",
                    "cuisine": "Italian",
                },
            ],
            "cooking_tips": {
                "pasta": "Always salt your pasta water generously - it should taste like the sea.",
                "stir_fry": "Keep ingredients moving in the wok and use high heat for best results.",
                "risotto": "Add stock gradually and stir constantly for creamy risotto.",
                "meat": "Let meat rest after cooking to redistribute juices.",
                "vegetables": "Don't overcook vegetables - they should retain some crunch.",
            },
            "techniques": {
                "sautéing": "Cook food quickly in a small amount of oil over relatively high heat.",
                "braising": "Brown food first, then cook slowly in liquid.",
                "grilling": "Cook food on a grill over direct heat.",
                "roasting": "Cook food in an oven with dry heat.",
                "steaming": "Cook food using steam from boiling water.",
            },
        }

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, Generator, Iterator]:
        """Main RAG processing function"""

        if not self.valves.enable_rag:
            # Pass through without RAG enhancement
            return "RAG is currently disabled. Enable it in the function settings."

        messages = body.get("messages", [])
        if not messages:
            return "No messages provided"

        last_message = messages[-1]
        user_query = last_message.get("content", "").lower()

        # Emit status if event emitter is available
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Searching knowledge base...",
                        "done": False,
                    },
                }
            )

        # Retrieve relevant context
        relevant_context = self.retrieve_context(user_query)

        # Generate enhanced response
        response = self.generate_response(user_query, relevant_context)

        # Emit completion status
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "RAG processing complete", "done": True},
                }
            )

        return response

    def retrieve_context(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant context from knowledge base"""
        context = {"recipes": [], "tips": [], "techniques": []}

        # Simple keyword-based retrieval (in production, use embeddings)
        query_words = query.split()

        # Search recipes
        for recipe in self.knowledge_base["recipes"]:
            relevance_score = 0

            # Check recipe name
            if any(word in recipe["name"].lower() for word in query_words):
                relevance_score += 3

            # Check ingredients
            for ingredient in recipe["ingredients"]:
                if any(word in ingredient.lower() for word in query_words):
                    relevance_score += 2

            # Check cuisine
            if any(word in recipe["cuisine"].lower() for word in query_words):
                relevance_score += 1

            # Check difficulty
            if any(word in recipe["difficulty"].lower() for word in query_words):
                relevance_score += 1

            if relevance_score > 0:
                context["recipes"].append(
                    {"recipe": recipe, "relevance": relevance_score}
                )

        # Sort by relevance and take top results
        context["recipes"] = sorted(
            context["recipes"], key=lambda x: x["relevance"], reverse=True
        )[: self.valves.context_window_size]

        # Search cooking tips
        for key, tip in self.knowledge_base["cooking_tips"].items():
            if any(word in key.lower() for word in query_words):
                context["tips"].append({"topic": key, "tip": tip})

        # Search techniques
        for technique, description in self.knowledge_base["techniques"].items():
            if any(word in technique.lower() for word in query_words):
                context["techniques"].append(
                    {"name": technique, "description": description}
                )

        if self.valves.debug_mode:
            logger.info(f"Retrieved context for query '{query}': {context}")

        return context

    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        """Generate response augmented with retrieved context"""

        response_parts = []

        # Add header
        response_parts.append("🔍 **RAG-Enhanced Response**\n")

        # Check what type of query it is
        if "recipe" in query or "cook" in query or "make" in query:
            if context["recipes"]:
                response_parts.append("## 📖 Relevant Recipes Found:\n")
                for item in context["recipes"]:
                    recipe = item["recipe"]
                    response_parts.append(f"\n### {recipe['name']}")
                    response_parts.append(f"- **Cuisine:** {recipe['cuisine']}")
                    response_parts.append(f"- **Difficulty:** {recipe['difficulty']}")
                    response_parts.append(f"- **Time:** {recipe['time']}")
                    response_parts.append(
                        f"- **Main Ingredients:** {', '.join(recipe['ingredients'][:5])}"
                    )

                    # Add specific tips if available
                    if (
                        recipe["cuisine"].lower() == "italian"
                        and "pasta" in recipe["name"].lower()
                    ):
                        if pasta_tip := self.knowledge_base["cooking_tips"].get(
                            "pasta"
                        ):
                            response_parts.append(f"\n💡 **Pro Tip:** {pasta_tip}")
            else:
                response_parts.append(
                    "\nNo specific recipes found in the knowledge base for your query."
                )

        # Add cooking tips if relevant
        if context["tips"]:
            response_parts.append("\n## 💡 Cooking Tips:\n")
            for tip in context["tips"]:
                response_parts.append(f"- **{tip['topic'].title()}:** {tip['tip']}")

        # Add techniques if relevant
        if context["techniques"]:
            response_parts.append("\n## 🔧 Cooking Techniques:\n")
            for technique in context["techniques"]:
                response_parts.append(
                    f"- **{technique['name'].title()}:** {technique['description']}"
                )

        # Add context display if enabled
        if self.valves.enable_context_display and (
            context["recipes"] or context["tips"] or context["techniques"]
        ):
            response_parts.append("\n---")
            response_parts.append(
                f"\n*📊 RAG Context: Retrieved {len(context['recipes'])} recipes, "
                f"{len(context['tips'])} tips, and {len(context['techniques'])} techniques*"
            )

        # If no context was found
        if not any([context["recipes"], context["tips"], context["techniques"]]):
            response_parts = [
                "I couldn't find specific information in my knowledge base for your query.\n\n",
                "Try asking about:\n",
                "- Specific recipes (e.g., 'How do I make carbonara?')\n",
                "- Cooking techniques (e.g., 'What is braising?')\n",
                "- General cooking tips (e.g., 'Tips for cooking pasta')\n",
                "\nAvailable recipes in my knowledge base:\n",
                ", ".join([r["name"] for r in self.knowledge_base["recipes"]]),
            ]

        return "\n".join(response_parts)
