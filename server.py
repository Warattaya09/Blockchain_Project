# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app) # อนุญาตให้หน้าเว็บเรียกใช้งานได้

@app.route('/predict', methods=['POST'])
def predict():
    if 'video' not in request.files:
        return jsonify({'error': 'No video uploaded'}), 400
    
    video = request.files['video']
    print(f"Received video: {video.filename}")
    
    # --- จำลองการทำงาน AI (ใส่ Code AI จริงตรงนี้) ---
    time.sleep(2) # แกล้งหน่วงเวลา
    is_fake = random.choice([True, False])
    confidence = random.uniform(80, 99)
    
    return jsonify({
        'filename': video.filename,
        'result': 'FAKE' if is_fake else 'REAL',
        'confidence': f"{confidence:.2f}"
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    
#py -m streamlit run app.py