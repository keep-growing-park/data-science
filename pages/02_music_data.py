import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st

st.set_page_config(page_title="수업용 K-POP 데이터 수집기", layout="wide")
st.title("🎵 K-POP 실시간 데이터 수집 및 정제")
st.caption("Spotify Official Web API 기반 | 회귀·군집·연관 분석 실습용 데이터셋 제공")

# 1시간 동안 API 호출 결과를 메모리에 저장하는 캐싱 함수
@st.cache_data(ttl=3600)
def fetch_spotify_kpop_data():
    # Streamlit Secrets에서 표준 Client ID & Secret 로드
    client_id = st.secrets["SPOTIPY_CLIENT_ID"]
    client_secret = st.secrets["SPOTIPY_CLIENT_SECRET"]

    # Spotify 공식 Client Credentials 인증 방식
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Spotify 'Top 50 - 대한민국' 공식 플레이리스트 ID
    playlist_id = '37i9dQZEVXbJx5231P32uL'
    results = sp.playlist_items(playlist_id, limit=50)

    data = []
    for idx, item in enumerate(results.get('items', [])):
        track = item.get('track')
        if not track:
            continue
        
        # 1. 기본 실시간 음원 데이터
        rank = idx + 1
        title = track.get('name', '')
        artist = track.get('artists', [{}])[0].get('name', '')
        album = track.get('album', {}).get('name', '')
        popularity = track.get('popularity', 0)                  # 스포티파이 실제 인기도 (0~100)
        duration_sec = round(track.get('duration_ms', 0) / 1000) # 재생시간(초)

        # 2. 수업용 파생 변수 생성
        title_length = len(title)
        artist_length = len(artist)
        
        if duration_sec < 180:
            duration_group = "Short"
        elif duration_sec <= 210:
            duration_group = "Medium"
        else:
            duration_group = "Long"

        artist_tag = f"Artist_{artist}"

        data.append({
            '순위': rank,
            '곡명': title,
            '가수명': artist,
            '앨범명': album,
            '인기도(Y)': popularity,
            '재생시간_초': duration_sec,
            '제목_글자수': title_length,
            '가수명_글자수': artist_length,
            '재생시간_그룹': duration_group,
            '연관분석_태그': artist_tag
        })

    return pd.DataFrame(data)

# 데이터 수집 실행
try:
    with st.spinner("Spotify Official API 연결 및 1시간 캐시 데이터 처리 중..."):
        df = fetch_spotify_kpop_data()

    st.success("데이터 로드 완료 (수집 후 1시간 동안 빠른 캐시 데이터를 불러옵니다)")

    # 탭 구성: 데이터 확인 및 분석 가이드
    tab1, tab2 = st.tabs(["📊 전체 데이터프레임", "📘 수업 활용 가이드"])

    with tab1:
        st.dataframe(df, use_container_width=True)
        
        # CSV 다운로드
        csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 수업용 kpop_analysis_data.csv 다운로드",
            data=csv_data,
            file_name="kpop_analysis_data.csv",
            mime="text/csv"
        )

    with tab2:
        st.markdown("""
        **1. 회귀분석 (Regression)**
        * 독립변수(X): `제목_글자수`, `가수명_글자수`, `재생시간_초`
        * 종속변수(Y): `인기도(Y)` 또는 `순위`
        
        **2. 군집분석 (Clustering)**
        * 수치형 K-Means: `재생시간_초`, `제목_글자수`, `인기도(Y)` 3차원 클러스터링
        * 범주형 데이터: `재생시간_그룹`과 순위 구간별 집단 비교
        
        **3. 연관분석 (Association Rules)**
        * `가수명`과 `연관분석_태그` 항목을 활용한 차트 상위권 동시 진입/인기 패턴 분석
        """)

except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
