import sys
import ast


def parse_args(args):
    usage = "Usage: %s <json_string> <key>" % args[0]

    if len(args) != 3:
        raise SystemExit(usage)

    return {
        'json_string': args[1],
        'key': args[2]
    }


def main():
    args = parse_args(sys.argv)

    # Load to dict to avoid ' vs " in json_string
    d = ast.literal_eval(args['json_string'])

    try:
        print (eval('d' + args['key']))
    except KeyError:
        pass


if __name__ == "__main__":
    main()

