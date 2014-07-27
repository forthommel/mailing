# -*- coding: utf-8 -*-

from os.path import isfile, getsize
import sqlite3
import datetime
import dateutil.parser

class users:
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

    def get_user_by_email(self, email):
        c = self.conn.cursor()
        c.execute('SELECT id,name FROM user WHERE email="%s"' % email)
        res = c.fetchone()
        if res is None or len(res)==0:
            return None
        return {'id': res[0], 'name': res[1]}

    def get_user_by_id(self, id):
        c = self.conn.cursor()
        c.execute('SELECT email,name,max_priority FROM user WHERE id=?', (id,))
        res = c.fetchone()
        if res is None or len(res)==0:
            return None
        return {'email': res[0], 'name': res[1], 'max_priority': res[2]}

    def get_users_by_priority(self):
        out = []
        c = self.conn.cursor()
        for user in c.execute('''SELECT id,email,max_priority FROM user ORDER BY max_priority'''):
            out.append({'id': user[0], 'email': user[1], 'priority': user[2]})
        return out

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

    def buffer_size(self):
        c = self.conn.cursor()
        c.execute('SELECT count(*) FROM buffer')
        ent = c.fetchone()
        if ent==None or len(ent)==0:
            return -1
        return int(ent[0])

    def change_subscription_status(self, infos):
        if 'user' not in infos: return False
        if 'status' not in infos: return False
        if 'thread' not in infos: return False
        c = self.conn.cursor()
        c.execute('SELECT * FROM unsubscriptions WHERE user_id=? AND thread_id=?', (infos.user, infos.thread))
        ent = c.fetchone()
        if ent==None or len(ent)==0: # user is not unsubscribed from a thread
            if infos.status==True:
                return True
            self.conn.cursor().execute('INSERT INTO unsubscriptions(user_id,thread_id) VALUES (?, ?)', (infos.user, infos.thread))
            self.conn.commit()
            return True
        if infos.status==True: # user is unsubscribed from a thread and wants to subscribe again
            self.conn.cursor().execute('DELETE FROM unsubscriptions WHERE user_id=? AND thread_id=?', (infos.user, infos.thread))
            self.conn.commit()
            return True
        return True

    def create_db(self):
        self.conn = sqlite3.connect(self.path)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE user
                    (id INTEGER PRIMARY KEY,
                     email TEXT,
                     password TEXT,
                     name TEXT,
                     max_priority INTEGER DEFAULT 3,
                     reset_password_token TEXT,
                     confirmed_at DATETIME,
                     active INTEGER)''')
        c.execute('''CREATE TABLE unsubscriptions
                    (id INTEGER PRIMARY KEY,
                     user_id INTEGER,
                     thread_id INTEGER)''')
