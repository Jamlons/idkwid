from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    searched = TextAreaField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit Search")