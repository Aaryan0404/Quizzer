import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, randomstring

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///schedule.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of questions"""

    if request.method == "POST" or "GET":
        f = db.execute("SELECT * FROM testbank WHERE id = :user_id", user_id=session["user_id"])
        if not len(f) == 0:
            current_username = f[0]["username"]
            questions = db.execute("SELECT question_id, question, ca, test_id FROM testbank WHERE username = :username", username=current_username)
        else:
            questions = []

        #Redirects user to index.html
        return render_template("index.html", questions=questions)


@app.route("/creatorhelper", methods=["POST"])
@login_required
def creatorhelper():
    """Help create questions"""

    if not request.form.get("haha"):
        return apology("Please type in INDEPENDENT or TEST into the input box", 400)

    if request.form.get("haha") == "INDEPENDENT":
        alpo = randomstring()
        a = db.execute("SELECT * FROM testbank WHERE test_id = :test_id", test_id=alpo)

        while not len(a) == 0:
            alpo = randomstring()

        return render_template("creator1.html", test_id=alpo)
    elif request.form.get("haha") == "TEST":
        f = db.execute("SELECT * FROM testbank WHERE id = :user_id", user_id=session["user_id"])

        if not len(f) == 0:
            return render_template("creator2.html")
        else:
            return apology("You first have to create an independent question before you can add questions to a test")
    else:
        return apology("Please type in INDEPENDENT or TEST into the input box", 400)


@app.route("/createquestion", methods=["GET", "POST"])
@login_required
def createquestion():
    """Create questions"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #Ensure inputs are not blank
        if not request.form.get("test_id"):
            return apology("Please copy the Test ID shown", 400)

        if not request.form.get("question"):
            return apology("Please enter a valid input for the question", 400)

        if not request.form.get("answer4") or not request.form.get("answer3") or not request.form.get("answer2") or not request.form.get("answer1") or not request.form.get("ca"):
            return apology("Please enter a valid input for all the answer choices, and identify the correct choice", 400)

        if not (request.form.get("ca") == "A" or request.form.get("ca") == "B" or request.form.get("ca") == "C" or request.form.get("ca") == "D"):
            return apology("Please enter A, B, C, OR D, as the input for the correct answer choice", 400)

        f = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])
        current_username = f[0]["username"]

        test_id = request.form.get("test_id")
        question = request.form.get("question")
        answer1 = request.form.get("answer1")
        answer2 = request.form.get("answer2")
        answer3 = request.form.get("answer3")
        answer4 = request.form.get("answer4")
        correct = request.form.get("ca")

        if answer1 == answer2 or answer1 == answer3 or answer1 == answer4 or answer2 == answer3 or answer2 == answer4 or answer3 == answer4:
            return apology("Please enter unique choices for all answer options", 400)

        db.execute("INSERT INTO testbank (username, test_id, question, a1, a2, a3, a4, ca, id) VALUES (:username, :test_id, :question, :a1, :a2, :a3, :a4, :ca, :am)", username=current_username, test_id=test_id, question=question, a1=answer1, a2=answer2, a3=answer3, a4=answer4, ca=correct, am=session["user_id"])

        return redirect("/")

    elif request.method == "GET":
        return render_template("asker.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    if request.method == "GET":
        username = request.args.get("username")
        if len(username) >= 1:
            uuu = db.execute("SELECT * FROM users WHERE username = :a", a=username)
            if len(uuu) == 0:
                return jsonify(True)
            else:
                return jsonify(False)
        else:
            return jsonify(True)


@app.route("/answerlog")
@login_required
def answerlog():
    """Show history of answers to question"""

    f = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])
    current_username = f[0]["username"]

    bigs = db.execute("SELECT question FROM testbank WHERE username = :username", username=current_username)

    question_ids = []
    questions = []
    ias = []
    cas = []
    aus = []
    ts = []

    if not len(bigs) == 0:
        for i in range(len(bigs)):
            question = bigs[i]["question"]
            smalls = db.execute("SELECT * FROM answerlog WHERE question = :question", question=question)
            for x in range(len(smalls)):
                question_ids.append(smalls[x]["question_id"])
                questions.append(smalls[x]["question"])
                ias.append(smalls[x]["input_answer"])
                cas.append(smalls[x]["correct_answer"])
                aus.append(smalls[x]["username"])
                ts.append(smalls[x]["Attempt_Time"])
    else:
        smalls = []

    alpha = len(question_ids)
    dhs = list(range(alpha))
    return render_template("answerlog.html", dhs=dhs, question_ids=question_ids, questions=questions, ias=ias, cas=cas, aus=aus, ts=ts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #Ensure username input exists
        if not request.form.get("username"):
            return apology("Must register for a username", 400)

        # Query database to check whether the username already exisits
        abc = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if len(abc) != 0:
            return apology("Username inputted has already been taken", 400)

        #Ensure password input exists
        if not request.form.get("password"):
            return apology("Must register for a account password", 400)

        #Ensure password confirmation input exists
        if not request.form.get("confirmation"):
            return apology("Must confirm account password", 400)

        #Ensure password input matches password confirmation input
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Confirmation input must match password input", 400)

        new_user_username = request.form.get("username")
        new_user_password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        defa = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashy)", username=new_user_username, hashy=new_user_password)

        session["user_id"] = defa
        return redirect("/")

    elif request.method == "GET":
        return render_template("register.html")


@app.route("/answerquestion", methods=["GET", "POST"])
@login_required
def answerquestion():
    """Answer questions created by others"""
    if request.method == "GET":
        return render_template("ask.html")

    elif request.method == "POST":

        if not request.form.get("input"):
            return apology("Please enter a valid test ID", 400)

        test_id = request.form.get("input")
        adgc = db.execute("SELECT question, a1, a2, a3, a4, question_id, ca, username FROM testbank WHERE test_id = :amc", amc=test_id)
        globalizer(adgc)

        if len(adgc) == 0:
            return apology("Please enter a valid test ID", 400)

        else:
            return render_template("answerer1.html", questions=adgc)


def globalizer(x):
    global apple
    apple = x


@app.route("/answercheck", methods=["GET", "POST"])
@login_required
def answercheck():
    answers = request.form.getlist("beta")
    cv = 0
    iv = 0

    f = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])
    current_username = f[0]["username"]

    for i in range(len(answers)):
        question = apple[i]["question"]
        question_id = apple[i]["question_id"]
        ca = apple[i]["ca"]
        ia = answers[i]
        alal = db.execute("INSERT INTO answerlog (question_id, question, input_answer, correct_answer, username) VALUES (:question_id, :question, :input_answer, :correct_answer, :username)", question_id=question_id, question=question, input_answer=ia, correct_answer=ca, username=current_username)
        if ia == ca:
            cv = cv + 1
        else:
            iv = iv + 1

    percentage = (cv/len(answers)) * 100
    return render_template("score.html", percentage=percentage)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
