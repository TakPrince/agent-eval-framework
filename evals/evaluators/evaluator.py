# evals/evaluators/evaluator.py

class Evaluator:
    def __init__(self):
        pass

    def evaluate(self, test_case: dict, response: dict) -> dict:
        return {
            "id": test_case.get("id"),
            "status": "not_implemented"
        }