import os
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from twilio.rest import Client
import re
from dotenv import load_dotenv

# 📌 환경 변수 로드 (.env 파일에서 Twilio API 키 가져오기)
load_dotenv()
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# 📌 관리자 비밀번호 설정
ADMIN_PASSWORD = "4546"

# 📌 Twilio SMS 전송 함수 (오류 방지 코드 추가)
def send_sms(to_number, message):
    try:
        to_number = convert_to_international_number(to_number)  # 전화번호 변환
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message
        )
        st.success(f"✅ SMS 전송 완료: {to_number}")
    except Exception as e:
        st.warning(f"⚠️ SMS 전송 실패: {str(e)}")

# 📌 한국 전화번호 변환 (+82 적용)
def convert_to_international_number(phone):
    phone = re.sub(r'\D', '', phone)  # 숫자 이외의 문자 제거
    if phone.startswith("010"):  
        return "+82" + phone[1:]  # 앞자리 0을 제거하고 +82 추가
    return phone

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
    if len(name) == 2:
        return name[0] + "*"
    elif len(name) > 2:
        return name[0] + "*" * (len(name) - 2) + name[-1]
    return name

def mask_phone(phone):
    if len(phone) >= 7:
        return phone[:-3].replace(phone[:-3], "*" * (len(phone[:-3]))) + phone[-3:]
    return phone

# 📌 예약 가능한 시간 조회
def get_available_slots(selected_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ?", (selected_date,))
    booked_times = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    return [time for time in ["09:00", "10:30", "13:00", "15:00", "17:00"] if time not in booked_times]

# 📌 예약 추가 함수 (Twilio 오류 핸들링 추가)
def book_appointment(patient_name, phone, selected_date, selected_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_name, phone, date, time) VALUES (?, ?, ?, ?)",
                   (patient_name, phone, selected_date, selected_time))
    conn.commit()
    conn.close()

    # 📌 Twilio 메시지 전송 (오류 발생해도 예약이 정상적으로 저장됨)
    message = f"김삥뿅 의원에 예약해주셔서 감사합니다.\n📅 예약일: {selected_date} ⏰ 예약시간: {selected_time}"
    send_sms(phone, message)

# 📌 예약 목록 조회 함수 (Twilio 오류로 인해 UI 사라지는 문제 해결)
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

# 📌 Streamlit UI
st.title("🏥 병원 상담 예약 시스템")
st.markdown("---")

# 📌 UI 탭 구성 (3개 탭 추가)
tab1, tab2, tab3 = st.tabs(["📅 상담 예약", "📜 예약 목록", "🔒 예약 목록 관리"])

# 📌 상담 예약 탭
with tab1:
    st.header("📅 병원 상담 예약")
    selected_date = st.date_input("📅 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")
    available_slots = get_available_slots(selected_date)
    selected_time = st.selectbox("⏰ 상담 시간 선택", available_slots if available_slots else ["예약 가능 시간 없음"])
    patient_name = st.text_input("🧑‍⚕️ 환자 이름")
    phone = st.text_input("📞 전화번호")

    if st.button("📌 예약하기"):
        if patient_name and phone and selected_time != "예약 가능 시간 없음":
            book_appointment(patient_name, phone, selected_date, selected_time)
            st.success(f"✅ {patient_name}님 {selected_date} {selected_time} 예약 완료!")
            st.rerun()

# 📌 예약 목록 탭
with tab2:
    st.header("📜 예약 목록 (개인정보 보호)")
    try:
        appointments_df = get_appointments()
        st.dataframe(appointments_df)
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
                new_time = st.selectbox("⏰ 새로운 상담 시간 선택", get_available_slots(new_date))
                
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
