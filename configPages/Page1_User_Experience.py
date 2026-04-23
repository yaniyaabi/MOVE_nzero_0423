import streamlit as st
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from Modules.P1_Kakao_service_waiting import return_waitings
from Modules.P1_Dispatch_success_ratio import return_dispatch_ratio
from Modules.P1_sevice_arrival_operation_times import return_graphs_and_stats
from Modules.N2_Kakao_realtime_loader import return_realtime_operations
from utils.maps import normalize_weights, markers_map_html, default_map_html, routes_map_html


def render(current_time, temp_interval, PAGES_URL, kakao_api_key):
    st.header(f"♿ MOVE / 이용자 경험")
    st.markdown('##### MOVE (Mobility On-demand for Vulnerable & Elderly)')
    st.markdown('---')
    st.markdown('#### **|** 대상 지역')

    service_options = {
        "통합 (교통약자지역 + 교통소외지역)": [1, 2],
        "교통약자지역": [1],
        "교통소외지역": [2]
    }

    service_option_labels = list(service_options.keys())
    service_default_index = service_option_labels.index("통합 (교통약자지역 + 교통소외지역)")
    selected_service_label = st.selectbox(f"🕒 현재 시간: {current_time}", service_option_labels, index=service_default_index)
    selected_service_values = service_options[selected_service_label]
  
    st.markdown('---')

    col = st.columns((1, 1, 1), gap='large')
    with col[0]:
        st.markdown('#### **|** 배차 소요시간 (초)')
        chart_response, _, _, stats, _ = return_waitings(current_time=current_time, days_interval=temp_interval, reserveType=None, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="배차 소요시간 (초)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_response, use_container_width=True)

    with col[1]:
        st.markdown('#### **|** 서비스 대기시간 (분)')
        _, chart_waiting, _, stats, _ = return_waitings(current_time=current_time, days_interval=temp_interval, reserveType=None, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="서비스 대기시간 (분)", value=np.round(stats[2]/60, 2), delta=np.round((stats[2] - stats[3])/60, 2), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_waiting, use_container_width=True)
            
    with col[2]:
        st.markdown('#### **|** 배차 성공률 (%)')
        chart_success, stats = return_dispatch_ratio(current_time=current_time, days_interval=temp_interval, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="배차 성공률 (%)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_success, use_container_width=True)

    st.markdown('---')

    col = st.columns((1, 1, 1), gap='large')
    with col[0]:
        st.markdown('#### **|** 서비스 이용시간 (분)')
        chart_Actual_use_time, _, _, stats = return_graphs_and_stats(current_time=current_time, days_interval=temp_interval, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="서비스 이용시간 (분)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_Actual_use_time, use_container_width=True)

    with col[1]:
        st.markdown('#### **|** 차량 도착 정시성 (분)')
        _, chart_pickup_delay, _, stats = return_graphs_and_stats(current_time=current_time, days_interval=temp_interval, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="차량 도착 정시성 (분)", value=np.round(stats[2], 1), delta=np.round((stats[2] - stats[3]), 1), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_pickup_delay, use_container_width=True)

    with col[2]:
        st.markdown('#### **|** 차량 주행 정시성 (분)')
        _, _, chart_Actual_operation_delay, stats = return_graphs_and_stats(current_time=current_time, days_interval=temp_interval, sevice_Type=selected_service_values)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            st.metric(label="차량 주행 정시성 (분)", value=np.round(stats[4], 1), delta=np.round((stats[4] - stats[5]), 1), label_visibility='hidden')
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_Actual_operation_delay, use_container_width=True)

    st.markdown('---')

    sub_service_options = {
    "교통약자지역": [1],
    "교통소외지역": [2]
    }
    sub_service_labels = list(sub_service_options.keys())
    sub_service_default_index = sub_service_labels.index("교통약자지역" if selected_service_label != "교통소외지역" else "교통소외지역")
    selected_sub_service = st.selectbox("", sub_service_labels, index=sub_service_default_index)

    col = st.columns((1.3, 1), gap='large')
    with col[0]:
        st.markdown('#### **|** 서비스 대기 시간 지도')

        options = {
            "사전 예약": 1,
            "실시간 예약": 2,
        }
        option_labels = list(options.keys())
        default_index = option_labels.index("사전 예약")
        selected_label = st.selectbox(f"🕒 현재 시간: {current_time}", option_labels, index=default_index)
        _, _, _, _, locations = return_waitings(current_time=current_time, days_interval=temp_interval, reserveType=selected_label, sevice_Type=selected_service_values)

        # 2026.03.08 업데이트 - 백정엽 (지도 옆에 표 표출)
        waiting_df = pd.DataFrame(locations)
        waiting_df = waiting_df[['station', 'weight']]

        waiting_df = (
            waiting_df
            .groupby('station')
            .agg(
                예약건수=('station', 'count'),
                평균대기시간=('weight', 'mean')
            )
            .reset_index()
        )
        waiting_df = waiting_df.rename(columns={
            'station': '정류장 ID',
            '평균대기시간': '(평균)대기시간 (분)'
        })

        waiting_df = waiting_df.sort_values('(평균)대기시간 (분)', ascending=False).reset_index(drop=True)
        waiting_df.index = waiting_df.index + 1

        top2_values = waiting_df["(평균)대기시간 (분)"].nlargest(2).unique()
        max_rows = waiting_df[waiting_df["(평균)대기시간 (분)"].isin(top2_values)]


        if len(max_rows) > 1:
            highlight_idx = max_rows.index
        else:
            highlight_idx = waiting_df.nlargest(3, "(평균)대기시간 (분)").index

        def highlight_rows(row):
            if row.name in highlight_idx:
                return ["background-color: rgba(255, 215, 0, 0.3); font-weight: bold;"] * len(row)
            return [""] * len(row)
        
        styled_df = waiting_df.style.apply(highlight_rows, axis=1).format({
                        '(평균)대기시간 (분)': '{:.1f}'
                    })

        if selected_sub_service == "교통소외지역":
            col_subs = st.columns((2, 1), gap='small')
            with col_subs[0]:
                try:
                    map_html = markers_map_html(PAGES_URL, kakao_api_key, normalize_weights(locations), center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
                except Exception:
                    map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
                components.html(map_html, height=700)
            with col_subs[1]:
                st.dataframe(styled_df, use_container_width=True, height=700)

        else:
            col_subs = st.columns((2, 1), gap='small')
            with col_subs[0]:
                try:
                    map_html = markers_map_html(PAGES_URL, kakao_api_key, normalize_weights(locations), center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
                except Exception:
                    map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
                components.html(map_html, height=700)
            with col_subs[1]:
                st.dataframe(styled_df, use_container_width=True, height=700)

    with col[1]:
        st.markdown('#### **|** 실시간 운행 정보 - 30분 전후 포함')

        temp_oper_info, temp_routes, temp_pickup_info, temp_dropoff_info = return_realtime_operations(current_time, minutes_interval=30)
        selected_index = st.selectbox(f"🕒 현재 시간: {current_time}", range(len(temp_routes)), 
                                        format_func=lambda i: f"운행 #{i+1} | 차량 : {temp_oper_info[i][0]} - 운행시간 : 총 {int(temp_oper_info[i][1])}분 - 총 요청수 : {temp_oper_info[i][2]}개 - 총 승객수 : {temp_oper_info[i][3]} - 총 휠체어수 : {temp_oper_info[i][4]}")
        
        if selected_sub_service == "교통소외지역":
            try:
                temp_routes = [temp_routes[selected_index]]
                temp_pickup_info = temp_pickup_info[selected_index]
                map_html = routes_map_html(PAGES_URL, kakao_api_key, temp_routes, temp_pickup_info, center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
            except Exception:
                map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
            components.html(map_html, height=700)
        
        else:
            try:
                temp_routes = [temp_routes[selected_index]]
                temp_pickup_info = temp_pickup_info[selected_index]
                map_html = routes_map_html(PAGES_URL, kakao_api_key, temp_routes, temp_pickup_info, center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
            except Exception:
                map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
            components.html(map_html, height=700)
