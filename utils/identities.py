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


def lookup_usernames(client_id, client_secret, environment, usernames):
    # GET /v2/api/identities?usernames=<list-of-identity-names>
    auth_uri = AUTH_URIS[environment]
    payload = {
        'usernames': ','.join(usernames)
    }
    r = requests.get(auth_uri+'/v2/api/identities',
                     params=payload,
                     auth=(client_id, client_secret))

    return r.json()

def lookup_ids(client_id, client_secret, environment, ids):
    # GET /v2/api/identities?ids=<list-of-identity-ids>
    auth_uri = AUTH_URIS[environment]
    payload = {
        'ids': ','.join(ids)
    }
    r = requests.get(auth_uri+'/v2/api/identities',
                     params=payload,
                     auth=(client_id, client_secret))

    return r.json()

def lookup_identities(client_id, client_secret, environment, identities):
    if '@' in identities[0]:
        return lookup_usernames(client_id,
                                client_secret, 
                                environment, 
                                identities)

    return lookup_ids(client_id, client_secret, environment, identities)

def _parse_args(args):
    environments = '|'.join(AUTH_URIS.keys())
    usage = (
              "Usage: CLIENT_ID=<client_id> "
              "CLIENT_SECRET=<secret> "
              "%s %s usernames_or_ids"
            ) % (args[0], environments)

    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if client_id == None or client_secret == None:
        raise SystemExit(usage)

    if len(args) < 3 or args[1] not in AUTH_URIS.keys():
        raise SystemExit(usage)

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'environment': args[1],
        'identities': args[2:]
    }



def main():
    args = _parse_args(sys.argv)

    result = lookup_identities(**args)
    print (result)

if __name__ == "__main__":
    main()
