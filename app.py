import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
import os

from forms import UserAddForm, LoginForm, MessageForm, UserUpdateForm, ChangePasswordForm, DirectMessageForm
from models import db, connect_db, User, Message, DirectMessage







CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('SUPABASE_DB_URI', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)
with app.app_context():
    connect_db(app)
    db.drop_all()
    db.create_all()

print(app.config['SQLALCHEMY_DATABASE_URI'])



##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS

    do_logout()
    flash("You have been logged out of the Warbler.", "success")
    return redirect("/")


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # IMPLEMENT THIS
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = UserUpdateForm(obj=g.user) # Prepopulate from with current user's data


    if form.validate_on_submit():
        # Authenticate the user before allowing profile updates
        if User.authenticate(g.user.username, form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data
            g.user.location = form.location.data

            db.session.commit()
            flash("Profile Updated Sucessfully!", "success")
            return redirect(f"/users/{g.user.id}")
        else:
            flash("Incorrect Password. Changes not Saved.", "danger")


    return render_template("users/edit.html", form=form)

    
@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    Message.query.filter_by(user_id=g.user.id).delete()

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    flash("User and associated messages have been deleted.", "Succes")
    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/direct-messages')
def view_messages():
    """view all direct messages for the logeed in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect( url_for("login"))
    
    inbox = DirectMessage.query.filter_by(recipient_id=g.user.id).order_by(DirectMessage.timestamp.desc()).all()
    sent = DirectMessage.query.filter_by(sender_id=g.user.id).order_by(DirectMessage.timestamp.desc()).all()

    return render_template("/messages/direct_messages.html", inbox=inbox, sent=sent)


@app.route("/messages/send", methods=["GET", "POST"])
def send_message():
    """Send a direct message to another user."""
    if not g.user:
        flash("Access unauthorized. Please log in.", "danger")
        return redirect(url_for("login"))

    form = DirectMessageForm()

    if form.validate_on_submit():
        recipient_username = form.recipient.data.strip()
        content = form.content.data.strip()

        recipient = User.query.filter_by(username=recipient_username).first()
        if not recipient:
            flash("Recipient not found.", "danger")
            return redirect(url_for("/messages/send_messages"))

        message = DirectMessage(
            sender_id=g.user.id,
            recipient_id=recipient.id,
            content=content,
        )
        db.session.add(message)
        db.session.commit()

        flash("Message sent!", "success")
        return redirect(url_for("view_messages"))

    return render_template("/messages/send_messages.html", form=form)



#############################################################################
# Liked_messages routes

@app.route('/users/add_like/<int:message_id>', methods=['POST'])
def add_like(message_id):
    """Add a like for the currently logged in user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    message = Message.query.get_or_404(message_id)

    # Ensure users cannot like thier own warbles
    if message.user_id == g.user.id:
        flash("You cannot like your own warble.", "danger")
        return redirect("/")
    
    
    
    g.user.likes.append(message)
    db.session.commit()
    flash("you liked the message.")
    return redirect("/")

@app.route('/users/remove_like/<int:message_id>', methods=['POST'])
def remove_like(message_id):
    """Remove a like for the currently logged in user."""


    if not g.user:
        flash("Access unautherized.", "danger")
        return redirect("/")
    

    message = Message.query.get_or_404(message_id)


    
    g.user.likes.remove(message)
    db.session.commit()
    flash("you unliked the message.")
        
    return redirect("/")


@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show the messages a user has liked."""

    user = User.query.get_or_404(user_id)


    return redirect('/', user=user, messages=user.likes)


###############################################################################
# Change password route

from forms import ChangePasswordForm

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data

        if g.user.change_password(current_password, new_password):
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect("/users")
        else:
            flash("Current password is incorrect.", "danger")

    return render_template("change_password.html", form=form)



##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        #Get IDs of followed users + the current user's ID
        followed_user_ids = [user.id for user in g.user.following]
        followed_user_ids.append(g.user.id)


        messages = (Message
                    .query
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req


if __name__ == "__main__":
    app.run(debug=True)

