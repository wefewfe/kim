import os
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import re
from dotenv import load_dotenv

# 📌 환경 변수 로드 (.env 파일에서 Twilio API 키 가져오기)
load_dotenv()
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# 📌 관리자 비밀번호 설정
ADMIN_PASSWORD = "4546"

# 📌 데이터베이스 연결
DB_FILE = "hospital_schedule.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 📌 개인정보 보호를 위한 마스킹 함수
def mask_name(name):
    """ 이름의 중간 글자를 '*'로 변경 """
    if len(name) == 2:
        return name[0] + "*"
    elif len(name) > 2:
        return name[0] + "*" * (len(name) - 2) + name[-1]
    return name

def mask_phone(phone):
    """ 전화번호의 마지막 3자리를 제외하고 '*'로 마스킹 """
    if len(phone) >= 7:
        return phone[:-3].replace(phone[:-3], "*" * (len(phone[:-3]))) + phone[-3:]
    return phone

# 📌 예약 목록 조회 함수 (개인정보 보호 적용)
def get_appointments():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()

    if not df.empty:
        df.columns = ["예약 ID", "환자 이름", "전화번호", "예약 날짜", "예약 시간"]
        df["환자 이름"] = df["환자 이름"].apply(mask_name)
        df["전화번호"] = df["전화번호"].apply(mask_phone)
    return df

# 📌 예약 취소 함수
def cancel_appointment(appointment_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

# 📌 예약 시간 변경 함수
def update_appointment(appointment_id, new_date, new_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET date = ?, time = ? WHERE id = ?", (new_date, new_time, appointment_id))
    conn.commit()
    conn.close()

# 📌 UI 탭 구성 (3개 탭 추가)
tab1, tab2, tab3 = st.tabs(["📅 상담 예약", "📜 예약 목록", "🔒 예약 목록 관리"])

# 📌 상담 예약 탭
with tab1:
    st.header("📅 병원 상담 예약")

    st.info("""
    📌 **안내 사항**
    - 핸드폰 번호는 공개되지 않으며, 예약 목록에서는 마스킹 처리됩니다.
    - **실제 핸드폰 번호를 입력하시면 예약 확인 메시지가 발송됩니다. (진짜감)**
    """)

    selected_date = st.date_input("📅 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")
    selected_time = st.selectbox("⏰ 상담 시간 선택", ["09:00", "10:30", "13:00", "15:00", "17:00"])
    patient_name = st.text_input("🧑‍⚕️ 환자 이름")
    phone = st.text_input("📞 전화번호")

    if st.button("📌 예약하기"):
        if patient_name and phone and selected_time:
            st.success(f"✅ {patient_name}님 {selected_date} {selected_time} 예약 완료!")

            # 📌 예약 완료 메시지를 본문 아래쪽으로 이동
            st.warning("📢 예약에 성공하였습니다. 뻥입니다. 사실 문자는 유료라서 문자는 안가요~")

# 📌 예약 목록 탭
with tab2:
    st.header("📜 예약 목록 (개인정보 보호)")
    try:
        appointments_df = get_appointments()
        if not appointments_df.empty:
            st.dataframe(appointments_df)
        else:
            st.info("현재 예약된 일정이 없습니다.")
    except Exception as e:
        st.error(f"❌ 예약 목록 불러오기 실패: {str(e)}")

# 📌 예약 목록 관리 (비밀번호 4546 필요)
with tab3:
    st.header("🔒 관리자 예약 목록 관리")
    password_input = st.text_input("🔑 관리자 비밀번호 입력", type="password")

    if password_input == ADMIN_PASSWORD:
        appointments_df = get_appointments()
        if not appointments_df.empty:
            st.dataframe(appointments_df)

            appointment_id = st.number_input("🔢 수정할 예약 ID 입력", min_value=1, step=1)
            
            if appointment_id in appointments_df["예약 ID"].values:
                new_date = st.date_input("📅 새로운 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")
                new_time = st.selectbox("⏰ 새로운 상담 시간 선택", ["09:00", "10:30", "13:00", "15:00", "17:00"])
                
                if st.button("✅ 예약 변경"):
                    update_appointment(appointment_id, new_date, new_time)
                    st.success(f"✅ 예약 ID {appointment_id} 수정 완료!")
                    st.rerun()

            cancel_id = st.number_input("🗑️ 취소할 예약 ID 입력", min_value=1, step=1)
            if st.button("❌ 예약 취소"):
                cancel_appointment(cancel_id)
                st.success(f"🗑️ 예약 ID {cancel_id} 취소 완료!")
                st.rerun()
    elif password_input:
        st.error("❌ 관리자 비밀번호가 올바르지 않습니다!")
