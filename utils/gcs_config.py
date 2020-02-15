import re
import sys
import subprocess


########################################################################
#
#  globus-connect-server-config OPERATIONS
#
########################################################################


def _run_gcs_config(command):
    args = ['sudo', '/sbin/globus-connect-server-config'] + command
    return subprocess.run(args, stdout=subprocess.PIPE)


def endpoint_show():
    result = _run_gcs_config(['endpoint', 'show'])

    uuid_regex = "[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    pattern = 'Endpoint ID\n(%s)\n' % uuid_regex
    match = re.match(pattern, result.stdout.decode("utf-8"))

    return {'uuid': match.group(1)}


def _get_gw_opt_value(line):
    assert line.startswith('--')

    option = line.rstrip('\n').split(' ')[0]
    value  = ''.join(' '.join(line.split(' ')[1:]).split('"'))

    return (option, value)


def gateway_show():
    result = _run_gcs_config(['storage-gateway', 'show'])

    gateways = []
    for gw in result.stdout.decode("utf-8").split('\n\n'):
        lines = gw.rstrip('\n').split('\n')

        d = {'uuid': lines[0]}
        for line in lines[1:]:
            option, value = _get_gw_opt_value(line)

            if option in [
                              '--root',
                              '--domain',
                              '--connector',
                              '--authentication-assurance-timeout',
                              '--display-name',
                              '--identity-provider',
                              '--restrict-paths'
                         ]:
                d[option[2:].replace('-', '_')] = value

            if option in [
                              '--box-json-config',
                              '--bp-access-id-file',
                              '--ceph-admin-key-id',
                              '--ceph-admin-secret-key',
                              '--client-id',
                              '--client-secret',
                              '--google-cloud-storage-project',
                              '--google-cloud-storage-bucket',
                              '--groups-allow',
                              '--groups-deny',
                              '--s3-endpoint',
                              '--s3-bucket',
                              '--s3-user-credential',
                              '--users-allow',
                              '--users-deny',
                              '--user-api-rate-quota'
                         ]:
                if d['connector'] not in d:
                    d[d['connector']] = {}
                d[d['connector']][option[2:].replace('-', '_')] = value

            if option == '--high-assurance':
                d['high_assurance'] = True
            if option == '--allow-mapped-collections':
                d['mapped_collections'] = 'allow'
            if option == '--disallow-mapped-collections':
                d['mapped_collections'] = 'disallow'
            if option == '--allow-guest-collections':
                d['guest_collections'] = 'allow'
            if option == '--disallow-guest-collections':
                d['guest_collections'] = 'disallow'
            if option == '--s3-unauthenticated':
                if d['connector'] not in d:
                    d[d['connector']] = {}
                d[d['connector']]['s3_user_credential'] = None

        gateways.append(d)
    return gateways


def collection_list():
    result = _run_gcs_config(['collection', 'list'])
    collections = []
    for collection in result.stdout.decode("utf-8").split('\n')[1:-1]:
        fields = collection.split(' | ')
        collections.append(
            {
                'uuid': fields[0],
                'type': fields[3],
                'display_name': fields[4],
                'fqdn': fields[5],
                'gateway': {
                    'connector': fields[1],
                    'display_name': fields[2],
                }
            }
        )
    return collections


def show_all():
    return {
        'endpoint': endpoint_show(),
        'gateways': gateway_show(),
        'collections': collection_list()
    }


def _parse_args(args):
    usage = "Usage: %s [endpoint|gateways|collections]" % args[0]

    if len(args) != 2:
        raise SystemExit(usage)


    return {
        'cmd': args[1]
    }


def main():
    args = _parse_args(sys.argv)

    if args['cmd'] == 'endpoint':
        print (endpoint_show())

    elif args['cmd'] == 'gateways':
        print (gateway_show())

    elif args['cmd'] == 'collections':
        print (collection_list())


if __name__ == "__main__":
    main()

