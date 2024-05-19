import os
import subprocess
import cv2
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json

import firebase_admin
from firebase_admin import credentials, db, storage

app = Flask(__name__, static_folder="Z:\\NoProxy\\static")

UPLOAD_FOLDER = "Images"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://noproxy-a9ae8-default-rtdb.asia-southeast1.firebasedatabase.app/",
        "storageBucket": "noproxy-a9ae8.appspot.com",
    },
)
ref = db.reference("Students")

current_time = datetime.now()

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure key
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "smart_cctv"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


@app.route("/", methods=["GET"])
def index():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" in session:
        students_ref = db.reference("Students")
        students = students_ref.get()
        student_list = []
        total_attendance_list = []

        for idx, student_data in enumerate(students):
            if student_data is None:
                student_dict = {
                    "id": None,
                    "name": None,
                    "course": None,
                    "starting_year": None,
                    "total_attendance": None,
                    "standing": None,
                    "year": None,
                    "last_attendance_time": None,
                    "image_url": None,
                }
            else:
                student_dict = student_data
                student_dict["id"] = idx  # Set the 'id' key with the index

                # Collect total attendance for the bar chart
                if "total_attendance" in student_dict:
                    total_attendance_list.append(student_dict["total_attendance"])

                # Generate image URL if exists
                bucket = storage.bucket()
                blob = bucket.get_blob(f"Images/{idx}.jpg") or bucket.get_blob(
                    f"Images/{idx}.jpeg"
                )
                if blob:
                    student_dict["image_url"] = blob.generate_signed_url(
                        timedelta(seconds=300), method="GET"
                    )
                else:
                    student_dict["image_url"] = None

            student_list.append(student_dict)

        print(student_list)

        # Calculate total students
        total_students = len(student_list)

        # Convert data to JSON for use in JavaScript
        student_data_json = json.dumps(student_list)
        total_attendance_json = json.dumps(total_attendance_list)

        if request.method == "POST":
            ref = db.reference(f"Students")
            if "delete_student" in request.form:
                student_id = request.form["delete_student"]
                ref_to_delete = ref.child(student_id)
                ref_to_delete.delete()
                return redirect(url_for("dashboard"))
            else:
                roll_number = request.form["roll_number"]
                name = request.form["name"]
                course = request.form["course"]
                starting_year = int(request.form["starting_year"])
                total_attendance = int(request.form["total_attendance"])
                standing = request.form["standing"]
                year = int(request.form["year"])
                last_attendance_time = request.form["last_attendance_time"]
                profile_pic = request.files["profile_pic"]

                if "profile_pic" not in request.files:
                    return "No file part"

                if profile_pic.filename == "":
                    return "No selected file"

                if profile_pic:
                    filename = secure_filename(
                        roll_number + os.path.splitext(profile_pic.filename)[-1]
                    )
                    # Save the file locally
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    profile_pic.save(file_path)
                    subprocess.run(["py", "EncodeGenerator.py"])

                    img = cv2.imread(file_path)
                    resized_img = cv2.resize(
                        img, (216, 216), interpolation=cv2.INTER_AREA
                    )
                    cv2.imwrite(file_path, resized_img)

                    folderPath = "Images"
                    pathList = os.listdir(folderPath)
                    imgList = []
                    studentIds = []

                    for path in pathList:
                        imgList.append(cv2.imread(os.path.join(folderPath, path)))
                        studentIds.append(os.path.splitext(path)[0])
                        fileName = f"{folderPath}/{path}"
                        bucket = storage.bucket()
                        blob = bucket.blob(fileName)
                        blob.upload_from_filename(fileName)

                    # Upload to Firebase Storage
                    # bucket = storage.bucket()
                    # blob = bucket.blob(filename)
                    # blob.upload_from_filename(file_path)

                data = {
                    "name": name,
                    "course": course,
                    "starting_year": starting_year,
                    "total_attendance": total_attendance,
                    "standing": standing,
                    "year": year,
                    "last_attendance_time": last_attendance_time,
                }

                existing_data = ref.child("Students").child(roll_number).get()
                if existing_data is not None and existing_data.val():
                    print(f"Roll Number {roll_number} already exists.")
                    return render_template(
                        "dashboard.html", error="Roll Number already exists."
                    )
                else:
                    ref.child(roll_number).set(data)
                    print(f"Data inserted with Roll Number {roll_number}.")
                    return render_template(
                        "dashboard.html", success="Data inserted successfully."
                    )
            # ref.push().set(data)
            # ref.child("Students").child(roll_number).set(data)
        return render_template(
            "dashboard.html",
            username=session["username"],
            students=student_list,
            total_students=total_students,
            student_data_json=student_data_json,
            total_attendance_json=total_attendance_json,
            now=current_time,
        )
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,),
        )
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            session["username"] = username
            return redirect(url_for("index"))
        else:
            form.username.errors.append("Invalid username or password")
            form.password.errors.append("Invalid username or password")
    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("index"))
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,),
        )
        user = cur.fetchone()
        if user:
            form.username.errors.append("Username already exists")
            return render_template("signup.html", form=form)
        password = bcrypt.hashpw(
            form.password.data.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password),
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    students_ref = db.reference("Students")
    students = students_ref.get()
    student_list = []
    for idx, student_data in enumerate(students):
        if student_data is None:
            student_dict = {
                "id": None,
                "name": None,
                "course": None,
                "starting_year": None,
                "total_attendance": None,
                "standing": None,
                "year": None,
                "last_attendance_time": None,
                "image_url": None,
            }
        else:
            student_dict = student_data
            student_dict["id"] = idx  # Set the 'id' key with the index

            bucket = storage.bucket()
            blob = bucket.get_blob(f"Images/{idx}.jpg") or bucket.get_blob(
                f"Images/{idx}.jpeg"
            )
            if blob:
                student_dict["image_url"] = blob.generate_signed_url(
                    timedelta(seconds=300), method="GET"
                )
            else:
                student_dict["image_url"] = None

        student_list.append(student_dict)

    return render_template("attendance.html", students=student_list, now=current_time)


@app.route("/home")
def home():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    else:
        return redirect(url_for("login"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

# @app.teardown_request
# def clear_session(exception=None):
#     session.clear()
