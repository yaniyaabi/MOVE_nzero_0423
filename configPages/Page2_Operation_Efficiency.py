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


def apply_donut_layout(fig, center_text, legend_y=-0.15, height=360, bottom_margin=80, font_size=16, domain_y_start=0.25):
    fig.update_layout(
        annotations=[dict(text=center_text, x=0.5, y=0.58, font_size=24, showarrow=False)],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=legend_y,
            xanchor="center",
            x=0.5,
            font=dict(size=font_size)
        ),
        hoverlabel=dict(font_size=16),
        margin=dict(t=20, b=bottom_margin, l=20, r=20),
        height=height
    )
    fig.update_traces(domain=dict(x=[0.15, 0.85], y=[domain_y_start, 1.0]))


DATA_ERRORS = (
    IndexError,
    KeyError,
    TypeError,
    ValueError,
    AttributeError,
    ZeroDivisionError,
)


def safe_data_call(func, *args, **kwargs):
    """데이터가 없을 때 발생하는 일반적인 오류를 빈 결과로 변환합니다."""
    try:
        return func(*args, **kwargs)
    except DATA_ERRORS:
        return None


def to_dataframe(data):
    try:
        return pd.DataFrame(data)
    except DATA_ERRORS:
        return pd.DataFrame()


def has_required_data(dataframe, required_columns):
    return (
        dataframe is not None
        and not dataframe.empty
        and set(required_columns).issubset(dataframe.columns)
    )


def render_donut_or_no_data(
    data,
    value_column,
    colors,
    center_text,
    **layout_kwargs
):
    dataframe = to_dataframe(data)

    if not has_required_data(dataframe, [value_column]):
        st.info("No data")
        return

    counts = dataframe[value_column].dropna().value_counts().sort_index()
    total = counts.sum()

    if counts.empty or total <= 0:
        st.info("No data")
        return

    labels = counts.index.tolist()
    hovertext = [
        f"{label}<br>{count}건<br>{count / total:.1%}"
        for label, count in counts.items()
    ]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=counts.values,
        hole=.45,
        textinfo='percent',
        textfont=dict(size=20),
        hoverinfo='text',
        hovertext=hovertext,
        marker=dict(colors=colors, line=dict(color='white', width=0)),
        sort=False,
        direction='clockwise'
    )])
    apply_donut_layout(fig, center_text, **layout_kwargs)
    st.plotly_chart(fig, use_container_width=True)


def has_valid_stats(stats):
    try:
        values = np.asarray(stats[:2], dtype=float)
        return len(values) >= 2 and np.all(np.isfinite(values))
    except DATA_ERRORS:
        return False


def unpack_pair(result):
    if isinstance(result, (tuple, list)) and len(result) >= 2:
        return result[0], result[1]
    return [], None


