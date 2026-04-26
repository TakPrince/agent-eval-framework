import json
import pandas as pd
import glob


def load_reports():
    files = glob.glob("evals/reports/report_*.json")

    all_data = []

    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
            all_data.extend(data)

    return all_data


def generate_excel(output_path="evals/reports/benchmark.xlsx"):
    data = load_reports()

    rows = []

    for item in data:
        rows.append({
            "model": item["model"],
            "query": item["query"],
            "expected_sql": item.get("expected_sql"),
            "predicted_sql": item.get("predicted_sql"),

            "sql_score": item["final"]["sql_score"],
            "agent_score": item["final"]["agent_score"],
            "performance_score": item["final"]["performance_score"],
            "final_score": item["final"]["final_score"],

            "latency": item["performance_eval"]["latency"]
        })

    df = pd.DataFrame(rows)

    # 🔹 RAW DATA SHEET
    with pd.ExcelWriter(output_path) as writer:
        df.to_excel(writer, sheet_name="raw_data", index=False)

        # 🔹 SUMMARY SHEET
        summary = df.groupby("model").mean(numeric_only=True)
        summary.to_excel(writer, sheet_name="summary")

    print(f"✅ Excel generated: {output_path}")