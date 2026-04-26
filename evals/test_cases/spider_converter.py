# evals/test_cases/spider_converter.py

import json
from utils.logger import get_logger

logger = get_logger()


def convert_spider_sample(sample: dict):
    return {
        "id": sample.get("question_id", sample.get("id", "unknown")),
        "query": sample.get("question", ""),
        "expected_sql": sample.get("query", ""),
        "db_id": sample.get("db_id", "unknown"),
        "query_type": "unknown",
        "difficulty": sample.get("hardness", "unknown")
    }


def load_spider_dataset(path: str, limit: int = 10):
    try:
        with open(path, "r") as f:
            spider_data = json.load(f)

        #  LIMIT DATASET (CRITICAL)
        spider_data = spider_data[:limit]

        converted = []
        for sample in spider_data:
            try:
                converted.append(convert_spider_sample(sample))
            except Exception as e:
                logger.warning(f"Skipping bad sample: {e}")

        logger.info(f"Loaded Spider dataset: {len(converted)} samples")
        return converted

    except Exception as e:
        logger.error(f"Spider load failed: {e}")
        return []