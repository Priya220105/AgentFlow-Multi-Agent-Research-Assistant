import os
import json
import google.generativeai as genai
from tavily import TavilyClient
from dotenv import load_dotenv


load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


SYSTEM_PROMPT = """
You are a Search Agent in a multi-agent research assistant.

You receive a research question and web search results.

Your task:
1. Select the most relevant information.
2. Extract factual findings.
3. Return structured JSON with sources.

Always return ONLY valid JSON in this format:

{
  "question": "user question",
  "findings": [
    {
      "fact": "a factual statement",
      "source_title": "website title",
      "source_url": "website URL"
    }
  ],
  "top_sources": [
    "url1",
    "url2"
  ]
}

Rules:
- Give 2 to 4 findings.
- Use only information from provided search results.
- Do not hallucinate.
- No markdown, no explanations.
"""


def fetch_search_results(query: str) -> list:
    """
    Calls Tavily Search API and returns clean search results.
    """

    response = tavily.search(
        query=query,
        search_depth="basic",
        max_results=5
    )

    results = response.get("results", [])

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")
        }
        for r in results
    ]


def run_search_agent(question: str) -> dict:
    """
    Searches the web and extracts structured findings.
    """

    # Step 1: Retrieve web results
    search_results = fetch_search_results(question)

    if not search_results:
        return {
            "question": question,
            "findings": [],
            "top_sources": [],
            "error": "No search results found"
        }

    # Step 2: Format results for Gemini
    results_text = ""

    for i, result in enumerate(search_results):
        results_text += (
            f"\nResult {i+1}\n"
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Snippet: {result['snippet']}\n"
        )

    user_message = f"""
Question:
{question}

Search Results:
{results_text}

Extract the important facts.
"""

    # Step 3: Gemini analyzes search results
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=SYSTEM_PROMPT
    )

    response = model.generate_content(user_message)

    raw_text = response.text.strip()

    # Remove markdown JSON fences if Gemini adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]

        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

        raw_text = raw_text.strip()

    return json.loads(raw_text)


# Quick Test
if __name__ == "__main__":

    question = "What were the main causes of the 2008 financial crisis?"

    result = run_search_agent(question)

    print(json.dumps(result, indent=2))