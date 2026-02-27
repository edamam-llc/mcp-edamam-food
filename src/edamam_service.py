"""
Edamam Food Database API Service.

This module provides async functions to interact with the Edamam Food Database API
for searching foods, getting nutrition information, and analyzing food images.
"""

import os
from typing import Optional, Dict, Any
import httpx
from src.logger import mcp_logger

# Edamam API endpoints
FOOD_SEARCH_URL = "https://api.edamam.com/api/food-database/v2/parser"
NUTRIENTS_URL = "https://api.edamam.com/api/food-database/v2/nutrients"
NUTRIENTS_FROM_IMAGE_URL = "https://api.edamam.com/api/food-database/v2/nutrients-from-image"


def is_upc(query: str) -> bool:
    """
    Detect valid UPC/EAN/PLU codes.

    Edamam rule: If UPC/EAN/PLU is provided, DO NOT send 'ingr' parameter.
    UPC codes are typically 8-14 digits.

    Args:
        query: The search query to check

    Returns:
        True if the query is a valid UPC code, False otherwise
    """
    return query.isdigit() and 8 <= len(query) <= 14


async def search_food(query: str, limit: int = 5) -> Optional[Dict[str, Any]]:
    """
    Search for food in the Edamam database.

    Automatically detects UPC/barcode codes and uses the appropriate API parameters.

    Args:
        query: Food name or UPC/barcode code to search for
        limit: Maximum number of results (not used in current implementation)

    Returns:
        Dictionary containing food information (foodId, label, category, nutrients, image)
        or None if no food found

    Raises:
        ValueError: If API credentials are not set
        httpx.HTTPError: If the API request fails
    """
    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")
    if not app_id or not app_key:
        raise ValueError("EDAMAM_APP_ID or EDAMAM_APP_KEY not set in environment")

    # UPC detection and proper Edamam routing
    if is_upc(query):
        params = {
            "upc": query,
            "app_id": app_id,
            "app_key": app_key,
        }
        mcp_logger.info(f"[MCP→Edamam] Search by UPC: {query}")
    else:
        params = {
            "ingr": query,
            "app_id": app_id,
            "app_key": app_key,
            "nutrition-type": "logging"
        }
        mcp_logger.info(f"[MCP→Edamam] Search food: '{query}'")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(FOOD_SEARCH_URL, params=params)
        mcp_logger.info(
            f"[Edamam→MCP] Status: {resp.status_code}, Response: {resp.text[:400]}"
        )

        resp.raise_for_status()
        data = resp.json()

        # Try to extract food from parsed or hints
        food = None
        if data.get("parsed"):
            food = data["parsed"][0]["food"]
        elif data.get("hints"):
            food = data["hints"][0]["food"]

        if not food:
            return None

        return {
            "foodId": food.get("foodId"),
            "label": food.get("label"),
            "category": food.get("category"),
            "nutrients": food.get("nutrients"),
            "image": food.get("image"),
        }


async def get_food_nutrition(food_id: str, quantity: float = 100.0) -> Dict[str, Any]:
    """
    Get detailed nutrition information for a specific food.

    Args:
        food_id: The Edamam foodId from a search result
        quantity: Amount in grams (default: 100g)

    Returns:
        Dictionary containing detailed nutrition information

    Raises:
        ValueError: If API credentials are not set
        httpx.HTTPError: If the API request fails
    """
    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")
    if not app_id or not app_key:
        raise ValueError("EDAMAM_APP_ID or EDAMAM_APP_KEY not set in environment")

    payload = {
        "ingredients": [
            {
                "quantity": quantity,
                "measureURI": "http://www.edamam.com/ontologies/edamam.owl#Measure_gram",
                "foodId": food_id,
            }
        ]
    }

    mcp_logger.info(f"[MCP→Edamam] Nutrients for foodId={food_id}, quantity={quantity}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{NUTRIENTS_URL}?app_id={app_id}&app_key={app_key}",
            json=payload,
        )
        mcp_logger.info(
            f"[Edamam→MCP] Status: {resp.status_code}, Response: {resp.text[:400]}"
        )

        resp.raise_for_status()
        return resp.json()


async def get_nutrition_from_image(image_url: str) -> Dict[str, Any]:
    """
    Analyze a food image and extract nutrition information.

    Uses Edamam's beta image analysis feature to detect ingredients
    and calculate nutrition from a food photo.

    Args:
        image_url: URL of the food image to analyze

    Returns:
        Dictionary containing detected ingredients and nutrition information

    Raises:
        ValueError: If API credentials are not set
        httpx.HTTPError: If the API request fails
    """
    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")
    if not app_id or not app_key:
        raise ValueError("EDAMAM_APP_ID or EDAMAM_APP_KEY not set in environment")

    payload = {"image_url": image_url}

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "beta": "true",
    }

    mcp_logger.info(f"[MCP→Edamam] Nutrients-from-image: {image_url[:100]}")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(NUTRIENTS_FROM_IMAGE_URL, params=params, json=payload)
        mcp_logger.info(
            f"[Edamam→MCP] Status: {resp.status_code}, Response: {resp.text[:400]}"
        )

        resp.raise_for_status()
        return resp.json()
