import re
import os
import sys
import requests
from urllib.parse import urlencode as urlencode

AUTH_URIS = {
    'Production'  : 'https://auth.globus.org',
    'Preview'     : 'https://auth.preview.globus.org',
    'Staging'     : 'https://auth.staging.globuscs.info',
    'Test'        : 'https://auth.test.globuscs.info',
    'Integration' : 'https://auth.integration.globuscs.info',
    'Sandbox'     : 'https://auth.sandbox.globuscs.info'
}


###################################################################
#
#  GET USERINFO FUNCTIONS
#
###################################################################


def get_userinfo(environment, token):
    auth_uri = AUTH_URIS[environment]

    headers = {
        'Authorization': 'Bearer ' + token
    }

    r = requests.post(auth_uri + '/v2/oauth2/userinfo', headers=headers)
    return r.json()

def _get_main(args0, cmd, args):
    usage = "Some useful usage message"

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    token = args[1]

    resp = get_userinfo(environment, token)
    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  MAIN FUNCTIONS
#
###################################################################

def _parse_args(args):
    cmds = [
        'get',
    ]

    usage = ("Usage: %s [%s]") % (args[0], '|'.join(cmds))

    if len(args) == 1 or args[1] not in cmds:
        raise SystemExit(usage)
    return (args[0], args[1], args[2:])


def main():
    (args0, cmd, args) = _parse_args(sys.argv)

    cmd_main = globals().get('_' + cmd + '_main')
    assert cmd_main
    return cmd_main(args0, cmd, args)


if __name__ == "__main__":
    main()
