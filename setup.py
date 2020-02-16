import sys
import utils.yaml as yaml
import utils.tokens as tokens
import utils.identities as identities
import utils.clients as clients


def _is_client_valid(environment, client_id, client_secret):
    if client_id is None or client_secret is None:
        return False

    resp = clients.get_client(client_id, client_secret, environment, client_id)
    if 'client' not in resp:
        return False
    if 'id' not in resp['client']:
        return False

    return resp['client']['id'] == client_id
 
#####################################################################
#
#  ACCESS TOKEN PROCESSING
#
#####################################################################


def _lookup_identity_username(client_id, client_secret, environment, username):
    resp = identities.lookup_identities(client_id,
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

def _process_access_tokens(config, environment):
    requested_tokens = yaml.get_key_value(config, '__tokens__')
    if requested_tokens is None:
        return

    for index, token_request in enumerate(requested_tokens):
        scopes = token_request['scopes']
        scope_names = list(map(lambda x: x['name'], scopes))
        grant_type = token_request['grant_type']
        client_id = token_request['client']['id']
        client_secret = token_request['client']['secret']

        if token_request['grant_type'] == 'authorization_code':
            kwargs = _get_auth_grant_options(token_request, environment)
            t = tokens.authorization_grant(token_request['client']['id'],
                                           token_request['client']['secret'],
                                           environment,
                                           scope_names,
                                           **kwargs)
        elif token_request['grant_type'] == 'client_credentials':
            t = tokens.credentials_grant(token_request['client']['id'],
                                         token_request['client']['secret'],
                                         environment,
                                         scope_names)


        token_map = {}
        for t in t.pop('other_tokens') + [t]:
            i = tokens.introspect_token(token_request['client']['id'],
                                        token_request['client']['secret'],
                                        environment,
                                        t['access_token'])
            t['introspect'] = i
            token_map[t['resource_server']] = t

        yaml.set_key_value(config,
                           '__tokens__.'+str(index)+'.tokens',
                           token_map)


#####################################################################
#
#  NATIVE APP PROCESSING
#
#####################################################################

def _is_native_app_defined(path):
    native_app = yaml.get_key_value(path, '__native_app__')
    if native_app is None:
        return False

    if native_app.get('id', None) is None:
        return False
    if native_app.get('secret', None) is None:
        return False

    return True


def _process_native_app(config, environment):
    if _is_native_app_defined(config):
        id = yaml.get_key_value(config, '__native_app__.id')
        secret = yaml.get_key_value(config, '__native_app__.secret')
        if _is_client_valid(environment, id, secret):
            return

    client = clients.create_client(environment)

    app_id = client['included']['client_credential']['client']
    app_secret = client['included']['client_credential']['secret']

    yaml.set_key_value(config, '__native_app__.id',     app_id)
    yaml.set_key_value(config, '__native_app__.secret', app_secret)


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
        'environment' : yaml.get_key_value(args[1], 'globus_environment')
    }


def main():
    args = _parse_args(sys.argv)

    _process_native_app(**args)
    _process_access_tokens(**args)


if __name__ == "__main__":
    main()

