# api/app.py

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS

from agents.orchestrator import run_orchestrator
from agents.decomposer import run_decomposer
from agents.search_agent import run_search_agent
from agents.summarizer import run_summarizer
from agents.fact_checker import run_fact_checker
from utils.rate_limit import gemini_safe_call    # ← ADD this import near the top, with the other imports

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://agent-flow-multi-agent-research-ass.vercel.app"
            ]
        }
    },
    supports_credentials=True
)
MAX_CRITIQUE_ITERATIONS = 3


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    trace = []

    try:
        # ---- STEP 1: Orchestrator plans the pipeline ----
        t0 = time.time()
        plan = gemini_safe_call(run_orchestrator, user_query)    # ← REPLACES: plan = run_orchestrator(user_query)
        trace.append({
            "agent": "orchestrator",
            "output": plan,
            "time_ms": int((time.time() - t0) * 1000)
        })

        # ---- STEP 2: Decomposer breaks query into sub-questions ----
        t0 = time.time()
        decomposed = gemini_safe_call(run_decomposer, user_query)    # ← REPLACES: decomposed = run_decomposer(user_query)
        sub_questions = decomposed.get("sub_questions", [user_query])
        trace.append({
            "agent": "decomposer",
            "output": decomposed,
            "time_ms": int((time.time() - t0) * 1000)
        })

        # ---- STEP 3: Search Agent runs once per sub-question ----
        all_findings = []
        for sub_q in sub_questions:
            t0 = time.time()
            result = gemini_safe_call(run_search_agent, sub_q)    # ← REPLACES: result = run_search_agent(sub_q)
            all_findings.append(result)
            trace.append({
                "agent": "search_agent",
                "input": sub_q,
                "output": result,
                "time_ms": int((time.time() - t0) * 1000)
            })

        # ---- STEP 4: Summarizer creates first draft ----
        t0 = time.time()
        draft = gemini_safe_call(run_summarizer, user_query, all_findings)    # ← REPLACES: draft = run_summarizer(user_query, all_findings)
        trace.append({
            "agent": "summarizer",
            "output": draft,
            "time_ms": int((time.time() - t0) * 1000)
        })

        # ---- STEP 5: Critique loop (Fact Checker <-> Summarizer) ----
        current_draft = draft
        final_confidence = 0
        critique_status = "validated"

        for iteration in range(MAX_CRITIQUE_ITERATIONS):
            t0 = time.time()
            check = gemini_safe_call(run_fact_checker, current_draft, all_findings)    # ← REPLACES: check = run_fact_checker(current_draft, all_findings)
            trace.append({
                "agent": "fact_checker",
                "iteration": iteration + 1,
                "output": check,
                "time_ms": int((time.time() - t0) * 1000)
            })

            final_confidence = check["confidence"]

            if check["is_valid"]:
                critique_status = "validated"
                break

            t0 = time.time()
            current_draft = gemini_safe_call(    # ← ALSO wrap this revision call
                run_summarizer,
                user_query,
                all_findings,
                revision_instructions=check["revision_instructions"],
                previous_draft=current_draft
            )
            trace.append({
                "agent": "summarizer",
                "iteration": iteration + 1,
                "note": "revision pass",
                "output": current_draft,
                "time_ms": int((time.time() - t0) * 1000)
            })

            critique_status = "max_iterations_reached"

        # ---- STEP 6: Return final response ----
        return jsonify({
            "answer": current_draft.get("draft_answer", ""),
            "sources": current_draft.get("citations_used", []),
            "confidence": final_confidence,
            "status": critique_status,
            "trace": trace
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "trace": trace
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))