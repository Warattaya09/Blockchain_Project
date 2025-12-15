import torch
import cv2
import numpy as np
from torchvision import transforms
from model import DeepfakeDetector
from video_utils import extract_frames
from face_utils import extract_faces

device = "cpu"

model = DeepfakeDetector().to(device)
model.eval()

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((299, 299)),
    transforms.ToTensor(),
])

def detect_ai_generated(video_path):
    frames = extract_frames(video_path)
    scores = []

    for frame in frames:
        faces = extract_faces(frame)

        for face in faces:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            x = transform(face).unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(x)
                prob = torch.sigmoid(output).item()
                scores.append(prob)

    if not scores:
        return "UNKNOWN", 0.0

    avg_score = sum(scores) / len(scores)

    verdict = "AI-GENERATED" if avg_score > 0.7 else "REAL"

    return verdict, round(avg_score, 3)
