import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from Modules.P2_Donuts import return_reserveType, return_serviceType, operation_vehicle, return_failinfo
from Modules.P2_operation_percentage import return_boaring_rates
from Modules.P2_service_capacity import return_service_capacity
from Modules.P2_boarding_vehicle_rate import return_boaring_vehicle_rates
from Modules.P2_Kakao_link_loader import return_link_frequency
from Modules.N1_Kakao_data_loader import return_pickup_station_count
from utils.maps import normalize_weights, markers_map_html, default_map_html, links_map_html

def render(current_time, temp_interval, PAGES_URL, kakao_api_key):

    st.header(f"♿ MOVE / 운영 효율")
    st.markdown('##### MOVE (Mobility On-demand for Vulnerable & Elderly)')
    st.markdown('---')

    options = {
        "최근 1일": 1,
        "최근 3일": 3,
        "최근 7일": 7,
        "최근 14일": 14
    }
    option_labels = list(options.keys())
    default_index = option_labels.index("최근 7일")
    selected_label = st.selectbox(f"🕒 현재 시간: {current_time} ", option_labels, index=default_index)
    selected_days = options[selected_label]


    col = st.columns((1, 1, 1, 1), gap='large')
    with col[0]:
        st.markdown('#### **|** 예약 유형')
        temp_dispatch_df = return_reserveType(current_time=current_time, day_interval=selected_days)
        reserve_counts = temp_dispatch_df['reserveType'].value_counts().sort_index()
        reserve_labels = reserve_counts.index.tolist()
        hovertext = [
            f"{rtype}<br>{count}건<br>{count / reserve_counts.sum():.1%}"
            for rtype, count in reserve_counts.items()
        ]
        colors = ['#4A90E2', '#F5A623']
        fig = go.Figure(data=[go.Pie(
            labels=reserve_labels,
            values=reserve_counts.values,
            hole=.45,
            textinfo='percent',
            textfont=dict(size=20),
            hoverinfo='text',
            hovertext=hovertext,
            marker=dict(colors=colors, line=dict(color='white', width=0))
        )])
        fig.update_layout(
            annotations=[dict(text='예약<br>유형', x=0.5, y=0.5, font_size=24, showarrow=False)],
            showlegend=True,
            legend=dict(font=dict(size=18)),
            hoverlabel=dict(font_size=16),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col[1]:
        st.markdown('#### **|** 서비스 유형')
        temp_dispatch_df = return_serviceType(current_time=current_time, day_interval=selected_days)
        reserve_counts = temp_dispatch_df['serviceType'].value_counts().sort_index()
        reserve_labels = reserve_counts.index.tolist()
        hovertext = [
            f"{rtype}<br>{count}건<br>{count / reserve_counts.sum():.1%}"
            for rtype, count in reserve_counts.items()
        ]
        colors = ['#F6D55C', '#173F5F']
        fig = go.Figure(data=[go.Pie(
            labels=reserve_labels,
            values=reserve_counts.values,
            hole=.45,
            textinfo='percent',
            textfont=dict(size=20),
            hoverinfo='text',
            hovertext=hovertext,
            marker=dict(colors=colors, line=dict(color='white', width=0))
        )])
        fig.update_layout(
            annotations=[dict(text='서비스<br>유형', x=0.5, y=0.5, font_size=24, showarrow=False)],
            showlegend=True,
            legend=dict(font=dict(size=18)),
            hoverlabel=dict(font_size=16),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col[2]:
        st.markdown('#### **|** 운행 차량')
        temp_request_df = operation_vehicle(current_time=current_time, day_interval=selected_days)
        reserve_counts = temp_request_df['VehicleType'].value_counts().sort_index()
        reserve_labels = reserve_counts.index.tolist()
        hovertext = [
            f"{rtype}<br>{count}건<br>{count / reserve_counts.sum():.1%}"
            for rtype, count in reserve_counts.items()
        ]
        colors = ['#20639B', '#3CAEA3', '#F6D55C']
        fig = go.Figure(data=[go.Pie(
            labels=reserve_labels,
            values=reserve_counts.values,
            hole=.45,
            textinfo='percent',
            textfont=dict(size=20),
            hoverinfo='text',
            hovertext=hovertext,
            marker=dict(colors=colors, line=dict(color='white', width=0))
        )])
        fig.update_layout(
            annotations=[dict(text='운행<br>차량', x=0.5, y=0.5, font_size=24, showarrow=False)],
            showlegend=True,
            legend=dict(font=dict(size=18)),
            hoverlabel=dict(font_size=16),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col[3]:
        st.markdown('#### **|** 배차 거절 사유')
        temp_request_df = return_failinfo(current_time=current_time, day_interval=selected_days)
        reserve_counts = temp_request_df['failInfo_Main'].value_counts().sort_index()
        reserve_labels = reserve_counts.index.tolist()
        hovertext = [
            f"{rtype}<br>{count}건<br>{count / reserve_counts.sum():.1%}"
            for rtype, count in reserve_counts.items()
        ]
        colors = ['#840032', '#002642', '#E59500', '#02040F', '#253D5B']
        fig = go.Figure(data=[go.Pie(
            labels=reserve_labels,
            values=reserve_counts.values,
            hole=.45,
            textinfo='percent',
            textfont=dict(size=20),
            hoverinfo='text',
            hovertext=hovertext,
            marker=dict(colors=colors, line=dict(color='white', width=0))
        )])
        fig.update_layout(
            annotations=[dict(text='배차거절<br>사유', x=0.5, y=0.5, font_size=24, showarrow=False)],
            showlegend=True,
            legend=dict(font=dict(size=18)),
            hoverlabel=dict(font_size=16),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    col = st.columns((2, 0.2, 1.2), gap='small')
    with col[0]:
        st.markdown('#### **|** 실차 탑승시간 비율 (%)')
        chart_daily, chart_hourly, stats = return_boaring_rates(current_time=current_time, days_interval=temp_interval)

        col_sub = st.columns((0.3, 1, 1), gap='small')
        with col_sub[0]:
            #st.metric(label="실차 운행률 (%)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.metric(
                label="실차 운행률 (%)",
                value=float(np.round(stats[0], 1)),
                delta=float(np.round(stats[0] - stats[1], 1)),
                label_visibility='hidden'
                )
            
            
            
            
            
            
            
            
            
            
            
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_daily, use_container_width=True)
        with col_sub[2]:
            st.altair_chart(chart_hourly, use_container_width=True)

        st.markdown('---')

        st.markdown('#### **|** 실차 운행률 (%)')
        chart_daily, chart_hourly, stats = return_boaring_vehicle_rates(current_time=current_time, days_interval=temp_interval)
        
        col_sub = st.columns((0.3, 1, 1), gap='small')
        with col_sub[0]:
            #st.metric(label="실차 운행률 (%)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.metric(
                label="실차 운행률 (%)",
                value=float(np.round(stats[0], 1)),
                delta=float(np.round(stats[0] - stats[1], 1)),
                label_visibility='hidden'
            )
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_daily, use_container_width=True)
        with col_sub[2]:
            st.altair_chart(chart_hourly, use_container_width=True)

    with col[2]:
        st.markdown('#### **|** 승객 탑승률 (%)')
        chart_daily, stats = return_service_capacity(current_time=current_time, days_interval=temp_interval)
        col_sub = st.columns((0.3, 1), gap='small')
        with col_sub[0]:
            #st.metric(label="승객 탑승률 (%)", value=np.round(stats[0], 1), delta=np.round((stats[0] - stats[1]), 1), label_visibility='hidden')
            st.metric(
                label="승객 탑승률 (%)",
                value=float(np.round(stats[0], 1)),
                delta=float(np.round(stats[0] - stats[1], 1)),
                label_visibility='hidden'
            )
            
            
            
            
            
            
            
            
            st.markdown(f'###### 지난 {temp_interval}일 평균')
        with col_sub[1]:
            st.altair_chart(chart_daily, use_container_width=True)

    st.markdown('---')

    sub_service_options = {
    "교통약자지역": [1],
    "교통소외지역": [2]
    }
    sub_service_labels = list(sub_service_options.keys())
    sub_service_default_index = sub_service_labels.index("교통약자지역")
    selected_sub_service = st.selectbox("", sub_service_labels, index=sub_service_default_index)

    col = st.columns((1, 1), gap='large')
    
    with col[0]:
        st.markdown('#### **|** 출발 정류장 이용 빈도')
        locations, last_log = return_pickup_station_count(current_time, days_interval=14)
        options = {
            "최근 1일": 1,
            "최근 3일": 3,
            "최근 7일": 7,
            "최근 14일": 14
        }
        option_labels = list(options.keys())
        default_index = option_labels.index("최근 3일")
        selected_label = st.selectbox(f"🕒 마지막 업데이트: {last_log}", option_labels, index=default_index)
        selected_days = options[selected_label]
        locations, last_log = return_pickup_station_count(current_time, days_interval=selected_days)

        # 2026.03.08 업데이트 - 백정엽 (지도 옆에 표 표출)
        use_frequency_df = pd.DataFrame(locations)
        use_frequency_df = use_frequency_df[['station', 'weight']]
        use_frequency_df = use_frequency_df.sort_values('weight', ascending=False).reset_index(drop=True)
        use_frequency_df = use_frequency_df.drop_duplicates('station').reset_index(drop=True)
        use_frequency_df = use_frequency_df.rename(columns={
            'station': '정류장 ID',
            'weight' : '출발 빈도수 (건)'
        })
        use_frequency_df.index = use_frequency_df.index + 1
        use_frequency_df['출발 빈도수 (건)'] = use_frequency_df['출발 빈도수 (건)'].round(0)

        top2_values = use_frequency_df["출발 빈도수 (건)"].nlargest(2).unique()
        max_rows = use_frequency_df[use_frequency_df["출발 빈도수 (건)"].isin(top2_values)]

        if len(max_rows) > 1:
            highlight_idx = max_rows.index
        else:
            highlight_idx = use_frequency_df.nlargest(3, "출발 빈도수 (건)").index

        def highlight_rows(row):
            if row.name in highlight_idx:
                return ["background-color: rgba(255, 215, 0, 0.3); font-weight: bold;"] * len(row)
            return [""] * len(row)
        
        styled_df = use_frequency_df.style.apply(highlight_rows, axis=1)


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
        st.markdown('#### **|** 운행 경로 빈도')
        temp_df, last_log = return_link_frequency(current_time, day_interval=14)
        options = {
            "최근 1일": 1,
            "최근 3일": 3,
            "최근 7일": 7,
            "최근 14일": 14
        }
        option_labels = list(options.keys())
        default_index = option_labels.index("최근 3일")
        selected_label = st.selectbox(f"🕒 마지막 업데이트: {last_log}", option_labels, index=default_index)
        selected_days = options[selected_label]
        link_df, last_log = return_link_frequency(current_time, day_interval=selected_days)

        # 2026.03.08 업데이트 - 백정엽 (지도 옆에 표 표출)
        link_frequency_df = pd.DataFrame(link_df)
        link_frequency_df = link_frequency_df[['linkID', 'count']]
        link_frequency_df = link_frequency_df.sort_values('count', ascending=False).reset_index(drop=True)
        link_frequency_df = link_frequency_df.drop_duplicates('linkID').reset_index(drop=True)
        link_frequency_df = link_frequency_df.rename(columns={
            'linkID': '경로 ID',
            'count' : '경로 이용 빈도수 (건)'
        })
        link_frequency_df.index = link_frequency_df.index + 1
        link_frequency_df['경로 이용 빈도수 (건)'] = link_frequency_df['경로 이용 빈도수 (건)'].round(0)

        top2_values = link_frequency_df["경로 이용 빈도수 (건)"].nlargest(2).unique()
        max_rows = link_frequency_df[link_frequency_df["경로 이용 빈도수 (건)"].isin(top2_values)]

        if len(max_rows) > 1:
            highlight_idx = max_rows.index
        else:
            highlight_idx = link_frequency_df.nlargest(3, "경로 이용 빈도수 (건)").index

        def highlight_rows(row):
            if row.name in highlight_idx:
                return ["background-color: rgba(255, 215, 0, 0.3); font-weight: bold;"] * len(row)
            return [""] * len(row)
        
        styled_df = link_frequency_df.style.apply(highlight_rows, axis=1)

        if selected_sub_service == "교통소외지역":
            col_subs = st.columns((2, 1), gap='small')
            with col_subs[0]:
                try:
                    map_html = links_map_html(PAGES_URL, kakao_api_key, link_df, center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
                except Exception:
                    map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("underserved_area", "")["lat"], st.secrets.get("underserved_area", "")["lng"]), level=st.secrets.get("underserved_area", "")["level"])
                components.html(map_html, height=700)
            with col_subs[1]:
                st.dataframe(styled_df, use_container_width=True, height=700)
        
        else:
            col_subs = st.columns((2, 1), gap='small')
            with col_subs[0]:
                try:
                    map_html = links_map_html(PAGES_URL, kakao_api_key, link_df, center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
                except Exception:
                    map_html = default_map_html(PAGES_URL, kakao_api_key, center=(st.secrets.get("vulnerable_area", "")["lat"], st.secrets.get("vulnerable_area", "")["lng"]), level=st.secrets.get("vulnerable_area", "")["level"])
                components.html(map_html, height=700)
            with col_subs[1]:
                st.dataframe(styled_df, use_container_width=True, height=700)
