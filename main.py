import streamlit as st

home = st.Page("home.py", title="홈", icon="🏠", default=True)
page1 = st.Page("pages/01_one_year_boxoffice_data.py", title="1년치 박스오피스 데이터")
page2 = st.Page("pages/02_music_data.py", title="유투브 뮤직 데이터")

pg = st.navigation([home, page1, page2])
pg.run()
