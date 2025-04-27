####################################
# File name: models.py             #
# Author: Joe Abbate               #
####################################
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, SelectField, Form
from wtforms.validators import DataRequired


class DBCreate(FlaskForm):
    db_type = SelectField(
        "Database Type",
        choices=[("POSTGRES", "PostgreSQL"), ("MYSQL", "MySQL"), ("MONGO", "Mongo")],
        validators=[DataRequired()],
    )
    name = StringField("Database Name", validators=[DataRequired()])
    submit = SubmitField(("Submit"), validators=[DataRequired()])

    def validate(self, extra_validators=None):
        if not Form.validate(self, extra_validators=extra_validators):
            return False
        return True

class S3Create(FlaskForm):
    name = StringField("S3 Username", validators=[DataRequired()])
    submit = SubmitField(("Submit"), validators=[DataRequired()])

    def validate(self, extra_validators=None):
        if not Form.validate(self, extra_validators=extra_validators):
            return False
        return True
