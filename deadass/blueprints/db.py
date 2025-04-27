from flask import Blueprint, render_template, request, redirect, url_for, flash
from deadass import deadass_db, postgres_db, mysql_db, mongo_db, auth, commit
from deadass.utils import get_user
from deadass.models import Database
from sqlalchemy.orm import Session
import random
import secrets
from sqlalchemy import text
from deadass.forms import DBCreate


db_bp = Blueprint("db", __name__)


@db_bp.route("/db/create", methods=["GET", "POST"])
@auth.oidc_auth("default")
@get_user
def create_db(user_dict=None):
    form = DBCreate()
    if form.validate_on_submit():
        db_type = form.db_type.data
        name = form.name.data
        if not name.isalnum():
            abort(400)
        password = gen_password()
        if db_type == "POSTGRES":
            with postgres_db.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as connection:
                with connection.begin():
                    db_check = text(
                        "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname=:name"
                    )
                    if connection.execute(db_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_check = text(
                        "SELECT COUNT(1) FROM pg_roles WHERE rolname=:name"
                    )
                    if connection.execute(user_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_text = text(f"CREATE USER {name} WITH PASSWORD :password;")
                    connection.execute(user_text, password=password)
                    connection.execute(f"CREATE DATABASE {name} OWNER {name};")
        elif db_type == "MYSQL":
            with mysql_db.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as connection:
                with connection.begin():
                    db_check = text(
                        "SELECT COUNT(1) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :name"
                    )
                    if connection.execute(db_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_check = text(
                        "SELECT COUNT(1) FROM mysql.user WHERE user = :name"
                    )
                    if connection.execute(user_check, name=name).scalar_one() > 0:
                        abort(400)
                    user_text = text("CREATE USER :name@'%' IDENTIFIED BY :password;")
                    perm_text = text(f"GRANT ALL ON {name}.* TO :name@'%';")
                    connection.execute(user_text, name=name, password=password)
                    connection.execute(f"CREATE DATABASE {name};")
                    connection.execute(perm_text, name=name)
        elif db_type == "MONGO":
            if name in mongo_db.list_database_names():
                abort(400)
            db = mongo_db[name]
            db.command(
                "createUser",
                name,
                pwd=password,
                roles=[{"role": "dbOwner", "db": name}],
            )
            db["default"].insert_one({})
        new_db = Database(db_type, name, user_dict["username"])
        with Session(deadass_db) as session:
            session.add(new_db)
            session.commit()
        flash(
            f'Your Database has been created with username "{name}" and password "{password}"!'
        )
        return redirect("/")
    return render_template(
        "dbform.html", form=form, commit=commit, username=user_dict["username"]
    )


@db_bp.route("/db/<db_id>/reset", methods=["POST"])
@auth.oidc_auth("default")
@get_user
def reset_password(db_id, user_dict=None):
    with Session(deadass_db) as session:
        db = session.query(Database).get(int(db_id))
    if db.owner != user_dict["username"]:
        abort(403)
    name = db.name
    if not name.isalnum():
        abort(400)
    password = gen_password()
    if db.db_type == "POSTGRES":
        with postgres_db.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            with connection.begin():
                alter_text = text(f"ALTER USER {name} WITH PASSWORD :password;")
                connection.execute(alter_text, password=password)
    elif db.db_type == "MYSQL":
        with mysql_db.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            with connection.begin():
                alter_text = text("ALTER USER :name@'%' IDENTIFIED BY :password;")
                connection.execute(alter_text, name=name, password=password)
    elif db.db_type == "MONGO":
        db = mongo_db[name]
        db.command("changeUserPassword", name, pwd=password)
    flash(f'Password has been changed to "{password}"!')
    return redirect("/")


@db_bp.route("/db/<db_id>/delete", methods=["POST"])
@auth.oidc_auth("default")
@get_user
def delete(db_id, user_dict=None):
    with Session(deadass_db) as session:
        database = session.query(Database).get(int(db_id))
    if database.owner != user_dict["username"]:
        abort(403)
    name = database.name
    if not name.isalnum():
        abort(400)
    if database.db_type == "POSTGRES":
        with postgres_db.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            with connection.begin():
                connection.execute(f"DROP DATABASE {name};")
                connection.execute(f"DROP USER {name};")
    elif database.db_type == "MYSQL":
        with mysql_db.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            with connection.begin():
                connection.execute(f"DROP DATABASE {name};")
                connection.execute(f"DROP USER {name};")
    elif database.db_type == "MONGO":
        db = mongo_db[name]
        db.command("dropUser", name)
        db.command("dropDatabase")
    with Session(deadass_db) as session:
        session.delete(database)
        session.commit()
    return redirect("/")


def gen_password():
    # Set password creation defaults
    allCharsSet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*"
    length = 18

    # Shuffle charset
    allChars = shuffle_chars(allCharsSet)

    password = ""
    newChar = ""

    while len(password) < length:
        password += secrets.choice(allCharsSet)

    return password


def shuffle_chars(string):
    string_list = list(string)
    random.shuffle(string_list)
    return "".join(string_list)
