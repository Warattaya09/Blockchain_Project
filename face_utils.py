import cv2

# โหลดโมเดลตรวจจับหน้า (มากับ OpenCV)
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def extract_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces_rect = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    faces = []
    for (x, y, w, h) in faces_rect:
        face = frame[y:y+h, x:x+w]
        faces.append(face)

    return faces
