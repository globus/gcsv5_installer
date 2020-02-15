import os
import sys
import ast

from ruamel.yaml import YAML
from jinja2 import Environment


def _load_jinja(path, context):
    if not os.path.exists(path):
        return None

    with open(path) as f:
        data = Environment().from_string(f.read()).render(context)
    return data


def _load_yaml(path, with_jinja):
    if not os.path.exists(path):
        return None

    with open(path) as f:
        data = YAML().load(f)

    if data is None or not with_jinja:
        return data
    return YAML().load(_load_jinja(path, data))


def _save_yaml(path, data):
    with open(path, 'w+') as f:
        YAML().dump(data, f)


def _split_key(key):
    return key.split('.')


def _get_key_value(data, key):
    if isinstance(data, dict):
        return data.get(key, None)

    if isinstance(data, list):
        return data[int(key)]
    raise TypeError(key + ' is not a dict or list')


def get_key_value(path, key):
    data = _load_yaml(path, with_jinja=True)

    if data is None:
        return None

    for k in _split_key(key):
        data = _get_key_value(data, k)
    return data


def set_key_value(path, key, value):
    data = _load_yaml(path, with_jinja=False);
    if data is None:
        data = {}

    value_at_key = data
    for k in _split_key(key)[0:-1]:
        if isinstance(value_at_key, dict) and k not in value_at_key:
            value_at_key[k] = {}
        value_at_key = _get_key_value(value_at_key, k)

    k = _split_key(key)[-1]
    if isinstance(value_at_key, list):
        k = int(k)
    value_at_key[k] = value
    _save_yaml(path, data)


def _display_key_from_file(path, key):
    value = get_key_value(path, key)
    if value is not None:
        print(value)


#
# We attempt to convert strings representing lists or dictionaries. If we 
# fail (ex value is 1 or 'a' or None), just return value.
#
def _eval_value(value):
    try:
        return ast.literal_eval(value)
    except:
        pass
    return value


def _parse_args(args):
    usage = "Usage: %s <file> <key>[=<value>]" % args[0]

    if len(args) != 3:
        raise SystemExit(usage)

    kv = args[2].split('=', maxsplit=1)

    key = kv[0]
    value = _eval_value(kv[1]) if len(kv) == 2 else None

    return {
        'file':  args[1],
        'key':   key,
        'value': value
    }


def main():
    args = _parse_args(sys.argv)

    if args['value'] is None:
        _display_key_from_file(args['file'], args['key'])
    else:
        set_key_value(args['file'], args['key'], args['value'])


if __name__ == "__main__":
    main()

