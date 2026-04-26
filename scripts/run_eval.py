# scripts/run_eval.py
from evals.metrics.performance_metrics import evaluate_performance
from evals.metrics.agent_metrics import evaluate_agent
from evals.metrics.sql_metrics import evaluate_sql
from evals.runners.agent_runner import AgentRunner
from evals.configs.config import config
from evals.test_cases.dataset_loader import load_dataset
from evals.test_cases.validator import validate_dataset
from evals.evaluators.final_evaluator import combine_scores
from evals.reports.report_generator import generate_report, generate_summary
from evals.runners.gemini_runner import GeminiRunner
import os
from dotenv import load_dotenv
from evals.runners.ollama_runner import OllamaRunner
from evals.runners.groq_runner import GroqRunner
from evals.runners.openrouter_runner import OpenRouterRunner


load_dotenv()
api_key = os.getenv("gemKey")
groq_key = os.getenv("GROQ_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")

def main():

    models = [
    # {"name": "gemini_flash", "type": "gemini", "model": "gemini-1.5-flash"},
    # {"name": "gemini_pro", "type": "gemini", "model": "gemini-1.5-pro"},
    # {"name": "gemini_lite", "type": "gemini", "model": "gemini-2.5-flash-lite"},
    
    # optional
     
     {"name": "groq_llama3", "type": "groq", "model": "llama-3.3-70b-versatile"},
     {"name": "openrouter_mixtral", "type": "openrouter", "model": "openrouter/auto"},
     {"name": "ollama_llama3", "type": "ollama", "model": "llama3"},

    ]

    dataset = load_dataset(config)
    dataset = validate_dataset(dataset)

    results = []

    for model_cfg in models:

        print(f"\n\n🚀 Running model: {model_cfg['name']}")

        # 🔁 Select runner
        if model_cfg["type"] == "gemini":
            runner = GeminiRunner(
                api_key=api_key,
                model_name=model_cfg["model"]
            )
        elif model_cfg["type"] == "groq":
            runner = GroqRunner(api_key=groq_key, model_name=model_cfg["model"])
        elif model_cfg["type"] == "openrouter":
            runner = OpenRouterRunner(api_key=openrouter_key, model_name=model_cfg["model"])
        elif model_cfg["type"] == "ollama":
            runner = OllamaRunner(model_name=model_cfg["model"])


        results = []

        # 🔁 SAME dataset loop
        for test in dataset:
            response = runner.run(test["query"])

            sql_eval = evaluate_sql(
                predicted_sql=response.get("sql"),
                expected_sql=test.get("expected_sql")
            )

            agent_eval = evaluate_agent(response, test)
            perf_eval = evaluate_performance(response)
            final_eval = combine_scores(sql_eval, agent_eval, perf_eval)

            result = {
                "model": model_cfg["name"],
                "query": test["query"],

                # 🔥 ADD THIS
                "expected_sql": test.get("expected_sql"),

                "predicted_sql": response.get("sql"),

                "sql_eval": sql_eval,
                "agent_eval": agent_eval,
                "performance_eval": perf_eval,
                "final": final_eval
            }

            results.append(result)

            print("\n---")
            print("Model:", model_cfg["name"])
            print("Query:", test["query"])
            print("FINAL SCORE:", final_eval["final_score"])

        # 🔥 SAVE REPORT PER MODEL
        output_path = f"evals/reports/report_{model_cfg['name']}.json"
        generate_report(results, output_path)

        # 🔥 SUMMARY
        summary = generate_summary(results)

        print(f"\n=== SUMMARY ({model_cfg['name']}) ===")
        print(summary)

    for test in dataset:
        response = runner.run(test["query"])

        sql_eval = evaluate_sql(
            predicted_sql=response.get("sql"),
            expected_sql=test.get("expected_sql")
        )

        agent_eval = evaluate_agent(response, test)
        perf_eval = evaluate_performance(response)
        final_eval = combine_scores(sql_eval, agent_eval, perf_eval)

        result = {
            "query": test["query"],
            "predicted_sql": response.get("sql"),
            "sql_eval": sql_eval,
            "agent_eval": agent_eval,
            "performance_eval": perf_eval,
            "final": final_eval
        }

        results.append(result)

        print("\n---")
        print("Query:", test["query"])
        print("FINAL SCORE:", final_eval["final_score"])


    # 🔥 Generate report
    generate_report(results)

    # 🔥 Generate summary
    summary = generate_summary(results)

    print("\n=== SUMMARY ===")
    print(summary)

if __name__ == "__main__":
    main()