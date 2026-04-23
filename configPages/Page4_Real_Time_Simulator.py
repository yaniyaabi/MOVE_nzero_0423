import streamlit as st
import streamlit.components.v1 as components

def render(current_time, temp_interval, PAGES_URL, kakao_api_key):
    st.header(f"♿ MOVE / 실시간 시뮬레이터")
    st.markdown('##### MOVE (Mobility On-demand for Vulnerable & Elderly)')
    st.markdown('---')

    st.subheader("🔍 실시간 시뮬레이터 시각화")
    components.iframe("https://drt-simulation.vercel.app/", height=800, scrolling=True)