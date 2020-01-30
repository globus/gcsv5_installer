import re
import os
import sys
import requests

AUTH_URIS = {
    'Production': 'https://auth.globus.org',
    'Preview': 'https://auth.preview.globus.org',
    'Staging': 'https://auth.staging.globuscs.info',
    'Test': 'https://auth.test.globuscs.info',
    'Integration': 'https://auth.integration.globuscs.info',
    'Sandbox': 'https://auth.sandbox.globuscs.info'
}


def display_tokens(tokens):
    print(tokens)


def get_api_tokens(client_id, client_secret, environment, scopes, grant_name):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'state': '_default',
        'redirect_uri': auth_uri+'/v2/web/auth-code',
        'prefill_grant_name': grant_name,
        'response_type': 'code',
        'client_id': client_id,
        'scope': scopes,
        'access_type': 'offline'
    }
    r = requests.get(auth_uri+'/v2/oauth2/authorize',
                     params=payload,
                     allow_redirects=False)
    needle = (
               'The resource has been moved to (.*);' +
               ' you should be redirected automatically'
    )
    result = re.search(needle, r.text)

    with open("/dev/tty", "wb+", buffering=0) as term:
        term.write("\n".encode())
        term.write("FOLLOW THIS LINK AND PASTE IN THE AUTHORIZATION CODE:".encode())
        term.write("\n".encode())
        term.write(result.group(1).encode())
        term.write("\n".encode())
        term.write('Enter the authorization code: '.encode())

    code = input()

    data = {
        'code': code, 
        'redirect_uri': auth_uri+'/v2/web/auth-code', 
        'grant_type': 'authorization_code'
   }
    r = requests.post(auth_uri+'/v2/oauth2/token',
                      data=data, 
                      auth=(client_id, client_secret))

    return r.json()


def parse_args(args):
    environments = '|'.join(AUTH_URIS.keys())
    usage = (
              "Usage: CLIENT_ID=<client_id> "
              "CLIENT_SECRET=<secret> "
              "%s %s \"scopes\" [grant_name]"
            ) % (args[0], environments)

    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if client_id == None or client_secret == None:
        raise SystemExit(usage)

    if len(args) < 3 or len(args) > 4 or args[1] not in AUTH_URIS.keys():
        raise SystemExit(usage)

    scopes = args[2]
    grant_name = args[3] if len(args) == 4 else 'Auto generated grant name'

    return {
        'environment': args[1],
        'grant_name': grant_name,
        'scopes': scopes,
        'client_id': client_id,
        'client_secret': client_secret
    }


def main():
    args = parse_args(sys.argv)
    tokens = get_api_tokens(args['client_id'],
                            args['client_secret'],
                            args['environment'],
                            args['scopes'],
                            args['grant_name'])
    display_tokens(tokens)


if __name__ == "__main__":
    main()
