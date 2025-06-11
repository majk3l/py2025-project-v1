import yaml
import os

def load_config():
    path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file '{path}' not found")
    with open(path, 'r') as f:
        return yaml.safe_load(f)
