import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from twilio.rest import Client
import re

# 📌 Twilio API 설정 (여기에 본인의 Twilio 계정 정보 입력)
ACCOUNT_SID = "ACc185bc14dfed50ab021255bc0223e5c7"
AUTH_TOKEN = "b143672aad972a0b7ea56b9e6789c572"
TWILIO_PHONE_NUMBER = "+14179813887"  # Twilio에서 제공한 발신 번호

# 📌 Twilio SMS 전송 함수
def send_sms(to_number, message):
    """ Twilio를 통해 한국 국제 표준(+82)으로 SMS 전송 """
    to_number = convert_to_international_number(to_number)  # 전화번호 변환
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    client.messages.create(
        to=to_number,
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )

# 📌 한국 전화번호 변환 함수 (+82 적용)
def convert_to_international_number(phone):
    """
    사용자가 010-xxxx-xxxx 형식으로 입력하면 +8210-xxxx-xxxx 로 변환
    """
    phone = re.sub(r'\D', '', phone)  # 숫자 이외의 문자 제거

    if phone.startswith("010"):  
        return "+82" + phone[1:]  # 앞자리 0을 제거하고 +82 추가
    return phone  # 이미 국제 번호 형식이면 그대로 반환

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

# 📌 상담 가능 시간 목록
AVAILABLE_SLOTS = ["09:00", "10:30", "13:00", "15:00", "17:00"]

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

# 📌 예약 가능한 시간 조회
def get_available_slots(selected_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ?", (selected_date,))
    booked_times = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    return [time for time in AVAILABLE_SLOTS if time not in booked_times]

# 📌 예약 추가 함수 (예약 후 문자 자동 발송)
def book_appointment(patient_name, phone, selected_date, selected_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_name, phone, date, time) VALUES (?, ?, ?, ?)",
                   (patient_name, phone, selected_date, selected_time))
    conn.commit()
    conn.close()

    # 📌 예약 완료 후 문자 메시지 전송
    message = f"김삥뿅 의원에 예약해주셔서 감사합니다.\n📅 예약일: {selected_date} ⏰ 예약시간: {selected_time}"
    send_sms(phone, message)

# 📌 예약 목록 조회 함수 (마스킹 적용)
def get_appointments():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()

    if not df.empty:
        # 컬럼명 변경
        df.columns = ["예약 ID", "환자 이름", "전화번호", "예약 날짜", "예약 시간"]
        # 개인정보 보호 (이름과 전화번호 마스킹)
        df["환자 이름"] = df["환자 이름"].apply(mask_name)
        df["전화번호"] = df["전화번호"].apply(mask_phone)

    return df

# 📌 Streamlit UI
st.title("🏥 병원 상담 예약 시스템")
st.markdown("---")

# 📌 UI 탭 구성
tab1, tab2 = st.tabs(["📅 상담 예약", "📜 예약 목록"])

# 📌 상담 예약 탭
with tab1:
    st.header("📅 병원 상담 예약")
    
    # 📌 안내 문구 추가
    st.info("""
    📌 **안내 사항**
    - 핸드폰 번호는 공개되지 않으며, 예약 목록에서는 마스킹 처리됩니다.
    - **실제 핸드폰 번호를 입력하시면 예약 확인 메시지가 전송됩니다. (진짜감)**
    - **010-XXXX-XXXX 형식으로 입력해 주세요. 국제 번호 변환은 자동으로 진행됩니다.**
    """)

    # 날짜 선택
    selected_date = st.date_input("📅 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")

    # 상담 가능 시간 목록 업데이트
    available_slots = get_available_slots(selected_date)
    selected_time = st.selectbox("⏰ 상담 시간 선택", available_slots if available_slots else ["예약 가능 시간 없음"])

    # 환자 정보 입력
    patient_name = st.text_input("🧑‍⚕️ 환자 이름")
    phone = st.text_input("📞 전화번호")

    # 예약 버튼
    if st.button("📌 예약하기"):
        if patient_name and phone and selected_time != "예약 가능 시간 없음":
            book_appointment(patient_name, phone, selected_date, selected_time)
            st.success(f"✅ {patient_name}님 {selected_date} {selected_time} 예약 완료! SMS가 전송되었습니다.")
            st.rerun()
        else:
            st.warning("⚠️ 모든 정보를 입력하세요!")

# 📌 예약 목록 탭 (마스킹 적용)
with tab2:
    st.header("📜 예약 목록 (개인정보 보호)")

    appointments_df = get_appointments()
    if not appointments_df.empty:
        st.dataframe(appointments_df)
    else:
        st.info("현재 예약된 일정이 없습니다.")
