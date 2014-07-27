from flask import Flask, redirect, render_template_string, request, url_for
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter

import modules.dbutil.mails

def create_app(db, ConfigClass, test_config=None):                   # For automated tests
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
    sqladb = SQLAlchemy(app)
    mail = Mail(app)

    #database = modules.dbutil.db(app.config.SQLALCHEMY_DATABASE_URI)

    @babel.localeselector
    def get_locale():
        translations = [str(translation) for translation in babel.list_translations()]
        return request.accept_languages.best_match(translations)

    # Define User model. Make sure to add flask.ext.user UserMixin!!
    class User(sqladb.Model, UserMixin):
        id = sqladb.Column(sqladb.Integer, primary_key=True)
        active = sqladb.Column(sqladb.Boolean(), nullable=False, default=False)
        email = sqladb.Column(sqladb.String(255), nullable=False, unique=True)
        name = sqladb.Column(sqladb.String(50), nullable=False, unique=True)
        max_priority = sqladb.Column(sqladb.Integer, nullable=False, default=3)
        password = sqladb.Column(sqladb.String(255), nullable=False, default='')
        confirmed_at = sqladb.Column(sqladb.DateTime())
        reset_password_token = sqladb.Column(sqladb.String(100), nullable=False, default='')

    # Create all database tables
    sqladb.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(sqladb, User)        # Select database adapter
    user_manager = UserManager(db_adapter, app)     # Init Flask-User and bind to app

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
        return render_template_string("""
            {% extends "base.html" %}
            {% block content %}
                <h2>{%trans%}Profile Page{%endtrans%}</h2>
                <p> {%trans%}Hello{%endtrans%}
                    {{ current_user.name or current_user.email }},</p>
                <p> <a href="{{ url_for('user.change_password') }}">
                    {%trans%}Change password{%endtrans%}</a></p>
                <p> <a href="/threads">
                    {%trans%}List all threads{%endtrans%}</a></p>
                <p> <a href="{{ url_for('user.logout') }}?next={{ url_for('user.login') }}">
                    {%trans%}Sign out{%endtrans%}</a></p>
            {% endblock %}
            """)

    @app.route('/threads')
    @login_required
    def list_threads():
        threads_list = db.list_threads()
        return render_template_string("""
        {% extends "base.html" %}
        {% block content %}
        {% for thr in threads_list %}
        {{ thr.title }}
        {% endfor %}
        {% endblock %}
        """)

    return app
