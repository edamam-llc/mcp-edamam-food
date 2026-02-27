# tests/conftest.py
import os
import pytest
from unittest.mock import AsyncMock

# Set test environment variables
os.environ["EDAMAM_APP_ID"] = "test_app_id"
os.environ["EDAMAM_APP_KEY"] = "test_app_key"


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response object."""
    def _make_response(status_code=200, json_data=None, text=""):
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data or {}
        mock_resp.text = text
        mock_resp.raise_for_status = MagicMock()
        return mock_resp
    return _make_response


@pytest.fixture
def sample_food_search_response():
    """Sample successful food search response from Edamam."""
    return {
        "text": "banana",
        "parsed": [
            {
                "food": {
                    "foodId": "food_test123",
                    "label": "Banana",
                    "category": "Generic foods",
                    "nutrients": {
                        "ENERC_KCAL": 89,
                        "PROCNT": 1.1,
                        "FAT": 0.3,
                        "CHOCDF": 22.8
                    },
                    "image": "https://example.com/banana.jpg"
                }
            }
        ],
        "hints": []
    }


@pytest.fixture
def sample_food_nutrition_response():
    """Sample successful nutrition response from Edamam."""
    return {
        "uri": "test_uri",
        "calories": 89,
        "totalWeight": 100.0,
        "dietLabels": [],
        "healthLabels": [],
        "cautions": [],
        "totalNutrients": {
            "ENERC_KCAL": {"label": "Energy", "quantity": 89, "unit": "kcal"},
            "FAT": {"label": "Fat", "quantity": 0.3, "unit": "g"},
            "PROCNT": {"label": "Protein", "quantity": 1.1, "unit": "g"},
            "CHOCDF": {"label": "Carbs", "quantity": 22.8, "unit": "g"}
        },
        "totalDaily": {},
        "ingredients": [
            {
                "parsed": [
                    {
                        "quantity": 100,
                        "measure": "gram",
                        "food": "Banana",
                        "foodId": "food_test123",
                        "weight": 100.0,
                        "nutrients": {}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_image_analysis_response():
    """Sample successful image analysis response from Edamam."""
    return {
        "ingredients": [
            {
                "text": "1 banana",
                "parsed": [
                    {
                        "quantity": 1,
                        "measure": "whole",
                        "food": "banana",
                        "foodId": "food_test123",
                        "weight": 118.0,
                        "nutrients": {
                            "ENERC_KCAL": 105,
                            "PROCNT": 1.3,
                            "FAT": 0.4,
                            "CHOCDF": 27.0
                        }
                    }
                ]
            }
        ],
        "totalNutrients": {
            "ENERC_KCAL": {"label": "Energy", "quantity": 105, "unit": "kcal"}
        },
        "totalWeight": 118.0,
        "calories": 105
    }
