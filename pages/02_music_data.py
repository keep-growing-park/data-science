import pandas as pd
import re
import streamlit as st
from ytmusicapi import YTMusic

st.set_page_config(page_title="K-POP 데이터 수집기", layout="wide")

st.title("🎵 K-POP 최신 차트 데이터 수집기")

# 세션 상태 초기화 (데이터 휘발 방지)
if "kpop_df" not in st.session_state:
    st.session_state.kpop_df = None

if st.button("🚀 최신 K-POP 데이터 수집 시작"):
    with st.spinner("유튜브 뮤직 서버에 연결하는 중..."):
        try:
            ytmusic = YTMusic()
            charts = ytmusic.get_charts(country='KR')
            
            # 차트 응답 확인
            if not charts or 'videos' not in charts:
                st.error("유튜브 뮤직에서 차트 데이터를 가져오지 못했습니다. (클라우드 IP 차단 가능성)")
            else:
                playlist_id = charts['videos']['playlist']
                tracks = ytmusic.get_playlist(playlist_id, limit=100)['tracks']

                data = []
                for track in tracks[:100]:
                    title = track.get('title', '')
                    artists = track.get('artists', [])
                    artist_names = ", ".join([a['name'] for a in artists])
                    
                    # 재생시간 변환
                    duration_str = track.get('duration', '0:00')
                    time_parts = duration_str.split(':')
                    duration_sec = int(time_parts[0]) * 60 + int(time_parts[1]) if len(time_parts) == 2 else 0
                    
                    # 조회수 변환
                    views_raw = track.get('views', '0')
                    views_num = 0
                    if '만' in views_raw:
                        num = re.sub(r'[^0-9.]', '', views_raw.split('만')[0])
                        views_num = int(float(num) * 10000) if num else 0
                    elif '억' in views_raw:
                        num = re.sub(r'[^0-9.]', '', views_raw.split('억')[0])
                        views_num = int(float(num) * 100000000) if num else 0

                    data.append({
                        '곡명': title,
                        '가수명': artist_names,
                        '조회수_숫자': views_num,
                        '재생시간_초': duration_sec,
                        '제목_글자수': len(title),
                        '참여가수수': len(artists)
                    })

                # 결과를 세션에 저장
                st.session_state.kpop_df = pd.DataFrame(data)
                st.success(f"수집 완료! 총 {len(st.session_state.kpop_df)}개 곡을 가져왔습니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")

# 수집된 데이터가 세션에 존재할 때 화면에 출력
if st.session_state.kpop_df is not None and not st.session_state.kpop_df.empty:
    st.dataframe(st.session_state.kpop_df, use_container_width=True)
    
    csv_data = st.session_state.kpop_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 최신 kpop_learning_data.csv 다운로드",
        data=csv_data,
        file_name="kpop_learning_data.csv",
        mime="text/csv"
    )
