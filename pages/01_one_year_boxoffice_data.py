import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz

# 페이지 기본 설정 (가로 너비를 넓게 설정)
st.set_page_config(page_title="1년치 박스오피스 데이터 조회", layout="wide")

# -------------------------------------------------------------------
# [1] API 키 불러오기 및 기본 처리
# Streamlit secrets에서 KOBIS_KEY를 가져옵니다.
# -------------------------------------------------------------------
try:
    API_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    API_KEY = None

st.title("🎬 KOBIS 1년치 박스오피스 데이터 수집 및 조회")

# API 키가 등록되지 않았을 때 사용자에게 안내 문구를 띄웁니다.
if not API_KEY:
    st.error("⚠️ API 키를 넣어주세요. (.streamlit/secrets.toml 파일에 KOBIS_KEY를 설정해야 합니다.)")
    st.stop()


# -------------------------------------------------------------------
# [2] 1년치 박스오피스 데이터 수집 함수 (캐싱 적용)
# @st.cache_data를 사용하여 이미 가져온 데이터는 재요청 없이 기억해둡니다.
# -------------------------------------------------------------------
@st.cache_data(ttl=86400 * 30)  # 한 번 가져온 데이터는 한 달간 재사용합니다.
def fetch_one_year_boxoffice(api_key):
    # 서버 시계와 상관없이 한국 표준시(KST) 기준으로 날짜를 계산합니다.
    tz_kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(tz_kst)
    
    # '어제' 날짜를 구합니다 (오늘 데이터는 집계 전이므로 어제부터 시작)
    yesterday = now_kst - timedelta(days=1)
    
    # 어제부터 과거 365일간의 날짜 객체 목록을 만듭니다.
    dates = [yesterday - timedelta(days=i) for i in range(365)]
    
    all_data = []      # 모든 일자별 영화 데이터를 담을 리스트
    failed_dates = []  # 데이터를 불러오지 못한 날짜를 담을 리스트
    
    # 화면에 수집 진행 상황을 보여주는 바(Bar)와 텍스트를 준비합니다.
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_days = len(dates)
    
    base_url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    
    # 365일 데이터를 하루씩 반복해서 가져옵니다.
    for index, date_obj in enumerate(dates):
        # API 요청용 날짜 형식: YYYYMMDD (예: 20260908)
        target_dt = date_obj.strftime('%Y%m%d')
        # 화면 표기용 날짜 형식: YYYY-MM-DD (예: 2026-09-08)
        formatted_date = date_obj.strftime('%Y-%m-%d')
        
        # 진행 상황 안내 문구 업데이트
        status_text.text(f"⏳ 데이터 수집 중... ({index + 1}/{total_days} 일) - 기준일자: {formatted_date}")
        progress_bar.progress((index + 1) / total_days)
        
        try:
            params = {
                'key': api_key,
                'targetDt': target_dt
            }
            # API 요청 보내기 (타임아웃 10초 설정)
            response = requests.get(base_url, params=params, timeout=10)
            
            # 네트워크 요청 실패 시 해당 날짜 건너뛰기
            if response.status_code != 200:
                failed_dates.append(formatted_date)
                continue
            
            data = response.json()
            
            # API 내부 에러(faultInfo)가 포함되어 있는 경우 건너뛰기
            if 'faultInfo' in data:
                failed_dates.append(formatted_date)
                continue
                
            box_office_result = data.get('boxOfficeResult', {})
            daily_list = box_office_result.get('dailyBoxOfficeList', [])
            
            # 영화 목록이 비어있는 경우 건너뛰기
            if not daily_list:
                failed_dates.append(formatted_date)
                continue
            
            # 맨 앞 컬럼에 '기준일자'를 넣어줍니다.
            for movie in daily_list:
                movie_with_date = {'기준일자': formatted_date}
                movie_with_date.update(movie)
                all_data.append(movie_with_date)
                
        except Exception:
            # 에러 발생 시 해당 날짜를 failure에 기록하고 계속 진행
            failed_dates.append(formatted_date)
            continue

    # 작업 완료 후 진행 표시줄 숨기기
    progress_bar.empty()
    status_text.empty()
    
    # 수집된 데이터를 판다스 데이터프레임으로 변환
    df = pd.DataFrame(all_data)
    
    # ---------------------------------------------------------------
    # [3] 데이터 전처리 (영문 컬럼명을 한글로 변경 및 숫자 데이터 변환)
    # ---------------------------------------------------------------
    if not df.empty:
        # 1. API 영문 속성 이름을 학생들이 이해하기 쉬운 한글 이름으로 매핑합니다.
        column_mapping = {
            'rnum': '순번',
            'rank': '박스오피스순위',
            'rankInten': '전일대비순위증감',
            'rankOldAndNew': '신규진입여부',
            'movieCd': '영화대표코드',
            'movieNm': '영화명',
            'openDt': '개봉일',
            'salesAmt': '해당일매출액',
            'salesShare': '매출점유율',
            'salesInten': '전일대비매출증감',
            'salesChange': '전일대비매출증감비율',
            'salesAcc': '누적매출액',
            'audiCnt': '해당일관객수',
            'audiInten': '전일대비관객수증감',
            'audiChange': '전일대비관객수증감비율',
            'audiAcc': '누적관객수',
            'scrnCnt': '스크린수',
            'showCnt': '상영횟수'
        }
        
        # 데이터프레임의 컬럼명을 한글로 일괄 변경합니다.
        df = df.rename(columns=column_mapping)
        
        # 2. 숫자로 처리할 한글 컬럼 목록
        numeric_columns = [
            '순번', '박스오피스순위', '전일대비순위증감', 
            '해당일매출액', '매출점유율', '전일대비매출증감', '전일대비매출증감비율', '누적매출액',
            '해당일관객수', '전일대비관객수증감', '전일대비관객수증감비율', '누적관객수',
            '스크린수', '상영횟수'
        ]
        
        # 문자열로 온 숫자 값들을 실제 숫자형(Int/Float)으로 변경합니다.
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
    return df, failed_dates


