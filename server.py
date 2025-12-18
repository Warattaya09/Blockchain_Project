import os
import hashlib
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from blockchain import Blockchain
import json
import time
import random
import math

# --- Load Libraries ---

import cv2
from transformers import pipeline
from PIL import Image

    # 1. โหลดตัวจับหน้าคน
human_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # 2. โหลดตัวจับหน้าแมว
cat_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalcatface.xml')
    # 3. โหลด AI
deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-v2-Model")

# ==========================================
# 🧠 ส่วนที่ 1: ระบบ AI (แก้บั๊ก Score แล้ว)
# ==========================================

def analyze_video(video_path):

    cap = cv2.VideoCapture(video_path)
    fake_scores = []
   
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(5, total_frames // 15) 

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # หาคนก่อน
        faces = human_cascade.detectMultiScale(gray, 1.1, 4)
        face_type = "HUMAN"

        for (x, y, w, h) in faces:
            if w < 60: continue 

            face = frame[y:y+h, x:x+w]
            rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)

            results = deepfake_detector(pil_image)

            fake_score = 0.0
            for r in results:
                label = r["label"].upper()
                if "FAKE" in label or "AI" in label or "0" in label:
                    fake_score = r["score"]
                    break
                elif "REAL" in label or "HUMAN" in label or "1" in label:
                    fake_score = 1.0 - r["score"]

            fake_scores.append(fake_score)
                
    cap.release()
    
    if not fake_scores:
            return "REAL", 50.0
    
    avg = sum(fake_scores) / len(fake_scores)
    if avg > 0.55:
        return "FAKE", round(avg * 100, 2)
    
    return "REAL", round((1.0 - avg) * 100, 2)

#
           

USERS_FILE = "users.json"
NODES_FILE = "nodes.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(users, user_id):
    if user_id not in users:
        users[user_id] = {
            "reputation": 0,
            "reward": 0,
            "balance": 100,
            "last_win": 0
        }
    else:
        users[user_id].setdefault("reputation", 0)
        users[user_id].setdefault("reward", 0)
        users[user_id].setdefault("balance", 100)
        users[user_id].setdefault("last_win", 0)
    return users[user_id]


def load_nodes():
    if not os.path.exists(NODES_FILE):
        return set()
    with open(NODES_FILE, "r") as f:
        data = json.load(f)
        return set(data.get("nodes", []))

def save_nodes(nodes):
    with open(NODES_FILE, "w") as f:
        json.dump({"nodes": list(nodes)}, f, indent=2)


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

blockchain = Blockchain()
pending_block = None
NODES = load_nodes()

REQUIRED_VOTES = math.ceil (len(NODES) * 2 / 3)

