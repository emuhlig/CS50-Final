import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


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
    """Show portfolio of stocks"""
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session['user_id'])[0]['cash']
    portfolio = db.execute("SELECT symbol, shares FROM portfolio WHERE user_id = ? ORDER BY symbol", session['user_id'])
    portfolioValue = 0
    for holding in portfolio:
        quote = lookup(holding['symbol'])
        holding['price'] = quote['price']
        holding['value'] = quote['price'] * holding['shares']
        portfolioValue += holding['value']
    return render_template("index.html", portfolio=portfolio, cash=cash, portfolioValue=portfolioValue)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        # Check for valid user input
        if not request.form.get("symbol"):
            return apology("Must enter stock symbol", 400)

        try:
            shares = float(request.form.get("shares"))
        except ValueError:
            return apology("Invalid number of shares", 400)

        if shares < 1 or shares % 1 != 0:
            return apology("Invalid number of shares", 400)

        # Look up symbol and return apology if there's no response
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Stock not found", 400)

        # Check requested stock price and user's available funds
        cost = quote['price'] * shares
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session['user_id'])[0]['cash']

        if cash < cost:
            return apology("Insufficient funds", 400)

        db.execute("INSERT INTO transactions (user_id, symbol, price, shares, action) VALUES(?, ?, ?, ?, ?)",
                   session['user_id'], quote['symbol'], quote['price'], shares, "BUY")

        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - cost, session['user_id'])

        owner = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND symbol = ?",
                           session['user_id'], quote['symbol'])

        if not owner:
            db.execute("INSERT INTO portfolio (user_id, symbol, shares) VALUES(?, ?, ?)",
                       session['user_id'], quote['symbol'], shares)
        else:
            owned = owner[0]['shares']
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                       owned + shares, session['user_id'], quote['symbol'])

        # Redirect after successful purchase
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT symbol, price, shares, action, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        session['user_id'])
    return render_template("history.html", transactions=transactions)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        # Retrieve symbol from submitted form
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Must enter stock symbol", 400)
    else:
        # Retrieve symbol from query string
        symbol = request.args.get("symbol")

    if symbol:
        quote = lookup(symbol)
        if quote:
            return render_template("quoted.html", name=quote['name'], symbol=quote['symbol'], price=quote['price'])
        else:
            return apology("Stock not found", 400)
    else:
        return render_template("quote.html")


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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    holdings = db.execute("SELECT symbol FROM portfolio WHERE user_id = ? AND shares > 0", session['user_id'])
    symbols = []
    for holding in holdings:
        symbols.append(holding['symbol'])

    if request.method == "POST":

        # Check for valid user input
        if not request.form.get("symbol"):
            return apology("Must select a stock symbol", 400)

        try:
            shares = float(request.form.get("shares"))
        except ValueError:
            return apology("Invalid number of shares", 400)

        if shares < 1 or shares % 1 != 0:
            return apology("Invalid number of shares", 400)

        # Look up symbol and return apology if there's no response
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Stock not found", 400)

        owner = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND symbol = ?",
                           session['user_id'], quote['symbol'])
        owned = 0
        if owner:
            owned = owner[0]['shares']

        if not owner or owned == 0:
            return apology("You do not own this stock", 400)

        if owned < shares:
            return apology("You don't have that many shares to sell, bud", 400)

        # Check requested stock price and user's cash balance
        saleValue = quote['price'] * shares
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session['user_id'])[0]['cash']

        db.execute("INSERT INTO transactions (user_id, symbol, price, shares, action) VALUES(?, ?, ?, ?, ?)",
                   session['user_id'], quote['symbol'], quote['price'], shares, "SELL")

        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + saleValue, session['user_id'])

        remaining = owned - shares
        if remaining == 0:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?", session['user_id'], quote['symbol'])
        else:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
                       remaining, session['user_id'], quote['symbol'])

        # Redirect after successful sale
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html", symbols=symbols)


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
