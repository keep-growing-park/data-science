import pandas as pd
import requests
import random
import streamlit as st

st.set_page_config(page_title="K-POP 데이터 수집기", layout="wide")
st.title("🎵 K-POP 최신 음원 데이터 수집기")
st.caption("실시간 수집 + 네트워크 예외 자동 복구 기능이 적용된 수업 전용 수집기입니다.")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

def get_fallback_data():
    """네트워크 차단 시 수업 마비를 막기 위한 최신 K-POP 데이터 100개 자동 생성 함수"""
    artists = ["NewJeans", "IVE", "LE SSERAFIM", "aespa", "SEVENTEEN", "BTS", "BLACKPINK", "RIIZE", "NCT", "PLAVE", "IU", "DAY6", "TWS", "QWER", "ILLIT"]
    song_keywords = ["Supernova", "Drama", "Magnetic", "Spot!", "HEYA", "EASY", "Perfect Night", "Ditto", "Super Shy", "Love wins all", "Fate", "Plot Twist", "Small Girl"]
    
    data = []
    random.seed(42)  # 재현성을 위한 고정 시드
    
    for idx in range(1, 101):
        title = f"{random.choice(song_keywords)} #{idx}" if idx > 13 else song_keywords[idx - 1]
        artist = random.choice(artists)
        duration_sec = random.randint(160, 240)      # 재생시간 (160초~240초)
        views = random.randint(500000, 80000000)      # 조회수
        likes = int(views * random.uniform(0.05, 0.15)) # 좋아요 수
        
        data.append({
            '순위': idx,
            '곡명': title,
            '가수명': artist,
            '조회수': views,
            '좋아요수': likes,
            '재생시간_초': duration_sec,
            '제목_글자수': len(title),
            '가수명_글자수': len(artist)
        })
    return pd.DataFrame(data)

if st.button("🚀 K-POP 음원 데이터 수집 시작"):
    with st.spinner("최신 K-POP 음원 데이터를 불러오는 중..."):
        try:
            # 브라우저 차단 우회를 위한 User-Agent 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            url = "https://itunes.apple.com/kr/rss/topsongs/limit=100/json"
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                res_json = response.json()
                entries = res_json.get('feed', {}).get('entry', [])
                
                if len(entries) > 0:
                    data = []
                    for idx, entry in enumerate(entries):
                        title = entry.get('im:name', {}).get('label', '')
                        artist = entry.get('im:artist', {}).get('label', '')
                        release_date = entry.get('im:releaseDate', {}).get('label', '')[:10]
                        release_year = int(release_date[:4]) if release_date else 2026
                        rank = idx + 1
                        
                        data.append({
                            '순위': rank,
                            '곡명': title,
                            '가수명': artist,
                            '발매연도': release_year,
                            '제목_글자수': len(title),
                            '가수명_글자수': len(artist),
                            '추천지수': 101 - rank
                        })
                    st.session_state.kpop_df = pd.DataFrame(data)
                    st.success(f"실시간 API 수집 성공! 총 {len(st.session_state.kpop_df)}개 곡의 데이터를 불러왔습니다.")
                else:
                    st.session_state.kpop_df = get_fallback_data()
                    st.warning("외부 API 응답 지연으로 수업용 백업 데이터셋(100개)을 즉시 생성했습니다.")
            else:
                st.session_state.kpop_df = get_fallback_data()
                st.warning("외부 서버 응답 오류로 수업용 백업 데이터셋(100개)을 즉시 생성했습니다.")

        except Exception as e:
            st.session_state.kpop_df = get_fallback_data()
            st.warning("네트워크 연결 예외 발생으로 수업용 백업 데이터셋(100개)을 자동 활성화했습니다.")

# 결과 화면 출력 및 CSV 다운로드
if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 수업용 kpop_learning_data.csv 다운로드",
        data=csv_data,
        file_name="kpop_learning_data.csv",
        mime="text/csv"
    )
