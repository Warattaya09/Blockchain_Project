import streamlit as st
import time
import hashlib
import random
import json

# ==========================================
# 1. ส่วนจำลองระบบ AI (AI Simulation)
# ==========================================
def mock_ai_predict(filename):
    """
    ฟังก์ชันจำลอง AI (ฉบับเสถียร):
    1. เช็คคีย์เวิร์ด real/fake ก่อน
    2. ถ้าไม่มีคีย์เวิร์ด จะคำนวณจาก Hash ของชื่อไฟล์ (ชื่อเดิม = ผลเดิมเสมอ)
    """
    time.sleep(2.0) 
    name_lower = filename.lower()
    
    # 1. เช็คคีย์เวิร์ด (Priority สูงสุด)
    if "fake" in name_lower:
        return True, 98.50 # เป็นของปลอมแน่นอน
    elif "real" in name_lower:
        return False, 96.20 # เป็นของจริงแน่นอน

    # 2. ถ้าไม่มีคีย์เวิร์ด ให้ใช้ Hash คำนวณ (Stable Random)
    # หลักการ: ชื่อไฟล์เดิม -> จะได้ค่า Hash เดิมเสมอ -> ผลลัพธ์จะเหมือนเดิมตลอดกาล
    hash_object = hashlib.sha256(name_lower.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    
    # เอาค่าตัวเลขมาหารเอาเศษ (Modulo) เพื่อตัดสิน
    # ถ้าเศษเป็นเลขคู่ = Fake, เลขคี่ = Real (หรือสลับกันก็ได้)
    is_fake = (hash_int % 2 == 0)
    
    # สร้างค่าความมั่นใจจาก Hash เหมือนกัน (จะได้เลขเดิมตลอด)
    confidence = 80.0 + (hash_int % 2000) / 100.0
    
    return is_fake, confidence

# ==========================================
# 2. ส่วนจำลอง Blockchain (Blockchain Simulation)
# ==========================================
def mock_blockchain_record(filename, ai_result, confidence):
    """
    ฟังก์ชันจำลองการบันทึกข้อมูลลง Blockchain
    """
    time.sleep(1.5) # จำลองเวลา Mining
    
    # สร้างข้อมูล Transaction
    timestamp = time.ctime()
    validator_id = "0x" + "".join([random.choice("0123456789ABCDEF") for i in range(40)])
    
    # ข้อมูลที่จะเก็บใน Block
    block_data = {
        "block_height": random.randint(10500, 10600),
        "timestamp": timestamp,
        "video_name": filename,
        "video_hash": hashlib.sha256(filename.encode()).hexdigest(), # Hash ของชื่อไฟล์
        "ai_verdict": ai_result,
        "confidence_score": f"{confidence:.2f}%",
        "validator_node": validator_id
    }
    
    # สร้าง Transaction Hash (เลขที่ใบเสร็จ)
    tx_string = json.dumps(block_data)
    tx_hash = "0x" + hashlib.sha256(tx_string.encode()).hexdigest()
    
    return tx_hash, block_data

# ==========================================
# 3. ส่วนหน้าจอ UI (User Interface)
# ==========================================
def main():
    st.set_page_config(
        page_title="Deepfake Detective",
        page_icon="🛡️",
        layout="centered"
    )

    # หัวข้อหลัก
    st.title("🛡️ Deepfake Detection System")
    st.markdown("### ระบบตรวจสอบวิดีโอปลอมและยืนยันหลักฐานผ่าน Blockchain")
    st.info("💡 **Tip:** ในการ Demo ให้ตั้งชื่อไฟล์มีคำว่า **'real'** หรือ **'fake'** เพื่อกำหนดผลลัพธ์")
    
    st.divider()

    # พื้นที่อัปโหลด
    uploaded_file = st.file_uploader("📂 เลือกไฟล์วิดีโอ (.mp4)", type=['mp4', 'mov', 'avi'])

    if uploaded_file is not None:
        # แสดงวิดีโอ
        st.video(uploaded_file)
        st.caption(f"Filename: {uploaded_file.name}")

        # ปุ่มกดเริ่มงาน
        if st.button("🚀 เริ่มการตรวจสอบ (Verify Video)", type="primary"):
            
            # --- PHASE 1: AI SCANNING ---
            st.write("---")
            st.subheader("1. AI Analysis Result")
            
            with st.spinner('🤖 AI กำลังวิเคราะห์ใบหน้าและเสียง... (Processing)'):
                # เรียกฟังก์ชัน AI (ส่งชื่อไฟล์เข้าไป)
                is_fake, conf = mock_ai_predict(uploaded_file.name)

            # แสดงผลลัพธ์ AI
            col1, col2 = st.columns(2)
            if is_fake:
                col1.error("🚨 RESULT: **FAKE VIDEO**")
                col2.metric("Confidence", f"{conf:.2f}%", delta="-High Risk")
                result_text = "FAKE"
            else:
                col1.success("✅ RESULT: **REAL VIDEO**")
                col2.metric("Confidence", f"{conf:.2f}%", delta="Safe")
                result_text = "REAL"

            # --- PHASE 2: BLOCKCHAIN RECORDING ---
            st.write("---")
            st.subheader("2. Blockchain Verification")
            
            with st.spinner('🔗 กำลังสร้าง Hash และบันทึกลง Blockchain... (Mining)'):
                tx_hash, block_data = mock_blockchain_record(uploaded_file.name, result_text, conf)

            st.success("บันทึกข้อมูลสำเร็จ! (Data Immutable)")
            
            # แสดงข้อมูล Blockchain
            st.markdown(f"**Transaction Hash:**")
            st.code(tx_hash)

            with st.expander("🔍 ดูข้อมูลภายใน Block (Block Data)"):
                st.json(block_data)

if __name__ == "__main__":
    main()
    
    
#py app.py
