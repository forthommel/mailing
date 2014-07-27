#!/usr/bin/python

# -*- encoding: utf-8 -*-
#
# Service fetching all new mails on a given account
#
# L. Forthomme, Jul 2014

import argparse
import ConfigParser

from modules.dbutil import users, mails
from modules.mailutil import read, write

def main(argv):
    config = ConfigParser.ConfigParser()
    config.read(argv.config)

    database_users = users.users(config.get('general', 'users_database_location'))
    database_mails = mails.mails(config.get('general', 'mails_database_location'))
    infos = {'username':         config.get('mailaccount', 'incoming_username'),
             'out_username':     config.get('mailaccount', 'outgoing_username'),
             'password':         config.get('mailaccount', 'password'),
             'reply_to_address': config.get('mailaccount', 'reply_to_address'),
             'in_server':        config.get('mailserver', 'incoming_host'),
             'in_port':          config.get('mailserver', 'incoming_port'),
             'out_server':       config.get('mailserver', 'outgoing_host'),
             'out_port':         config.get('mailserver', 'outgoing_port')}

    me = {'name': 'Laurent Forthomme', 'email':'forthomme@apinc.org'}
    database_users.add_user(me)

    read.fetch_mails(infos, database_mails, database_users)
    write.send_mails_in_buffer(infos, database_mails, database_users)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Process checking the arrival of new mails in the list')
    parser.add_argument('config', type=str, default='default.cfg', help='Configuration file for the running environment')
    args = parser.parse_args()

    main(args)
