import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_places")
def get_places():
    places = mongo.db.places.find()
    return render_template("places.html", places=places)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    places = mongo.db.places.find({"$text": {"$search": query}})
    return render_template("places.html", places=places)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):

    if session.get("user"):

        username = mongo.db.users.find_one({"username": session["user"]})["username"]

        if session["user"] == username:
            places = list(mongo.db.places.find({"created_by": username}))

            return render_template("profile.html", username=username, places=places)

    else:
        flash("You need to be logged in to view this")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_places", methods=["GET", "POST"])
def add_place():
    if request.method == "POST":
        places = {
            "place_name": request.form.get("place_name"),
            "country_name": request.form.get("country_name"),
            "cover_picture": request.form.get("cover_picture"),
            "place_description": request.form.get("place_description"),
            "place_website": request.form.get("place_website"),
            "place_map": request.form.get("place_map"),
            "created_by": session["user"]
        }
        mongo.db.places.insert_one(places)
        flash("New Place Successfully Added")
        return redirect(url_for("get_places"))

    return render_template("add_place.html")


@app.route("/edit_places/<place_id>", methods=["GET", "POST"])
def edit_places(place_id):
    if request.method == "POST":
        submit = {
            "place_name": request.form.get("place_name"),
            "country_name": request.form.get("country_name"),
            "cover_picture": request.form.get("cover_picture"),
            "place_description": request.form.get("place_description"),
            "place_website": request.form.get("place_website"),
            "place_map": request.form.get("place_map"),
            "created_by": session["user"]
        }
        mongo.db.places.update({"_id": ObjectId(place_id)}, submit)
        flash("Place Successfully Updated!")
        return redirect(url_for("get_places"))
    place = mongo.db.places.find_one({"_id": ObjectId(place_id)})
    return render_template("edit_place.html", place=place)


@app.route("/delete_place/<place_id>")
def delete_place(place_id):
    mongo.db.places.remove({"_id": ObjectId(place_id)})
    flash("Place Successfully Deleted")
    return redirect(url_for("get_places"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
