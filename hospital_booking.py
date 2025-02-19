import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 📌 페이지 설정 (앱 제목 변경)
st.set_page_config(
    page_title="병원 상담 예약",
    page_icon="🏥",
    layout="wide"
)

# 데이터베이스 연결 함수
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

# 상담 가능 시간 설정
AVAILABLE_SLOTS = ["09:00", "10:30", "13:00", "15:00", "17:00"]

# 예약 가능한 시간 조회 (이미 예약된 시간 제외)
def get_available_slots(selected_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = ?", (selected_date,))
    booked_times = {row[0] for row in cursor.fetchall()}
    conn.close()
    return [time for time in AVAILABLE_SLOTS if time not in booked_times]

# 예약 추가 함수
def book_appointment(patient_name, phone, selected_date, selected_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_name, phone, date, time) VALUES (?, ?, ?, ?)",
                   (patient_name, phone, selected_date, selected_time))
    conn.commit()
    conn.close()

# 예약 목록 조회 함수
def get_appointments():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()
    return df

# 예약 취소 함수
def cancel_appointment(appointment_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

# 📌 Streamlit UI (탭 방식으로 "예약하기" & "예약 목록 확인" 분리)
st.sidebar.title("🏥 병원 상담 예약")
tab1, tab2 = st.tabs(["📅 상담 예약", "📜 예약 목록"])

# 📌 예약하기 페이지
with tab1:
    st.header("📅 병원 상담 예약")
    
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
            st.success(f"✅ {patient_name}님 {selected_date} {selected_time} 예약 완료!")
            st.rerun()
        else:
            st.warning("⚠️ 모든 정보를 입력하세요!")

# 📌 예약 목록 페이지
with tab2:
    st.header("📜 예약 목록 확인")
    
    # 예약 목록 테이블 표시
    appointments_df = get_appointments()
    if not appointments_df.empty:
        st.dataframe(appointments_df)

        # 예약 취소 기능
        appointment_id = st.number_input("❌ 취소할 예약 ID 입력", min_value=1, step=1)
        if st.button("❌ 예약 취소"):
            cancel_appointment(appointment_id)
            st.success(f"🗑️ 예약 ID {appointment_id} 취소됨!")
            st.rerun()
    else:
        st.info("현재 예약된 일정이 없습니다.")
