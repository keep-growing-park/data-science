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
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "❌ API 키를 찾을 수 없습니다! "
        "프로젝트 폴더 내 `.streamlit/secrets.toml` 파일에 "
        "`KOBIS_KEY = '발급받은_키'` 형태로 설정해주세요."
    )
    st.stop()

API_KEY = st.secrets["KOBIS_KEY"]


# ==========================================
# 3. KST 기준 과거 365일 날짜 리스트 생성 함수
# ==========================================
def get_past_365_days():
    """한국 표준시(KST) 기준으로 어제부터 과거 365일간의 YYYYMMDD 날짜 리스트를 생성합니다."""
    tz_kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.now(tz_kst)

    # 오늘 날짜는 집계 중일 수 있으므로 어제 날짜를 기준으로 설정
    yesterday = today_kst - timedelta(days=1)

    date_list = []
    for i in range(365):
        target_date = yesterday - timedelta(days=i)
        date_list.append(target_date.strftime("%Y%m%d"))

    return date_list


# ==========================================
# 4. 데이터 수집 함수 (2시간 캐시 적용)
# ==========================================
# ttl=7200 (2시간): 수집된 데이터는 2시간 동안 메모리에 보관되어 재사용됩니다.
# cache_key: 2시간 단위로 캐시 키가 변하므로, 2시간이 지난 후 클릭 시 자동으로 새 데이터를 수집합니다.
@st.cache_data(ttl=7200, show_spinner=False)
def fetch_boxoffice_data_for_365_days(api_key, cache_key):
    """365일치 박스오피스 데이터를 수집하여 하나의 데이터프레임으로 변환하는 함수"""
    dates = get_past_365_days()
    all_records = []
    failed_dates = []

    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_days = len(dates)

    for idx, dt in enumerate(dates):
        current_step = idx + 1
        progress_bar.progress(current_step / total_days)
        status_text.text(
            f"⏳ 데이터 수집 중... ({current_step}/{total_days}일) - 조회일자: {dt}"
        )

        params = {"key": api_key, "targetDt": dt}

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                failed_dates.append(dt)
                continue

            data = response.json()

            if "faultInfo" in data:
                failed_dates.append(dt)
                continue

            daily_list = data.get("boxOfficeResult", {}).get(
                "dailyBoxOfficeList", []
            )

            if not daily_list:
                failed_dates.append(dt)
                continue

            formatted_date = f"{dt[:4]}-{dt[4:6]}-{dt[6:]}"

            for item in daily_list:
                item["기준일자"] = formatted_date
                all_records.append(item)

        except Exception:
            failed_dates.append(dt)
            continue

    progress_bar.empty()
    status_text.empty()

    if not all_records:
        return pd.DataFrame(), failed_dates

    df = pd.DataFrame(all_records)

    # ==========================================
    # 5. 데이터 전처리
    # ==========================================
    column_mapping = {
        "기준일자": "기준일자",
        "rank": "박스오피스순위",
        "movieNm": "영화명",
        "audiCnt": "해당일관객수",
        "audiAcc": "누적관객수",
        "scrnCnt": "스크린수",
        "showCnt": "상영횟수",
    }

    available_cols = [c for c in column_mapping.keys() if c in df.columns]
    df = df[available_cols]
    df = df.rename(columns=column_mapping)

    numeric_cols = [
        "박스오피스순위",
        "해당일관객수",
        "누적관객수",
        "스크린수",
        "상영횟수",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df, failed_dates


# ==========================================
# 6. 세션 상태(session_state) 초기화
# ==========================================
if "boxoffice_df" not in st.session_state:
    st.session_state["boxoffice_df"] = None
if "failed_dates" not in st.session_state:
    st.session_state["failed_dates"] = None


# ==========================================
# 7. 버튼 및 메인 로직
# ==========================================
if st.button("🚀 최근 365일치 박스오피스 데이터 수집 시작"):
    with st.spinner("데이터 수집을 시작합니다..."):
        tz_kst = pytz.timezone("Asia/Seoul")
        now_kst = datetime.now(tz_kst)

        # 2시간 단위로 변경되는 캐시 키 생성 (예: 2026-09-10_5 -> 10시~12시 사이 동일)
        cache_key = f"{now_kst.strftime('%Y-%m-%d')}_{now_kst.hour // 2}"

        # API_KEY와 함께 2시간 단위 cache_key를 함께 전달
        df_result, fails = fetch_boxoffice_data_for_365_days(API_KEY, cache_key)
        st.session_state["boxoffice_df"] = df_result
        st.session_state["failed_dates"] = fails

# 데이터가 세션에 존재하는 경우 화면 출력
if st.session_state["boxoffice_df"] is not None:
    df = st.session_state["boxoffice_df"]
    fails = st.session_state["failed_dates"]

    st.divider()

    if not df.empty:
        st.success(f"🎉 총 **{len(df):,}개**의 데이터 수집 완료!")

        if fails:
            st.warning(
                f"⚠️ 데이터 수집 실패 날짜: 총 **{len(fails)}일** (해당 날짜는 건너뛰었습니다.)"
            )
        else:
            st.balloons()
            st.info("🎊 365일 모든 날짜의 데이터를 한 건의 누락 없이 성공적으로 가져왔습니다!")

        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV 파일로 다운로드하기",
            data=csv_data,
            file_name="kobis_1year_boxoffice.csv",
            mime="text/csv",
        )

        st.subheader("📊 수집된 박스오피스 전체 데이터")
        st.dataframe(df, use_container_width=True)

    else:
        st.error("❌ 수집된 데이터가 없습니다. API 키 상태를 확인해주세요.")
