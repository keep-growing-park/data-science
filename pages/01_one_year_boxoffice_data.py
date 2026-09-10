
import time
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정 (넓은 레이아웃 적용)
# ==========================================
st.set_page_config(
    page_title="KOBIS 1개년 박스오피스 수집기",
    page_icon="🎬",
    layout="wide",  # 화면 전체를 활용하는 Wide 모드 설정
)

st.title("🎬 KOBIS 최근 1년(365일) 박스오피스 데이터 수집기")
st.markdown(
    """
    이 프로그램은 영화진흥위원회(KOBIS) API를 활용하여 **어제 날짜부터 과거 365일간**의 일별 박스오피스 데이터를 자동으로 수집합니다.
    """
)

# ==========================================
# 2. API 키 보안 검사 (Streamlit secrets 활용)
# ==========================================
# secrets.toml 파일에 API 키가 제대로 설정되어 있는지 확인합니다.
# 코드에 직접 키를 작성하면 GitHub 등에 올려졌을 때 보안 문제가 발생할 수 있습니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "❌ API 키를 찾을 수 없습니다! "
        "프로젝트 폴더 내 `.streamlit/secrets.toml` 파일에 "
        "`KOBIS_KEY = '발급받은_키'` 형태로 설정해주세요."
    )
    # API 키가 없으면 아래 코드를 더 이상 실행하지 않고 중단합니다.
    st.stop()

# 저장되어 있는 API 키를 변수에 할당합니다.
API_KEY = st.secrets["KOBIS_KEY"]


# ==========================================
# 3. KST 기준 과거 365일 날짜 리스트 생성 함수
# ==========================================
def get_past_365_days():
    """한국 표준시(KST) 기준으로 어제부터 과거 365일간의 YYYYMMDD 날짜 리스트를 생성합니다."""
    # pytz 라이브러리를 사용하여 서울 타임존 지정
    tz_kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.now(tz_kst)

    # 오늘 날짜는 집계 중일 수 있으므로 어제 날짜를 기준으로 설정
    yesterday = today_kst - timedelta(days=1)

    date_list = []
    # 어제(0일 전)부터 과거 364일 전까지 총 365일 반복
    for i in range(365):
        target_date = yesterday - timedelta(days=i)
        # API에서 요구하는 YYYYMMDD 형태로 포맷팅 (예: 20260908)
        date_list.append(target_date.strftime("%Y%m%d"))

    return date_list


