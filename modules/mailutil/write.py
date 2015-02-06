#!/usr/bin/python

import smtplib
import email
import email.parser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import mimetools

class write:
    def __init__(self, server_infos):
        if 'out_server' not in server_infos: return False
        if 'out_port' not in server_infos: return False
        if 'username' not in server_infos: return False
        if 'password' not in server_infos: return False
        if 'out_username' not in server_infos:
            server_infos['out_username'] = server_infos['username']
        if 'reply_to_address' not in server_infos:
            server_infos['reply_to_address'] = None

        self.server_infos = server_infos
        self.server = smtplib.SMTP(self.server_infos['out_server'], self.server_infos['out_port'])
        try:
            self.server.login(self.server_infos['out_username'], self.server_infos['password'])
        except smtplib.SMTPAuthenticationError:
            print '[send_one_mail] ERROR: unable to login on the SMTP server'
            return False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.server.quit()
    
    def send_mails_in_buffer(self, db):
        for mail in db.get_mails_in_buffer():
            email_from = formataddr((mail['from_name'], mail['from_email']))
            if self.send_one_mail(email_from=email_from, email_to=mail['to'], content=mail['content']):
                db.mark_mail_as_sent(mail['id'])
    
    def send_one_mail(self, email_from, email_to, content):
        msg = email.parser.Parser().parsestr(content.encode('utf-8'))
        #if self.server_infos['reply_to_address'] is not None:
        #    msg['Reply-to'] = self.server_infos['reply_to_address']
        #msg['In-Reply-To'] = 
        #FIXME need to figure out whether this is required or not
        self.server.sendmail(email_from, email_to, msg.as_string())
        print "-> E-mail sent from %s to %s" % (email_from, email_to)
        return True

    def send_one_mail_with_header(self, email_from, email_to, subject, content, date):
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = formataddr((name_from, email_from))
        msg['To'] = email_to
        msg.preamble = 'This is a multi-part message in MIME format.'

        msg_content = MIMEMultipart('alternative')
        msg.attach(msg_content)
        if '<html>' in content:
            msg_content.attach(MIMEText(content.encode('utf-8'), 'html', 'utf-8'))
            print 'Mail is html'
        else:
            msg_content.attach(MIMEText(content.encode('utf-8'), 'plain', 'utf-8'))
            print 'Mail is plain'
    
        #####server.sendmail(msg['From'], msg['To'], msg.as_string())

        print "-> E-mail sent from %s (%s) to %s on %s" % (email_from, name_from, email_to, date)
        return True
