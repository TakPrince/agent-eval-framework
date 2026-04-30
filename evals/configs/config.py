import yaml

def load_config():
    with open("evals/configs/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 🔥 Safe default
    if "debug_phase3" not in config:
        config["debug_phase3"] = False

    return config

config = load_config()