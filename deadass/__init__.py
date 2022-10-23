####################################
# File name: __init__.py           #
# Author: Joe Abbate               #
####################################
from subprocess import check_output
from datetime import datetime
import os
import pytz
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask import Flask, render_template, send_from_directory, redirect, abort, flash
from flask_wtf.csrf import CSRFProtect
from sqlalchemy_utils import database_exists, create_database
from flask_pymongo import PyMongo
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import requests
#from flask_login import login_user, logout_user, login_required, LoginManager, current_user


# Setting up Flask and csrf token for forms.
app = Flask(__name__)
csrf = CSRFProtect(app)
csrf.init_app(app)
# Get app config from absolute file path
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Establish SQL Database
deadass_db = create_engine(app.config["DEADASS_URI"])
postgres_db = create_engine(app.config["POSTGRES_URI"])
mysql_db = create_engine(app.config["MYSQL_URI"])
mongo_db = PyMongo(app)

# OIDC Authentication
CSH_AUTH = ProviderConfiguration(issuer=app.config["OIDC_ISSUER"],
                                 client_metadata=ClientMetadata(
                                     app.config["OIDC_CLIENT_ID"],
                                     app.config["OIDC_CLIENT_SECRET"]))
auth = OIDCAuthentication({'default': CSH_AUTH},
                          app)

auth.init_app(app)

# Commit
commit = check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').rstrip()

# pylint: disable=wrong-import-position
from .models import Database
from .forms import DBCreate
from .utils import get_user

# time setup for the server side time
eastern = pytz.timezone('America/New_York')
fmt = '%Y-%m-%d %H:%M'

# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/assets'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/logout")
@auth.oidc_logout
def _logout():
    return redirect("/", 302)

@app.route('/')
@auth.oidc_auth('default')
@get_user
def home(user_dict=None):
    with Session(deadass_db) as session:
        dbs = session.query(Database).filter(Database.owner==user_dict['username']).all()
    return render_template('index.html', dbs=dbs, commit=commit, username=user_dict['username']) 

@app.route('/db/create', methods=['GET', 'POST'])
@auth.oidc_auth('default')
@get_user
def create_db(user_dict=None):
    form = DBCreate()
    if form.validate_on_submit():
        db_type = form.db_type.data
        name = form.name.data
        if not name.isalnum():
            abort(400)
        password = get_haddock_password();
        if db_type == 'POSTGRES':
            with postgres_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                with connection.begin():
                    db_check = text("SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname=:name")
                    if connection.execute(db_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_check = text("SELECT COUNT(1) FROM pg_roles WHERE rolname=:name")
                    if connection.execute(user_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_text = text(f"CREATE USER {name} WITH PASSWORD :password;")
                    connection.execute(user_text, password=password)
                    connection.execute(f"CREATE DATABASE {name} OWNER {name};")
        elif db_type == 'MYSQL':
            with mysql_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                with connection.begin():
                    db_check = text("SELECT COUNT(1) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :name")
                    if connection.execute(db_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_check = text("SELECT COUNT(1) FROM mysql.user WHERE user = :name")
                    if connection.execute(user_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_text = text("CREATE USER :name@'%' IDENTIFIED BY :password;")
                    perm_text = text(f"GRANT ALL ON {name}.* TO :name@'%';")
                    connection.execute(user_text, name=name, password=password)
                    connection.execute(f"CREATE DATABASE {name};")
                    connection.execute(perm_text, name=name)
        elif db_type == 'MONGO':
            if name in mongo_db.cx.list_database_names():
                abort(400)
            db = mongo_db.cx[name]
            db.command(
                'createUser', name, 
                pwd=password,
                roles=[{'role': 'dbOwner', 'db': name}]
            )
            db['default'].insert_one({})
        new_db = Database(db_type, name, user_dict['username'])
        with Session(deadass_db) as session:
            session.add(new_db)
            session.commit()
        flash(f'Your Database has been created with username "{name}" and password "{password}"!')
        return redirect('/')
    return render_template('dbform.html', form=form, commit=commit, username=user_dict['username']) 

@app.route('/db/<db_id>/reset', methods=['POST'])
@auth.oidc_auth('default')
@get_user
def reset_password(db_id, user_dict=None):
    with Session(deadass_db) as session:
        db = session.query(Database).get(int(db_id))
    if db.owner != user_dict['username']:
        abort(403)
    name = db.name
    if not name.isalnum():
        abort(400)
    password = get_haddock_password()
    if db.db_type == 'POSTGRES':
        with postgres_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            with connection.begin():
                alter_text = text(f"ALTER USER {name} WITH PASSWORD :password;")
                connection.execute(alter_text, password=password)
    elif db.db_type == 'MYSQL':
        with mysql_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            with connection.begin():
                alter_text = text("ALTER USER :name@'%' IDENTIFIED BY :password;")
                connection.execute(alter_text, name=name, password=password)
    elif db.db_type == 'MONGO':
        db = mongo_db.cx[name]
        db.command(
            'changeUserPassword', name, 
            pwd=password
        )
    flash(f"Password has been changed to {password}")
    return redirect('/')

@app.route('/db/<db_id>/delete', methods=['POST'])
@auth.oidc_auth('default')
@get_user
def delete(db_id, user_dict=None):
    with Session(deadass_db) as session:
        database = session.query(Database).get(int(db_id))
    if database.owner != user_dict['username']:
        abort(403)
    name = database.name
    if not name.isalnum():
        abort(400)
    if database.db_type == 'POSTGRES':
        with postgres_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            with connection.begin():
                connection.execute(f"DROP DATABASE {name};")
                connection.execute(f"DROP USER {name};")
    elif database.db_type == 'MYSQL':
        with mysql_db.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            with connection.begin():
                connection.execute(f"DROP DATABASE {name};")
                connection.execute(f"DROP USER {name};")
    elif database.db_type == 'MONGO':
        db = mongo_db.cx[name]
        db.command(
            'dropUser', name
        )
        db.command(
            'dropDatabase'
        )
    with Session(deadass_db) as session:
        session.delete(database)
        session.commit()
    return redirect('/')

def get_haddock_password():
    req = requests.get("https://haddock.csh.rit.edu/api/v1/haddock")
    data = req.json()
    return data[0]
