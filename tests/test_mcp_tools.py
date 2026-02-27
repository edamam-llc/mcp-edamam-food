"""
Unit tests for MCP tools in mcp_server.py

Tests each tool function with mocked service layer.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.mcp_server import (
    get_food_nutrition,
    search_food,
    analyze_food_image,
    is_image_url
)


class TestIsImageURL:
    """Test image URL detection."""

    def test_valid_image_urls(self):
        """Test various valid image URL formats."""
        assert is_image_url("https://example.com/image.jpg") is True
        assert is_image_url("http://example.com/image.jpeg") is True
        assert is_image_url("https://example.com/image.png") is True
        assert is_image_url("https://example.com/image.gif") is True
        assert is_image_url("https://example.com/image.webp") is True
        assert is_image_url("https://example.com/image.bmp") is True

    def test_image_urls_with_query_params(self):
        """Test image URLs with query parameters."""
        assert is_image_url("https://example.com/image.jpg?size=large") is True
        assert is_image_url("https://example.com/image.png?v=1&token=abc") is True

    def test_invalid_image_urls(self):
        """Test non-image URLs."""
        assert is_image_url("https://example.com/page.html") is False
        assert is_image_url("https://example.com/document.pdf") is False
        assert is_image_url("banana") is False
        assert is_image_url("12345678") is False
        assert is_image_url("") is False

    def test_case_insensitive(self):
        """Test that extension matching is case-insensitive."""
        assert is_image_url("https://example.com/image.JPG") is True
        assert is_image_url("https://example.com/image.PNG") is True


@pytest.mark.asyncio
class TestGetFoodNutrition:
    """Test get_food_nutrition tool."""

    async def test_get_nutrition_by_name_success(self):
        """Test getting nutrition by food name."""
        mock_food = {
            "foodId": "food_test123",
            "label": "Banana",
            "category": "Generic foods",
            "nutrients": {"ENERC_KCAL": 89},
            "image": "https://example.com/banana.jpg"
        }
        mock_nutrition = {
            "calories": 89,
            "totalWeight": 100.0,
            "totalNutrients": {"ENERC_KCAL": {"quantity": 89}}
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)):
                result = await get_food_nutrition("banana", 100.0)

                assert "food_info" in result
                assert result["food_info"]["label"] == "Banana"
                assert result["calories"] == 89
                assert result["totalWeight"] == 100.0

    async def test_get_nutrition_by_upc(self):
        """Test getting nutrition by UPC code."""
        mock_food = {
            "foodId": "food_upc123",
            "label": "Product Name",
            "category": "Packaged foods",
            "nutrients": {"ENERC_KCAL": 100},
            "image": "https://example.com/product.jpg"
        }
        mock_nutrition = {
            "calories": 100,
            "totalWeight": 100.0,
            "totalNutrients": {}
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)):
                result = await get_food_nutrition("737628064502", 100.0)

                assert "food_info" in result
                assert result["food_info"]["label"] == "Product Name"

    async def test_get_nutrition_with_image_url_redirect(self):
        """Test that image URLs are redirected to analyze_food_image."""
        mock_analysis = {
            "ingredients": [{"text": "1 banana"}],
            "calories": 105
        }

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await get_food_nutrition("https://example.com/food.jpg")

            assert "ingredients" in result
            assert result["calories"] == 105

    async def test_get_nutrition_food_not_found(self):
        """Test handling when food is not found."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=None)):
            result = await get_food_nutrition("nonexistentfood123456")

            assert "error" in result
            assert result["error"] == "Food not found"
            assert result["query"] == "nonexistentfood123456"

    async def test_get_nutrition_configuration_error(self):
        """Test handling of configuration errors."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(side_effect=ValueError("API key missing"))):
            result = await get_food_nutrition("banana")

            assert "error" in result
            assert result["error"] == "Configuration error"
            assert "API key missing" in result["message"]

    async def test_get_nutrition_generic_error(self):
        """Test handling of generic errors."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(side_effect=Exception("Network error"))):
            result = await get_food_nutrition("banana")

            assert "error" in result
            assert result["error"] == "Failed to retrieve nutrition information"
            assert "Network error" in result["message"]

    async def test_get_nutrition_custom_quantity(self):
        """Test getting nutrition with custom quantity."""
        mock_food = {
            "foodId": "food_test123",
            "label": "Chicken Breast",
            "category": "Generic foods",
            "nutrients": {},
            "image": None
        }
        mock_nutrition = {
            "calories": 330,
            "totalWeight": 200.0,
            "totalNutrients": {}
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)) as mock_get:
                result = await get_food_nutrition("chicken breast", 200.0)

                # Verify service_get_nutrition was called with correct quantity
                mock_get.assert_called_once_with("food_test123", 200.0)
                assert result["totalWeight"] == 200.0