def style_frequency_table(dataframe, value_column):
    top_values = dataframe[value_column].nlargest(2).unique()
    max_rows = dataframe[dataframe[value_column].isin(top_values)]

    if len(max_rows) > 1:
        highlight_idx = max_rows.index
    else:
        highlight_idx = dataframe.nlargest(3, value_column).index

    def highlight_rows(row):
        if row.name in highlight_idx:
            return [
                "background-color: rgba(255, 215, 0, 0.3); font-weight: bold;"
            ] * len(row)
        return [""] * len(row)

    return dataframe.style.apply(highlight_rows, axis=1)


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
        temp_dispatch_df = safe_data_call(
            return_reserveType,
            current_time=current_time,
            day_interval=selected_days
        )
        render_donut_or_no_data(
            temp_dispatch_df,
            value_column='reserveType',
            colors=['#4A90E2', '#F5A623'],
            center_text='예약<br>유형'
        )

    with col[1]:
        st.markdown('#### **|** 서비스 유형')
        temp_dispatch_df = safe_data_call(
            return_serviceType,
            current_time=current_time,
            day_interval=selected_days
        )
        render_donut_or_no_data(
            temp_dispatch_df,
            value_column='serviceType',
            colors=['#F6D55C', '#173F5F'],
            center_text='서비스<br>유형'
        )

    with col[2]:
        st.markdown('#### **|** 운행 차량')
        temp_request_df = safe_data_call(
            operation_vehicle,
            current_time=current_time,
            day_interval=selected_days
        )
        render_donut_or_no_data(
            temp_request_df,
            value_column='VehicleType',
            colors=['#20639B', '#3CAEA3', '#F6D55C'],
            center_text='운행<br>차량'
        )

    with col[3]:
        st.markdown('#### **|** 배차 거절 사유')
        temp_request_df = safe_data_call(
            return_failinfo,
            current_time=current_time,
            day_interval=selected_days
        )
        render_donut_or_no_data(
            temp_request_df,
            value_column='failInfo_Main',
            colors=['#840032', '#002642', '#E59500', '#02040F', '#253D5B'],
            center_text='배차거절<br>사유',
            legend_y=-0.22,
            height=390,
            bottom_margin=110,
            font_size=14,
            domain_y_start=0.30
        )

    st.markdown('---')

    col = st.columns((2, 0.2, 1.2), gap='small')
    with col[0]:
        st.markdown('#### **|** 실차 탑승시간 비율 (%)')
        boarding_result = safe_data_call(
            return_boaring_rates,
            current_time=current_time,
            days_interval=temp_interval
        )

        if (
            not isinstance(boarding_result, (tuple, list))
            or len(boarding_result) < 3
            or boarding_result[0] is None
            or boarding_result[1] is None
            or not has_valid_stats(boarding_result[2])
        ):
            st.info("No data")
        else:
            chart_daily, chart_hourly, stats = boarding_result
            col_sub = st.columns((0.3, 1, 1), gap='small')
            with col_sub[0]:
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
        vehicle_rate_result = safe_data_call(
            return_boaring_vehicle_rates,
            current_time=current_time,
            days_interval=temp_interval
        )

        if (
            not isinstance(vehicle_rate_result, (tuple, list))
            or len(vehicle_rate_result) < 3
            or vehicle_rate_result[0] is None
            or vehicle_rate_result[1] is None
            or not has_valid_stats(vehicle_rate_result[2])
        ):
            st.info("No data")
        else:
            chart_daily, chart_hourly, stats = vehicle_rate_result
            col_sub = st.columns((0.3, 1, 1), gap='small')
            with col_sub[0]:
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
        capacity_result = safe_data_call(
            return_service_capacity,
            current_time=current_time,
            days_interval=temp_interval
        )

        if (
            not isinstance(capacity_result, (tuple, list))
            or len(capacity_result) < 2
            or capacity_result[0] is None
            or not has_valid_stats(capacity_result[1])
        ):
            st.info("No data")
        else:
            chart_daily, stats = capacity_result
            col_sub = st.columns((0.3, 1), gap='small')
            with col_sub[0]:
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
        options = {
            "최근 1일": 1,
            "최근 3일": 3,
            "최근 7일": 7,
            "최근 14일": 14
        }

        initial_result = safe_data_call(
            return_pickup_station_count,
            current_time,
            days_interval=14
        )
        _, initial_last_log = unpack_pair(initial_result)
        last_log_text = initial_last_log if initial_last_log is not None else "No data"

        option_labels = list(options.keys())
        default_index = option_labels.index("최근 3일")
        selected_label = st.selectbox(
            f"🕒 마지막 업데이트: {last_log_text}",
            option_labels,
            index=default_index,
            key="pickup_station_frequency_days"
        )
        selected_days = options[selected_label]
        pickup_result = safe_data_call(
            return_pickup_station_count,
            current_time,
            days_interval=selected_days
        )
        locations, last_log = unpack_pair(pickup_result)
        use_frequency_df = to_dataframe(locations)

        if (
            last_log is None
            or not has_required_data(use_frequency_df, ['station', 'weight'])
        ):
            st.info("No data")
        else:
            use_frequency_df = (
                use_frequency_df[['station', 'weight']]
                .sort_values('weight', ascending=False)
                .drop_duplicates('station')
                .reset_index(drop=True)
                .rename(columns={
                    'station': '정류장 ID',
                    'weight': '출발 빈도수 (건)'
                })
            )
            use_frequency_df.index = use_frequency_df.index + 1
            use_frequency_df['출발 빈도수 (건)'] = (
                pd.to_numeric(
                    use_frequency_df['출발 빈도수 (건)'],
                    errors='coerce'
                ).round(0)
            )
            use_frequency_df = use_frequency_df.dropna(
                subset=['출발 빈도수 (건)']
            )

            if use_frequency_df.empty:
                st.info("No data")
            else:
                styled_df = style_frequency_table(
                    use_frequency_df,
                    '출발 빈도수 (건)'
                )

                area_key = (
                    "underserved_area"
                    if selected_sub_service == "교통소외지역"
                    else "vulnerable_area"
                )
                area_config = st.secrets.get(area_key, "")

                col_subs = st.columns((2, 1), gap='small')
                with col_subs[0]:
                    try:
                        map_html = markers_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            normalize_weights(locations),
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"]
                        )
                    except Exception:
                        map_html = default_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"]
                        )
                    components.html(map_html, height=700)
                with col_subs[1]:
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=700
                    )

    with col[1]:
        st.markdown('#### **|** 운행 경로 빈도')
        options = {
            "최근 1일": 1,
            "최근 3일": 3,
            "최근 7일": 7,
            "최근 14일": 14
        }

        initial_result = safe_data_call(
            return_link_frequency,
            current_time,
            day_interval=14
        )
        _, initial_last_log = unpack_pair(initial_result)
        last_log_text = initial_last_log if initial_last_log is not None else "No data"

        option_labels = list(options.keys())
        default_index = option_labels.index("최근 3일")
        selected_label = st.selectbox(
            f"🕒 마지막 업데이트: {last_log_text}",
            option_labels,
            index=default_index,
            key="link_frequency_days"
        )
        selected_days = options[selected_label]
        link_result = safe_data_call(
            return_link_frequency,
            current_time,
            day_interval=selected_days
        )
        link_df, last_log = unpack_pair(link_result)
        link_frequency_df = to_dataframe(link_df)

        if (
            last_log is None
            or not has_required_data(link_frequency_df, ['linkID', 'count'])
        ):
            st.info("No data")
        else:
            link_frequency_df = (
                link_frequency_df[['linkID', 'count']]
                .sort_values('count', ascending=False)
                .drop_duplicates('linkID')
                .reset_index(drop=True)
                .rename(columns={
                    'linkID': '경로 ID',
                    'count': '경로 이용 빈도수 (건)'
                })
            )
            link_frequency_df.index = link_frequency_df.index + 1
            link_frequency_df['경로 이용 빈도수 (건)'] = (
                pd.to_numeric(
                    link_frequency_df['경로 이용 빈도수 (건)'],
                    errors='coerce'
                ).round(0)
            )
            link_frequency_df = link_frequency_df.dropna(
                subset=['경로 이용 빈도수 (건)']
            )

            if link_frequency_df.empty:
                st.info("No data")
            else:
                styled_df = style_frequency_table(
                    link_frequency_df,
                    '경로 이용 빈도수 (건)'
                )

                area_key = (
                    "underserved_area"
                    if selected_sub_service == "교통소외지역"
                    else "vulnerable_area"
                )
                area_config = st.secrets.get(area_key, "")

                col_subs = st.columns((2, 1), gap='small')
                with col_subs[0]:
                    try:
                        map_html = links_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            link_df,
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"]
                        )
                    except Exception:
                        map_html = default_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"]
                        )
                    components.html(map_html, height=700)
                with col_subs[1]:
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=700
                    )
