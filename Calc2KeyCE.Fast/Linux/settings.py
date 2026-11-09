import json

def load_config():
    with open('.config/default.json', 'r') as f:
        default = json.load(f)
    config_file = f'.config/{default}.json'
    with open(config_file, 'r') as f:
        settings = json.load(f)

    return settings
