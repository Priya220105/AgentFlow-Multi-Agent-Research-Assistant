import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are an orchestrator agent for a multi-agent research assistant.

Given a user research query, your job is to break it into a structured 
pipeline of tasks for specialized agents.

Available agents:
- decomposer: breaks a complex question into simpler sub-questions
- search_agent: searches for information on a specific question
- summarizer: synthesizes multiple search results into a coherent answer
- fact_checker: validates claims in a draft against source documents

Always respond with ONLY valid JSON in this exact format:
{
  "original_query": "the user's query",
  "tasks": [
    {"agent": "decomposer", "input": "the full query"},
    {"agent": "search_agent", "input": "sub-question 1"},
    {"agent": "search_agent", "input": "sub-question 2"},
    {"agent": "summarizer", "input": "synthesize all search results"},
    {"agent": "fact_checker", "input": "validate the summary"}
  ]
}

Rules:
- Always start with decomposer
- Always end with summarizer then fact_checker
- Include 1-3 search_agent tasks depending on query complexity
- No explanation, no markdown, just raw JSON
"""

def run_orchestrator(user_query: str) -> dict:
    """
    Takes a user query and returns a structured task plan.
    """
    model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

    response = model.generate_content(user_query)
    raw_text = response.text.strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    plan = json.loads(raw_text)
    return plan


# Quick test — run this file directly to check it works
if __name__ == "__main__":
    query = "What are the causes and effects of the 2008 financial crisis?"
    result = run_orchestrator(query)
    print(json.dumps(result, indent=2))