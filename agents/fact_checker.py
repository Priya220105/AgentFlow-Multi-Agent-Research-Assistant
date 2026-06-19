import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a Fact-Checker Agent in a multi-agent research assistant.

You will be given:
1. A draft answer written by a Summarizer agent
2. The original source findings the Summarizer was supposed to base it on

Your job is to validate every claim in the draft against the source findings.

For each claim in the draft, check:
- Is this claim directly supported by one of the source findings?
- Or is it unsupported / invented / not present in the sources?

Always respond with ONLY valid JSON in this exact format:
{
  "is_valid": true or false,
  "confidence": a number between 0 and 1,
  "issues": [
    {
      "claim": "the unsupported claim from the draft",
      "reason": "why it is not supported by the sources"
    }
  ],
  "revision_instructions": "specific guidance for the Summarizer to fix the issues, or empty string if no issues"
}

Rules:
- is_valid is true ONLY if every claim is supported by the sources
- confidence reflects how well-grounded the overall draft is (1.0 = fully grounded)
- If is_valid is false, issues must list every unsupported claim
- Be strict — vague or partially-supported claims count as issues
- No explanation outside the JSON, no markdown, just raw JSON
"""

def run_fact_checker(draft: dict, source_findings: list) -> dict:
    """
    Validates a Summarizer draft against original source findings (MCP context).
    
    draft: output from summarizer.py — {"draft_answer": "...", "citations_used": [...]}
    source_findings: the original findings from search_agent.py calls — 
                      this is the MCP-style structured context that makes
                      fact-checking grounded, not just self-referential.
    """
    # Build the structured context block — this is the MCP principle:
    # the fact-checker gets RAW sources, not just the draft
    sources_text = ""
    for i, finding_set in enumerate(source_findings):
        sources_text += f"\n--- Search result set {i+1} ---\n"
        for f in finding_set.get("findings", []):
            sources_text += f"Fact: {f.get('fact')}\n"
            sources_text += f"Source: {f.get('source_title')} ({f.get('source_url')})\n\n"

    user_message = f"""
Draft Answer to validate:
{draft.get('draft_answer', '')}

Original Source Findings (ground truth):
{sources_text}

Validate every claim in the draft against these source findings.
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

    if not raw_text:
        # Model returned nothing usable — fail safe instead of crashing
        print("WARNING: Fact Checker got an empty response from Gemini")
        return {
            "is_valid": False,
            "confidence": 0.0,
            "issues": [{"claim": "N/A", "reason": "Fact checker received an empty model response"}],
            "revision_instructions": "Retry — the validator did not return a usable response."
        }

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"WARNING: Fact Checker got unparseable JSON: {raw_text[:200]}")
        return {
            "is_valid": False,
            "confidence": 0.0,
            "issues": [{"claim": "N/A", "reason": "Fact checker response was not valid JSON"}],
            "revision_instructions": "Retry — the validator's response could not be parsed."
        }

    return result

def run_critique_loop(draft: dict, source_findings: list, summarizer_fn, max_iterations: int = 3) -> dict:
    """
    The full critique loop: fact-check -> if issues, revise -> repeat
    until valid or max_iterations reached.

    summarizer_fn: pass in run_summarizer from summarizer.py so this loop
                   can call it again for revisions without circular imports.
    """
    current_draft = draft
    iteration_log = []

    for i in range(max_iterations):
        check_result = run_fact_checker(current_draft, source_findings)

        iteration_log.append({
            "iteration": i + 1,
            "is_valid": check_result["is_valid"],
            "confidence": check_result["confidence"],
            "issues_found": len(check_result.get("issues", []))
        })

        if check_result["is_valid"]:
            return {
                "final_draft": current_draft,
                "confidence": check_result["confidence"],
                "iterations": iteration_log,
                "status": "validated"
            }

        # Revise: send issues back to summarizer
        current_draft = summarizer_fn(
            revision_instructions=check_result["revision_instructions"],
            previous_draft=current_draft,
            source_findings=source_findings
        )

    # Max iterations hit without full validation
    return {
        "final_draft": current_draft,
        "confidence": check_result["confidence"],
        "iterations": iteration_log,
        "status": "max_iterations_reached"
    }


if __name__ == "__main__":
    # Mock data simulating output from summarizer.py and search_agent.py
    mock_draft = {
        "draft_answer": "The 2008 financial crisis was caused by subprime lending and securitization. It was also directly caused by a meteor strike on Wall Street.",
        "citations_used": ["https://en.wikipedia.org/wiki/2008_financial_crisis"]
    }

    mock_sources = [
        {
            "findings": [
                {
                    "fact": "A primary cause was subprime lending.",
                    "source_title": "2008 financial crisis - Wikipedia",
                    "source_url": "https://en.wikipedia.org/wiki/2008_financial_crisis"
                },
                {
                    "fact": "Securitization spread risk through the financial system.",
                    "source_title": "Origins of the Crisis - FDIC",
                    "source_url": "https://www.fdic.gov/media/18636"
                }
            ]
        }
    ]

    result = run_fact_checker(mock_draft, mock_sources)
    print(json.dumps(result, indent=2))