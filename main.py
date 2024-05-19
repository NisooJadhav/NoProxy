import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://noproxy-a9ae8-default-rtdb.asia-southeast1.firebasedatabase.app/",
        "storageBucket": "noproxy-a9ae8.appspot.com",
    },
)

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

bg = cv2.imread("Resources/bg.png")

# importing mode images
folderModePath = "Resources/Modes"
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

print("Loading Encode File ...")
file = open("EncodeFile.p", "rb")
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode file loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    success, img = cap.read()
    if img is not None:
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    else:
        print("error: img not loaded")

    faceFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceFrame)

    # resized_img = cv2.resize(img, (585, 318))
    # img[162:162 + 480, 55:55 + 640] = img[162:162 + 480, 55:55 + 640]

    bg[162 : 162 + 480, 55 : 55 + 640] = img
    bg[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

    if faceFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                bg = cvzone.cornerRect(bg, bbox, rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    cvzone.putTextRect(bg, "Loading", (275, 400))
                    cv2.imshow("Student Attendance", bg)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

            if counter != 0:
                if counter == 1:
                    studentInfo = db.reference(f"Students/{id}").get()
                    print(studentInfo)
                    blob = bucket.get_blob(f"Images/{id}.jpg") or bucket.get_blob(
                        f"Images/{id}.jpeg"
                    )
                    if blob:
                        print(f"Found image: {blob.name}")
                        array = np.frombuffer(blob.download_as_string(), np.uint8)
                        imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    else:
                        print("img not found")
                        imgStudent = None

                    datetimeObject = datetime.strptime(
                        studentInfo["last_attendance_time"], "%Y-%m-%d %H:%M:%S"
                    )
                    timeDiff = datetime.now() - datetimeObject

                    if timeDiff.total_seconds() > 86400:  # 24 hours in seconds
                        ref = db.reference(f"Students/{id}")
                        studentInfo["total_attendance"] += 1
                        ref.child("total_attendance").set(
                            studentInfo["total_attendance"]
                        )
                        ref.child("last_attendance_time").set(
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    else:
                        modeType = 3
                        counter = 0
                        bg[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

                if counter != 0 and modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2

                    bg[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        cv2.putText(
                            bg,
                            str(studentInfo["total_attendance"]),
                            (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            (255, 255, 255),
                            1,
                        )
                        cv2.putText(
                            bg,
                            str(studentInfo["course"]),
                            (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.5,
                            (255, 255, 255),
                            1,
                        )
                        cv2.putText(
                            bg,
                            str(id),
                            (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.5,
                            (255, 255, 255),
                            1,
                        )
                        cv2.putText(
                            bg,
                            str(studentInfo["standing"]),
                            (910, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1,
                        )
                        cv2.putText(
                            bg,
                            str(studentInfo["year"]),
                            (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1,
                        )
                        cv2.putText(
                            bg,
                            str(studentInfo["starting_year"]),
                            (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1,
                        )
                        (w, h), _ = cv2.getTextSize(
                            studentInfo["name"], cv2.FONT_HERSHEY_COMPLEX, 1, 1
                        )
                        offset = (414 - w) // 2
                        cv2.putText(
                            bg,
                            str(studentInfo["name"]),
                            (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            (50, 50, 50),
                            1,
                        )
                        if imgStudent is not None:
                            bg[175 : 175 + 216, 909 : 909 + 216] = imgStudent

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = []
                        imgStudent = []
                        bg[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    cv2.imshow("Student Attendance", bg)
    cv2.waitKey(1)
