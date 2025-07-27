# Horoscope News App

This is a simple horoscope news agent that uses the Horoscope API to get daily horoscopes for different zodiac signs.

This was inspired by [Embabel's sample code](https://github.com/embabel/embabel-agent-examples/blob/main/examples-kotlin/src/main/kotlin/com/embabel/example/horoscope/StarNewsFinder.kt). It turns out that [Simon Willison and Tom Coates did this 20 years ago](https://simonwillison.net/2025/Jul/13/django-birthday/#django-birthday22.jpg) while at Yahoo! I used Simon's explanation for some inspiration as well.

## Installation

This app uses `uv` to manage dependencies. To install, run:

```bash
uv sync
```

## Usage

Command Line:
```bash
uv run horoscope.py
```

Web app:
```
uv run uvicorn main:app --reload
```

## Dependencies
 
Horoscope API: https://horoscope-app-api.vercel.app/ h/t [Ashutosh Krishna](https://ashutoshkrris.in/)

Some possibilities for News APIs:

- newsapi.org
- newsdata.io
- https://github.com/unclecode/crawl4ai

## TODOs

1. Add caching for the news, we don't need to load every time
2. Add caching for horoscopes, they update only once a day
3. Cache results for overall requests (Name + Zodiac) to avoid hitting LLM.
4. Make code switchable to different LLMs besides OpenAI