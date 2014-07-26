# -*- encoding: utf-8 -*-
#
# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#
# Thanks to Arnar Birgisson (arnarbi -at- gmail) for this implementation !

import cherrypy
from modules.dbutil.db import db

SESSION_KEY = '_cp_username'

def check_credentials(email, password):
    """Verifies credentials for email and password.
    Returns None on success or a string describing the error on failure"""
    # Adapt to your needs
    if email in ('joe', 'steve') and password == 'secret':
        return None
    else:
        return u"Incorrect email or password."
    
def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)

    # An example implementation which uses an ORM could be:
    # u = User.get(email)
    # if u is None:
    #     return u"Email %s is unknown to me." % email
    # if u.password != md5.new(password).hexdigest():
    #     return u"Incorrect password"

def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfill"""
    conditions = cherrypy.request.config.get('auth.require', None)
    if conditions is not None:
        email = cherrypy.session.get(SESSION_KEY)
        if email:
            cherrypy.request.login = email
            for condition in conditions:
                # A condition is just a callable that returns true or false
                if not condition():
                    raise cherrypy.HTTPRedirect("/auth/login")
        else:
            raise cherrypy.HTTPRedirect("/auth/login")
    
cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)

def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current email as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <email> is in <groupname>
        return cherrypy.request.login == 'joe' and groupname == 'admin'
    return check

def name_is(reqd_email):
    return lambda: reqd_email == cherrypy.request.login

# These might be handy

def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check

# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


# Controller to provide login and logout actions

class AuthController(object):
    
    def on_login(self, email):
        """Called on successful login"""
    
    def on_logout(self, email):
        """Called on logout"""
    
    def get_loginform(self, email, msg="Enter login information", from_page="/"):
        return """
        <a href="/auth/register">Registration</a><br />
        <form method="post" action="/auth/login">
        <input type="hidden" name="from_page" value="%(from_page)s" />
        %(msg)s<br />
        E-mail: <input type="text" name="email" value="%(email)s" /><br />
        Password: <input type="password" name="password" /><br />
        <input type="submit" value="Log in" />
        </form>
        """ % locals()

    def get_registrationform(self, email="", name="", msg="", from_page="/"):
        return """
        <form method="post" action="/auth/register">
        %(msg)s<br />
        <input type="hidden" name="from_page" value="%(from_page)s" />
        E-mail: <input type="text" name="email" value="%(email)s" /><br />
        Full name: <input type="text" name="name" value="%(name)s" /><br />
        Password: <input type="password" name="password1" /><br />
        Password (confirm): <input type="password" name="password2" /><br />
        <input type="submit" value="Register" />
        </form>
        """ % locals()

    def check_password_validity(self, password1=None, password2=None):
        if password1 is None or password2 is None:
            return -1
        if password1!=password2:
            return -2
        if len(password1)<8:
            return -3
        return 0

    @cherrypy.expose
    def register(self, email=None, name=None, password1=None, password2=None, from_page="/"):
        if email is None or name is None or password1 is None:
            return self.get_registrationform("", from_page=from_page)

        if self.check_password_validity(password1, password2)!=0:
            return self.get_registrationform(email=email, name=name, from_page=from_page)
                
    
    @cherrypy.expose
    def login(self, email=None, password=None, from_page="/"):
        if email is None or password is None:
            return self.get_loginform("", from_page=from_page)
        
        error_msg = check_credentials(email, password)
        if error_msg:
            return self.get_loginform(email, error_msg, from_page)
        else:
            cherrypy.session.regenerate()
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
            self.on_login(email)
            raise cherrypy.HTTPRedirect(from_page or "/")
    
    @cherrypy.expose
    def logout(self, from_page="/"):
        sess = cherrypy.session
        email = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if email:
            cherrypy.request.login = None
            self.on_logout(email)
        raise cherrypy.HTTPRedirect(from_page or "/")
