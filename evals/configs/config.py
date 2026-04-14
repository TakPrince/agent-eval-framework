# evals/configs/config.py

import yaml

def load_config():
    with open("evals/configs/config.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_config()