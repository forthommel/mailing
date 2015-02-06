#!/usr/bin/python

# -*- encoding: utf-8 -*-
#
# Service fetching all new mails on a given account
#
# L. Forthomme, Jul 2014

import argparse
import ConfigParser

from modules.dbutil import db
from modules.mailutil import read, write

def main(argv):
    database = db.db('mails.db')
    config = ConfigParser.ConfigParser()
    config.read(argv.config)

    infos = {'username':         config.get('mailaccount', 'incoming_username'),
             'out_username':     config.get('mailaccount', 'outgoing_username'),
             'password':         config.get('mailaccount', 'password'),
             'reply_to_address': config.get('mailaccount', 'reply_to_address'),
             'in_server':        config.get('mailserver', 'incoming_host'),
             'in_port':          config.get('mailserver', 'incoming_port'),
             'out_server':       config.get('mailserver', 'outgoing_host'),
             'out_port':         config.get('mailserver', 'outgoing_port')}

    me = {'name': 'Laurent Forthomme', 'email':'forthomme@apinc.org', 'password':'$2a$12$lsRp8oDjNl9BVHX8d0b8.eCJd45/aRbVH8zNK.qCaNsgswgWkzZ7C'}
    database.add_user(me)

    read.fetch_mails(infos, database)
    if database.buffer_size():
        writer = write.write(infos)
        writer.send_mails_in_buffer(database)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Process checking the arrival of new mails in the list')
    parser.add_argument('config', type=str, default='default.cfg', help='Configuration file for the running environment')
    args = parser.parse_args()

    main(args)
