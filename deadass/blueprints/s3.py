from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from deadass import deadass_db, rgwadmin, auth, commit
from deadass.utils import get_user
from deadass.models import S3
from sqlalchemy.orm import Session
import random
import secrets
from sqlalchemy import text
from deadass.forms import S3Create


s3_bp = Blueprint("s3", __name__)


@s3_bp.route("/s3/create", methods=["GET", "POST"])
@auth.oidc_auth("default")
@get_user
def create_bucket(user_dict=None):
    form = S3Create()
    if form.validate_on_submit():
        name = form.name.data
        if not name.isalnum():
            abort(400)
        user = rgwadmin.create_user(name, display_name=name)
        access_key = user.keys[0].access_key
        secret_key = user.keys[0].secret_key
        new_bucket = S3(name, access_key, user_dict["username"])
        with Session(deadass_db) as session:
            session.add(new_bucket)
            session.commit()
        flash(
            f'Your S3 User has been created with UID "{name}", Access Key "{access_key}", and Secret Key "{secret_key}"!'
        )
        return redirect("/")
    return render_template(
        "s3form.html", form=form, commit=commit, username=user_dict["username"]
    )


@s3_bp.route("/s3/<s3_id>/reset", methods=["POST"])
@auth.oidc_auth("default")
@get_user
def reset_password(s3_id, user_dict=None):
    with Session(deadass_db) as session:
        s3 = session.query(S3).get(int(s3_id))
    if s3.owner != user_dict["username"]:
        abort(403)
    name = s3.name
    if not name.isalnum():
        abort(400)
    keys = rgwadmin.create_key(s3.name, access_key=s3.access_key, generate_key=True)
    secret_key = keys[0]['secret_key']
    flash(f'Secret Key has been changed to "{secret_key}"!')
    return redirect("/")


@s3_bp.route("/s3/<s3_id>/delete", methods=["POST"])
@auth.oidc_auth("default")
@get_user
def delete(s3_id, user_dict=None):
    with Session(deadass_db) as session:
        s3 = session.query(S3).get(int(s3_id))
    if s3.owner != user_dict["username"]:
        abort(403)
    name = s3.name
    if not name.isalnum():
        abort(400)
    rgwadmin.delete_user(name)
    with Session(deadass_db) as session:
        session.delete(s3)
        session.commit()
    return redirect("/")
