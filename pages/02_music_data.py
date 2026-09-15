import sys
import subprocess
import pandas as pd
import streamlit as st

# 차단 우회용 curl_cffi 및 bs4 자동 설치
try:
    from curl_cffi import requests as curl_requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi", "beautifulsoup4"])
    from curl_cffi import requests as curl_requests
    from bs4 import BeautifulSoup

st.set_page_config(page_title="Melon TOP 100 데이터 수집기", layout="wide")
st.title("🎵 멜론(Melon) 실시간 TOP 100 데이터 수집기")
st.caption("클라우드 서버 차단을 우회하여 멜론 실시간 TOP 100 실제 데이터를 수집합니다.")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 멜론 TOP 100 실제 데이터 수집 시작"):
    with st.spinner("멜론 보안 서버 검증 통과 중..."):
        try:
            url = "https://www.melon.com/chart/index.htm"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.melon.com/'
            }
            
            # Chrome 브라우저의 TLS 지문(Fingerprint)을 복제하여 해외 IP 차단 우회
            response = curl_requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            lst50 = soup.select('tr.lst50')
            lst100 = soup.select('tr.lst100')
            tr_list = lst50 + lst100
            
            data = []
            for tr in tr_list:
                rank_elem = tr.select_one('span.rank')
                if not rank_elem:
                    continue
                rank = int(rank_elem.text.strip())
                
                title_elem = tr.select_one('div.ellipsis.rank01 a')
                title = title_elem.text.strip() if title_elem else ""
                
                artist_elem = tr.select_one('div.ellipsis.rank02 > a')
                artist = artist_elem.text.strip() if artist_elem else ""
                
                album_elem = tr.select_one('div.ellipsis.rank03 a')
                album = album_elem.text.strip() if album_elem else ""
                
                data.append({
                    '순위': rank,
                    '곡명': title,
                    '가수명': artist,
                    '앨범명': album,
                    '추천점수': 101 - rank,
                    '제목_글자수': len(title),
                    '가수명_글자수': len(artist)
                })

            df = pd.DataFrame(data)
            
            if not df.empty and len(df) >= 50:
                st.session_state.kpop_df = df
                st.success(f"수집 성공! 멜론 TOP 100 실제 데이터({len(df)}개)를 정상 수집했습니다.")
            else:
                st.error("데이터 추출에 실패했습니다.")

        except Exception as e:
            st.error(f"수집 오류 발생: {e}")

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
