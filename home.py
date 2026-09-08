import streamlit as st

st.title("데이터 과학 수업 자료")
st.write("아래 버튼을 눌러 원하는 차시로 이동하세요.")

col1, col2 = st.columns(2)
with col1:
    if st.button("1년치 박스오피스 데이터", use_container_width=True):
        st.switch_page("pages/01_one_year_boxoffice_data.py")
with col2:
    if st.button("회귀분석", use_container_width=True):
        st.switch_page("pages/02_regression.py")