# ==========================================
# 4. 데이터 수집 함수 (캐싱 적용)
# ==========================================
# @st.cache_data를 적용하면 실행 결과를 저장(캐시)해두므로
# 한 번 불러온 데이터를 30일 동안 다시 API 요청 없이 빠르게 재사용할 수 있습니다.
@st.cache_data(ttl=3600 * 24 * 30, show_spinner=False)
def fetch_boxoffice_data_for_365_days(api_key):
    """365일치 박스오피스 데이터를 수집하여 하나의 데이터프레임으로 변환하는 함수"""
    dates = get_past_365_days()
    all_records = []
    failed_dates = []

    # API 요청 기본 URL 및 진행률 표시줄 준비
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_days = len(dates)

    for idx, dt in enumerate(dates):
        # UI 업데이트: 진행 상황 안내
        current_step = idx + 1
        progress_bar.progress(current_step / total_days)
        status_text.text(
            f"⏳ 데이터 수집 중... ({current_step}/{total_days}일) - 조회일자: {dt}"
        )

        params = {"key": api_key, "targetDt": dt}

        try:
            response = requests.get(url, params=params, timeout=10)

            # 1) 요청 실패 (상태코드가 200 OK가 아닌 경우)
            if response.status_code != 200:
                failed_dates.append(dt)
                continue

            data = response.json()

            # 2) 응답 결과에 faultInfo(에러 정보)가 들어있는 경우
            if "faultInfo" in data:
                failed_dates.append(dt)
                continue

            daily_list = data.get("boxOfficeResult", {}).get(
                "dailyBoxOfficeList", []
            )

            # 3) 박스오피스 리스트 데이터가 비어있는 경우
            if not daily_list:
                failed_dates.append(dt)
                continue

            # 정상 응답 시 '기준일자' 컬럼을 추가하며 레코드 저장
            # YYYYMMDD -> YYYY-MM-DD 변환
            formatted_date = f"{dt[:4]}-{dt[4:6]}-{dt[6:]}"

            for item in daily_list:
                item["기준일자"] = formatted_date
                all_records.append(item)

        except Exception:
            # 4) 네트워크 미연결 등 기타 예상치 못한 예외 발생 시 건너뛰기
            failed_dates.append(dt)
            continue

    # 수집 안내 문구 및 진행바 제거
    progress_bar.empty()
    status_text.empty()

    # 데이터가 전혀 수집되지 않은 경우 빈 데이터프레임 반환
    if not all_records:
        return pd.DataFrame(), failed_dates

    # 전체 수집 결과를 판다스 데이터프레임으로 변환
    df = pd.DataFrame(all_records)

    # ==========================================
    # 5. 데이터 전처리
    # ==========================================
    # 사용할 6개 컬럼 선정 및 한글 이름 매핑
    column_mapping = {
        "기준일자": "기준일자",
        "rank": "박스오피스순위",
        "movieNm": "영화명",
        "audiCnt": "해당일관객수",
        "audiAcc": "누적관객수",
        "scrnCnt": "스크린수",
        "showCnt": "상영횟수",
    }

    # 존재하는 컬럼만 선별하여 추출 후 이름 변경
    available_cols = [c for c in column_mapping.keys() if c in df.columns]
    df = df[available_cols]
    df = df.rename(columns=column_mapping)

    # 숫자로 변환해야 하는 컬럼들 지정
    numeric_cols = [
        "박스오피스순위",
        "해당일관객수",
        "누적관객수",
        "스크린수",
        "상영횟수",
    ]

    # pd.to_numeric을 사용해 문자열 형태의 숫자를 정수/실수형으로 변환 (변환 불가 시 0으로 채움)
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df, failed_dates


# ==========================================
# 6. 세션 상태(session_state) 초기화
# ==========================================
# 화면이 새로고침되어도 수집한 데이터가 사라지지 않도록 st.session_state에 저장합니다.
if "boxoffice_df" not in st.session_state:
    st.session_state["boxoffice_df"] = None
if "failed_dates" not in st.session_state:
    st.session_state["failed_dates"] = None

# ==========================================
# 7. 버튼 및 메인 로직
# ==========================================
# 데이터 수집 시작 버튼
if st.button("🚀 최근 365일치 박스오피스 데이터 수집 시작"):
    with st.spinner("데이터 수집을 시작합니다..."):
        df_result, fails = fetch_boxoffice_data_for_365_days(API_KEY)
        st.session_state["boxoffice_df"] = df_result
        st.session_state["failed_dates"] = fails

# 데이터가 세션에 존재하는 경우 화면 출력
if st.session_state["boxoffice_df"] is not None:
    df = st.session_state["boxoffice_df"]
    fails = st.session_state["failed_dates"]

    st.divider()

    if not df.empty:
        # 결과 메시지 출력
        st.success(f"🎉 총 **{len(df):,}개**의 데이터 수집 완료!")

        if fails:
            st.warning(
                f"⚠️ 데이터 수집 실패 날짜: 총 **{len(fails)}일** (해당 날짜는 건너뛰었습니다.)"
            )
        else:
            st.balloons()
            st.info("🎊 365일 모든 날짜의 데이터를 한 건의 누락 없이 성공적으로 가져왔습니다!")

        # CSV 다운로드 기능 제공 (한글 깨짐 방지를 위해 utf-8-sig 활용)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV 파일로 다운로드하기",
            data=csv_data,
            file_name="kobis_1year_boxoffice.csv",
            mime="text/csv",
        )

        st.subheader("📊 수집된 박스오피스 전체 데이터")
        # 데이터프레임을 전체 화면 너비로 깔끔하게 표시
        st.dataframe(df, use_container_width=True)

    else:
        st.error("❌ 수집된 데이터가 없습니다. API 키 상태를 확인해주세요.")
