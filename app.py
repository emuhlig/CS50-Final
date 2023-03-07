import json

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, sendCommand

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///huefx.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    groups = lookup('groups')
    lights = lookup('lights')
    return render_template("index.html", groups=groups, lights=lights)


@app.route("/group/<id>")
@login_required
def group(id):
    group = lookup(f'groups/{id}')
    lights = lookup('lights')
    return render_template("group.html", group=group, lights=lights)


@app.route("/light/<id>", methods=["GET", "POST"])
@login_required
def light(id):
    light = lookup(f'lights/{id}')
    lightOn = light['state']['on']
    return render_template("light.html", light=light, lightOn=lightOn, id=id)


@app.route("/control/<id>", methods=["POST"])
@login_required
def control(id):
    # collect command from form
    payload = request.data
    print(f'the payload is {payload}')

    # send JSON command to Hue hub
    response = sendCommand(f'lights/{id}/state', payload)

    # interpret Hue hub response
    print(f'#### the response is {response}')
    updates = {}
    for item in response:
        for outcome in item:
            if outcome == 'success' or outcome == 'updated':
                command = item[outcome]
                for path in command:
                    value = command[path]
                    control = path.replace(f'/lights/{id}/state/', '')
                    updates[control] = value
            else:
                error = item[outcome]
                control = error['address'].replace(f'/lights/{id}/state/', '')
                updates[control] = error
    
    # inform client of new light state
    print(f'#### the updates dict is {updates}')
    return json.dumps(updates)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure username is available
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            return apology("username unavailable", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure password confirmation was submitted
        elif not confirmation:
            return apology("must confirm password", 400)

        # Ensure password confirmation is correct
        elif confirmation != password:
            return apology("passwords do not match", 400)

        # Add user to database
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/account", methods=["GET", "POST"])
def account():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        oldpass = request.form.get("oldpass")
        if not oldpass:
            return apology("must provide old password", 400)

        # Ensure password was submitted
        newpass = request.form.get("newpass")
        if not newpass:
            return apology("must provide new password", 400)

        if newpass != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        oldHash = db.execute("SELECT hash FROM users WHERE id = ?", session['user_id'])[0]['hash']
        if not check_password_hash(oldHash, oldpass):
            return apology("old password is incorrect", 400)

        newHash = generate_password_hash(newpass)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", newHash, session['user_id'])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        username = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
        return render_template("account.html", username=username)