def consensus_reached(votes):

    # if len(NODES) == 0:
    #     return False
    
    # agree = sum(1 for v in votes if v["vote"] == "AGREE")
    # # return agree > len(NODES) / 2
    # return agree >= (len(NODES) // 2 + 1)
    return len(votes) >= (len(NODES) // 2 + 1)

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

    UPLOAD_FEE = 20

    prediction = request.form.get("prediction")  # REAL / FAKE

    users = load_users()
    
    uploader = request.form.get("uploader", "anonymous")
    uploader_user = get_user(users, uploader)

    if uploader_user["balance"] < UPLOAD_FEE:
        return jsonify({
            "error": "Insufficient balance to upload video"
        }), 403

    uploader_user["balance"] -= UPLOAD_FEE
    save_users(users)

    # if "video" not in request.files:
    #     return jsonify({"error": "No video file"}), 400
    global pending_block

    if "video" not in request.files:
        return jsonify({"error": "No video file"}), 400
    
    uploader = request.form.get("uploader", "anonymous")

    file = request.files["video"]
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    # filename = secure_filename(file.filename)
    # filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)


    with open(filepath, "rb") as f:
        video_hash = hashlib.sha256(f.read()).hexdigest()

    verdict, confidence = analyze_video(filepath)

    # block_data = {
    #     "video_hash": video_hash,
    #     "verdict": verdict,
    #     "confidence": confidence,
    #     "model": "Demo Deepfake Detector"
    # }

    # new_block = blockchain.create_block(block_data)
    # global pending_block

    pending_block = {
        "data": {
            "video_hash": video_hash,
            "verdict": verdict,
            "confidence": confidence,
            "uploader": uploader,
            "prediction": prediction,
            "model": "Demo Deepfake Detector",
            "created_at": time.time(),
        },
        "votes": [],
        "uploader_pool": UPLOAD_FEE
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
    
    # # data = request.json
    # node_id = data.get("node")
    # vote_value = data.get("vote")
    data = request.get_json() or request.form
    node = request.json.get("node")
    vote = request.json.get("vote")

    if vote not in ["REAL", "FAKE"]:
        return jsonify({"error": "Invalid vote value"}), 400


    if node not in NODES:
        return jsonify({"error": "Unknown node"}), 400
    
    if not node or not vote:
        return jsonify({"error": "Missing data"}), 400
    

    # กันโหวตซ้ำ
    if any(v["node"] == node for v in pending_block["votes"]):
        return jsonify({"error": "Node already voted"}), 400

    pending_block["votes"].append({
        "node": node,
        "vote": vote
    })
    result = check_timeout_and_finalize()
    if result:
        return jsonify(result), 201

    # return jsonify({
    #     "message": "Vote recorded",
    #     "current_votes": len(pending_block["votes"])
    # }), 200


    # ----- HYBRID CONSENSUS -----
    ai_verdict = pending_block["data"]["verdict"]
    ai_confidence = pending_block["data"]["confidence"]

    # เมื่อมี vote ครบขั้นต่ำ
    REQUIRED_VOTES = len(NODES) // 2 + 1

    if len(pending_block["votes"]) >= REQUIRED_VOTES:

        ai_verdict = pending_block["data"]["verdict"]
        ai_confidence = pending_block["data"]["confidence"]

        # final_result, final_score = hybrid_consensus(
        #     ai_verdict,
        #     ai_confidence,
        #     pending_block["votes"]
        # )
        consensus = hybrid_consensus(
            ai_verdict,
            ai_confidence,
            pending_block["votes"]
        )

        final_result = consensus["final_result"]
        final_score = consensus["final_score"]


        users = load_users()
        uploader = pending_block["data"]["uploader"]
        uploader_user = get_user(users, uploader)

      

        created_at = pending_block["data"]["created_at"]
        if time.time() - created_at > 120:
            users = load_users()
            # winner = weighted_random_winner(NODES, users)

        # users = load_users()

        # uploader = pending_block["data"]["uploader"]
        # uploader_user = get_user(users, uploader)

        # คนที่โหวตตรงกับผลสุดท้าย
        correct_voters = [
            v["node"]
            for v in pending_block["votes"]
            if v["vote"] == final_result
        ]
        # winner = random.choice(correct_voters) if correct_voters else None

        #กูเอาคอมเม้นออก อิอิ
        winner = weighted_random_winner(correct_voters, users)

        #กูเพิ่มโค้ดตรงนี้มาเอง
        pool = pending_block.get("uploader_pool", 0)
        if winner and pool > 0:
            user[winner]["Balance"] += pool

        for n in correct_voters:
            get_user(users, n)

        winner = weighted_random_winner(correct_voters, users)


        if winner:
            users[winner]["last_win"] = time.time()


        # รางวัล uploader
        if final_result == ai_verdict:
            uploader_user["reward"] += 5
        else:
            uploader_user["reward"] += 10

        # uploader_user["reputation"] += 1
        if pending_block["data"]["prediction"] == final_result:
            uploader_user["balance"] += 10   # คืนบางส่วน
            uploader_user["reputation"] += 2
        else:
            uploader_user["reputation"] += 1


        # รางวัล validator
        for v in pending_block["votes"]:
            voter = v["node"]
            voter_user = get_user(users, voter)

            if v["vote"] == final_result:
                if voter == winner:
                    # 🏆 WINNER
                    voter_user["reputation"] += 3
                    voter_user["reward"] += 20
                else:
                    # 👍 โหวตถูกแต่ไม่ใช่ winner
                    voter_user["reputation"] += 1
                    voter_user["reward"] += 5


        save_users(users)

        # 🔗 เพิ่ม block (เก็บผล hybrid)
        new_block = blockchain.create_block(
            data={
                # **pending_block["data"],
                # "final_result": final_result,
                # "consensus_score": final_score,
                # "votes": pending_block["votes"],
                # "block_creator": winner   # 🧱 ผู้สร้าง block
                **pending_block["data"],

                # 🔹 AI
                "ai_verdict": pending_block["data"]["verdict"],
                "ai_confidence": pending_block["data"]["confidence"],
                "ai_score": consensus["ai_score"],
                "ai_weight": consensus["ai_weight"],

                # 🔹 HUMAN
                "human_score": consensus["human_score"],
                "human_weight": consensus["human_weight"],
                # "votes": pending_block["votes"],

                # 🔹 FINAL
                "final_score": consensus["final_score"],
                "final_result": consensus["final_result"],

                # 🔹 BLOCK
                "block_creator": winner

            }
        )

        votes_count = len(pending_block["votes"])
        pending_block = None

        return jsonify({
            "message": "Hybrid consensus reached",
            "final_result": final_result,
            "consensus_score": final_score,
            "winner": winner,
            "block": new_block,
            "current_votes": votes_count,
            "required_votes": REQUIRED_VOTES

        }), 201
    return jsonify({
        "message": "Vote recorded",
        "current_votes": len(pending_block["votes"])
    }), 200

@app.route("/register_node", methods=["POST"])
def register_node():
    global NODES

    data = request.get_json(silent=True) or request.form
    node_name = data.get("node")
    # node = request.form.get("node")
    ip = request.remote_addr

    if not node_name:
        return jsonify({"error": "Node name required"}), 400

    node_id = f"{node_name}:{ip}"

    for n in NODES:
        existing_name, existing_ip = n.split(":")
        if existing_name == node_name:
            return jsonify({
                "error": "Node name already exists"
            }), 403

    for n in NODES:
        if n.endswith(f":{ip}"):
            return jsonify({
                "error": "This IP already registered a node"
            }), 403
    

    if node_id  in NODES:
        return jsonify({"message": "Node already registered"}), 200

    NODES.add(node_id)
    save_nodes(NODES)

    global REQUIRED_VOTES
    REQUIRED_VOTES = math.ceil(len(NODES) * 2 / 3)

        # return {"message": "Node registered", "node": node_name, "nodes": list(nodes)}, 201

    return jsonify({
        "message": "Node registered",
        "node": node_id,
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
    result = check_timeout_and_finalize()
    if result:
        return jsonify(result), 200
    
    if pending_block is None:
        return jsonify({
            "message": "No pending block"
        }), 200

    return jsonify({
        "pending_block": pending_block,
        "required_votes": len(NODES) // 2 + 1,
        "total_nodes": len(NODES),
        "remaining_time": max(0,120 - int(time.time() - pending_block["data"]["created_at"]))
    }), 200

def hybrid_consensus(ai_verdict, ai_confidence, votes):
    """
    ai_verdict: 'REAL' | 'FAKE' | 'UNCERTAIN'
    ai_confidence: 0 - 100
    votes: [{node, vote}]
    """

    # -------- AI SCORE (60%) --------
    if ai_verdict == "REAL":
        ai_score = ai_confidence / 100
    elif ai_verdict == "FAKE":
        ai_score = 1 - (ai_confidence / 100)
    else:  # UNCERTAIN
        ai_score = 0.5

    ai_weighted = ai_score * 0.6

    # -------- HUMAN SCORE (40%) --------
    if not votes:
        human_score = 0.5
    else:
        agree = sum(1 for v in votes if v["vote"] == "REAL")
        human_score = agree / len(votes)

    human_weighted = human_score * 0.4

    # -------- FINAL --------
    final_score = ai_weighted + human_weighted
    final_result = "REAL" if final_score > 0.7 else "FAKE"

    # return final_result, round(final_score, 3)
    return {
        "ai_score": round(ai_score, 3),
        "ai_weight": ai_weighted,
        "ai_weighted": round(ai_weighted, 3),

        "human_score": round(human_score, 3),
        "human_weight": human_weight,
        "human_weighted": round(human_weighted, 3),

        "final_score": round(final_score, 3),
        "final_result": final_result
    }

def weighted_random_winner(nodes, users):
    candidates = []
    for n in nodes:
        u = get_user(users, n)
        last_win = u.get("last_win", 0)
        if time.time() - last_win < 120:
            continue  # ❌ ชนะติดกันไม่ได้
        weight = max(1, u["reputation"])
        candidates.extend([n] * weight)

    return random.choice(candidates) if candidates else None

def check_timeout_and_finalize():
    global pending_block

    if pending_block is None:
        return None

    created_at = pending_block["data"]["created_at"]

    # ยังไม่ครบ 2 นาที
    if time.time() - created_at < 120:
        return None

    votes = pending_block["votes"]

    # ❌ ไม่มีคนโหวต
    if len(votes) == 0:
        pending_block = None
        return {
            "status": "discarded",
            "reason": "No votes"
        }

    # ✅ มีคนโหวต → สุ่ม winner
    users = load_users()
    voters = [v["node"] for v in votes]

    winner = weighted_random_winner(voters, users)

    if not winner:
        pending_block = None
        return {
            "status": "discarded",
            "reason": "No eligible winner"
        }

    # 🎁 ให้รางวัล
    winner_user = get_user(users, winner)
    winner_user["reward"] += 20
    winner_user["reputation"] += 3
    winner_user["last_win"] = time.time()

    save_users(users)

    # 🔗 สร้าง block
    new_block = blockchain.create_block(
        data={
            **pending_block["data"],
            "block_creator": winner,
            # "votes": votes
        }
    )

    pending_block = None

    return {
        "status": "finalized",
        "winner": winner,
        "block": new_block
    }


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
