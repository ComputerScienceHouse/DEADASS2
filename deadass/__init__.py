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
import random
import radosgw

# from flask_login import login_user, logout_user, login_required, LoginManager, current_user


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
rgwadmin = radosgw.connection.RadosGWAdminConnection(
    host=app.config["S3_HOST"],
    access_key=app.config["S3_ACCESS_KEY"],
    secret_key=app.config["S3_SECRET_KEY"],
)

# OIDC Authentication
CSH_AUTH = ProviderConfiguration(
    issuer=app.config["OIDC_ISSUER"],
    client_metadata=ClientMetadata(
        app.config["OIDC_CLIENT_ID"], app.config["OIDC_CLIENT_SECRET"]
    ),
)
auth = OIDCAuthentication({"default": CSH_AUTH}, app)

auth.init_app(app)

# Commit
commit = check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").rstrip()

# pylint: disable=wrong-import-position
from .utils import get_user
from .models import Database, S3

# time setup for the server side time
eastern = pytz.timezone("America/New_York")
fmt = "%Y-%m-%d %H:%M"


# Favicon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/assets"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/logout")
@auth.oidc_logout
def _logout():
    return redirect("/", 302)


@app.route("/")
@auth.oidc_auth("default")
@get_user
def home(user_dict=None):
    with Session(deadass_db) as session:
        dbs = (
            session.query(Database)
            .filter(Database.owner == user_dict["username"])
            .all()
        )
        s3 = (
            session.query(S3)
            .filter(S3.owner == user_dict["username"])
            .all()
        )
    return render_template(
        "index.html", dbs=dbs, s3s=s3, commit=commit, username=user_dict["username"]
    )


from .blueprints.db import db_bp
from .blueprints.s3 import s3_bp

app.register_blueprint(db_bp)
app.register_blueprint(s3_bp)
