"""
Integration tests for the MCP server.

Tests complete workflows and server functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.mcp_server import (
    get_food_nutrition,
    search_food,
    analyze_food_image
)


@pytest.mark.asyncio
class TestFullWorkflows:
    """Test complete user workflows."""

    async def test_search_then_nutrition_workflow(self):
        """Test typical workflow: search for food, then get detailed nutrition."""
        # Mock the service layer
        mock_food = {
            "foodId": "food_banana123",
            "label": "Banana, raw",
            "category": "Generic foods",
            "nutrients": {
                "ENERC_KCAL": 89,
                "PROCNT": 1.1,
                "FAT": 0.3,
                "CHOCDF": 22.8
            },
            "image": "https://example.com/banana.jpg"
        }

        mock_nutrition = {
            "uri": "test_uri",
            "calories": 89,
            "totalWeight": 100.0,
            "totalNutrients": {
                "ENERC_KCAL": {"label": "Energy", "quantity": 89, "unit": "kcal"},
                "FAT": {"label": "Fat", "quantity": 0.3, "unit": "g"},
                "PROCNT": {"label": "Protein", "quantity": 1.1, "unit": "g"},
                "CHOCDF": {"label": "Carbs", "quantity": 22.8, "unit": "g"}
            }
        }

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            # Step 1: Search for the food
            search_result = await search_food("banana")

            assert search_result["count"] == 1
            assert len(search_result["results"]) == 1
            food = search_result["results"][0]
            assert food["label"] == "Banana, raw"
            assert food["foodId"] == "food_banana123"

            # Step 2: Get detailed nutrition using the foodId
            # (In the tool, we search again, so mock it for the nutrition call too)
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)):
                nutrition_result = await get_food_nutrition("banana", 100.0)

                assert "food_info" in nutrition_result
                assert nutrition_result["food_info"]["label"] == "Banana, raw"
                assert nutrition_result["calories"] == 89
                assert "totalNutrients" in nutrition_result
                assert "ENERC_KCAL" in nutrition_result["totalNutrients"]

    async def test_upc_workflow(self):
        """Test UPC barcode lookup workflow."""
        mock_upc_food = {
            "foodId": "food_upc_test",
            "label": "Organic Banana - Chiquita",
            "category": "Packaged foods",
            "nutrients": {
                "ENERC_KCAL": 105,
                "PROCNT": 1.3,
                "FAT": 0.4
            },
            "image": "https://example.com/chiquita.jpg"
        }

        mock_nutrition = {
            "calories": 105,
            "totalWeight": 100.0,
            "totalNutrients": {
                "ENERC_KCAL": {"label": "Energy", "quantity": 105, "unit": "kcal"}
            }
        }

        # Test with a 12-digit UPC
        upc_code = "737628064502"

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_upc_food)):
            # Search by UPC
            search_result = await search_food(upc_code)

            assert search_result["count"] == 1
            assert search_result["results"][0]["label"] == "Organic Banana - Chiquita"

            # Get nutrition by UPC
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)):
                nutrition_result = await get_food_nutrition(upc_code, 100.0)

                assert nutrition_result["calories"] == 105
                assert "food_info" in nutrition_result

    async def test_image_analysis_workflow(self):
        """Test image analysis workflow."""
        mock_analysis = {
            "ingredients": [
                {
                    "text": "1 banana",
                    "parsed": [
                        {
                            "quantity": 1,
                            "measure": "whole",
                            "food": "banana",
                            "foodId": "food_banana",
                            "weight": 118.0,
                            "nutrients": {
                                "ENERC_KCAL": 105,
                                "PROCNT": 1.3,
                                "FAT": 0.4,
                                "CHOCDF": 27.0
                            }
                        }
                    ]
                },
                {
                    "text": "1 apple",
                    "parsed": [
                        {
                            "quantity": 1,
                            "measure": "whole",
                            "food": "apple",
                            "foodId": "food_apple",
                            "weight": 182.0,
                            "nutrients": {
                                "ENERC_KCAL": 95,
                                "PROCNT": 0.5,
                                "FAT": 0.3,
                                "CHOCDF": 25.0
                            }
                        }
                    ]
                }
            ],
            "totalNutrients": {
                "ENERC_KCAL": {"label": "Energy", "quantity": 200, "unit": "kcal"},
                "FAT": {"label": "Fat", "quantity": 0.7, "unit": "g"},
                "PROCNT": {"label": "Protein", "quantity": 1.8, "unit": "g"},
                "CHOCDF": {"label": "Carbs", "quantity": 52.0, "unit": "g"}
            },
            "totalWeight": 300.0,
            "calories": 200
        }

        image_url = "https://example.com/fruit-bowl.jpg"

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            # Direct image analysis
            result = await analyze_food_image(image_url)

            assert "ingredients" in result
            assert len(result["ingredients"]) == 2
            assert result["calories"] == 200
            assert result["totalWeight"] == 300.0

            # Test auto-detection in get_food_nutrition
            result2 = await get_food_nutrition(image_url)

            assert result2 == result  # Should be identical

    async def test_error_handling_workflow(self):
        """Test error handling across workflows."""
        # Test 1: Food not found
        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=None)):
            search_result = await search_food("nonexistentfood12345")
            assert search_result["results"] == []
            assert "message" in search_result

            nutrition_result = await get_food_nutrition("nonexistentfood12345")
            assert "error" in nutrition_result
            assert nutrition_result["error"] == "Food not found"

        # Test 2: Invalid image URL
        invalid_result = await analyze_food_image("not-a-url")
        assert "error" in invalid_result
        assert invalid_result["error"] == "Invalid URL"

        # Test 3: Service error handling
        with patch('src.mcp_server.service_search_food', new=AsyncMock(side_effect=Exception("API timeout"))):
            error_result = await search_food("banana")
            assert "error" in error_result
            assert "API timeout" in error_result["message"]


@pytest.mark.asyncio
class TestImageURLDetection:
    """Test automatic image URL detection in get_food_nutrition."""

    async def test_jpg_url_detection(self):
        """Test .jpg URL is auto-detected and redirected."""
        mock_analysis = {"ingredients": [], "calories": 0}

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await get_food_nutrition("https://example.com/food.jpg")
            assert "ingredients" in result

    async def test_jpeg_url_detection(self):
        """Test .jpeg URL is auto-detected."""
        mock_analysis = {"ingredients": [], "calories": 0}

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await get_food_nutrition("https://example.com/food.jpeg")
            assert "ingredients" in result

    async def test_png_url_detection(self):
        """Test .png URL is auto-detected."""
        mock_analysis = {"ingredients": [], "calories": 0}

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await get_food_nutrition("https://example.com/food.png")
            assert "ingredients" in result

    async def test_url_with_query_params(self):
        """Test image URL with query parameters."""
        mock_analysis = {"ingredients": [], "calories": 0}

        with patch('src.mcp_server.get_nutrition_from_image', new=AsyncMock(return_value=mock_analysis)):
            result = await get_food_nutrition("https://example.com/food.jpg?size=large&v=2")
            assert "ingredients" in result

    async def test_non_image_url_not_detected(self):
        """Test that non-image URLs are not auto-detected."""
        mock_food = {
            "foodId": "food_test",
            "label": "Test Food",
            "category": "Generic foods",
            "nutrients": {},
            "image": None
        }
        mock_nutrition = {"calories": 100, "totalWeight": 100.0, "totalNutrients": {}}

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)):
                # This should NOT trigger image analysis
                result = await get_food_nutrition("https://example.com/page.html")

                # Should have gone through normal nutrition path
                assert "food_info" in result
                assert result["food_info"]["label"] == "Test Food"


@pytest.mark.asyncio
class TestQuantityHandling:
    """Test quantity parameter handling across tools."""

    async def test_default_quantity_100g(self):
        """Test that default quantity is 100g."""
        mock_food = {
            "foodId": "food_test",
            "label": "Test Food",
            "category": "Generic foods",
            "nutrients": {},
            "image": None
        }
        mock_nutrition = {"calories": 100, "totalWeight": 100.0, "totalNutrients": {}}

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)) as mock_get:
                await get_food_nutrition("test food")

                # Verify default 100.0 was used
                mock_get.assert_called_once_with("food_test", 100.0)

    async def test_custom_quantity(self):
        """Test custom quantity is passed correctly."""
        mock_food = {
            "foodId": "food_test",
            "label": "Test Food",
            "category": "Generic foods",
            "nutrients": {},
            "image": None
        }
        mock_nutrition = {"calories": 250, "totalWeight": 250.0, "totalNutrients": {}}

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)) as mock_get:
                await get_food_nutrition("test food", 250.0)

                # Verify 250.0 was used
                mock_get.assert_called_once_with("food_test", 250.0)

    async def test_fractional_quantity(self):
        """Test fractional quantities work."""
        mock_food = {
            "foodId": "food_test",
            "label": "Test Food",
            "category": "Generic foods",
            "nutrients": {},
            "image": None
        }
        mock_nutrition = {"calories": 44.5, "totalWeight": 50.0, "totalNutrients": {}}

        with patch('src.mcp_server.service_search_food', new=AsyncMock(return_value=mock_food)):
            with patch('src.mcp_server.service_get_nutrition', new=AsyncMock(return_value=mock_nutrition)) as mock_get:
                await get_food_nutrition("test food", 50.5)

                # Verify 50.5 was used
                mock_get.assert_called_once_with("food_test", 50.5)
