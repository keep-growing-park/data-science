import pandas as pd
import re
import streamlit as st
from ytmusicapi import YTMusic

st.set_page_config(page_title="K-POP 데이터 수집기", layout="wide")
st.title("🎵 K-POP 최신 음원 데이터 수집기")

if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 진짜 K-POP 음원 데이터 수집 시작"):
    with st.spinner("유튜브 뮤직에서 인기 K-POP 곡들을 가져오는 중..."):
        try:
            ytmusic = YTMusic()
            
            # 검증된 유튜브 뮤직 K-Pop 공식 플레이리스트 ID 직접 지정 (검색 과정 생략)
            # (K-Pop Hotlist 고유 ID)
            playlist_id = "RDCLAK5uy_kmPRB3eM142E9oL_T-L8fT5-E86uO8_c" 
            
            playlist_data = ytmusic.get_playlist(playlist_id, limit=100)
            tracks = playlist_data.get('tracks', [])

            data = []
            for track in tracks:
                title = track.get('title', '')
                artists = track.get('artists', [])
                artist_names = ", ".join([a['name'] for a in artists if 'name' in a]) if artists else "Unknown"
                
                # 재생시간(초 단위 변환)
                duration_str = str(track.get('duration', '0:00'))
                time_parts = duration_str.split(':')
                duration_sec = int(time_parts[0]) * 60 + int(time_parts[1]) if len(time_parts) == 2 else 0
                
                # 조회수 텍스트 -> 수치 변환
                views_raw = str(track.get('views', '0'))
                views_num = 0
                if '만' in views_raw:
                    num = re.sub(r'[^0-9.]', '', views_raw.split('만')[0])
                    views_num = int(float(num) * 10000) if num else 0
                elif '억' in views_raw:
                    num = re.sub(r'[^0-9.]', '', views_raw.split('억')[0])
                    views_num = int(float(num) * 100000000) if num else 0
                elif views_raw.isdigit():
                    views_num = int(views_raw)

                data.append({
                    '곡명': title,
                    '가수명': artist_names,
                    '조회수_숫자': views_num,
                    '재생시간_초': duration_sec,
                    '제목_글자수': len(title),
                    '참여가수수': len(artists) if artists else 1
                })

            st.session_state.kpop_df = pd.DataFrame(data)
            st.success(f"수집 완료! 총 {len(st.session_state.kpop_df)}개 곡의 실제 데이터를 가져왔습니다.")

        except Exception as e:
            st.error(f"유튜브 서버 연결 실패: {e}")

if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 수업용 kpop_learning_data.csv 다운로드",
        data=csv_data,
        file_name="kpop_learning_data.csv",
        mime="text/csv"
    )
