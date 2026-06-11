import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a decomposer agent in a multi-agent research assistant.

Your ONLY job is to take a complex research question and break it down 
into smaller, atomic, self-contained sub-questions that can each be 
answered independently.

Rules:
- Each sub-question must be specific and searchable on its own
- Do NOT answer the questions — only decompose them
- Aim for 2-4 sub-questions (never more than 5)
- If the question is already simple, return just 1 sub-question
- Always respond with ONLY valid JSON, no explanation, no markdown

Response format:
{
  "original_query": "the original question",
  "sub_questions": [
    "specific sub-question 1",
    "specific sub-question 2",
    "specific sub-question 3"
  ],
  "complexity": "simple" or "moderate" or "complex"
}
"""

def run_decomposer(query: str) -> dict:
    """
    Takes a complex query and breaks it into atomic sub-questions.
    """
    model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT)

    try:
        response = model.generate_content(query)
        raw_text = response.text.strip()

        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)
        return result

    except json.JSONDecodeError as e:
        # Graceful fallback — return the query as-is if parsing fails
        return {
            "original_query": query,
            "sub_questions": [query],
            "complexity": "unknown",
            "error": f"JSON parsing failed: {str(e)}"
        }


# Quick test
if __name__ == "__main__":
    query = "What are the causes and long-term effects of the 2008 financial crisis on global banking?"
    result = run_decomposer(query)
    print(json.dumps(result, indent=2))