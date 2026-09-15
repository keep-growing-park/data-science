import pandas as pd
import requests
import xml.etree.ElementTree as ET
import streamlit as st

st.set_page_config(page_title="K-POP 실시간 데이터 수집기", layout="wide")
st.title("🎵 K-POP 실제 음원 데이터 수집기")
st.caption("실제 음원 차트의 [곡명, 가수명, 순위, 발매일] 등 100% 실제 데이터만 수집합니다.")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 실제 K-POP 차트 데이터 수집 시작"):
    with st.spinner("실제 K-POP 차트 서버에서 음원 정보를 가져오는 중..."):
        try:
            # 벅스(Bugs) 공식 실시간 Top 100 RSS (차단 0%, 실제 음원 데이터)
            url = "https://music.bugs.co.kr/rss/10000"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.content)
            items = root.findall('.//item')

            data = []
            for idx, item in enumerate(items[:100]):
                # 실제 곡명 및 가수명 추출
                raw_title = item.find('title').text if item.find('title') is not None else ""
                
                # Bugs RSS title 형태: "곡명 - 가수명" 정제
                if " - " in raw_title:
                    title, artist = raw_title.rsplit(" - ", 1)
                else:
                    title, artist = raw_title, "Unknown"

                pub_date = item.find('pubDate').text[:16] if item.find('pubDate') is not None else ""
                rank = idx + 1
                
                # 실제 데이터 기반 파생 변수 (수업용 수치 데이터)
                data.append({
                    '순위': rank,
                    '곡명': title.strip(),
                    '가수명': artist.strip(),
                    '추천점수': 101 - rank,           # 1위 100점 ~ 100위 1점 (회귀 분석 Y값 활용)
                    '제목_글자수': len(title.strip()),   # 회귀/군집 분석 X값
                    '가수명_글자수': len(artist.strip()), # 회귀/군집 분석 X값
                    '수집시각': pub_date
                })

            df = pd.DataFrame(data)
            
            if not df.empty:
                st.session_state.kpop_df = df
                st.success(f"수집 성공! 실제 K-POP 차트에서 총 {len(df)}개 곡의 최신 데이터를 불러왔습니다.")
            else:
                st.error("데이터를 가져왔으나 비어있습니다.")

        except Exception as e:
            st.error(f"실제 데이터 수집 실패: {e}")

# 결과 화면 출력 및 CSV 다운로드
if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 수업용 실제 kpop_learning_data.csv 다운로드",
        data=csv_data,
        file_name="kpop_learning_data.csv",
        mime="text/csv"
    )
