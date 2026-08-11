# ==========================================
# 2. 데이터 로드 (업로드 파일 우선 적용 + 인코딩 자동 예외 처리)
# ==========================================
@st.cache_data
def load_default_data():
    data = {
        "지역명": ["오창읍 (산단)", "오송읍 (KTX)", "가경동 (터미널)", "복대동 (상업/주거)", "성안동 (구도심)"],
        "인구수(명)": [71000, 31000, 52000, 53000, 15000],
        "일평균 승하차(건)": [14000, 7500, 16000, 17500, 9000],
        "위도": [36.7153, 36.6205, 36.6240, 36.6355, 36.6338],
        "경도": [127.4258, 127.3274, 127.3900, 127.4221, 127.4879]
    }
    return pd.DataFrame(data)

if uploaded_file is not None:
    try:
        # 1차 시도: utf-8 인코딩으로 읽기
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        st.sidebar.success("✅ 사용자 데이터 로드 성공 (UTF-8)!")
    except UnicodeDecodeError:
        try:
            # 2차 시도: 한글 윈도우 기본 인코딩인 cp949로 읽기
            uploaded_file.seek(0) # 파일 포인터 초기화
            df = pd.read_csv(uploaded_file, encoding='cp949')
            st.sidebar.success("✅ 사용자 데이터 로드 성공 (CP949)!")
        except Exception as e:
            st.sidebar.error(f"파일 읽기 오류: {e}")
            df = load_default_data()
    except Exception as e:
            st.sidebar.error(f"파일 읽기 오류: {e}")
            df = load_default_data()
else:
    df = load_default_data()
    st.sidebar.info("💡 파일을 업로드하지 않아 기본 청주시 샘플 데이터로 구동됩니다.")
