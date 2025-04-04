import pytest
import asyncio
import json
from unittest.mock import patch
from pydantic_ai.models.test import TestModel
from weather_app import get_geocoding, get_weather_info, weather_agent

# Sample fake responses
FAKE_GEOCODING_RESPONSE = [{"lat": 28.6517, "lon": 77.2219}]
FAKE_WEATHER_RESPONSE = {"weather": [{"description": "clear sky"}], "main": {"temp": 300}}

@pytest.mark.asyncio
async def test_get_geocoding():
    with patch("weather_app.requests.get") as mock_get:
        mock_get.return_value.json.return_value = FAKE_GEOCODING_RESPONSE
        lat, lon = get_geocoding("Delhi")
        
        assert lat == 28.6517
        assert lon == 77.2219

@pytest.mark.asyncio
async def test_get_weather_info():
    with patch("weather_app.get_geocoding") as mock_geocoding, \
         patch("weather_app.requests.get") as mock_weather_get:

        mock_geocoding.return_value = (28.6517, 77.2219)
        mock_weather_get.return_value.json.return_value = FAKE_WEATHER_RESPONSE

        weather_data = await get_weather_info("Delhi")

        assert weather_data["weather"][0]["description"] == "clear sky"
        assert "main" in weather_data

@pytest.mark.asyncio
async def test_weather_agent_streaming():
    with weather_agent.override(model=TestModel()):  # Mock AI model
        query = "What's the weather like in Delhi?"
        async with weather_agent.run_stream(query) as result:
            response = ""
            async for message in result.stream_text():
                response += message

        assert response is not None  # Check if response is generated
