from evals.metrics.performance_metrics import evaluate_performance
from evals.metrics.agent_metrics import evaluate_agent
from evals.metrics.sql_metrics import evaluate_sql
from evals.runners.agent_runner import AgentRunner
from evals.configs.config import config
from evals.test_cases.dataset_loader import load_dataset
from evals.test_cases.validator import validate_dataset
from evals.evaluators.final_evaluator import combine_scores
from evals.reports.report_generator import generate_report, generate_summary
from evals.reports.excel_exporter import generate_excel
from evals.runners.gemini_runner import GeminiRunner
import os
from dotenv import load_dotenv
from evals.runners.ollama_runner import OllamaRunner
from evals.runners.groq_runner import GroqRunner
from evals.runners.openrouter_runner import OpenRouterRunner
from evals.runners.multi_agent_runner import MultiAgentRunner

# ── Stage 1: graph imports ────────────────────────────────────────────────────
from evals.graph import AgentState, build_graph
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()
api_key        = os.getenv("gemKey")
groq_key       = os.getenv("GROQ_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")


# ─────────────────────────────────────────────────────────────────────────────
# Helper: run one test case through the graph with a safe fallback
# ─────────────────────────────────────────────────────────────────────────────

def run_with_graph(runner, query: str, model_name: str) -> dict:
    try:
        graph = build_graph(runner)

        initial_state = AgentState(
            query=query,
            model=model_name,
        )

        # LangGraph returns a dict, not the original dataclass
        # result: dict = graph.invoke(initial_state)

        result = graph.invoke(initial_state)

        if hasattr(result, "to_response_dict"):
            response = result.to_response_dict()
        else:
            response = {
                "sql": result.get("sql"),
                "execution_result": result.get("execution_result"),
                "error": result.get("error"),
                "steps": [vars(s) for s in result.get("steps", [])],
            }
        # Extract fields directly from the returned dict
        return {
            "sql":              result.get("sql"),
            "execution_result": result.get("execution_result"),
            "error":            result.get("error"),
            "steps":            [vars(s) for s in result.get("steps", [])],
        }

    except Exception as exc:
        print(
            f"  ⚠️  Graph failed ({type(exc).__name__}: {exc}). "
            f"Falling back to runner.run() for query: {query!r}"
        )
        try:
            fallback_response = runner.run(query)
        except Exception as fallback_exc:
            print(f"  ❌ Fallback runner.run() also failed: {fallback_exc}")
            fallback_response = {"sql": None, "execution_result": None, "error": str(fallback_exc)}

        fallback_response.setdefault("steps", [])
        return fallback_response

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():

    models = [
        #   {"name": "gemini_flash", "type": "gemini", "model": "gemini-1.5-flash"},
        # {"name": "gemini_pro",   "type": "gemini", "model": "gemini-1.5-pro"},
        # {"name": "gemini_lite",  "type": "gemini", "model": "gemini-2.5-flash-lite"},

          {"name": "groq_llama3",        "type": "groq",       "model": "llama-3.3-70b-versatile"},
        #  {"name": "openrouter_mixtral", "type": "openrouter", "model": "openrouter/auto"},
        #  {"name": "ollama_llama3",    "type": "ollama",     "model": "llama3"},

         {
             "name": "multi_agent_groq_openrouter",
             "type": "multi_agent",
         }
    ]

    dataset = load_dataset(config)
    dataset = validate_dataset(dataset)

    # Collect ALL results across every model for the combined Excel report
    all_results = []

    for model_cfg in models:

        print(f"\n\n🚀 Running model: {model_cfg['name']}")

        if model_cfg["type"] == "gemini":
            runner = GeminiRunner(api_key=api_key, model_name=model_cfg["model"])

        elif model_cfg["type"] == "groq":
            runner = GroqRunner(api_key=groq_key, model_name=model_cfg["model"])

        elif model_cfg["type"] == "openrouter":
            runner = OpenRouterRunner(api_key=openrouter_key, model_name=model_cfg["model"])

        elif model_cfg["type"] == "ollama":
            runner = OllamaRunner(model_name=model_cfg["model"])

        elif model_cfg["type"] == "multi_agent":
            planner   = GroqRunner(api_key=groq_key, model_name="llama-3.3-70b-versatile")
            generator = OpenRouterRunner(api_key=openrouter_key, model_name="mistralai/mixtral-8x7b-instruct")
            runner    = MultiAgentRunner(planner=planner, generator=generator)

        # Fresh results list per model
        results = []

        for test in dataset:
            # ── CHANGED: use graph pipeline instead of runner.run() ──────────
            response = run_with_graph(
                runner=runner,
                query=test["query"],
                model_name=model_cfg["name"],
            )
            # ── everything below is UNCHANGED ────────────────────────────────

            sql_eval   = evaluate_sql(predicted_sql=response.get("sql"), expected_sql=test.get("expected_sql"))
            agent_eval = evaluate_agent(response, test)
            perf_eval  = evaluate_performance(response)
            final_eval = combine_scores(sql_eval, agent_eval, perf_eval)

            result = {
                "model":        model_cfg["name"],
                "query":        test["query"],
                "expected_sql": test.get("expected_sql"),
                "predicted_sql": response.get("sql"),
                "sql_eval":     sql_eval,
                "agent_eval":   agent_eval,
                "performance_eval": perf_eval,
                "final":        final_eval,
                # NEW: preserved from graph state — safe to add since
                # generate_report / generate_excel ignore unknown keys.
                "steps":        response.get("steps", []),
            }

            results.append(result)

            print("\n---")
            print("Model:", model_cfg["name"])
            print("Query:", test["query"])
            print("FINAL SCORE:", final_eval["final_score"])

        # Save per-model JSON report
        output_path = f"evals/reports/report_{model_cfg['name']}.json"
        generate_report(results, output_path)

        # Per-model summary in terminal
        summary = generate_summary(results)
        print(f"\n=== SUMMARY ({model_cfg['name']}) ===")
        print(summary)

        # Accumulate into all_results for Excel
        all_results.extend(results)

    # ─────────────────────────────────────────────────────────────
    # Auto-generate Excel report after ALL runners finish
    # Contains: Raw Data sheet, Summary sheet, Multi-Agent Detail sheet
    # ─────────────────────────────────────────────────────────────
    generate_excel(
        results=all_results,
        output_path="evals/reports/benchmark.xlsx"
    )


if __name__ == "__main__":
    main()