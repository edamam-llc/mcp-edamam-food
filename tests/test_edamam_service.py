"""
Unit tests for edamam_service.py

Tests all service functions with mocked httpx calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.edamam_service import (
    is_upc,
    search_food,
    get_food_nutrition,
    get_nutrition_from_image
)


class TestIsUPC:
    """Test UPC detection logic."""

    def test_valid_upc_8_digits(self):
        """Test 8-digit UPC code."""
        assert is_upc("12345678") is True

    def test_valid_upc_12_digits(self):
        """Test 12-digit UPC code."""
        assert is_upc("123456789012") is True

    def test_valid_upc_14_digits(self):
        """Test 14-digit UPC code."""
        assert is_upc("12345678901234") is True

    def test_invalid_upc_too_short(self):
        """Test code that's too short."""
        assert is_upc("1234567") is False

    def test_invalid_upc_too_long(self):
        """Test code that's too long."""
        assert is_upc("123456789012345") is False

    def test_invalid_upc_not_digits(self):
        """Test non-numeric string."""
        assert is_upc("banana") is False
        assert is_upc("12345ABC") is False

    def test_empty_string(self):
        """Test empty string."""
        assert is_upc("") is False


@pytest.mark.asyncio
class TestSearchFood:
    """Test search_food function."""

    async def test_search_food_by_name_success(self, mock_httpx_response, sample_food_search_response):
        """Test successful food search by name."""
        mock_resp = mock_httpx_response(200, sample_food_search_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

            result = await search_food("banana")

            assert result is not None
            assert result["foodId"] == "food_test123"
            assert result["label"] == "Banana"
            assert result["category"] == "Generic foods"
            assert "nutrients" in result
            assert result["image"] == "https://example.com/banana.jpg"

    async def test_search_food_by_upc_success(self, mock_httpx_response):
        """Test successful food search by UPC code."""
        upc_response = {
            "hints": [
                {
                    "food": {
                        "foodId": "food_upc123",
                        "label": "Product Name",
                        "category": "Packaged foods",
                        "nutrients": {"ENERC_KCAL": 100},
                        "image": "https://example.com/product.jpg"
                    }
                }
            ]
        }
        mock_resp = mock_httpx_response(200, upc_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

            result = await search_food("737628064502")

            assert result is not None
            assert result["foodId"] == "food_upc123"
            assert result["label"] == "Product Name"

    async def test_search_food_no_results(self, mock_httpx_response):
        """Test search with no results."""
        empty_response = {"parsed": [], "hints": []}
        mock_resp = mock_httpx_response(200, empty_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

            result = await search_food("nonexistentfood123456")

            assert result is None

    async def test_search_food_missing_credentials(self, monkeypatch):
        """Test search without API credentials."""
        monkeypatch.delenv("EDAMAM_APP_ID", raising=False)
        monkeypatch.delenv("EDAMAM_APP_KEY", raising=False)

        with pytest.raises(ValueError, match="EDAMAM_APP_ID or EDAMAM_APP_KEY not set"):
            await search_food("banana")

    async def test_search_food_api_error(self, mock_httpx_response):
        """Test search with API error."""
        mock_resp = mock_httpx_response(404, {}, "Not found")
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_resp
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

            with pytest.raises(httpx.HTTPStatusError):
                await search_food("banana")

    async def test_search_food_timeout(self):
        """Test search with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            with pytest.raises(httpx.TimeoutException):
                await search_food("banana")


@pytest.mark.asyncio
class TestGetFoodNutrition:
    """Test get_food_nutrition function."""

    async def test_get_nutrition_success(self, mock_httpx_response, sample_food_nutrition_response):
        """Test successful nutrition retrieval."""
        mock_resp = mock_httpx_response(200, sample_food_nutrition_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            result = await get_food_nutrition("food_test123", 100.0)

            assert result is not None
            assert "totalNutrients" in result
            assert result["calories"] == 89
            assert result["totalWeight"] == 100.0

    async def test_get_nutrition_custom_quantity(self, mock_httpx_response, sample_food_nutrition_response):
        """Test nutrition with custom quantity."""
        # Adjust response for 200g
        custom_response = sample_food_nutrition_response.copy()
        custom_response["calories"] = 178
        custom_response["totalWeight"] = 200.0

        mock_resp = mock_httpx_response(200, custom_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            result = await get_food_nutrition("food_test123", 200.0)

            assert result["totalWeight"] == 200.0

    async def test_get_nutrition_missing_credentials(self, monkeypatch):
        """Test nutrition without API credentials."""
        monkeypatch.delenv("EDAMAM_APP_ID", raising=False)
        monkeypatch.delenv("EDAMAM_APP_KEY", raising=False)

        with pytest.raises(ValueError, match="EDAMAM_APP_ID or EDAMAM_APP_KEY not set"):
            await get_food_nutrition("food_test123", 100.0)

    async def test_get_nutrition_api_error(self, mock_httpx_response):
        """Test nutrition with API error."""
        mock_resp = mock_httpx_response(500, {}, "Internal server error")
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_resp
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            with pytest.raises(httpx.HTTPStatusError):
                await get_food_nutrition("food_test123", 100.0)


@pytest.mark.asyncio
class TestGetNutritionFromImage:
    """Test get_nutrition_from_image function."""

    async def test_analyze_image_success(self, mock_httpx_response, sample_image_analysis_response):
        """Test successful image analysis."""
        mock_resp = mock_httpx_response(200, sample_image_analysis_response)

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            result = await get_nutrition_from_image("https://example.com/food.jpg")

            assert result is not None
            assert "ingredients" in result
            assert "totalNutrients" in result
            assert result["calories"] == 105
            assert len(result["ingredients"]) == 1

    async def test_analyze_image_missing_credentials(self, monkeypatch):
        """Test image analysis without API credentials."""
        monkeypatch.delenv("EDAMAM_APP_ID", raising=False)
        monkeypatch.delenv("EDAMAM_APP_KEY", raising=False)

        with pytest.raises(ValueError, match="EDAMAM_APP_ID or EDAMAM_APP_KEY not set"):
            await get_nutrition_from_image("https://example.com/food.jpg")

    async def test_analyze_image_api_error(self, mock_httpx_response):
        """Test image analysis with API error."""
        mock_resp = mock_httpx_response(400, {}, "Bad request")
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=mock_resp
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

            with pytest.raises(httpx.HTTPStatusError):
                await get_nutrition_from_image("https://example.com/food.jpg")

    async def test_analyze_image_timeout(self):
        """Test image analysis with timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            with pytest.raises(httpx.TimeoutException):
                await get_nutrition_from_image("https://example.com/food.jpg")
