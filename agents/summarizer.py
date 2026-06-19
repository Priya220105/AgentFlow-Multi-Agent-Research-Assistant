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

Sometimes you will also be given revision instructions from a Fact-Checker 
agent and your own previous draft — in that case, your job is to FIX the 
issues raised while keeping everything that was already correct.

Your job is to:
1. Synthesize the findings into one coherent, well-organized answer
2. Preserve attribution — note which source supports which claim
3. Do not add facts that are not present in the findings
4. Write in clear, neutral, explanatory prose (not bullet points)
5. If revision instructions are provided, remove or fix exactly what they flag

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

def run_summarizer(
    original_query: str,
    all_findings: list,
    revision_instructions: str = "",
    previous_draft: dict = None
) -> dict:
    """
    Takes the original query + combined findings from all search agents,
    and returns a synthesized draft answer with citations.

    If revision_instructions is non-empty, this call is a REVISION pass —
    previous_draft is included so the model fixes issues rather than
    starting from scratch. This is what makes the critique loop work:
    fact_checker.run_critique_loop() calls this same function again
    with feedback instead of needing a separate "revise" function.
    """
    # Flatten findings into readable text for the model (same as before)
    findings_text = ""
    for i, finding_block in enumerate(all_findings):
        findings_text += f"\nSub-question: {finding_block.get('question', '')}\n"
        for f in finding_block.get("findings", []):
            findings_text += f"- Fact: {f['fact']}\n"
            findings_text += f"  Source: {f['source_title']} ({f['source_url']})\n"

    # Build the user message differently depending on first-draft vs revision
    if revision_instructions:
        user_message = f"""
Original Query: {original_query}

Findings gathered from research:
{findings_text}

Your previous draft:
{previous_draft.get('draft_answer', '') if previous_draft else ''}

A Fact-Checker agent reviewed your draft and found issues.
Revision instructions: {revision_instructions}

Rewrite the draft to fix these issues. Keep everything else that was 
already correct and well-supported by the findings.
"""
    else:
        user_message = f"""
Original Query: {original_query}

Findings gathered from research:
{findings_text}

Synthesize these into one coherent draft answer.
"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
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

    # Test 1: first draft (original behavior, unchanged)
    result = run_summarizer(original_query, mock_findings)
    print("--- First draft ---")
    print(json.dumps(result, indent=2))

    # Test 2: simulate a revision pass
    revised = run_summarizer(
        original_query,
        mock_findings,
        revision_instructions="Remove any mention of a meteor strike — it is not supported by the sources.",
        previous_draft=result
    )
    print("\n--- Revised draft ---")
    print(json.dumps(revised, indent=2))