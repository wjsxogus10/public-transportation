import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(page_title="대중교통 취약성 분석 대시보드", layout="wide")

st.title("📊 AI 기반 대중교통 서비스 취약성(PTVI) 분석 모델")
st.markdown("데이터사이언스 공간분석 기법을 적용하여, 인구 밀도·정류장 접근성·배차 간격을 융합한 **취약지역 핫스팟**을 도출합니다.")
st.markdown("---")

# ==========================================
# 1. 가상 공간 데이터 로드 (청주시 읍면동 기준)
# 실제 데이터사이언스 과목에서 썼던 QGIS 추출 데이터를 대체하는 샘플
# ==========================================
@st.cache_data
def load_vulnerability_data():
    data = {
        "행정동": ["오창읍", "오송읍", "가경동", "복대동", "성안동", "내수읍", "강내면", "산남동"],
        "위도": [36.7153, 36.6205, 36.6240, 36.6355, 36.6338, 36.7180, 36.6025, 36.6110],
        "경도": [127.4258, 127.3274, 127.3900, 127.4221, 127.4879, 127.5200, 127.3600, 127.4650],
        "인구밀도(명/km2)": [4200, 2100, 8500, 9200, 5000, 1200, 900, 7500],
        "정류장접근거리(m)": [650, 450, 150, 200, 300, 1200, 1500, 250],  # 공간적 취약성 (멀수록 취약)
        "평균배차간격(분)": [35, 40, 12, 10, 15, 60, 65, 15]           # 시간적 취약성 (길수록 취약)
    }
    return pd.DataFrame(data)

df = load_vulnerability_data()

# ==========================================
# 2. 사이드바: 데이터사이언스 가중치 모델링
# ==========================================
st.sidebar.header("⚙️ 취약성 분석 가중치 (MCDA)")
st.sidebar.markdown("지역 특성에 맞춰 취약성 지표의 가중치를 조정하세요.")

w_pop = st.sidebar.slider("1. 인구 밀도 (수요층)", 0.0, 1.0, 0.4, 0.1)
w_dist = st.sidebar.slider("2. 정류장 접근 거리 (공간 소외)", 0.0, 1.0, 0.3, 0.1)
w_time = st.sidebar.slider("3. 평균 배차 간격 (시간 비효율)", 0.0, 1.0, 0.3, 0.1)

# 가중치 합계를 1.0으로 강제 보정 (사용자 편의)
total_weight = w_pop + w_dist + w_time
if total_weight > 0:
    w_pop, w_dist, w_time = w_pop/total_weight, w_dist/total_weight, w_time/total_weight

# ==========================================
# 3. 데이터 전처리 (Min-Max 정규화 및 지수 산출)
# ==========================================
# 스케일이 다른 변수들을 0~100 사이로 정규화 (Data Science 기법)
def min_max_scale(series):
    return (series - series.min()) / (series.max() - series.min()) * 100

df["인구_Score"] = min_max_scale(df["인구밀도(명/km2)"])
df["거리_Score"] = min_max_scale(df["정류장접근거리(m)"])
df["시간_Score"] = min_max_scale(df["평균배차간격(분)"])

# 최종 대중교통 취약지수 (PTVI) 계산
df["취약지수(PTVI)"] = (df["인구_Score"] * w_pop) + (df["거리_Score"] * w_dist) + (df["시간_Score"] * w_time)
df = df.sort_values(by="취약지수(PTVI)", ascending=False).reset_index(drop=True)

# ==========================================
# 4. 메인 화면 UI (결과 시각화)
# ==========================================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🚨 최우선 취약지역 (Top 3)")
    st.write("산출된 취약지수(PTVI)를 바탕으로 도출된 핫스팟입니다.")
    
    # 상위 3개 지역 강조
    top_3 = df.head(3)
    for idx, row in top_3.iterrows():
        st.error(f"**Top {idx+1}. {row['행정동']}** (취약지수: {row['취약지수(PTVI)']:.1f}점)  \n"
                 f"- 접근거리: {row['정류장접근거리(m)']}m | 배차간격: {row['평균배차간격(분)']}분")

    st.subheader("📊 지역별 취약지수 랭킹")
    # 바 차트 시각화
    chart_data = df[["행정동", "취약지수(PTVI)"]].set_index("행정동")
    st.bar_chart(chart_data, height=250)

with col2:
    st.subheader("🗺️ 취약성 공간 맵핑 (디지털 트윈)")
    
    # Folium 지도 시각화 (청주시 중심)
    m = folium.Map(location=[36.65, 127.42], zoom_start=11, tiles="CartoDB positron")
    
    # 데이터프레임을 순회하며 취약지수에 따라 색상과 크기가 다른 마커 표시
    for idx, row in df.iterrows():
        # 취약지수에 따른 색상 결정 (높을수록 Red)
        score = row["취약지수(PTVI)"]
        if score >= 70:
            color = "red"
        elif score >= 40:
            color = "orange"
        else:
            color = "green"
            
        folium.CircleMarker(
            location=[row["위도"], row["경도"]],
            radius=score / 3 + 5, # 지수에 비례하여 원 크기 설정
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            tooltip=f"<b>{row['행정동']}</b><br>취약지수: {score:.1f}점"
        ).add_to(m)
        
    st_folium(m, width=650, height=550)
