# 📌 UI 탭 구성 (3개 탭 추가)
tab1, tab2, tab3 = st.tabs(["📅 상담 예약", "📜 예약 목록", "🔒 예약 목록 관리"])

# 📌 상담 예약 탭
with tab1:
    st.header("📅 병원 상담 예약")

    # 📌 안내 문구 추가
    st.info("""
    📌 **안내 사항**
    - 핸드폰 번호는 공개되지 않으며, 예약 목록에서는 마스킹 처리됩니다.
    - **실제 핸드폰 번호를 입력하시면 예약 확인 메시지가 발송됩니다. (진짜감)**
    """)

    selected_date = st.date_input("📅 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")
    available_slots = get_available_slots(selected_date)
    selected_time = st.selectbox("⏰ 상담 시간 선택", available_slots if available_slots else ["예약 가능 시간 없음"])
    patient_name = st.text_input("🧑‍⚕️ 환자 이름")
    phone = st.text_input("📞 전화번호")

    if st.button("📌 예약하기"):
        if patient_name and phone and selected_time != "예약 가능 시간 없음":
            with st.spinner("⏳ 예약을 진행 중입니다..."):
                book_appointment(patient_name, phone, selected_date, selected_time)
            st.success(f"✅ {patient_name}님 {selected_date} {selected_time} 예약 완료!")
            
            # 📌 작은 추가 창(토스트 메시지) 표시
            st.toast("📢 예약에 성공하였습니다. 사실 유료라서 문자는 안가요~", icon="💬")
            
            st.rerun()

# 📌 예약 목록 탭
with tab2:
    st.header("📜 예약 목록 (개인정보 보호)")
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM appointments", conn)
        conn.close()

        if not df.empty:
            df.columns = ["예약 ID", "환자 이름", "전화번호", "예약 날짜", "예약 시간"]
            st.dataframe(df)
        else:
            st.info("현재 예약된 일정이 없습니다.")
    except Exception as e:
        st.error(f"❌ 예약 목록 불러오기 실패: {str(e)}")

# 📌 예약 목록 관리 (비밀번호 4546 필요)
with tab3:
    st.header("🔒 관리자 예약 목록 관리")
    password_input = st.text_input("🔑 관리자 비밀번호 입력", type="password")

    if password_input == "4546":
        appointments_df = get_appointments()
        if not appointments_df.empty:
            st.dataframe(appointments_df)

            # 📌 예약 수정 기능
            appointment_id = st.number_input("🔢 수정할 예약 ID 입력", min_value=1, step=1)
            
            if appointment_id in appointments_df["예약 ID"].values:
                new_date = st.date_input("📅 새로운 상담 날짜 선택", datetime.today()).strftime("%Y-%m-%d")
                new_time = st.selectbox("⏰ 새로운 상담 시간 선택", get_available_slots(new_date))
                
                if st.button("✅ 예약 변경"):
                    update_appointment(appointment_id, new_date, new_time)
                    st.success(f"✅ 예약 ID {appointment_id} 수정 완료!")
                    st.rerun()

            # 📌 예약 취소 기능
            cancel_id = st.number_input("🗑️ 취소할 예약 ID 입력", min_value=1, step=1)
            if st.button("❌ 예약 취소"):
                cancel_appointment(cancel_id)
                st.success(f"🗑️ 예약 ID {cancel_id} 취소 완료!")
                st.rerun()
    elif password_input:
        st.error("❌ 관리자 비밀번호가 올바르지 않습니다!")
