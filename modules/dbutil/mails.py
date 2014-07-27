# -*- coding: utf-8 -*-

from os.path import isfile, getsize
import sqlite3
import datetime
import dateutil.parser

class mails:
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

    def add_mail_in_buffer(self, infos, db_users):
        if 'email' not in infos: return False
        if 'content' not in infos: return False
        if 'date' not in infos: return False
        c = self.conn.cursor()
        user = db_users.get_user_by_email(infos['email'])
        if user is None: # user in not registered in the system
            print '=> Unknown e-mail (%s) sent a mail on the list on %s' % (infos['email'], infos['date'])
            return False
        self.conn.cursor().execute('INSERT INTO buffer(date_arrival,user_id,subject,content) VALUES (?, ?, ?, ?)', (infos['date'], user['id'], infos['subject'], infos['content']))
        self.conn.commit()
        print '=> User "%s" (id=%i) sent a mail on %s' % (user['name'], user['id'], infos['date'])
        return True

    def get_mails_in_buffer(self, db_users):
        out = []
        c = self.conn.cursor()
        priorities = {1: [], 2: [], 3: []}

        for user in db_users.get_users_by_priority():
            if user not in priorities[user['priority']]:
                priorities[user['priority']].append(user)

        for mail in c.execute('''SELECT id,user_id,date_arrival,priority,subject,content FROM buffer'''):
            mail_id, user_id, arrival, mail_priority, mail_subject, mail_content = mail
            mail_priority = int(mail_priority)
            user_from = db_users.get_user_by_id(user_id)
            if user_from is None:
                continue
            for user in priorities[mail_priority]:
                out.append({
                    'id': int(mail_id),
                    'from_email': user_from['email'],
                    'from_name': user_from['name'],
                    'to': user['email'],
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
        c.execute('SELECT date_arrival,user_id,priority,subject,content FROM buffer WHERE id=?', (str(mail_id)))
        ent = c.fetchone()
        if ent is None or len(ent)==0:
            return False
        
        subject_stripped = ent[3].replace("Re: ", "")
        thread_id = self.search_threads(subject_stripped)

        if thread_id==-1:
            thread_id = self.add_new_thread(subject_stripped, ent[0])

        self.conn.cursor().execute('''INSERT INTO mails(thread_id,user_id,priority,content,date_arrival) VALUES (?, ?, ?, ?, ?)''', (thread_id, ent[1], ent[2], ent[4], ent[0]))
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

    def list_threads(self):
        out = []
        for thread in self.conn.cursor().execute('''SELECT id,title,date_creation FROM threads ORDER BY date_creation LIMIT 10'''):
            out.append({'id': thread[0], 'title': thread[1], 'date_creation': dateutil.parser.parse(thread[2])})
        return out

    def add_new_thread(self, subject, date):
        self.conn.cursor().execute('INSERT INTO threads(title,date_creation) VALUES (?, ?)', (subject, date))
        self.conn.commit()
        print '=> New thread created on %s : %s' % (date, subject)
        return self.conn.cursor().execute('SELECT id FROM threads WHERE title=? AND date_creation=?', (subject, date)).fetchone()[0]

    def create_db(self):
        self.conn = sqlite3.connect(self.path)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE buffer
                    (id INTEGER PRIMARY KEY,
                     date_arrival DATETIME,
                     user_id INTEGER,
                     priority INTEGER DEFAULT 3,
                     subject TEXT,
                     content TEXT)''')
        c.execute('''CREATE TABLE threads
                    (id INTEGER PRIMARY KEY,
                     title TEXT,
                     date_creation DATETIME)''')
        c.execute('''CREATE TABLE mails
                    (id INTEGER PRIMARY KEY,
                     thread_id INTEGER,
                     user_id INTEGER,
                     priority INTEGER DEFAULT 3,
                     content TEXT,
                     date_arrival DATETIME)''')
