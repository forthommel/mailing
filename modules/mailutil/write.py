#!/usr/bin/python

import smtplib
import email
import email.parser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import mimetools

def send_registration_confirmation(email, name=None, registration_code=None):
    print 'aa'

def send_mails_in_buffer(server_infos, db_mails, db_users):
    if 'out_server' not in server_infos: return False
    if 'out_port' not in server_infos: return False
    if 'username' not in server_infos: return False
    if 'password' not in server_infos: return False
    if 'out_username' not in server_infos:
        server_infos['out_username'] = server_infos['username']
    if 'reply_to_address' not in server_infos:
        server_infos['reply_to_address'] = None

    for mail in db_mails.get_mails_in_buffer(db_users):
        email_from = formataddr((mail['from_name'], mail['from_email']))
        #send_one_mail(server_infos, email_from=email_from, email_to=mail['to'], subject=mail['subject'], content=mail['content'], date=mail['date'])
        if send_one_mail(server_infos, email_from=email_from, email_to=mail['to'], content=mail['content'], reply_to=server_infos['reply_to_address']):
            db_mails.mark_mail_as_sent(mail['id'])
    
def send_one_mail(server_infos, email_from, email_to, content, reply_to=None):
    server = smtplib.SMTP(server_infos['out_server'], server_infos['out_port'])
    try:
        server.login(server_infos['out_username'], server_infos['password'])
    except smtplib.SMTPAuthenticationError:
        print '[send_one_mail] ERROR: unable to login on the SMTP server'
        return False
    msg = email.parser.Parser().parsestr(content.encode('utf-8'))
    if reply_to is not None:
        msg['Reply-to'] = reply_to
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()

    print "-> E-mail sent from %s to %s" % (email_from, email_to)

    return True

def send_one_mail_with_header(server_infos, email_from, email_to, subject, content, date):

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
    
    server = smtplib.SMTP(server_infos['out_server'], server_infos['out_port'])
    try:
        server.login(server_infos['out_username'], server_infos['password'])
    except smtplib.SMTPAuthenticationError:
        print '[send_one_mail] ERROR: unable to login on the SMTP server'
        return False
    #####server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

    print "-> E-mail sent from %s (%s) to %s on %s" % (email_from, name_from, email_to, date)
    return True
