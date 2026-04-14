# 🚀 Agentic Evaluation Framework

An extensible evaluation framework for AI agents that measures **accuracy, behavior, and performance** across multi-agent workflows.

---

## 🧠 Overview

This project is designed to evaluate AI systems like **NL2SQL agents** and **multi-agent pipelines**.

It supports:

* Natural Language → SQL evaluation
* Multi-agent workflow analysis
* Performance benchmarking

The framework is modular and can be extended to evaluate real-world systems like **TARS**.

---

## 🎯 Key Features

### ✅ 1. Dataset Integration

* Integrated with Spider dataset (benchmark for NL2SQL)
* Custom dataset loader and validator

---

### ✅ 2. Agent Simulation

* Built a dummy multi-agent API using FastAPI
* Simulates:

  * Retriever
  * Reasoner
  * SQL Generator
* Includes latency + failure simulation

---

### ✅ 3. SQL Evaluation

#### 🔹 Baseline

* Exact match
* Partial match

#### 🔹 Standard (Execution-Based)

* SQLite-based query execution
* Compares actual query results

---

### ✅ 4. Agent Evaluation

Evaluates internal agent behavior:

* Tool usage correctness
* Step efficiency
* Failure rate

---

### ✅ 5. Performance Metrics

Measures:

* Latency (response time)
* Reliability (error handling)

---

### ✅ 6. Final Evaluation

Combines all metrics:

* SQL Accuracy (50%)
* Agent Behavior (30%)
* Performance (20%)

---

### ✅ 7. Reporting System

* Generates JSON reports
* Provides summary statistics

---

## 🧱 Architecture

```text
Dataset (Spider)
      ↓
Converter + Validator
      ↓
Agent Runner
      ↓
Dummy Agent API
      ↓
Evaluation Layer
 ├── SQL Metrics
 ├── Agent Metrics
 ├── Performance Metrics
      ↓
Final Evaluator
      ↓
Report Generator
```

---

## 📂 Project Structure

```text
agent-eval-framework/
├── data/
│   └── spider_data/
│       ├── train_spider.json
│       └── dev.json
│
├── dummy_agent/
│   └── api.py
│
├── evals/
│   ├── configs/
│   │   ├── config.yaml
│   │   └── config.py
│   │
│   ├── test_cases/
│   │   ├── dataset_loader.py
│   │   ├── spider_converter.py
│   │   ├── validator.py
│   │   ├── nl2sql.json
│   │   └── multi_agent.json
│   │
│   ├── runners/
│   │   └── agent_runner.py
│   │
│   ├── metrics/
│   │   ├── sql_metrics.py
│   │   ├── agent_metrics.py
│   │   ├── performance_metrics.py
│   │   ├── db_utils.py
│   │   └── test.db
│   │
│   ├── evaluators/
│   │   └── final_evaluator.py
│   │
│   └── reports/
│       ├── report_generator.py
│       └── report.json
│
├── scripts/
│   └── run_eval.py
│
├── utils/
│   └── logger.py
│
├── README.md
└── requirements.txt
```

---

## 🧠 Module Explanation

### 📁 `data/`

Stores benchmark datasets (Spider) used for evaluation.

---

### 📁 `dummy_agent/`

Simulates a real AI system (like TARS), including:

* Tool usage
* Latency
* Failures

---

### 📁 `evals/` (Core Engine)

#### 🔹 `configs/`

Manages configuration (paths, settings)

#### 🔹 `test_cases/`

Handles dataset loading, conversion, and validation

#### 🔹 `runners/`

Executes queries against the agent with retry & validation

#### 🔹 `metrics/`

Implements evaluation logic:

* SQL correctness
* Agent behavior
* Performance

#### 🔹 `evaluators/`

Combines all metrics into a final score

#### 🔹 `reports/`

Generates structured reports and summaries

---

### 📁 `scripts/`

Entry point of the system (`run_eval.py`)

---

### 📁 `utils/`

Provides logging and utility functions

---

## ▶️ How to Run

### 1. Start Dummy Agent API

```bash
uvicorn dummy_agent.api:app --reload
```

---

### 2. Run Evaluation

```bash
python -m scripts.run_eval
```

---

## 📊 Sample Output

```text
Query: How many singers do we have?

SQL Evaluation: { score: 0 }
Agent Evaluation: { score: 0.4 }
Performance Evaluation: { score: 1.0 }

FINAL EVALUATION: { final_score: 0.32 }
```

---

## 📈 Summary Metrics

* Average SQL Accuracy
* Agent Behavior Score
* Performance Score
* Final System Score

---

## 🧠 Project Scope

This framework is designed to:

* Evaluate NL2SQL systems
* Benchmark multi-agent workflows
* Provide extensible evaluation infrastructure

---

## 🚧 Limitations

* Uses simplified SQLite schema (not full Spider DB)
* Execution-based evaluation limited to dummy DB

---

## 🔮 Future Improvements

* Full Spider DB execution support
* AST-based SQL comparison
* LLM-based evaluation
* Visualization dashboard

---

## 👨‍💻 Author

Developed as part of an **AI/ML engineering project** focused on building real-world evaluation systems.

---

## ⭐ Key Insight

> This project focuses not on building AI models, but on **evaluating and benchmarking AI systems**, which is critical for production AI.