@pytest.mark.asyncio
class TestSearchFood:
    """Test search_food tool."""

    async def test_search_food_success(self):
        """Test successful food search."""
        mock_food = {
            "foodId": "food_test123",
            "label": "Apple",
            "category": "Generic foods",
            "nutrients": {"ENERC_KCAL": 52},
            "image": "https://example.com/apple.jpg"
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            result = await search_food("apple")

            assert result["query"] == "apple"
            assert result["count"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["label"] == "Apple"

    async def test_search_food_by_upc(self):
        """Test searching by UPC code."""
        mock_food = {
            "foodId": "food_upc123",
            "label": "Product Name",
            "category": "Packaged foods",
            "nutrients": {},
            "image": None
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            result = await search_food("737628064502")

            assert result["count"] == 1
            assert result["results"][0]["label"] == "Product Name"

    async def test_search_food_no_results(self):
        """Test search with no results."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=None)):
            result = await search_food("nonexistentfood123456")

            assert result["query"] == "nonexistentfood123456"
            assert result["results"] == []
            assert "message" in result

    async def test_search_food_configuration_error(self):
        """Test handling of configuration errors."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(side_effect=ValueError("API key missing"))):
            result = await search_food("banana")

            assert "error" in result
            assert result["error"] == "Configuration error"

    async def test_search_food_generic_error(self):
        """Test handling of generic errors."""
        with patch('src.mcp_server.service_search_food', new=AsyncMock(side_effect=Exception("Network error"))):
            result = await search_food("banana")

            assert "error" in result
            assert result["error"] == "Search failed"


@pytest.mark.asyncio
class TestAnalyzeFoodImage:
    """Test analyze_food_image tool."""

    async def test_analyze_image_success(self):
        """Test successful image analysis."""
        mock_analysis = {
            "ingredients": [
                {
                    "text": "1 banana",
                    "parsed": [{"food": "banana", "quantity": 1}]
                }
            ],
            "totalNutrients": {"ENERC_KCAL": {"quantity": 105}},
            "calories": 105
        }

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await analyze_food_image("https://example.com/food.jpg")

            assert "ingredients" in result
            assert result["calories"] == 105
            assert len(result["ingredients"]) == 1

    async def test_analyze_image_invalid_url_format(self):
        """Test analysis with invalid URL format."""
        result = await analyze_food_image("not-a-valid-url")

        assert "error" in result
        assert result["error"] == "Invalid URL"
        assert "must start with http" in result["message"]

    async def test_analyze_image_http_url(self):
        """Test that HTTP URLs are accepted."""
        mock_analysis = {"ingredients": [], "calories": 0}

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await analyze_food_image("http://example.com/food.jpg")

            assert "error" not in result

    async def test_analyze_image_configuration_error(self):
        """Test handling of configuration errors."""
        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(side_effect=ValueError("API key missing"))):
            result = await analyze_food_image("https://example.com/food.jpg")

            assert "error" in result
            assert result["error"] == "Configuration error"

    async def test_analyze_image_generic_error(self):
        """Test handling of generic errors."""
        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(side_effect=Exception("Network error"))):
            result = await analyze_food_image("https://example.com/food.jpg")

            assert "error" in result
            assert result["error"] == "Image analysis failed"
