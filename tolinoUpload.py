#!/usr/bin/env python3
# Copyright (C) 2022 tobexyz
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import requests
import argparse
import sys
import yaml
import logging
from pprint import pformat

class TolinoException(Exception):
    pass


config_file = "~/.config.yaml" 

partner_settings = {
    3: {
        # Thalia.de
        'client_id'        : 'webreader',    
        'scope'            : 'SCOPE_BOSH',
        'token_url'        : 'https://thalia.de/auth/oauth2/token',
        'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description='cmd line client to access personal tolino cloud storage space.'
    )
    parser.add_argument('--config', metavar='FILE', default='~/.config.yaml', help='config file (default: .config.yaml)')
    parser.add_argument('--client', type=str, help='name of client in config file')
    parser.add_argument('--debug', action="store_true", default= False, help='log additional debugging info') 
    parser.add_argument('--filename', metavar='FILE', help = 'file to upload')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)         
    if args.config:
        global config_file
        config_file = args.config 
    if not args.client:
        print('name of client required!')
        parser.print_help()
        sys.exit(1)         
    if not args.filename:
        print('filename required!')
        parser.print_help()
        sys.exit(1)     
    session = requests.session()
    update_tokens(session, args.client)
    print(upload(session, args.client, args.filename))

def debug(response):
    if logging.getLogger().getEffectiveLevel() >= logging.DEBUG:
        logging.debug('-------------------- HTTP response --------------------')
        logging.debug('status code: {}'.format(response.status_code))
        logging.debug('cookies: {}'.format(pformat(response.cookies)))
        logging.debug('headers: {}'.format(pformat(response.headers)))
        try:
            j = response.json()
            logging.debug('json: {}'.format(pformat(j)))
        except:
            logging.debug('text: {}'.format(response.text))
        logging.debug('-------------------------------------------------------')


def update_tokens(session, client_name):
    config = read_config()
    partner_setting = partner_settings[config['client'][client_name]['partner_id']]
    logging.debug(config)
    payload = {
        'client_id'    : partner_setting['client_id'],
        'grant_type'   : 'refresh_token',
        'refresh_token': config['client'][client_name]['tokens']['refresh_token'],                
    }
    headers= {
        'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    logging.debug(payload)
    response =  session.post(partner_setting['token_url'], data=payload, headers= headers, verify=True, allow_redirects=True)
    debug(response)
    try:
        body = response.json()
        config['client'][client_name]['tokens']['access_token'] = body['access_token']
        config['client'][client_name]['tokens']['refresh_token'] = body['refresh_token']
    except:
        raise TolinoException('oauth token request failed.')
    write_config(config)


def read_config():
    with open(config_file,'r') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
        config = yaml.load(file, Loader=yaml.FullLoader)
        return config

def write_config(config):
    with open(config_file,'w') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
        yaml.dump(data=config,stream=file,  sort_keys=True)
        


def upload(session,client_name, filename):
    config = read_config()
    partner_setting = partner_settings[config['client'][client_name]['partner_id']]
    logging.debug(config)
    name = filename.split('/')[-1]
    ext = filename.split('.')[-1]    
    mime = {
        'pdf'  : 'application/pdf',
        'epub' : 'application/epub+zip'
    }.get(ext.lower(), 'application/pdf')
    headers= {
        'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
        't_auth_token' : config['client'][client_name]['tokens']['access_token'],
        'hardware_id'  : config['client'][client_name]['hardware_id'],
        'reseller_id'  : str(config['client'][client_name]['partner_id'])
    }
    response = session.post(partner_setting['upload_url'],
        files = [('file', (name, open(filename, 'rb'), mime))],
        headers = headers
    )
    debug(response)
    if response.status_code != 200:
        raise TolinoException('file upload failed.')

    try:
        body = response.json()
        return body['metadata']['deliverableId']
    except:
        raise TolinoException('file upload failed.')


if __name__ == '__main__':
    main()

