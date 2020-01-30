import sys
import requests

APP_TEMPLATE_IDS = {
    'Production': 'f340796d-d2b8-4957-a544-0eaa3716c5f7',
    'Preview': 'bdbaaf2c-2925-401e-8ce8-c2b3fe6491e0',
    'Staging': 'd5e6a0c7-2540-4421-a961-eaf454e8f6b5',
    'Test': 'a8398609-32fa-4f3f-bad5-b9b9717ff64f',
    'Integration': '9e995b15-be2f-444a-b242-e8d2e10c15ec',
    'Sandbox': '556229e7-4823-41d8-8203-83a12ae4ff10'
}


AUTH_URIS = {
    'Production': 'https://auth.globus.org',
    'Preview': 'https://auth.preview.globus.org',
    'Staging': 'https://auth.staging.globuscs.info',
    'Test': 'https://auth.test.globuscs.info',
    'Integration': 'https://auth.integration.globuscs.info',
    'Sandbox': 'https://auth.sandbox.globuscs.info'
}


def display_app_client(app_client):
    app_credentials = app_client['included']['client_credential']

    msg = {
        'client': app_credentials['client'],
        'secret': app_credentials['secret']
    }

    print(msg)


def create_app_client(environment, client_name):
    template_id = APP_TEMPLATE_IDS[environment]
    auth_uri = AUTH_URIS[environment]

    data = {
        'client': {
            'template_id': template_id,
            'name': client_name
        }
    }

    r = requests.post(auth_uri+'/v2/api/clients', json=data)
    return r.json()


def parse_args(args):
    environments = '|'.join(APP_TEMPLATE_IDS.keys())
    usage = "Usage: %s {environments} [client_name]" % args[0]

    if len(args) < 2 or len(args) > 3 or args[1] not in APP_TEMPLATE_IDS.keys():
        raise SystemExit(usage)

    name = args[2] if len(args) == 3 else 'Auto generated Globus Auth client'

    return {
        'environment': args[1],
        'name': name
    }


def main():
    args = parse_args(sys.argv)
    app = create_app_client(args['environment'], args['name'])
    display_app_client(app)


if __name__ == "__main__":
    main()
