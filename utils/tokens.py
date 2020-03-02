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


def _get_long_option(args, option_name, requires_value):
    found = False
    value = None

    for i in range(len(args)):
        if args[i] == option_name:
            if requires_value:
                if i == (len(args)-1):
                    raise SystemError(option_name + ' requires a value')
                value = args.pop(i+1)
            found = True
            del args[i]
            break
    return (args, found, value)


###################################################################
#
#  AUTHORIZATION CODE GRANT FUNCTIONS
#
###################################################################

def authorization_grant_build_url(client_id,
                                  environment,
                                  scopes,
                                  need_refresh_token = True,
                                  prefill_grant_name = None,
                                  session_identities = [],
                                  session_message = None,
                                  session_force_login = False,
                                  redirect_uri = None,
                                  force_new_session = False
):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'access_type'       : 'offline' if need_refresh_token else 'online',
        'client_id'         : client_id,
        'response_type'     : 'code',
        'scope'             : ' '.join(scopes),
        'state'             : '_default'
    }

    if prefill_grant_name is not None:
        payload['prefill_grant_name'] = prefill_grant_name

    if len(session_identities) > 0:
        payload['session_required_identities'] = ','.join(session_identities)

    if session_message is not None:
        payload['session_message'] = session_message

    if session_force_login:
        payload['prompt'] = 'login'

    if redirect_uri is None:
        redirect_uri = auth_uri+'/v2/web/auth-code'
    payload['redirect_uri'] = redirect_uri

    authorize_url = auth_uri + '/v2/oauth2/authorize?' + urlencode(payload)

    if force_new_session == True:
        payload = {
            'redirect_uri'  : authorize_url,
            'redirect_name' : 'Continue for authorization flow'
        }
        authorize_url = auth_uri + '/v2/web/logout?' + urlencode(payload)

    return authorize_url


def authorization_grant_prompt_user(url):
    directions = "FOLLOW THIS LINK AND PASTE IN THE AUTHORIZATION CODE:"
    with open("/dev/tty", "wb+", buffering=0) as term:
        term.write("\n".encode())
        term.write(directions.encode())
        term.write("\n".encode())
        term.write(b"="*len(directions) + b"\n")
        term.write(url.encode())
        term.write("\n".encode())
        term.write("\n".encode())
        term.write('Enter the authorization code: '.encode())
    return input()


def authorization_grant_get_token(client_id,
                                  client_secret,
                                  environment,
                                  authorization_code,
                                  redirect_uri = None
):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'code'       :  authorization_code,
        'grant_type' : 'authorization_code'
    }

    if redirect_uri is None:
        redirect_uri = auth_uri + '/v2/web/auth-code'
    payload['redirect_uri'] = redirect_uri

    r = requests.post(auth_uri + '/v2/oauth2/token',
                      data=payload, 
                      auth=(client_id, client_secret))
    return r.json()


def authorization_grant(client_id,
                        client_secret,
                        environment,
                        scopes,
                        user_prompt_func = authorization_grant_prompt_user,
                        need_refresh_token = True,
                        prefill_grant_name = None,
                        session_identities = [],
                        session_message = None,
                        session_force_login = False,
                        redirect_uri = None,
                        force_new_session = False
):

    url = authorization_grant_build_url(client_id,
                                        environment,
                                        scopes,
                                        need_refresh_token,
                                        prefill_grant_name,
                                        session_identities,
                                        session_message,
                                        session_force_login,
                                        redirect_uri,
                                        force_new_session)

    code = user_prompt_func(url)

    token = authorization_grant_get_token(client_id,
                                          client_secret,
                                          environment,
                                          code,
                                          redirect_uri)
    return token


