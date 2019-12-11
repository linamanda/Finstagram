from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")
SALT = 'cs3083'

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="vanillaroses",
                             db="finstagram",
                             charset="utf8mb4",
                             port=3308,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])

@app.route("/upload", methods=["GET"])
@login_required
def upload():
    query = "SELECT * FROM belongto WHERE member_username = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (session["username"]))
    data = cursor.fetchall()

    return render_template("upload.html", groups=data)

@app.route("/images", methods=["GET"])
@login_required
def images():
    query1 = "SELECT * FROM photo AS p1 JOIN person ON (photoPoster = username) WHERE (allFollowers = TRUE AND %s = (SELECT username_follower FROM follow WHERE username_followed = p1.photoPoster AND username_follower = %s AND followStatus = TRUE)) OR (%s IN (SELECT member_username FROM belongto WHERE (owner_username, groupName) IN (SELECT groupOwner, groupName FROM sharedwith WHERE photoID = p1.photoID))) ORDER BY postingdate DESC"
    with connection.cursor() as cursor:
        cursor.execute(query1, (session["username"], session["username"], session["username"]))
    imgsData = cursor.fetchall()

    query2 = "SELECT photoID, pe2.username AS username, pe2.firstName AS firstName, pe2.lastName AS lastName, t1.tagstatus AS tagstatus FROM photo AS p1 JOIN person AS pe1 ON (photoPoster = pe1.username) JOIN tagged AS t1 USING (photoID) JOIN person AS pe2 ON (t1.username = pe2.username) WHERE p1.photoID IN (SELECT photoID FROM photo AS p1 JOIN person ON (photoPoster = username) WHERE (allFollowers = TRUE AND %s= (SELECT username_follower FROM follow WHERE username_followed = p1.photoPoster AND username_follower = %s AND followStatus = TRUE)) OR (%s IN (SELECT member_username FROM belongto WHERE (owner_username, groupName) IN (SELECT groupOwner, groupName FROM sharedwith WHERE photoID = p1.photoID)))) AND t1.tagstatus = TRUE"
    with connection.cursor() as cursor:
        cursor.execute(query2, (session["username"], session["username"], session["username"]))
    taggedData = cursor.fetchall()

    query3 = "SELECT photoID, l1.username AS username, l1.rating AS rating FROM photo AS p1 JOIN likes AS l1 USING (photoID) WHERE p1.photoID IN (SELECT photoID FROM photo AS p1 JOIN person ON (photoPoster = username) WHERE (allFollowers = TRUE AND %s= (SELECT username_follower FROM follow WHERE username_followed = p1.photoPoster AND username_follower = %s AND followStatus = TRUE)) OR (%s IN (SELECT member_username FROM belongto WHERE (owner_username, groupName) IN (SELECT groupOwner, groupName FROM sharedwith WHERE photoID = p1.photoID))))"
    with connection.cursor() as cursor:
        cursor.execute(query3, (session["username"], session["username"], session["username"]))
    likesData = cursor.fetchall()

    return render_template("images.html", images=imgsData, tags=taggedData, likers=likesData)

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route("/follow", methods=["GET"])
def follow():
    return render_template("follow.html")

@app.route("/followAuth", methods=["POST"])
def followAuth():
    requestData = request.form
    followee = requestData["username"]
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO follow VALUES ((SELECT username FROM person WHERE username = %s), %s, %s)"
            cursor.execute(query, (followee, session['username'], "0"))
    except pymysql.err.IntegrityError:
        error = "%s cannot be added. Please check your spelling or your following page" % (followee)
        return render_template('follow.html', error=error)

    error = "A request has been sent to %s." % (followee)
    return render_template("follow.html", error=error)

@app.route("/followers", methods=["GET"])
def followers():
    query1 = "SELECT username_follower AS username, firstName, lastName FROM follow JOIN person ON (username_follower = username) WHERE username_followed = %s AND followstatus = True"
    with connection.cursor() as cursor:
        cursor.execute(query1, (session['username']))
    followerData = cursor.fetchall()

    query2 = "SELECT username_follower AS username, firstName, lastName FROM follow JOIN person ON (username_follower = username) WHERE username_followed = %s AND followstatus = False"
    with connection.cursor() as cursor:
        cursor.execute(query2, (session['username']))
    followerRequestData = cursor.fetchall()

    return render_template("followers.html", followersData=followerData, followRequests=followerRequestData)

