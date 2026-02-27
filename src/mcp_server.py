#!/usr/bin/env python3
"""
Edamam Food Database MCP Server.

Provides three MCP tools for food and nutrition information:
- get_food_nutrition: Get nutrition info for a food by name or UPC code
- search_food: Search for foods in the Edamam database
- analyze_food_image: Extract nutrition from a food image
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import src module
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import re
from typing import Any

from fastmcp import FastMCP
from src.edamam_service import (
    search_food as service_search_food,
    get_food_nutrition as service_get_nutrition,
    get_nutrition_from_image,
    is_upc
)
from src.logger import mcp_logger

# Initialize FastMCP server
mcp = FastMCP("edamam-food")

# Image URL pattern detection
IMAGE_URL_PATTERN = re.compile(
    r'https?://.*\.(jpg|jpeg|png|gif|webp|bmp)(\?.*)?$',
    re.IGNORECASE
)


def is_image_url(text: str) -> bool:
    """Check if a string looks like an image URL."""
    return bool(IMAGE_URL_PATTERN.match(text.strip()))


@mcp.tool()
async def get_food_nutrition(query: str, quantity: float = 100.0) -> dict[str, Any]:
    """
    Get detailed nutrition information for a food item.

    Supports food names, UPC/barcode codes (8-14 digits), and image URLs.
    When a UPC code is detected, it automatically searches by barcode.
    When an image URL is detected, it automatically analyzes the image.

    Args:
        query: Food name, UPC/barcode code, or image URL
        quantity: Amount in grams (default: 100g, only used for food names/UPC)

    Returns:
        Detailed nutrition information including calories, macros, vitamins, and minerals

    Examples:
        - get_food_nutrition(query="banana", quantity=100)
        - get_food_nutrition(query="737628064502")  # UPC code
        - get_food_nutrition(query="https://example.com/food.jpg")
    """
    mcp_logger.info(f"Tool called: get_food_nutrition(query='{query}', quantity={quantity})")

    try:
        # Auto-detect image URLs and redirect to image analysis
        if is_image_url(query):
            mcp_logger.info(f"Detected image URL, redirecting to analyze_food_image")
            return await analyze_food_image(query)

        # Search for the food (handles both names and UPC codes)
        food_result = await service_search_food(query)

        if not food_result:
            mcp_logger.warning(f"Food not found: {query}")
            return {
                "error": "Food not found",
                "query": query,
                "message": "No matching food found in the database. Try a different search term."
            }

        food_id = food_result["foodId"]
        mcp_logger.info(f"Found food: {food_result['label']} (ID: {food_id})")

        # Get detailed nutrition information
        nutrition = await service_get_nutrition(food_id, quantity)

        # Add the original food info to the response
        nutrition["food_info"] = {
            "label": food_result["label"],
            "category": food_result["category"],
            "image": food_result["image"]
        }

        mcp_logger.info(f"Successfully retrieved nutrition for {food_result['label']}")
        return nutrition

    except ValueError as e:
        error_msg = str(e)
        mcp_logger.error(f"Configuration error: {error_msg}")
        return {
            "error": "Configuration error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        mcp_logger.error(f"Error getting nutrition: {error_msg}")
        return {
            "error": "Failed to retrieve nutrition information",
            "message": error_msg,
            "query": query
        }


@mcp.tool()
async def search_food(query: str, limit: int = 5) -> dict[str, Any]:
    """
    Search for foods in the Edamam database.

    Returns a list of matching foods with basic nutrition information.
    Automatically detects and handles UPC/barcode codes (8-14 digits).

    Args:
        query: Food name or UPC/barcode code to search for
        limit: Maximum number of results to return (default: 5, currently returns 1)

    Returns:
        List of matching foods with foodId, name, category, basic nutrients, and image

    Examples:
        - search_food(query="apple")
        - search_food(query="737628064502")  # UPC code
    """
    mcp_logger.info(f"Tool called: search_food(query='{query}', limit={limit})")

    try:
        # Search for the food (handles both names and UPC codes)
        result = await service_search_food(query)

        if not result:
            mcp_logger.warning(f"No results found for: {query}")
            return {
                "query": query,
                "results": [],
                "message": "No matching foods found"
            }

        mcp_logger.info(f"Found food: {result['label']}")

        # Return as a list for consistency
        return {
            "query": query,
            "results": [result],
            "count": 1
        }

    except ValueError as e:
        error_msg = str(e)
        mcp_logger.error(f"Configuration error: {error_msg}")
        return {
            "error": "Configuration error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        mcp_logger.error(f"Error searching food: {error_msg}")
        return {
            "error": "Search failed",
            "message": error_msg,
            "query": query
        }


@mcp.tool()
async def analyze_food_image(image_url: str) -> dict[str, Any]:
    """
    Analyze a food image and extract nutrition information.

    Uses Edamam's beta image analysis feature to detect ingredients
    and calculate nutrition from a food photo.

    Args:
        image_url: URL of the food image to analyze (must be a valid HTTP/HTTPS URL)

    Returns:
        Analysis results including detected ingredients, nutrition info, and recipe metadata

    Examples:
        - analyze_food_image(image_url="https://example.com/salad.jpg")
    """
    mcp_logger.info(f"Tool called: analyze_food_image(image_url='{image_url[:100]}...')")

    try:
        # Validate URL format
        if not image_url.startswith(('http://', 'https://')):
            error_msg = "Image URL must start with http:// or https://"
            mcp_logger.error(f"Invalid URL format: {image_url}")
            return {
                "error": "Invalid URL",
                "message": error_msg,
                "url": image_url
            }

        # Analyze the image
        result = await get_nutrition_from_image(image_url)

        mcp_logger.info(f"Successfully analyzed image, found {len(result.get('ingredients', []))} ingredients")
        return result

    except ValueError as e:
        error_msg = str(e)
        mcp_logger.error(f"Configuration error: {error_msg}")
        return {
            "error": "Configuration error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        mcp_logger.error(f"Error analyzing image: {error_msg}")
        return {
            "error": "Image analysis failed",
            "message": error_msg,
            "url": image_url
        }


if __name__ == "__main__":
    # Run with streamable HTTP transport for web-based hosting
    mcp.run(transport="streamable-http", path="/mcp/food-database/v1")
