from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, URLField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class UserUpdateForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    image_url = URLField("Profile Image URL", validators=[Optional(), Length(max=200)])
    header_image_url = URLField("Header Image URL", validators=[Optional(), Length(max=200)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=300)])
    location = StringField("Location", validators=[Optional(), Length(max=100)])
    password = PasswordField("current Password", validators=[DataRequired()])



class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )


class DirectMessageForm(FlaskForm):
    """form for sending direct messages"""

    recipient = StringField(
        "Recipient",
        validators=[DataRequired(message="Recipient's is required"), Length(max=50)],
        render_kw={"placeholder": "Enter recipient's username."},
    )

    content = TextAreaField(
        "Message",
        validators=[DataRequired(message="Message content is required."), Length(max=500)],
        render_kw={"plcaeholder": "Write your message here (max 500 charecters)"}
    )
    submit = SubmitField("Send Message")