@app.route("/followersAuth", methods=["POST"])
def followersAuth():
    if request.form:
        requestData = request.form

        if "followRequestDecision" in requestData:
            decisions = requestData.getlist("followRequestDecision")
            for decision in decisions:
                decisionArr = decision.split("-")
                if decisionArr[0] == "1":
                    query = "UPDATE follow SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s"
                    with connection.cursor() as cursor:
                        cursor.execute(query, (session['username'], decisionArr[1]))
                if decisionArr[0] == "0":
                    query = "DELETE FROM follow WHERE username_followed = %s AND username_follower = %s"
                    with connection.cursor() as cursor:
                        cursor.execute(query, (session['username'], decisionArr[1]))
    return followers()

@app.route("/likeAuth", methods=["POST"])
def likeAuth():
    if request.form:
        requestData = request.form
        likeValue = requestData["rating"].split("-")

        query = "INSERT INTO likes VALUES (%s, %s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (session["username"], likeValue[1], time.strftime('%Y-%m-%d %H:%M:%S'), likeValue[0]))
    return images()

@app.route("/friendgroups", methods=["GET"])
def friendgroups():
    query = "SELECT * FROM friendgroup WHERE groupOwner = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (session["username"]))
    friendgroupsData = cursor.fetchall()
    return render_template("friendgroups.html", groups=friendgroupsData)

@app.route("/friendgroupadd", methods=["POST"])
def friendgroupadd():
    if request.form:
        requestData = request.form
        friendgroupName = requestData["groupname"]
        friendgroupDesc = "[No description.]"

        if "groupdesc" in requestData:
            friendgroupDesc = requestData["groupdesc"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO friendgroup VALUES (%s, %s, %s)"
                cursor.execute(query, (session['username'], friendgroupName, friendgroupDesc))
        except pymysql.err.IntegrityError:
            error = "%s is already an existing friend group you created." % (friendgroupName)

            query = "SELECT * FROM friendgroup WHERE groupOwner = %s"
            with connection.cursor() as cursor:
                cursor.execute(query, (session["username"]))
            friendgroupsData = cursor.fetchall()

            return render_template('friendgroups.html', groups=friendgroupsData, error=error)

    query = "SELECT * FROM friendgroup WHERE groupOwner = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (session["username"]))
    friendgroupsData = cursor.fetchall()

    error = "Friend group successfully created."
    return render_template("friendgroups.html", groups=friendgroupsData, error=error)

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"] + SALT
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)

@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"] + SALT
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO person (username, password, firstName, lastName) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (username, hashedPassword, firstName, lastName))
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")

@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    query = "SELECT * FROM belongto WHERE member_username = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (session["username"]))
    data = cursor.fetchall()

    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filePath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filePath)

        requestData = request.form
        captionInput = requestData["captionInput"]
        allFollowersBool = "0"

        if "allFollowersBool" in requestData:
            allFollowersBool = requestData["allFollowersBool"]

        query = "INSERT INTO photo (postingdate, filepath, allFollowers, caption, photoPoster) VALUES (%s, %s, %s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name, allFollowersBool, captionInput, session["username"]))

        if "fgroup" in requestData:
            friendGroups = requestData.getlist("fgroup")

            query2 = "SELECT LAST_INSERT_ID() FROM photo"
            with connection.cursor() as cursor:
                cursor.execute(query2)
            lastInsertedId = cursor.fetchone()

            query3 = "INSERT INTO sharedwith (groupOwner, groupName, photoID) VALUES (%s, %s, %s)"
            for fgroup in friendGroups:
                friendGroupArr = fgroup.split("-")

                with connection.cursor() as cursor:
                    cursor.execute(query3, (friendGroupArr[0], friendGroupArr[1], lastInsertedId["LAST_INSERT_ID()"]))

        message = "Image has been successfully uploaded."
        return render_template("upload.html", message=message, groups=data)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message, groups=data)

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run(debug=True)
