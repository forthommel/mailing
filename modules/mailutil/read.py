#!/usr/bin/python

# -*- coding: utf-8 -*-

import imaplib
import email
import dateutil.parser
import email.parser
import email.utils
import email.header
#import quopri
import codecs

def fetch_mails(infos, db):
    if 'in_server' not in infos: return False
    if 'in_port' not in infos: return False
    if 'username' not in infos: return False
    if 'password' not in infos: return False
    print infos

    conn = imaplib.IMAP4(infos['in_server'], infos['in_port'])
    conn.login(infos['username'], infos['password'])
    conn.select(mailbox='INBOX', readonly=False)
    typ, data = conn.search(None,'(NOT SEEN)')
    for num in data[0].split():
        typ, content = conn.fetch(num,'(RFC822)')
        header = email.parser.HeaderParser().parsestr(content[0][1])
        from_tuple = email.utils.parseaddr(header['From'])
        mail = {'date': dateutil.parser.parse(header['Date']),
                'name': from_tuple[0],
                'email': from_tuple[1],
                'subject': header['Subject'],
                'content': u''}

        mail['content'] = email.header.decode_header(content[0][1])[0][0]
        if not db.add_mail_in_buffer(mail): # mail is marked as not seen, since the user sending it was not identified
            typ, data = conn.store(num,'-FLAGS','\\Seen')
    return True
            
