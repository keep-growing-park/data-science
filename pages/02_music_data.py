import pandas as pd
from ytmusicapi import YTMusic

# 1. YTMusic 객체 초기화 (인증 없이 공개 데이터 접근 가능)
ytmusic = YTMusic()

# 2. 한국(South Korea) 지역의 최신 인기 곡 차트 조회
# 'ZZ'는 글로벌/지역 차트를 의미하며, country='KR'로 한국 차트 지정
try:
    charts = ytmusic.get_charts(country='KR')
    selected_playlist = charts['videos']['playlist']  # 인기 동영상/음악 차트
    tracks = ytmusic.get_playlist(selected_playlist, limit=100)['tracks']
except Exception as e:
    print(f"차트 데이터를 불러오는 중 오류 발생: {e}")
    tracks = []

# 3. 데이터 추출 및 정제
data = []

for track in tracks[:100]:
    title = track.get('title', '')
    
    # 아티스트 정보 추출 (여러 명일 경우 쉼표로 연결)
    artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
    
    # 조회수 정보 추출 (유튜브 뮤직 특성상 'views' 항목에 텍스트 형태로 들어옴)
    views = track.get('views', '0')
    
    # videoId를 통해 세부 정보 조회 (좋아요 수 수집용)
    video_id = track.get('videoId')
    
    # 기본 데이터 구조 저장
    data.append({
        '곡명': title,
        '가수명': artists,
        '조회수_텍스트': views,
        'videoId': video_id
    })

# DataFrame 변환
df = pd.DataFrame(data)

# 4. 데이터 저장
output_file = 'kpop_latest_youtube.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"총 {len(df)}개의 최신 K-POP 데이터 수집 완료! '{output_file}' 파일로 저장되었습니다.")