def _authorization_main(args0, cmd, args):
    usage = "Some useful usage message"

    client_id = os.environ.get('CLIENT_ID')
    if client_id is None:
        raise SystemExit(usage)

    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret is None:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    if len(args) == 0:
        raise SystemExit(usage)
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)

    option_list = [        # Requires value # Defaults
        ('session-force-login', False),     #   False
        ('force-new-session',   False),     #   False
        ('need-refresh-token',  False),     #   True
        ('prefill-grant-name',  True),      #   None
        ('session-identities',  True),      #   []
        ('session-message',     True),      #   None
        ('redirect-uri',        True)       #   None
    ]

    kwargs = {'need_refresh_token': False}
    for o in option_list:
        (args, found, value) = _get_long_option(args, '--'+o[0], o[1])

        if found:
            kwargs.update({o[0].replace('-', '_'): value if o[1] else True})

    if len(args) == 1:
        raise SystemExit(usage)
    scopes = args[1:]

    token = authorization_grant(client_id,
                                client_secret,
                                environment,
                                scopes,
                                **kwargs)

    print ("="*60)
    print (token)
    print ("="*60)


###################################################################
#
#  CLIENT CREDENTIALS GRANT FUNCTIONS
#
###################################################################


def credentials_grant(client_id, client_secret, environment, scopes):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'scope': ' '.join(scopes),
        'grant_type': 'client_credentials'
    }

    r = requests.post(auth_uri+'/v2/oauth2/token',
                      data=payload, 
                      auth=(client_id, client_secret))

    return r.json()


def _credentials_main(args0, cmd, args):
    usage = "Some useful usage message"

    client_id = os.environ.get('CLIENT_ID')
    if client_id is None:
        raise SystemExit(usage)

    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)
    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    scopes = args[1:]

    token = credentials_grant(client_id, client_secret, environment, scopes)

    print ("="*60)
    print (token)
    print ("="*60)


###################################################################
#
#  REFRESH TOKEN GRANT FUNCTIONS
#
###################################################################


def refresh_token(client_id, client_secret, environment, token):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'refresh_token':  token,
        'grant_type'   : 'refresh_token'
    }

    r = requests.post(auth_uri + '/v2/oauth2/token',
                      data=payload, 
                      auth=(client_id, client_secret))

    return r.json()


def _refresh_main(args0, cmd, args):
    usage = "Some useful usage message"

    client_id = os.environ.get('CLIENT_ID')
    if client_id is None:
        raise SystemExit(usage)

    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    token = args[1]

    token = refresh_token(client_id, client_secret, environment, token)
    print ("="*60)
    print (token)
    print ("="*60)


###################################################################
#
#  REVOKE TOKEN FUNCTIONS
#
###################################################################


def revoke_token(client_id, client_secret, environment, token):
    auth_uri = AUTH_URIS[environment]

    payload = { 'token': token }

    r = requests.post(auth_uri + '/v2/oauth2/token/revoke',
                      data=payload, 
                      auth=(client_id, client_secret))

    return r.json()


def _revoke_main(args0, cmd, args):
    usage = "Some useful usage message"

    client_id = os.environ.get('CLIENT_ID')
    if client_id is None:
        raise SystemExit(usage)

    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    token = args[1]

    resp = revoke_token(client_id, client_secret, environment, token)
    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  INTROSPECT TOKEN FUNCTIONS
#
###################################################################

def introspect_token(client_id, client_secret, environment, token):
    auth_uri = AUTH_URIS[environment]

    payload = {
        'token': token,
        'include': 'identities_set,session_info'
    }

    r = requests.post(auth_uri + '/v2/oauth2/token/introspect',
                      data=payload, 
                      auth=(client_id, client_secret))

    return r.json()


def _introspect_main(args0, cmd, args):
    usage = "Some useful usage message"

    client_id = os.environ.get('CLIENT_ID')
    if client_id is None:
        raise SystemExit(usage)

    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    token = args[1]

    resp = introspect_token(client_id, client_secret, environment, token)
    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  MAIN FUNCTIONS
#
###################################################################

def _parse_args(args):
    cmds = ['authorization','credentials','refresh','revoke','introspect']

    usage = (
              "Usage: %s [authorization|credentials|refresh|revoke|introspect]"
            ) % (args[0])

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
