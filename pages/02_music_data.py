import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="Melon TOP 100 데이터 수집기", layout="wide")
st.title("🎵 멜론(Melon) 실시간 TOP 100 데이터 수집기")
st.caption("요즘 학생들이 가장 많이 듣는 멜론 실시간 차트의 100% 실제 데이터를 수집합니다.")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 멜론 TOP 100 실제 데이터 수집 시작"):
    with st.spinner("실제 멜론 차트에서 최신 음원 정보를 불러오는 중..."):
        try:
            # 멜론 보안 차단을 우회하기 위한 브라우저 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.melon.com/'
            }
            
            url = "https://www.melon.com/chart/index.htm"
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 멜론 1~50위, 51~100위 태그 추출
            lst50 = soup.select('tr.lst50')
            lst100 = soup.select('tr.lst100')
            tr_list = lst50 + lst100
            
            data = []
            for tr in tr_list:
                # 순위
                rank = int(tr.select_one('span.rank').text.strip())
                
                # 곡명 (내부 불필요 텍스트 정제)
                title_elem = tr.select_one('div.ellipsis.rank01 a')
                title = title_elem.text.strip() if title_elem else ""
                
                # 가수명
                artist_elem = tr.select_one('div.ellipsis.rank02 > a')
                artist = artist_elem.text.strip() if artist_elem else ""
                
                # 앨범명
                album_elem = tr.select_one('div.ellipsis.rank03 a')
                album = album_elem.text.strip() if album_elem else ""
                
                data.append({
                    '순위': rank,
                    '곡명': title,
                    '가수명': artist,
                    '앨범명': album,
                    '추천점수': 101 - rank,            # 회귀분석 Y값 (1위 100점 ~ 100위 1점)
                    '제목_글자수': len(title),          # 회귀/군집 분석 X값
                    '가수명_글자수': len(artist)        # 회귀/군집 분석 X값
                })

            df = pd.DataFrame(data)
            
            if not df.empty and len(df) == 100:
                st.session_state.kpop_df = df
                st.success(f"수집 성공! 현재 멜론 TOP 100의 실제 데이터를 성공적으로 불러왔습니다.")
            else:
                st.warning(f"총 {len(df)}개 데이터가 수집되었습니다.")
                st.session_state.kpop_df = df

        except Exception as e:
            st.error(f"멜론 데이터 수집 실패: {e}")

# 결과 화면 출력 및 CSV 다운로드
if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 수업용 멜론 melon_top100_data.csv 다운로드",
        data=csv_data,
        file_name="melon_top100_data.csv",
        mime="text/csv"
    )
