import os
import sys
from ruamel.yaml import YAML


def parse_args(args):
    usage = "Usage: %s <file> <key>[=<value>]" % args[0]

    if len(args) != 3:
        raise SystemExit(usage)

    kv = args[2].split('=')

    return {
        'file':  args[1],
        'key':   kv[0],
        'value': "=".join(kv[1:]) if len(kv) >= 2 else None
    }


def display_key_from_file(file, key):
    if os.path.exists(file):
        with open(file) as f:
            data = YAML().load(f)
        if data is not None and key in data and data[key] is not None:
            print(data[key])


def set_key_value_in_file(file, key, value):
    data = None

    if os.path.exists(file):
        with open(file) as f:
            data = YAML().load(f)
    
    if data is None:
        data = YAML().load("%s: %s" % (key, value))
    else:
        data[key] = value

    with open(file, 'w+') as f:
        YAML().dump(data, f)


def main():
    args = parse_args(sys.argv)

    if args['value'] is None:
        display_key_from_file(args['file'], args['key'])
    else:
        set_key_value_in_file(args['file'], args['key'], args['value'])


if __name__ == "__main__":
    main()

