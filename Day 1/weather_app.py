from pydantic_ai import Agent
import requests
import asyncio
import logfire
import logging
from dotenv import load_dotenv
load_dotenv()

weather_agent = Agent(
    'groq:llama-3.1-8b-instant',
    system_prompt="You are weather agent who gives information about weather to the user. Use `get_weather_info` for weather related queries."
)

def get_geocoding(location):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&appid={'f210cbe2c2548d22f0d26c1630f5439b'}"
    response = requests.get(geo_url).json()
    if response:
        lat, lon  = response[0]['lat'], response[0]['lon']
        return lat,lon
    else:
        return "Unexpected error occured while Geocoding."


@weather_agent.tool_plain
async def get_weather_info(location:str):
    try:
        lat, lon  = get_geocoding(location)
        wea_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={'f210cbe2c2548d22f0d26c1630f5439b'}"
        response = requests.get(wea_url).json()
        if response:
            return response
        else:
            return "Error : No data found!"
    except Exception as e:
        print('Error : Something went wrong!')

# Configure Logfire
logfire.configure(token='pylf_v1_us_syxXlcvNdMZBlt1rwpYp1Jj7MHdwQWkQm5hhK6KCBWFV',)
logfire.instrument_openai()
# messages and chathistory implemented 
async def main():
    message_hist = []
    while True:
        query = input('👦  ')
        if query == 'quit':
            break
        # implemented Streaming Structured Responses
        async with weather_agent.run_stream(query, message_history=message_hist) as result:
            async for message in result.stream_text():  
                print('🤖  ', message)
        message_hist=result.all_messages()
        print(f"Query: {query}")
        with logfire.span(f'Query : {query}'):
            logfire.info(f'Reponse : {message}')
        
asyncio.run(main())