from flask import Flask, flash, redirect, render_template, render_template_string, request, url_for
from flask.ext.babel import Babel, format_datetime, gettext
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter

from sqlalchemy.orm import exc
from sqlalchemy import func
import email
import html2text

#from modules.web.db_structure import User, Threads, Unsubscriptions ##FIXME how to implement this ?

def create_app(ConfigClass, test_config=None):                   # For automated tests
    # Setup Flask and read config from ConfigClass defined above
    app = Flask(__name__)
    #app.config.from_object(__name__+'.ConfigClass')
    app.config.from_object(ConfigClass)

    # Load local_settings.py if file exists         # For automated tests
    try: app.config.from_object('local_settings')
    except: pass

    # Load optional test_config                     # For automated tests
    if test_config:
        app.config.update(test_config)

    # Initialize Flask extensions
    babel = Babel(app)
    db = SQLAlchemy(app)
    mail = Mail(app)

    #database = modules.dbutil.db(app.config.SQLALCHEMY_DATABASE_URI)

    @babel.localeselector
    def get_locale():
        translations = [str(translation) for translation in babel.list_translations()]
        return request.accept_languages.best_match(translations)

    # Define User model. Make sure to add flask.ext.user UserMixin!!
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column(db.Boolean(), nullable=False, default=False)
        email = db.Column(db.String(255), nullable=False, unique=True)
        name = db.Column(db.String(50), nullable=False, unique=True)
        max_priority = db.Column(db.Integer, nullable=False, default=3)
        password = db.Column(db.String(255), nullable=False, default='')
        confirmed_at = db.Column(db.DateTime())
        reset_password_token = db.Column(db.String(100), nullable=False, default='')

    class Threads(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(50), nullable=False, unique=True)
        date_creation = db.Column(db.DateTime())
        priority = db.Column(db.Integer, nullable=False, default=3)

        def __repr__(self):
            return '<Thread %r created on %s>' % (self.title, self.date_creation)

    class Mails(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False)
        account_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        content = db.Column(db.String(50), nullable=False, unique=True)
        date_arrival = db.Column(db.DateTime())

        thread = db.relationship('Threads', backref=db.backref('mails', lazy='dynamic'))
        account = db.relationship('User', backref=db.backref('mails', lazy='dynamic'))

    class Unsubscriptions(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        account_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False)
        
        account = db.relationship('User', backref=db.backref('unsubscriptions', lazy='dynamic'))
        thread = db.relationship('Threads', backref=db.backref('unsubscriptions', lazy='dynamic'))

        def __init__(self, user_id, thread_id):
            self.account_id=user_id
            self.thread_id=thread_id
    
    # Create all database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db, User)        # Select database adapter
    user_manager = UserManager(db_adapter, app)     # Init Flask-User and bind to app

    @app.template_filter('extract_mail')
    def extract_mail(mime_content):
        #msg = email.message_from_string(unicode(mime_content).encode('utf-8'))
        msg = email.message_from_string(mime_content.encode('utf-8'))
        out = u''
        for part in msg.walk():
            # each part is a either non-multipart, or another multipart message
            content_type = part.get_content_type()
            if part.is_multipart():
                for sp in part.get_payload():
                    out += html2text.html2text(sp.get_payload().decode('utf-8'))+'<br />'

            elif content_type=="text/plain":
                out += part.get_payload().decode('utf-8')+'<br />'
                #out += part.get_payload().replace('\r', '<br/>')
            else:
                out += html2text.html2text(part.get_payload().decode('utf-8'))
                #out += part.get_payload().decode('utf-8')
        return out.replace('\r', '<br />')


    @app.template_filter('datetime')
    def the_format_datetime(value, format='medium'):
        if format == 'full':
            format="EEEE, d. MMMM y 'at' HH:mm"
        elif format == 'medium':
            format="EE dd.MM.y HH:mm"
        return format_datetime(value, format)

    # Display Login page or Profile page
    @app.route('/')
    def home_page():
        if current_user.is_authenticated():
            return redirect(url_for('profile_page'))
        else:
            return redirect(url_for('user.login'))

    # The '/profile' page requires a logged-in user
    @app.route('/profile')
    @login_required
    def profile_page():
        return render_template('profile_page.html', num_threads=db.session.query(func.count(Threads.id)).one()[0])

    @app.route('/threads/unsubscribe/<thread_id>')
    @login_required
    def unsubscribe_thread(thread_id=None):
        if len(db.session.query(Unsubscriptions).filter_by(account_id=current_user.id, thread_id=thread_id).all())!=0:
            flash(gettext('You are already unsubscribed from thread <b>%s</b>' % Threads.query.filter_by(id=thread_id).first().title), 'error')
        else:
            uns = Unsubscriptions(current_user.id, thread_id)
            db.session.add(uns)
            db.session.commit()
            flash(gettext('You are now unsubscribed from thread <b>%s</b>' % Threads.query.filter_by(id=thread_id).first().title), 'success')
        return render_template("thread_display.html", Threads=Threads, Mails=Mails, Unsubscriptions=Unsubscriptions)

    @app.route('/threads/subscribe/<thread_id>')
    @login_required
    def subscribe_thread(thread_id=None):
        try:
            unsub = db.session.query(Unsubscriptions).filter_by(account_id=current_user.id, thread_id=thread_id).all()
            if len(unsub)<1:
                raise exc.NoResultFound
            for ent in unsub:
                db.session.delete(ent)
                db.session.commit()
            flash(gettext('You are now subscribed to the thread <b>%s</b>' % Threads.query.filter_by(id=thread_id).first().title), 'success')
        except exc.NoResultFound:
            flash(gettext('You are already subscribed to the thread <b>%s</b>' % Threads.query.filter_by(id=thread_id).first().title), 'error')
        return render_template("thread_display.html", Threads=Threads, Mails=Mails, Unsubscriptions=Unsubscriptions)

    @app.route('/threads')
    @login_required
    def list_threads():
        return render_template("thread_display.html", Threads=Threads, Mails=Mails, Unsubscriptions=Unsubscriptions)

    @app.route('/mail/<mail_id>')
    @login_required
    def show_mail(mail_id=None):
        mails = db.session.query(Mails).filter_by(id=mail_id).all()
        if len(mails)!=1:
            flash(gettext('The mail with id %i was not found in the database' % int(mail_id)), 'error')
            return render_template("mail_display.html", mail=None)
        return render_template("mail_display.html", mail=mails[0])

    return app
