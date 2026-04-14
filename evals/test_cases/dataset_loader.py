# evals/test_cases/dataset_loader.py

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


def load_dataset(config: dict):
    dataset_type = config["dataset"]["type"]
    path = config["dataset"]["path"]

    if dataset_type == "custom":
        return load_json_dataset(path)

    elif dataset_type == "spider":
        from evals.test_cases.spider_converter import load_spider_dataset
        return load_spider_dataset(path)

    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")