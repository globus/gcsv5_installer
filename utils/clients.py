import os
import sys
import requests

APP_TEMPLATE_IDS = {
    'Production'  : 'f340796d-d2b8-4957-a544-0eaa3716c5f7',
    'Preview'     : 'bdbaaf2c-2925-401e-8ce8-c2b3fe6491e0',
    'Staging'     : 'd5e6a0c7-2540-4421-a961-eaf454e8f6b5',
    'Test'        : 'a8398609-32fa-4f3f-bad5-b9b9717ff64f',
    'Integration' : '9e995b15-be2f-444a-b242-e8d2e10c15ec',
    'Sandbox'     : '556229e7-4823-41d8-8203-83a12ae4ff10'
}


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
#  CREATE CLIENT FUNCTIONS
#
###################################################################


def create_client(environment, client_name=None, template_id=None):

    if client_name is None:
        client_name = 'Auto generated Globus Auth client'
    if template_id is None:
        template_id = APP_TEMPLATE_IDS[environment]
    auth_uri = AUTH_URIS[environment]

    data = {
        'client': {
            'template_id' : template_id,
            'name'        : client_name
        }
    }

    r = requests.post(auth_uri + '/v2/api/clients', json=data)
    return r.json()


def _create_main(args0, cmd, args):
    usage = (
                 "Usage: %s %s environment [client_name] [--template-id <id>]" 
                 % (args0, '|'.join(APP_TEMPLATE_IDS.keys()))
            )

    (args, found, template_id) = _get_long_option(args, '--template-id', True)

    if len(args) < 1 or len(args) > 2 or args[0] not in APP_TEMPLATE_IDS.keys():
        raise SystemExit(usage)

    environment = args[0]
    client_name = args[1] if len(args) == 2 else None

    resp = create_client( environment, client_name, template_id)

    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  GET CLIENT FUNCTIONS
#
###################################################################


def get_client(auth_client_id,
               auth_client_secret, 
               environment, 
               target_client_id
):
    auth_uri = AUTH_URIS[environment]
    url = auth_uri + '/v2/api/clients/%s' % target_client_id
    r = requests.get(url, auth=(auth_client_id, auth_client_secret))
    return r.json()


def _get_main(args0, cmd, args):
    usage = "Some useful usage message"

    auth_client_id = os.environ.get('CLIENT_ID')
    if auth_client_id is None:
        raise SystemExit(usage)

    auth_client_secret = os.environ.get('CLIENT_SECRET')
    if auth_client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    target_client_id = args[1]

    resp = get_client(
               auth_client_id, 
               auth_client_secret, 
               environment, 
               target_client_id)

    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  DELETE CLIENT FUNCTIONS
#
###################################################################


def delete_client(auth_client_id,
                  auth_client_secret, 
                  environment, 
                  target_client_id
):
    auth_uri = AUTH_URIS[environment]
    url = auth_uri + '/v2/api/clients/%s' % target_client_id
    r = requests.delete(url, auth=(auth_client_id, auth_client_secret))
    return r.json()


def _delete_main(args0, cmd, args):
    usage = "Some useful usage message"

    auth_client_id = os.environ.get('CLIENT_ID')
    if auth_client_id is None:
        raise SystemExit(usage)

    auth_client_secret = os.environ.get('CLIENT_SECRET')
    if auth_client_secret is None:
        raise SystemExit(usage)

    if len(args) != 2:
        raise SystemExit(usage)

    environments = '|'.join(AUTH_URIS.keys())
    environment = args[0]
    if environment not in environments:
        raise SystemExit(usage)
    target_client_id = args[1]

    resp = delete_client(
               auth_client_id, 
               auth_client_secret, 
               environment, 
               target_client_id)

    print ("="*60)
    print (resp)
    print ("="*60)


###################################################################
#
#  MAIN FUNCTIONS
#
###################################################################


def _parse_args(args):
    cmds = ['create','get','delete']

    usage = ( "Usage: %s [%s]") % (args[0], '|'.join(cmds))

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
