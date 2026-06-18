
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a Summarizer Agent in a multi-agent research assistant.

You will be given the original research query and a list of findings 
gathered by search agents, each with a fact and a source.

Your job is to:
1. Synthesize the findings into one coherent, well-organized answer
2. Preserve attribution — note which source supports which claim
3. Do not add facts that are not present in the findings
4. Write in clear, neutral, explanatory prose (not bullet points)

Always respond with ONLY valid JSON in this exact format:
{
  "original_query": "the original question",
  "draft_answer": "a coherent multi-paragraph synthesis of the findings",
  "citations_used": ["url1", "url2", "url3"]
}

Rules:
- draft_answer should read like a well-written explainer, not a list
- Every claim in draft_answer must trace back to a finding you were given
- citations_used should list every source url actually referenced
- No explanation, no markdown, just raw JSON
"""

def run_summarizer(original_query: str, all_findings: list) -> dict:
    """
    Takes the original query + combined findings from all search agents,
    and returns a synthesized draft answer with citations.
    """
    # Flatten findings into readable text for the model
    findings_text = ""
    for i, finding_block in enumerate(all_findings):
        findings_text += f"\nSub-question: {finding_block.get('question', '')}\n"
        for f in finding_block.get("findings", []):
            findings_text += f"- Fact: {f['fact']}\n"
            findings_text += f"  Source: {f['source_title']} ({f['source_url']})\n"

    user_message = f"""
Original Query: {original_query}

Findings gathered from research:
{findings_text}

Synthesize these into one coherent draft answer.
"""

    model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)
    
    response = model.generate_content(user_message)
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    result = json.loads(raw_text)
    return result


if __name__ == "__main__":
    original_query = "What are the causes and long-term effects of the 2008 financial crisis?"

    # Mock findings (as if returned by search_agent.py for 2 sub-questions)
    mock_findings = [
        {
            "question": "What were the main causes of the 2008 financial crisis?",
            "findings": [
                {
                    "fact": "Subprime lending to borrowers with poor credit fueled a housing bubble.",
                    "source_title": "2008 financial crisis - Wikipedia",
                    "source_url": "https://en.wikipedia.org/wiki/2008_financial_crisis"
                },
                {
                    "fact": "Securitization packaged mortgages into investments, spreading risk globally.",
                    "source_title": "Origins of the Crisis - FDIC",
                    "source_url": "https://www.fdic.gov/media/18636"
                }
            ]
        }
    ]

    result = run_summarizer(original_query, mock_findings)
    print(json.dumps(result, indent=2))