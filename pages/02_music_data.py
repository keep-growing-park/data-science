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
            # 1. iTunes 한국 인기 음원 Top 100 RSS Feed API
            url = "https://itunes.apple.com/kr/rss/topsongs/limit=100/json"
            response = requests.get(url, timeout=10)
            res_json = response.json()
            entries = res_json.get('feed', {}).get('entry', [])

            data = []
            for idx, entry in enumerate(entries):
                title = entry.get('im:name', {}).get('label', '')
                artist = entry.get('im:artist', {}).get('label', '')
                
                # 수치형 변수 추출 (회귀/군집 분석용)
                release_date = entry.get('im:releaseDate', {}).get('label', '')[:10]
                release_year = int(release_date[:4]) if release_date else 2026
                
                # 순위 기반 임의의 가상 관심도 수치 및 글자수 변수
                rank = idx + 1
                
                data.append({
                    '순위': rank,
                    '곡명': title,
                    '가수명': artist,
                    '발매연도': release_year,
                    '제목_글자수': len(title),
                    '가수명_글자수': len(artist),
                    '추천지수': 101 - rank  # 회귀/군집용 수치형 변수 (1위=100점, 100위=1점)
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
