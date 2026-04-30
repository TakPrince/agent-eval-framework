import json
from utils.logger import get_logger

logger = get_logger()


def load_json_dataset(path: str):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            logger.info(f"Loaded dataset from {path}")
            return data
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return []


# 🔥 NEW: failure/debug test injector (Phase 3 verification)
def inject_failure_cases(dataset: list):
    """
    Adds temporary failure cases to test retry logic (Phase 3).
    Does NOT modify original dataset structure.
    """

    failure_tests = [
        {
            "query": "Give me singer data with wrong SQL syntax",
            "expected_sql": "SELECT name FROM singer"
        },
        {
            "query": "List singers but use invalid SQL",
            "expected_sql": "SELECT name FROM singer"
        }
    ]

    logger.info("Injecting Phase 3 failure test cases")

    return dataset + failure_tests


def load_dataset(config: dict):
    dataset_type = config["dataset"]["type"]
    path = config["dataset"]["path"]

    if dataset_type == "custom":
        dataset = load_json_dataset(path)

    elif dataset_type == "spider":
        from evals.test_cases.spider_converter import load_spider_dataset
        dataset = load_spider_dataset(path)

    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")

    # 🔥 NEW: Optional Phase 3 debug mode
    if config.get("debug_phase3", False):
        dataset = inject_failure_cases(dataset)

    return dataset