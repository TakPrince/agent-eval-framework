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

def main():
    runner = AgentRunner(base_url=config["agent"]["base_url"])

    dataset = load_dataset(config)
    dataset = validate_dataset(dataset)

    results = []

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