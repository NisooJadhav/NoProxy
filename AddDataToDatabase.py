import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://noproxy-a9ae8-default-rtdb.asia-southeast1.firebasedatabase.app/"
    },
)

ref = db.reference("Students")

data = {
    "2": {
        "name": "Elon Musk",
        "course": "9th",
        "starting_year": 2023,
        "total_attendance": 5,
        "standing": "G",
        "year": 15,
        "last_attendance_time": "2024-04-11 00:54:34",
    }
}

for key,value in data.items():
    ref.child(key).set(value)
