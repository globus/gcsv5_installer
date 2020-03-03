import sys
import utils.yaml as Yaml
import utils.tokens as Tokens
import utils.identities as Identities
import utils.clients as Clients


#####################################################################
#
#  ACCESS TOKEN PROCESSING
#
#####################################################################


def _lookup_identity_username(client_id, client_secret, environment, username):
    resp = Identities.lookup_identities(client_id,
                                        client_secret,
                                        environment,
                                        [username])
    for i in resp['identities']:
        if i['username'] == username:
            return i['id']


def _lookup_identity_id(client_id, client_secret, environment, _id):
    return _id


def _lookup_identity(client_id, client_secret, environment, id_or_username):
    if '@' not in id_or_username:
        return _lookup_identity_id(client_id,
                                   client_secret,
                                   environment,
                                   id_or_username)

    return _lookup_identity_username(client_id,
                                     client_secret,
                                     environment,
                                     id_or_username)


def _get_auth_grant_options(token, environment):
    options = {}

    # need_refresh_token: default True
    v = token.get('access_type', 'offline')
    options['need_refresh_token'] = True if v == 'offline' else False

    if 'session' in token:
        # session_identities: default []
        options['session_identities'] = []
        ids = token['session'].get('required_identities')

        if ids is not None:
            for index, _id in enumerate(ids):
                i = _lookup_identity(token['client']['id'],
                                     token['client']['secret'],
                                     environment,
                                     _id)

                options['session_identities'].append(i)

        # session_force_login: default False
        if 'prompt_login' in token['session']:
            options['session_force_login'] = True if token['session']['prompt_login'] is True else False

    return options


def _try_refresh_token(client, environment, token):
    if not 'refresh_token' in token:
        return None

    # Revoke the access token, if it exists
    if token.get('access_token') is not None:
        Tokens.revoke_token(client['id'],
                            client['secret'],
                            environment,
                            token.get('access_token'))
        token['access_token'] = None

    # Refresh the access token
    new_token = Tokens.refresh_token(client['id'],
                                     client['secret'],
                                     environment,
                                     token.get('refresh_token'))
    if 'access_token' not in new_token:
        return None
    if 'expires_in' not in new_token:
        return None
    return new_token


def _is_token_valid(client, environment, token):
    if token is None:
        return False

    if 'access_token' not in token:
        return False

    i = Tokens.introspect_token(client['id'],
                                client['secret'],
                                environment,
                                token['access_token'])

    if i is None:
        return False
    return i.get('active', False)


def _salvage_token_map(environment, token_request):
    token_map = token_request.get('tokens')
    if token_map is None:
        return None

    for token in token_map.values():
        new_token = _try_refresh_token(token_request['client'], environment, token)
        if new_token is not None:
            token['access_token'] = new_token['access_token']
            token['expires_in']   = new_token['expires_in']
            continue

        if not _is_token_valid(token_request['client'], environment, token):
            return None
    return token_map


def _create_token_map(environment, token_request):
    scopes = token_request['scopes']
    scope_names = list(map(lambda x: x['name'], scopes))
    grant_type = token_request['grant_type']
    client_id = token_request['client']['id']
    client_secret = token_request['client']['secret']

    if token_request['grant_type'] == 'authorization_code':
        kwargs = _get_auth_grant_options(token_request, environment)
        t = Tokens.authorization_grant(token_request['client']['id'],
                                       token_request['client']['secret'],
                                       environment,
                                       scope_names,
                                       **kwargs)
    elif token_request['grant_type'] == 'client_credentials':
        t = Tokens.credentials_grant(token_request['client']['id'],
                                     token_request['client']['secret'],
                                     environment,
                                     scope_names)

    token_map = {}
    for t in t.pop('other_tokens') + [t]:
        i = Tokens.introspect_token(token_request['client']['id'],
                                    token_request['client']['secret'],
                                    environment,
                                    t['access_token'])
        t['introspect'] = i
        token_map[t['resource_server']] = t
    return token_map


def _generate_token_map(environment, token_request):
    token_map = _salvage_token_map(environment, token_request)
    if token_map is not None and len(token_map.keys()) > 0:
        return token_map
    return _create_token_map(environment, token_request)


def _process__tokens__(config, environment):
    # Nothing to do if __tokens__ is not defined
    requested_tokens = Yaml.get_key_value(config, '__tokens__')
    if requested_tokens is None:
        return

    # For each token_request 
    for index, token_request in enumerate(requested_tokens):
        token_map = _generate_token_map(environment, token_request)
        Yaml.set_key_value(config,
                           '__tokens__.'+str(index)+'.tokens',
                           token_map)


#####################################################################
#
#  NATIVE APP PROCESSING
#
#####################################################################

def _is_native_app_defined(path):
    native_app = Yaml.get_key_value(path, '__native_app__')
    if native_app is None:
        return False

    if native_app.get('id', None) is None:
        return False
    if native_app.get('secret', None) is None:
        return False

    return True


def _is_client_valid(environment, client_id, client_secret):
    if client_id is None or client_secret is None:
        return False

    resp = Clients.get_client(client_id, client_secret, environment, client_id)
    if 'client' not in resp:
        return False
    if 'id' not in resp['client']:
        return False

    return resp['client']['id'] == client_id
 

def _process__native_app__(config, environment):
    if _is_native_app_defined(config):
        id = Yaml.get_key_value(config, '__native_app__.id')
        secret = Yaml.get_key_value(config, '__native_app__.secret')
        if _is_client_valid(environment, id, secret):
            return

    client = Clients.create_client(environment)

    app_id = client['included']['client_credential']['client']
    app_secret = client['included']['client_credential']['secret']

    Yaml.set_key_value(config, '__native_app__.id',     app_id)
    Yaml.set_key_value(config, '__native_app__.secret', app_secret)


#####################################################################
#
#  MAIN FUNCTIONS
#
#####################################################################


def _parse_args(args):
    usage = "Usage: %s <config>" % args[0]

    if len(args) != 2:
        raise SystemExit(usage)

    return {
        'config'      : args[1],
        'environment' : Yaml.get_key_value(args[1], 'globus_environment')
    }


def main():
    args = _parse_args(sys.argv)

    _process__native_app__(**args)
    _process__tokens__(**args)


if __name__ == "__main__":
    main()

