"""
evals/insights/insight_generator.py
-------------------------------------
Phase 5: LLM-based insights engine.

Design rules
~~~~~~~~~~~~
* Uses an existing runner instance — no new API clients created
* Never crashes — all LLM failures return a safe fallback string
* Does NOT touch scores, metrics, or evaluation logic
* Two public functions:
    generate_insight()         → per-result analysis
    generate_summary_insights() → batch-level pattern detection
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates  (single place to edit — never buried in logic)
# ─────────────────────────────────────────────────────────────────────────────

_SINGLE_RESULT_PROMPT = """\
You are an AI system evaluator.

Analyze the NL2SQL result strictly based on the data below.

Query: {query}
SQL: {predicted_sql}

Scores:
- SQL: {sql_score}
- Agent: {agent_score}
- Performance: {performance_score}

Trajectory:
- Steps: {step_count}
- Errors: {error_steps}
- Retries: {recovery_attempts}

STRICT RULES:
- If error_steps = 0 → system did NOT struggle
- If recovery_attempts = 0 → no retry occurred
- DO NOT assume failures if not present
- ONLY use given numbers

Tasks:
1. Explain why the result succeeded or failed
2. Identify if any stage struggled (ONLY if errors > 0)
3. Suggest one concrete system-level improvement (not about increasing scores) Keep answer concise (3-5 lines).\
"""

# ─────────────────────────────────────────────────────────────────────────────
# Public: per-result insight
# ─────────────────────────────────────────────────────────────────────────────

def generate_insight(result: dict, llm_runner) -> str:
    """
    Generate a human-readable insight for a single evaluation result.

    Parameters
    ----------
    result     : one result dict from the evaluation loop
                 Expected keys: query, predicted_sql, sql_eval,
                 agent_eval, performance_eval, trajectory_eval
    llm_runner : any existing runner with a .run(query: str) -> dict method

    Returns
    -------
    str — LLM-generated analysis, or a safe fallback message on failure
    """
    try:
        # ── extract all fields defensively ───────────────────────
        trajectory = result.get("trajectory_eval") or result.get("final", {}).get("trajectory_eval") or {}
        sql_eval   = result.get("sql_eval")        or {}
        agent_eval = result.get("agent_eval")      or {}
        perf_eval  = result.get("performance_eval") or {}

        prompt = _SINGLE_RESULT_PROMPT.format(
            query             = result.get("query",         "N/A"),
            predicted_sql     = result.get("predicted_sql", "N/A"),
            sql_score         = sql_eval.get("score",       "N/A"),
            agent_score       = agent_eval.get("score",     "N/A"),
            performance_score = perf_eval.get("score",      "N/A"),
            step_count        = trajectory.get("step_count",        "N/A"),
            error_steps       = trajectory.get("error_steps",       "N/A"),
            recovery_attempts = trajectory.get("recovery_attempts", "N/A"),
        )

        response = llm_runner.run(prompt)

        # Runners return a dict — extract the text content
        insight = _extract_text(response)
        return insight if insight else _fallback("empty response from LLM")

    except Exception as exc:  # noqa: BLE001
        return _fallback(f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Public: batch summary insight
# ─────────────────────────────────────────────────────────────────────────────

def generate_summary_insights(results: list, llm_runner) -> str:
    """
    Summarize failure patterns across an entire batch of results.

    Parameters
    ----------
    results    : list of result dicts from the evaluation loop
    llm_runner : any existing runner instance

    Returns
    -------
    str — LLM-generated batch summary, or a safe fallback on failure
    """
    if not results:
        return _fallback("no results provided for summary")

    try:
        # ── build a compact text summary of all results ───────────
        lines = []
        for i, r in enumerate(results, 1):
            traj = r.get("trajectory_eval") or r.get("final", {}).get("trajectory_eval") or {}
            final = r.get("final")           or {}
            lines.append(
                f"{i}. Query: {r.get('query','N/A')!r} | "
                f"Final: {final.get('final_score','N/A')} | "
                f"SQL: {(r.get('sql_eval') or {}).get('score','N/A')} | "
                f"Errors: {traj.get('error_steps','N/A')} | "
                f"Retries: {traj.get('recovery_attempts','N/A')}"
            )

        results_summary = "\n".join(lines)
        prompt   = _SUMMARY_PROMPT.format(results_summary=results_summary)
        response = llm_runner.run(prompt)

        insight = _extract_text(response)
        return insight if insight else _fallback("empty response from LLM")

    except Exception as exc:  # noqa: BLE001
        return _fallback(f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_text(runner_response) -> str:
    """
    Pull the text string out of a runner response.

    Runners can return:
      {"sql": ..., "raw": "some text"}   ← agent runners
      {"response": "some text"}          ← some custom runners
      "plain string"                     ← simple runners
    We try common keys; fall back to str() of the whole thing.
    """
    if isinstance(runner_response, str):
        return runner_response.strip()

    if isinstance(runner_response, dict):
        for key in ("response", "text", "content", "raw", "output", "sql"):
            val = runner_response.get(key)
            if val and isinstance(val, str):
                return val.strip().replace("\n\n", "\n")

    return str(runner_response).strip()


def _fallback(reason: str) -> str:
    return f"[Insight unavailable — {reason}]"