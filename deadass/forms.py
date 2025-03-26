####################################
# File name: models.py             #
# Author: Joe Abbate               #
####################################
from flask_wtf import FlaskForm
from wtforms import Form, SelectField, StringField, SubmitField, validators
from wtforms.validators import DataRequired, StopValidation


def is_alphanumeric(form, field):
    if not field.data.isalnum():
        raise StopValidation("Name must be alphanumeric")


class DBCreate(FlaskForm):
    db_type = SelectField(
        "Database Type",
        choices=[("POSTGRES", "PostgreSQL"), ("MYSQL", "MySQL"), ("MONGO", "Mongo")],
        validators=[DataRequired()],
    )
    name = StringField("Database Name", validators=[DataRequired(), is_alphanumeric])
    submit = SubmitField(("Submit"), validators=[DataRequired()])

    def validate(self, extra_validators=None):
        if not Form.validate(self, extra_validators=extra_validators):
            return False
        return True


class S3Create(FlaskForm):
    name = StringField("S3 Username", validators=[DataRequired(), is_alphanumeric])
    submit = SubmitField(("Submit"), validators=[DataRequired()])

    def validate(self, extra_validators=None):
        if not Form.validate(self, extra_validators=extra_validators):
            return False
        return True
