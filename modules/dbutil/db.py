# -*- coding: utf-8 -*-

from os.path import isfile, getsize
import sqlite3
import datetime
import dateutil.parser

class db:
    def __init__(self, path_):
        self.path = path_
        if not self.has_db():
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.path)
        self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    def close(self):
        self.conn.close()

    def has_db(self):
        if not isfile(self.path):
            return False
        if getsize(self.path)<100:
            hd = open(self.path, 'rb').read(100).close()
            if hd[0:16] != 'SQLite format 3\000':
                return False
        return True

    def add_mail_in_buffer(self, infos):
        if 'email' not in infos: return False
        if 'content' not in infos: return False
        if 'date' not in infos: return False
        c = self.conn.cursor()
        c.execute('SELECT id,name FROM user WHERE email="%s"' % infos['email'])
        ent = c.fetchone()
        if ent==None or len(ent)==0: # user in not registered in the system
            print '=> Unknown e-mail (%s) sent a mail on the list on %s' % (infos['email'], infos['date'])
            return False
        self.conn.cursor().execute('INSERT INTO buffer(date_arrival,account_id,subject,content) VALUES (?, ?, ?, ?)', (infos['date'], ent[0], infos['subject'], infos['content']))
        self.conn.commit()
        print '=> User "%s" (id=%i) sent a mail on %s' % (ent[1], ent[0], infos['date'])
        return True

    def add_user(self, infos):
        if 'email' not in infos: return False
        if 'name' not in infos: return False
        c = self.conn.cursor()
        c.execute('SELECT id,name FROM user WHERE email="%s"' % infos['email'])
        ent = c.fetchone()
        if ent==None or len(ent)==0: # user is not yet in the database
            if 'max_priority' in infos:
                self.conn.cursor().execute('''INSERT INTO user(email,name,max_priority) VALUES (?, ?, ?)''', (infos['email'], infos['name'], infos['max_priority']))
            else:
                self.conn.cursor().execute('''INSERT INTO user(email,name) VALUES (?, ?)''', (infos['email'], infos['name']))
            self.conn.commit()
            print '=> User "%s" with e-mail address "%s" was successfully added to the database!' % (infos['name'], infos['email'])
            return True
        print '=> User "%s" (id=%i) with e-mail address "%s" is already present in the database!' % (ent[1], ent[0], infos['email'])
        return False

    def check_user_password(self, mail_, password_):
        c = self.conn.cursor()
        c.execute('SELECT count(*) FROM user WHERE mail=? AND password=?', (mail_, password_))
        ent = c.fetchone()
        if ent==None or len(ent)==0: # authentication failed
            return False
        return True

    def get_salted_user_password(self, mail_):
        c = self.conn.cursor()
        c.execute('SELECT password FROM user WHERE mail=?', (mail_))
        ent = c.fetchone()
        if ent==None or len(ent)==0: # authentication failed
            return None
        return ent[0]

    def get_mails_in_buffer(self):
        out = []
        c = self.conn.cursor()
        priorities = {1: [], 2: [], 3: []}

        for account in c.execute('''SELECT id,email,max_priority FROM user ORDER BY max_priority'''):
            account_dict = {'id': account[0], 'email': account[1]}
            if account_dict not in priorities[account[2]]:
                priorities[account[2]].append(account_dict)

        for mail in c.execute('''SELECT buffer.id,
                                        buffer.date_arrival,
                                        user.email,
                                        user.name,
                                        buffer.priority,
                                        buffer.subject,
                                        buffer.content
                                 FROM buffer,user
                                 WHERE buffer.account_id==user.id'''):
            mail_id, arrival, email_from, name_from, mail_priority, mail_subject, mail_content = mail
            mail_priority = int(mail_priority)
            for account in priorities[mail_priority]:
                out.append({
                    'id': int(mail_id),
                    'from_email': email_from,
                    'from_name': name_from,
                    'to': account['email'],
                    'date': arrival,
                    'priority': mail_priority,
                    'subject': mail_subject,
                    'content': mail_content
                })
        return out

    def buffer_size(self):
        c = self.conn.cursor()
        c.execute('SELECT count(*) FROM buffer')
        ent = c.fetchone()
        if ent==None or len(ent)==0:
            return -1
        return int(ent[0])

    def mark_mail_as_sent(self, mail_id=None):
        if mail_id is None: return False
        c = self.conn.cursor()
        c.execute('SELECT date_arrival,account_id,priority,subject,content FROM buffer WHERE id=?', (str(mail_id)))
        ent = c.fetchone()
        if ent is None or len(ent)==0:
            return False
        
        subject_stripped = ent[3].replace("Re: ", "")
        thread_id = self.search_threads(subject_stripped)

        if thread_id==-1:
            thread_id = self.add_new_thread(subject_stripped, ent[0])

        self.conn.cursor().execute('''INSERT INTO mails(thread_id,account_id,priority,content,date_arrival) VALUES (?, ?, ?, ?, ?)''', (thread_id, ent[1], ent[2], ent[4], ent[0]))
        self.conn.cursor().execute('''DELETE FROM buffer WHERE id=?''', (str(mail_id)))
        self.conn.commit()
        return True

    def search_threads(self, subject):
        out_id = -1
        c = self.conn.cursor()
        search = subject+'%'
        print '''[search_threads] Looking for threads associated to subject "%s"''' % subject
        c.execute('''SELECT id FROM threads WHERE title LIKE ? ORDER BY date_creation DESC LIMIT 1''', (search,))
        thread_candidate = c.fetchone()
        if thread_candidate is None or len(thread_candidate)==0:
            return out_id;
        out_id = thread_candidate[0]
        if out_id!=-1:
            print '[search_threads] Thread "%s" was associated to thread %i already present in the database' % (subject, out_id)
        return out_id

    def add_new_thread(self, subject, date):
        self.conn.cursor().execute('INSERT INTO threads(title,date_creation) VALUES (?, ?)', (subject, date))
        self.conn.commit()
        print '=> New thread created on %s : %s' % (date, subject)
        return self.conn.cursor().execute('SELECT id FROM threads WHERE title=? AND date_creation=?', (subject, date)).fetchone()[0]

    def change_subscription_status(self, infos):
        if 'account' not in infos: return False
        if 'status' not in infos: return False
        if 'thread' not in infos: return False
        c = self.conn.cursor()
        c.execute('SELECT * FROM unsubscriptions WHERE account_id=? AND thread_id=?', (infos.account, infos.thread))
        ent = c.fetchone()
        if ent==None or len(ent)==0: # user is not unsubscribed from a thread
            if infos.status==True:
                return True
            self.conn.cursor().execute('INSERT INTO unsubscriptions(account_id,thread_id) VALUES (?, ?)', (infos.account, infos.thread))
            self.conn.commit()
            return True
        if infos.status==True: # user is unsubscribed from a thread and wants to subscribe again
            self.conn.cursor().execute('DELETE FROM unsubscriptions WHERE account_id=? AND thread_id=?', (infos.account, infos.thread))
            self.conn.commit()
            return True
        return True

    def create_db(self):
        self.conn = sqlite3.connect(self.path)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE buffer
                    (id INTEGER PRIMARY KEY,
                     date_arrival DATETIME,
                     account_id INTEGER,
                     priority INTEGER DEFAULT 3,
                     subject TEXT,
                     content TEXT)''')
        c.execute('''CREATE TABLE user
                    (id INTEGER PRIMARY KEY,
                     email TEXT,
                     password TEXT,
                     name TEXT,
                     max_priority INTEGER DEFAULT 3,
                     reset_password_token TEXT,
                     confirmed_at DATETIME,
                     active INTEGER)''')
        c.execute('''CREATE TABLE threads
                    (id INTEGER PRIMARY KEY,
                     title TEXT,
                     date_creation DATETIME)''')
        c.execute('''CREATE TABLE unsubscriptions
                    (id INTEGER PRIMARY KEY,
                     account_id INTEGER,
                     thread_id INTEGER)''')
        c.execute('''CREATE TABLE mails
                    (id INTEGER PRIMARY KEY,
                     thread_id INTEGER,
                     account_id INTEGER,
                     priority INTEGER DEFAULT 3,
                     content TEXT,
                     date_arrival DATETIME)''')
