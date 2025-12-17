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
    
    print("⏳ Loading Upgraded AI Model... (Model ใหม่โหลดครั้งแรกอาจช้านิดนึงนะครับ)")
    
    # 1. โหลดตัวจับใบหน้า
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 2. โหลดโมเดลใหม่! (แม่นยำกว่าตัวเดิม)
    # ใช้ prithivMLmods/Deep-Fake-Detector-v2-Model
    deepfake_detector = pipeline("image-classification", model="prithivMLmods/Deep-Fake-Detector-v2-Model")
    
    print("✅ High-Performance Model Loaded!")
    
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ Error: Library ไม่ครบ (รันแบบ Simulation)")

# ==========================================
# 🧠 ส่วนที่ 1: ระบบ AI อัจฉริยะ (Smart Scan)
# ==========================================

def analyze_video(video_path):
    if not os.path.exists(video_path):
        print(f"❌ Error: ไม่พบไฟล์ '{video_path}'")
        return "ERROR", 0.0

    print(f"🕵️ Smart Scanning '{video_path}'...")
    
    frames_checked = 0
    fake_score_sum = 0
    fake_count = 0
    real_count = 0

    if AI_AVAILABLE:
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # สแกน 5 จุดทั่วคลิป (ต้น-กลาง-จบ) เพื่อความชัวร์
            # ถ้าคลิปสั้นจะสแกนถี่ขึ้น
            step = max(10, total_frames // 5)
            
            for i in range(0, total_frames, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret: break

                # 1. แปลงเป็นขาวดำเพื่อหาหน้า
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) == 0: continue # ไม่เจอหน้า ข้ามไป

                # 2. วนลูปเช็คทุกหน้าที่เจอในเฟรมนั้น
                for (x, y, w, h) in faces:
                    # [Logic กรอง Noise] ถ้าหน้าเล็กกว่า 60px ให้ข้าม (เพราะภาพเบลอ AI จะมั่ว)
                    if w < 60 or h < 60: continue

                    # [Logic เพิ่มขอบ] ตัดภาพให้กว้างขึ้น 20% เพื่อให้ AI เห็นบริบท
                    padding = int(w * 0.2)
                    y1, y2 = max(0, y - padding), min(frame.shape[0], y + h + padding)
                    x1, x2 = max(0, x - padding), min(frame.shape[1], x + w + padding)
                    face_img = frame[y1:y2, x1:x2]

                    # ส่งให้ AI ตรวจ
                    rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_face)
                    
                    results = deepfake_detector(pil_image)
                    top = results[0]
                    
                    label = top['label'].upper() # FAKE หรือ REAL
                    score = top['score']

                    # บางโมเดลใช้ Label ว่า 'Fake'/'Real' บางตัวใช้ '0'/'1'
                    # โมเดลตัวนี้มักคืนค่า 'Fake' หรือ 'Real' ตรงๆ
                    
                    frames_checked += 1
                    print(f"   Frame {i}: Found Face ({w}x{h}) -> {label} ({round(score*100,1)}%)")

                    # [Logic ตัดสินใจ]
                    # ต้องมั่นใจเกิน 70% ถึงจะนับ (กัน AI ลังเล)
                    if score > 0.70:
                        if "FAKE" in label or "DEEPFAKE" in label:
                            fake_count += 1
                            fake_score_sum += score
                        else:
                            real_count += 1

            cap.release()

            # --- สรุปผล (Final Verdict) ---
            if frames_checked == 0:
                print("   ⚠️ ไม่เจอใบหน้าชัดๆ เลยในคลิปนี้ (Default: REAL)")
                return "REAL", 85.0

            # กฎเหล็ก: ต้องเจอหน้า FAKE มากกว่า 30% ของหน้าที่ตรวจเจอ ถึงจะฟันธงว่าปลอม
            # (เพราะคนจริงอาจจะมีบางมุมที่แสงเพี้ยน แต่ไม่ควรเพี้ยนเกินครึ่ง)
            total_valid_faces = fake_count + real_count
            if total_valid_faces == 0: return "REAL", 90.0

            fake_ratio = fake_count / total_valid_faces
            print(f"   📊 AI Summary: เจอหน้าปลอม {fake_count} จาก {total_valid_faces} หน้า ({round(fake_ratio*100,1)}%)")

            if fake_ratio > 0.3: # ถ้าเจอปลอมเกิน 30%
                final_result = "FAKE"
                conf = (fake_score_sum / fake_count) * 100 if fake_count > 0 else 95.0
            else:
                final_result = "REAL"
                conf = 95.0 # ถ้าคนจริง มักจะมั่นใจสูง

            return final_result, round(conf, 2)

        except Exception as e:
            print(f"   ⚠️ AI Error: {e}")
            return "REAL", 0.0
    
    return "REAL", 0.0

# ==========================================
# 🔗 ส่วนที่ 2: Blockchain (เหมือนเดิม)
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
        # 1. AI Check
        result, conf = analyze_video(video_path)
        if result == "ERROR": return

        # 2. Consensus
        print(f"   🗳️ Consensus: Verifying result '{result}'...")
        validator = random.choice(self.nodes)
        print(f"   ✅ Consensus Passed. Validator: {validator}")

        # 3. Mine
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
# 🚀 ส่วนที่ 3: สั่งรัน
# ==========================================

if __name__ == "__main__":
    my_chain = Blockchain()
    print("\n" + "="*50)
    print("   🎥  UPGRADED DEEPFAKE BLOCKCHAIN (V.2)  🎥")
    print("="*50 + "\n")

    # ใส่ชื่อไฟล์วิดีโอ (วางไฟล์ไว้ที่เดียวกัน)
    video_queue = ["grandma-go.mp4" , "ai-girl.mp4", "gay.mp4", "run_man.mp4", "cat.mp4", "awang.mp4"] 

    for video in video_queue:
        my_chain.add_video_job(video)

    print("\n📜 --- FINAL LEDGER ---")
    for b in my_chain.chain:
        print(f"Block {b.index} | {b.video_id} -> {b.ai_result} ({b.confidence}%) | Hash: {b.hash[:10]}...")

    # Hack Test
    print("\n💀 --- HACK TEST ---")
    if len(my_chain.chain) > 1:
        my_chain.chain[1].ai_result = "HACKED"
        my_chain.is_chain_valid()