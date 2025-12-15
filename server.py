# # server.py
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import time
# import random

# app = Flask(__name__)
# CORS(app) # อนุญาตให้หน้าเว็บเรียกใช้งานได้

# @app.route('/predict', methods=['POST'])
# def predict():
#     if 'video' not in request.files:
#         return jsonify({'error': 'No video uploaded'}), 400
    
#     video = request.files['video']
#     print(f"Received video: {video.filename}")
    
#     # --- จำลองการทำงาน AI (ใส่ Code AI จริงตรงนี้) ---
#     time.sleep(2) # แกล้งหน่วงเวลา
#     is_fake = random.choice([True, False])
#     confidence = random.uniform(80, 99)
    
#     return jsonify({
#         'filename': video.filename,
#         'result': 'FAKE' if is_fake else 'REAL',
#         'confidence': f"{confidence:.2f}"
#     })

# if __name__ == '__main__':
#     app.run(port=5000, debug=True)
    
# #py server.py


import os
import hashlib
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from ai_detector import detect_ai_generated
from blockchain import Blockchain

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

blockchain = Blockchain()
pending_block = None
NODES = set()

def consensus_reached(votes):
    agree = sum(1 for v in votes if v["vote"] == "AGREE")
    return agree > len(NODES) / 2

@app.route("/")
def home():
    return {
        "message": "Welcome to the AI Video Verification Blockchain Server",
        "endpoints": {
            "POST /upload_video": "Upload video → AI verify → add new block",
            "GET /chain": "View blockchain"
        }
    }


@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file"}), 400

    file = request.files["video"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    with open(filepath, "rb") as f:
        video_hash = hashlib.sha256(f.read()).hexdigest()

    verdict, confidence = detect_ai_generated(filepath)

    block_data = {
        "video_hash": video_hash,
        "verdict": verdict,
        "confidence": confidence,
        "model": "Demo Deepfake Detector"
    }

    # new_block = blockchain.create_block(block_data)
    global pending_block

    pending_block = {
        "data": block_data,
        "votes": []
}

    return jsonify({
        "message": "Block created successfully",
        # "block": new_block
        "pending_block": pending_block
    }), 202


@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(blockchain.chain)


@app.route("/vote", methods=["POST"])
def vote():
    global pending_block

    if pending_block is None:
        return jsonify({"error": "No pending block"}), 400

    data = request.json
    node = data.get("node")
    vote_value = data.get("vote")

    if node not in NODES:
        return jsonify({"error": "Unknown node"}), 400

    # กันโหวตซ้ำ
    if any(v["node"] == node for v in pending_block["votes"]):
        return jsonify({"error": "Node already voted"}), 400

    pending_block["votes"].append({
        "node": node,
        "vote": vote_value
    })

    # ตรวจ consensus
    if consensus_reached(pending_block["votes"]):
        new_block = blockchain.create_block(
            data=pending_block["data"]
        )
        pending_block = None

        return jsonify({
            "message": "Consensus reached, block added",
            "block": new_block
        }), 201

    return jsonify({
        "message": "Vote recorded, waiting for more votes",
        "votes": pending_block["votes"]
    }), 200

@app.route("/register_node", methods=["POST"])
def register_node():
    data = request.json
    node_name = data.get("node")
    ip = request.remote_addr

    if not node_name:
        return jsonify({"error": "Node name required"}), 400

    node_id = f"{node_name}:{ip}"
    NODES.add(node_id)
    return jsonify({
        "message": "Node registered",
        "nodes": list(NODES)
    }), 201

@app.route("/nodes", methods=["GET"])
def get_nodes():
    return jsonify({
        "nodes": list(NODES),
        "total": len(NODES)
    })


@app.route("/pending_block", methods=["GET"])
def get_pending_block():
    if pending_block is None:
        return jsonify({
            "message": "No pending block"
        }), 200

    return jsonify({
        "pending_block": pending_block,
        "required_votes": len(NODES) // 2 + 1,
        "total_nodes": len(NODES)
    }), 200

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
