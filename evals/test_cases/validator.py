# evals/test_cases/validator.py

from utils.logger import get_logger

logger = get_logger()

REQUIRED_FIELDS = ["id", "query"]

def validate_test_case(test_case: dict):
    for field in REQUIRED_FIELDS:
        if field not in test_case:
            logger.error(f"Missing field: {field}")
            return False
    return True


def validate_dataset(dataset: list):
    valid_data = []
    
    for test_case in dataset:
        if validate_test_case(test_case):
            valid_data.append(test_case)

    logger.info(f"Validated dataset: {len(valid_data)} valid / {len(dataset)} total")
    return valid_data