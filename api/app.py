# api/app.py

import sys
import os
import time

# Allow imports from agents/ folder (one level up)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS

from agents.orchestrator import run_orchestrator
from agents.decomposer import run_decomposer
from agents.search_agent import run_search_agent
from agents.summarizer import run_summarizer
from agents.fact_checker import run_fact_checker

app = Flask(__name__)
CORS(app)  # allows React (different port) to call this API

MAX_CRITIQUE_ITERATIONS = 3


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/query", methods=["POST"])
def query():
    """
    Main pipeline endpoint. Accepts {"query": "..."} and runs the 
    full multi-agent pipeline, returning the final answer + a full
    trace of what every agent did.
    """
    data = request.get_json()
    user_query = data.get("query", "").strip()

    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    trace = []  # this is what powers your frontend's "agent reasoning" panel

    try:
        # ---- STEP 1: Orchestrator plans the pipeline ----
        t0 = time.time()
        plan = run_orchestrator(user_query)
        trace.append({
            "agent": "orchestrator",
            "output": plan,
            "time_ms": int((time.time() - t0) * 1000)
        })

        # ---- STEP 2: Decomposer breaks query into sub-questions ----
        t0 = time.time()
        decomposed = run_decomposer(user_query)
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
            result = run_search_agent(sub_q)
            all_findings.append(result)
            trace.append({
                "agent": "search_agent",
                "input": sub_q,
                "output": result,
                "time_ms": int((time.time() - t0) * 1000)
            })

        # ---- STEP 4: Summarizer creates first draft ----
        t0 = time.time()
        draft = run_summarizer(user_query, all_findings)
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
            check = run_fact_checker(current_draft, all_findings)
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

            # Not valid -> revise
            t0 = time.time()
            current_draft = run_summarizer(
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
            "trace": trace  # return partial trace even on failure - useful for debugging
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)