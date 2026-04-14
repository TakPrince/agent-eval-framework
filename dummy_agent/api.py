# dummy_agent/api.py

from fastapi import FastAPI
from pydantic import BaseModel
import random
import time

app = FastAPI(title="Dummy Agent API")

# -----------------------------
# Request Schema
# -----------------------------
class QueryRequest(BaseModel):
    query: str


# -----------------------------
# Simulated Tools
# -----------------------------
TOOLS = ["retriever", "sql_generator", "reasoner"]

def simulate_tool(tool_name):
    latency = round(random.uniform(0.1, 0.5), 2)
    time.sleep(latency)

    # Random failure simulation
    if random.random() < 0.1:
        return {
            "tool": tool_name,
            "status": "failure",
            "latency": latency
        }

    return {
        "tool": tool_name,
        "status": "success",
        "latency": latency
    }


# -----------------------------
# SQL Generator (dummy logic)
# -----------------------------
def generate_sql(query: str):
    if "total" in query.lower():
        return "SELECT SUM(sales) FROM sales"
    elif "customers" in query.lower():
        return "SELECT * FROM customers"
    else:
        return "SELECT * FROM table"


# -----------------------------
# Main Endpoint
# -----------------------------
@app.post("/query")
def run_query(req: QueryRequest):
    start_time = time.time()

    steps = []

    # Step 1: Retrieval
    steps.append(simulate_tool("retriever"))

    # Step 2: Reasoning (optional)
    if random.random() > 0.3:
        steps.append(simulate_tool("reasoner"))

    # Step 3: SQL Generation
    steps.append(simulate_tool("sql_generator"))

    # Generate SQL
    sql_step = next((s for s in steps if s["tool"] == "sql_generator"), None)

    if sql_step and sql_step["status"] == "success":
        sql = generate_sql(req.query)
    else:
        sql = None

    total_latency = round(time.time() - start_time, 2)

    # Random global failure
    error = None
    if random.random() < 0.1:
        error = "Agent failed to process query"

    return {
        "query": req.query,
        "sql": sql if not error else None,
        "answer": "dummy_answer",
        "steps": steps,
        "total_latency": total_latency,
        "error": error
    }