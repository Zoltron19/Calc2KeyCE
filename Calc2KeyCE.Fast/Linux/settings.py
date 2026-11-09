import json

def load_config(args):
    try:
        with open('.config/default.json', 'r') as f:
            default = json.load(f)
        config_file = f'.config/{default}.json'
        with open(config_file, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        print('No configuration file found. Falling back on defaults.')
        settings = {}

    if args.x:
        settings['x'] = args.x
    if args.y:
        settings['y'] = args.y
    if args.width:
        settings['width'] = args.width
    if args.height:
        settings['height'] = args.height
    if args.type:
        settings['type'] = args.type
    if args.palette:
        settings['palette'] = args.palette
    if args.scaling:
        settings['scaling'] = args.scaling

    return settings
