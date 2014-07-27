import argparse
import ConfigParser

from modules.web.auth import create_app
from modules.dbutil import mails

# Start development web server
def main(argv):
    config = ConfigParser.ConfigParser()
    config.read(argv.config)

    # Use a Class-based config to avoid needing a 2nd file
    class ConfigClass(object):
        # Configure Flask
        SECRET_KEY = 'THIS IS AN INSECURE SECRET'               # Change this for production!!!
        SQLALCHEMY_DATABASE_URI = 'sqlite:///../../'+config.get('general', 'mails_database_location')+'?check_same_thread=False'
        CSRF_ENABLED = True
    
        # Configure Flask-Mail -- Required for Confirm email and Forgot password features
        MAIL_SERVER   = config.get('mailserver', 'outgoing_host')
        MAIL_PORT     = config.get('mailserver', 'outgoing_port')
        MAIL_USE_SSL  = False
        MAIL_USERNAME = config.get('mailaccount', 'outgoing_username')
        MAIL_PASSWORD = config.get('mailaccount', 'password')
        MAIL_DEFAULT_SENDER = config.get('mailaccount', 'reply_to_address')
        
        # Configure Flask-User
        USER_ENABLE_USERNAME = False
        USER_ENABLE_CONFIRM_EMAIL = True
        USER_ENABLE_MULTIPLE_EMAILS = True
        USER_ENABLE_MANAGE_EMAILS = True
        USER_ENABLE_CHANGE_USERNAME = False
        USER_ENABLE_CHANGE_PASSWORD = True
        USER_ENABLE_FORGOT_PASSWORD = True
        USER_ENABLE_RETYPE_PASSWORD = True
        USER_LOGIN_TEMPLATE = 'login_form.html'
        USER_REGISTER_TEMPLATE = 'login_form.html'

        BABEL_DEFAULT_LOCALE = 'fr'

    app = create_app(ConfigClass)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Web server for the accounts management')
    parser.add_argument('config', type=str, default='default.cfg', help='Configuration file for the running environment')
    args = parser.parse_args()

    main(args)