# -------------------------------------------------------------------
# [4] 데이터 수집 실행 버튼
# -------------------------------------------------------------------
if st.button("🚀 1년치 데이터 수집 시작"):
    df, failed_dates = fetch_one_year_boxoffice(API_KEY)
    
    # 가져온 데이터프레임을 세션 상태에 저장하여 화면에 유지
    st.session_state['df'] = df
    st.session_state['failed_dates'] = failed_dates


# -------------------------------------------------------------------
# [5] 데이터 수집 결과 출력 & 표 형태로 화면에 표시
# -------------------------------------------------------------------
if 'df' in st.session_state and st.session_state['df'] is not None:
    df = st.session_state['df']
    failed_dates = st.session_state['failed_dates']
    
    st.write("---")
    st.success(f"데이터 수집 완료! 총 **{len(df):,}개**의 영화 순위 데이터가 로드되었습니다.")
    
    # 실패/누락된 날짜 안내
    if failed_dates:
        st.warning(f"⚠️ 총 {len(failed_dates)}개 날짜 데이터를 가져오지 못했습니다. (누락 일자 수: {len(failed_dates)}일)")
    else:
        st.info("🎉 365일 전체 날짜 데이터를 누락 없이 가져왔습니다.")

    # CSV 변환 (엑셀에서 한글 깨짐 방지를 위해 utf-8-sig 인코딩 사용)
    csv_data = df.to_csv(index=False).encode('utf-8-sig')

    # 다운로드 버튼 및 제목 헤더 영역
    col_title, col_download = st.columns([3, 1])
    
    with col_title:
        st.subheader("📋 수집된 박스오피스 전체 데이터")
        
    with col_download:
        # CSV 다운로드 버튼
        st.download_button(
            label="💾 CSV 파일로 다운로드",
            data=csv_data,
            file_name="kobis_1year_boxoffice.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 메인 화면에 한글 컬럼으로 바뀐 데이터를 표(Table) 형태로 직접 보여줍니다.
    st.dataframe(df, use_container_width=True, height=600)
