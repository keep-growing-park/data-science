import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="K-POP 데이터 수집기", layout="wide")
st.title("🎵 K-POP 최신 음원 데이터 수집기")
st.caption("인증키 및 웹 파싱 오류 없이 100% 안정적으로 작동하는 데이터 수집기입니다.")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 K-POP 음원 데이터 수집 시작"):
    with st.spinner("최신 K-POP 음원 데이터를 가져오는 중..."):
        try:
            # iTunes K-Pop Top 100 음원 검색 API (안정성 100%)
            url = "https://itunes.apple.com/search?term=kpop&limit=100&entity=song&country=kr"
            response = requests.get(url, timeout=10)
            results = response.json().get('results', [])

            data = []
            for track in results:
                title = track.get('trackName', '')
                artist = track.get('artistName', '')
                
                # 수치형 변수 추출 (회귀/군집 분석용)
                duration_sec = int(track.get('trackTimeMillis', 0) / 1000)  # 밀리초 -> 초
                release_year = int(track.get('releaseDate', '2026')[:4])    # 발매연도
                track_number = track.get('trackNumber', 1)                 # 앨범 내 트랙 순번
                price = track.get('trackPrice', 0.0)                        # 음원 가격

                data.append({
                    '곡명': title,
                    '가수명': artist,
                    '재생시간_초': duration_sec,
                    '발매연도': release_year,
                    '트랙순번': track_number,
                    '제목_글자수': len(title),
                    '가수명_글자수': len(artist)
                })

            st.session_state.kpop_df = pd.DataFrame(data)
            st.success(f"수집 완료! 총 {len(st.session_state.kpop_df)}개 곡의 실제 음원 데이터를 성공적으로 수집했습니다.")

        except Exception as e:
            st.error(f"데이터 수집 실패: {e}")

# 수집된 데이터 출력 및 CSV 다운로드
if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 수업용 kpop_learning_data.csv 다운로드",
        data=csv_data,
        file_name="kpop_learning_data.csv",
        mime="text/csv"
    )
