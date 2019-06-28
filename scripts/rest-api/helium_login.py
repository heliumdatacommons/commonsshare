import requests
import json
import os
import time
import argparse
import sys
import six

base_url = 'https://test.commonsshare.org'
def login():
    resp1 = requests.get(base_url + '/authorize?provider=auth0&scope=openid%20email%20profile')
    print (resp1.status_code)
    if resp1.status_code != 200:
        raise RuntimeError('Failed to acquire login url')
    else:
        body = json.loads(resp1.content.decode('utf-8'))
        if 'authorization_url' not in body or 'nonce' not in body:
            raise RuntimeError('Improperly formatted response on initialization')
        print('Please log in with following URL:\n{}\n'.format(body['authorization_url']))

        max_wait = 60 
        interval = 3
        token_url = base_url + '/token?nonce=' + body['nonce']
        success = False
        for i in range(int(max_wait/interval)):
            resp2 = requests.get(token_url)
            if resp2.status_code == 200:
                body = json.loads(resp2.content.decode('utf-8'))
                if 'access_token' not in body or 'user_name' not in body:
                    raise RuntimeError('Improperly formatted response on token retrieval')
                print('Detected login for user: {}'.format(body['user_name']))
                inp = ''
                while inp.lower() not in ['y', 'n']:
                    inp = six.moves.input('Is this the correct identity you wish to use? (y/n) ')
                if inp == 'n':
                    print('Please log out of the Helium and Globus in your '
                        + 'browser and re-run this script to log in with a different account.')
                    return
                print('Access Token:')
                print(body['access_token'])
                success = True
                break
            time.sleep(interval)
        if not success:
            print('Failed to login within timeout window')

def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Authenticate to the Helium Data Commons Stack')
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    login_parser = subparsers.add_parser('login', help='Login')

    args = parser.parse_args(argv[1:])
    if args.subcommand == 'login':
        login()


if __name__ == '__main__':
    main(sys.argv)
