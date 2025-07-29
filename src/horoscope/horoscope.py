import os
from dataclasses import dataclass
from datetime import date
from pydantic_ai import Agent, RunContext, NativeOutput
from pydantic import BaseModel
from textwrap import dedent
from types import NoneType
from typing import List, Optional
from pydantic_ai import Agent
from dotenv import load_dotenv

import aiohttp

import logfire
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool, DuckDuckGoResult

load_dotenv()  # Load .env variables
NEWSAPI_KEY = os.getenv("NEWSAPI_ORG_KEY")
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))

# TODO: move config elsewhere
# 'if-token-present' means nothing will be sent if logfire isn't configured
logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


class Inputs(BaseModel):
    name: str  # Optional[str]
    star_sign: str
    # date: Optional[date]

    def __str__(self):
        return f"Create a personalized newspaper for {self.name}, whose Zodiac sign is {self.star_sign}."


class HoroscopeData(BaseModel):
    date: str
    horoscope_data: str


class Horoscope(BaseModel):
    data: HoroscopeData
    status: int
    success: bool


class NewspaperArticle(BaseModel):
    title: str
    summary: str
    url: str
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    source: Optional[str] = None


class PersonalizedNewspaper(BaseModel):
    header: str
    horoscope: str
    articles: List[NewspaperArticle]


from pydantic_ai import Agent
from textwrap import dedent
import click


horoscope_agent = Agent(
    "openai:gpt-4o",
    deps_type=Inputs,
    output_type=Horoscope,
    system_prompt=(
        "Use the `todays_horoscope` function to get today's horoscope for the given star sign."
    ),
)

star_news_agent = Agent(
    model="openai:gpt-4o",
    instructions=dedent(
        """
        Your job is to take a star sign and return a personalized "newspaper" for the day.

        - Use the `todays_horoscope` tool to get the horoscope for the given sign.
        - Use the `get_news` tool to gather general or entertainment-related news.
        - Reframe each news item subtly through the lens of the classic characteristics user's zodiac sign or their daily horoscope.
        - Use an engaging and personal tone, as if writing to the individual.
        - The final result should include:
            • A brief personalized header
            • Today's horoscope
            • A short curated list of 3–5 reframed headlines with summaries.
        - If you can't get enough news, return None.
        """
    ),
    output_type=Optional[PersonalizedNewspaper],
    deps_type=Inputs,
)


@star_news_agent.tool
async def todays_horoscope(ctx: RunContext[Horoscope], sign: str) -> str:
    """get the horoscope for the given star sign"""
    base_url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": "TODAY"}
    async with aiohttp.ClientSession() as session:
        logfire.info(f"Fetching horoscope for {sign} with params: {params}")
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                return data.get("data", {}).get(
                    "horoscope_data", "No horoscope available."
                )
            else:
                return "Failed to retrieve horoscope."


@star_news_agent.tool
async def get_news(
    ctx: RunContext[Horoscope], category: str = "general", limit: int = 25
) -> List[dict]:
    """Returns a list of news articles, each with 'title' and 'summary' keys."""
    endpoint = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        category: "entertainment",
        "apiKey": NEWSAPI_KEY,
        "pageSize": limit,
    }
    async with aiohttp.ClientSession() as session:
        logfire.info(f"Fetching news with params: {params}")
        async with session.get(endpoint, params=params) as response:
            if response.status == 200:
                data = await response.json()
                articles = data.get("articles", [])

                return [
                    {
                        "title": article.get("title", ""),
                        "summary": article.get("description", ""),
                        "url": article.get("url", ""),
                        "image_url": article.get("urlToImage", ""),
                        "published_at": article.get("publishedAt", ""),
                        "source": article.get("source", {}).get("name", ""),
                    }
                    for article in articles
                ]
            else:
                logfire.error(f"Failed to fetch news: {params} {response.status}")
                return []  # Return an empty list if the request fails


# Example usage
# horoscope_result = horoscope_agent.run_sync("What is the horoscope for Cancer today?")
# print(horoscope_result.output.data.horoscope_data)
# TODO: rearchitect along these lines https://ai.pydantic.dev/examples/weather-agent/#example-code
# logfire.instrument_httpx(client, capture_all=True)
@click.command()
@click.option(
    "--star-sign", required=True, help="Your star sign (e.g. Cancer, Leo, etc.)"
)
@click.option("--name", required=True, help="Your name")
def main(star_sign, name):
    inputs = Inputs(star_sign=star_sign, name=name)
    result = star_news_agent.run_sync(str(inputs), deps=inputs)
    if result.output is not None:
        print(result.output)
    else:
        print("Failed to create personalized newspaper.")
        if hasattr(result, "model_errors"):
            for error in result.model_errors:
                print(f"- {error}")

if __name__ == "__main__":
    main()
