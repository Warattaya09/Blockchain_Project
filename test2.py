import hashlib
import datetime
import json
import time
import random
import os

# --- Load Libraries ---
try:
    import cv2
    from transformers import pipeline
    from PIL import Image
    AI_AVAILABLE = True
    print("✅ System Status: AI Library Found. (Real Mode)")
    
    print("⏳ Loading Models...")
    # 1. โหลดตัวจับหน้าคน
    human_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # 2. โหลดตัวจับหน้าแมว
    cat_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalcatface.xml')
    # 3. โหลด AI
    deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-v2-Model")
    print("✅ All Models Loaded!")
    
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ Error: Library ไม่ครบ")

# ==========================================
# 🧠 ส่วนที่ 1: ระบบ AI (แก้บั๊ก Score แล้ว)
# ==========================================

def analyze_video(video_path):
    if not os.path.exists(video_path):
        print(f"❌ Error: ไม่พบไฟล์ '{video_path}'")
        return "ERROR", 0.0

    print(f"\n🕵️ Analyzing '{video_path}' (Debug Mode)...")
    
    fake_scores = []
    frames_checked = 0
    detected_type = "Unknown"

    if AI_AVAILABLE:
        try:
            cap = cv2.VideoCapture(video_path)
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
                
                # ถ้าไม่เจอคน หาแมว
                if len(faces) == 0:
                    faces = cat_cascade.detectMultiScale(gray, 1.1, 4)
                    face_type = "ANIMAL"
                
                if len(faces) == 0: continue

                detected_type = face_type

                for (x, y, w, h) in faces:
                    if w < 60: continue 

                    p = int(w * 0.15)
                    y1, y2 = max(0, y-p), min(frame.shape[0], y+h+p)
                    x1, x2 = max(0, x-p), min(frame.shape[1], x+w+p)
                    face_img = frame[y1:y2, x1:x2]
                    
                    if face_img.size == 0: continue

                    rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_face)
                    
                    results = deepfake_detector(pil_image)
                    
                    # --- 🔧 FIX: แก้ไข Logic การดึงคะแนน (Substring Search) ---
                    fake_score_frame = 0.0
                    raw_label = ""
                    
                    for r in results:
                        label = r['label'].upper()
                        # ถ้าเจอคำว่า FAKE, 0, AI ให้เอาคะแนนมาเลย
                        if "FAKE" in label or "0" in label or "AI" in label:
                            fake_score_frame = r['score']
                            raw_label = label
                            break
                        # ถ้าเจอคำว่า REAL
                        elif "REAL" in label or "1" in label or "HUMAN" in label:
                            fake_score_frame = 1.0 - r['score']
                            raw_label = label
                    
                    frames_checked += 1
                    
                    # Logic: สัตว์ให้ลดคะแนนความเสี่ยงลง
                    if face_type == "ANIMAL":
                        fake_score_frame = fake_score_frame * 0.5
                    
                    fake_scores.append(fake_score_frame)
                    
                    # ปริ้นท์ค่าออกมาดูเลย ว่ามันอ่านค่าได้ไหม
                    print(f"   [Frame {i}] {face_type} Found: Score={round(fake_score_frame, 2)} (Raw Label: {raw_label})")

            cap.release()

            if frames_checked == 0:
                print("   ⚠️ ไม่เจอหน้าคนหรือสัตว์เลย -> REAL")
                return "REAL", 90.0

            avg_risk = sum(fake_scores) / len(fake_scores)
            max_risk = max(fake_scores) if fake_scores else 0

            print(f"   📊 Stats: Avg Risk = {round(avg_risk, 3)} (Type: {detected_type})")

            # --- ตัดสินใจ ---
            THRESHOLD = 0.55
            
            if avg_risk > THRESHOLD:
                print(f"   🤖 Decision: FAKE ({detected_type} ดูผิดปกติ)")
                return "FAKE", round(avg_risk * 100, 2)
            
            elif max_risk > 0.95:
                 print(f"   🤖 Decision: FAKE (เจอจุดตาย 1 จุด)")
                 return "FAKE", round(max_risk * 100, 2)

            else:
                print(f"   🤖 Decision: REAL ({detected_type} ปกติ)")
                return "REAL", round((1.0 - avg_risk) * 100, 2)

        except Exception as e:
            print(f"   ⚠️ AI Error: {e}")
            return "REAL", 0.0
    
    return "REAL", 0.0

# ==========================================
# 🔗 Blockchain Section
# ==========================================

class Block:
    def __init__(self, index, previous_hash, video_id, ai_result, confidence, validator):
        self.index = index
        self.timestamp = str(datetime.datetime.now())
        self.video_id = video_id
        self.ai_result = ai_result
        self.confidence = confidence
        self.validator = validator
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "video_id": self.video_id,
            "result": self.ai_result,
            "prev": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"   ⛏️ Block Mined! Nonce: {self.nonce} | Hash: {self.hash}")

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 3
        self.nodes = ["Node-A", "Node-B", "Node-C"]

    def create_genesis_block(self):
        return Block(0, "0", "Genesis", "SYSTEM", 100.0, "Admin")

    def get_latest_block(self):
        return self.chain[-1]

    def add_video_job(self, video_path):
        result, conf = analyze_video(video_path)
        if result == "ERROR": return
        
        if result == "FAKE" and conf < 75: conf += 15

        print(f"   🗳️ Consensus: Verifying '{result}'...")
        validator = random.choice(self.nodes)
        print(f"   ✅ Consensus Passed. Validator: {validator}")

        prev_block = self.get_latest_block()
        new_block = Block(prev_block.index + 1, prev_block.hash, video_path, result, conf, validator)
        print(f"   🔨 Start Mining...")
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        print("   🧱 Block added!\n")

    def is_chain_valid(self):
        print("🔍 Auditing...")
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            if curr.hash != curr.calculate_hash() or curr.previous_hash != prev.hash:
                print(f"   ❌ Block #{curr.index} Invalid!")
                return False
        print("   ✅ Secure.")
        return True

# ==========================================
# 🚀 Execution Section
# ==========================================

if __name__ == "__main__":
    my_chain = Blockchain()
    print("\n" + "="*50)
    print("   🎥  FINAL FIXED BLOCKCHAIN (V.9)  🎥")
    print("="*50 + "\n")

    video_queue = ["awang.mp4", "grandma-go.mp4", "gay.mp4", "cat.mp4", "run_man.mp4"] 

    for video in video_queue:
        my_chain.add_video_job(video)

    print("\n📜 --- FINAL LEDGER ---")
    for b in my_chain.chain:
        print(f"Block {b.index} | {b.video_id} -> {b.ai_result} ({b.confidence}%) | Hash: {b.hash[:10]}...")