import streamlit as st
import numpy as np
import pandas as pd
import streamlit.components.v1 as components
from Modules.P1_Kakao_service_waiting import return_waitings
from Modules.P1_Dispatch_success_ratio import return_dispatch_ratio
from Modules.P1_sevice_arrival_operation_times import return_graphs_and_stats
from Modules.N2_Kakao_realtime_loader import return_realtime_operations
from utils.maps import (
    normalize_weights,
    markers_map_html,
    default_map_html,
    routes_map_html,
)


DATA_ERRORS = (
    IndexError,
    KeyError,
    TypeError,
    ValueError,
    AttributeError,
    ZeroDivisionError,
)


def safe_data_call(func, *args, **kwargs):
    """빈 데이터 처리 과정에서 발생하는 일반적인 오류를 빈 결과로 변환합니다."""
    try:
        return func(*args, **kwargs)
    except DATA_ERRORS:
        return None


def safe_length(value):
    if value is None:
        return 0

    try:
        return len(value)
    except DATA_ERRORS:
        return 0


def chart_has_data(chart):
    if chart is None:
        return False

    try:
        data = getattr(chart, "data", None)

        if isinstance(data, (pd.DataFrame, pd.Series)):
            return not data.empty

        if isinstance(data, (list, tuple, dict)):
            return len(data) > 0

        specification = chart.to_dict()
        datasets = specification.get("datasets")

        if datasets is not None:
            return any(bool(rows) for rows in datasets.values())
    except DATA_ERRORS:
        return False
    except Exception:
        # 차트 객체가 데이터 내용을 직접 노출하지 않는 경우에는
        # 객체가 존재한다는 사실을 기준으로 렌더링을 시도합니다.
        return True

    return True


def stats_are_valid(stats, indexes):
    try:
        values = np.asarray([stats[index] for index in indexes], dtype=float)
        return np.all(np.isfinite(values))
    except DATA_ERRORS:
        return False


def render_metric_chart(
    chart,
    stats,
    current_index,
    comparison_index,
    label,
    temp_interval,
    decimals=1,
    divisor=1,
):
    if (
        not chart_has_data(chart)
        or not stats_are_valid(stats, [current_index, comparison_index])
    ):
        st.info("No data")
        return

    current_value = float(stats[current_index]) / divisor
    comparison_value = float(stats[comparison_index]) / divisor

    col_sub = st.columns((0.3, 1), gap="small")
    with col_sub[0]:
        st.metric(
            label=label,
            value=float(np.round(current_value, decimals)),
            delta=float(np.round(current_value - comparison_value, decimals)),
            label_visibility="hidden",
        )
        st.markdown(f"###### 지난 {temp_interval}일 평균")
    with col_sub[1]:
        st.altair_chart(chart, use_container_width=True)


def style_frequency_table(dataframe, value_column):
    top_values = dataframe[value_column].nlargest(2).unique()
    max_rows = dataframe[dataframe[value_column].isin(top_values)]

    if len(max_rows) > 1:
        highlight_indexes = max_rows.index
    else:
        highlight_indexes = dataframe.nlargest(3, value_column).index

    def highlight_rows(row):
        if row.name in highlight_indexes:
            return [
                "background-color: rgba(255, 215, 0, 0.3); font-weight: bold;"
            ] * len(row)
        return [""] * len(row)

    return dataframe.style.apply(highlight_rows, axis=1).format(
        {"(평균)대기시간 (분)": "{:.1f}"}
    )


def render(current_time, temp_interval, PAGES_URL, kakao_api_key):
    st.header("♿ MOVE / 이용자 경험")
    st.markdown("##### MOVE (Mobility On-demand for Vulnerable & Elderly)")
    st.markdown("---")
    st.markdown("#### **|** 대상 지역")

    service_options = {
        "통합 (교통약자지역 + 교통소외지역)": [1, 2],
        "교통약자지역": [1],
        "교통소외지역": [2],
    }

    service_option_labels = list(service_options.keys())
    service_default_index = service_option_labels.index(
        "통합 (교통약자지역 + 교통소외지역)"
    )
    selected_service_label = st.selectbox(
        f"🕒 현재 시간: {current_time}",
        service_option_labels,
        index=service_default_index,
        key="user_experience_service_area",
    )
    selected_service_values = service_options[selected_service_label]

    st.markdown("---")

    waiting_result = safe_data_call(
        return_waitings,
        current_time=current_time,
        days_interval=temp_interval,
        reserveType=None,
        sevice_Type=selected_service_values,
    )

    if isinstance(waiting_result, (tuple, list)) and len(waiting_result) >= 5:
        chart_response = waiting_result[0]
        chart_waiting = waiting_result[1]
        waiting_stats = waiting_result[3]
    else:
        chart_response = None
        chart_waiting = None
        waiting_stats = None

    dispatch_result = safe_data_call(
        return_dispatch_ratio,
        current_time=current_time,
        days_interval=temp_interval,
        sevice_Type=selected_service_values,
    )

    if isinstance(dispatch_result, (tuple, list)) and len(dispatch_result) >= 2:
        chart_success, dispatch_stats = dispatch_result[:2]
    else:
        chart_success = None
        dispatch_stats = None

    col = st.columns((1, 1, 1), gap="large")
    with col[0]:
        st.markdown("#### **|** 배차 소요시간 (초)")
        render_metric_chart(
            chart_response,
            waiting_stats,
            current_index=0,
            comparison_index=1,
            label="배차 소요시간 (초)",
            temp_interval=temp_interval,
            decimals=1,
        )

    with col[1]:
        st.markdown("#### **|** 서비스 대기시간 (분)")
        render_metric_chart(
            chart_waiting,
            waiting_stats,
            current_index=2,
            comparison_index=3,
            label="서비스 대기시간 (분)",
            temp_interval=temp_interval,
            decimals=2,
            divisor=60,
        )

    with col[2]:
        st.markdown("#### **|** 배차 성공률 (%)")
        render_metric_chart(
            chart_success,
            dispatch_stats,
            current_index=0,
            comparison_index=1,
            label="배차 성공률 (%)",
            temp_interval=temp_interval,
            decimals=1,
        )

    st.markdown("---")

    operation_result = safe_data_call(
        return_graphs_and_stats,
        current_time=current_time,
        days_interval=temp_interval,
        sevice_Type=selected_service_values,
    )

    if isinstance(operation_result, (tuple, list)) and len(operation_result) >= 4:
        chart_actual_use_time = operation_result[0]
        chart_pickup_delay = operation_result[1]
        chart_actual_operation_delay = operation_result[2]
        operation_stats = operation_result[3]
    else:
        chart_actual_use_time = None
        chart_pickup_delay = None
        chart_actual_operation_delay = None
        operation_stats = None

    col = st.columns((1, 1, 1), gap="large")
    with col[0]:
        st.markdown("#### **|** 서비스 이용시간 (분)")
        render_metric_chart(
            chart_actual_use_time,
            operation_stats,
            current_index=0,
            comparison_index=1,
            label="서비스 이용시간 (분)",
            temp_interval=temp_interval,
            decimals=1,
        )

    with col[1]:
        st.markdown("#### **|** 차량 도착 정시성 (분)")
        render_metric_chart(
            chart_pickup_delay,
            operation_stats,
            current_index=2,
            comparison_index=3,
            label="차량 도착 정시성 (분)",
            temp_interval=temp_interval,
            decimals=1,
        )

    with col[2]:
        st.markdown("#### **|** 차량 주행 정시성 (분)")
        render_metric_chart(
            chart_actual_operation_delay,
            operation_stats,
            current_index=4,
            comparison_index=5,
            label="차량 주행 정시성 (분)",
            temp_interval=temp_interval,
            decimals=1,
        )

    st.markdown("---")

    sub_service_options = {
        "교통약자지역": [1],
        "교통소외지역": [2],
    }
    sub_service_labels = list(sub_service_options.keys())
    sub_service_default_index = sub_service_labels.index(
        "교통약자지역"
        if selected_service_label != "교통소외지역"
        else "교통소외지역"
    )
    selected_sub_service = st.selectbox(
        "",
        sub_service_labels,
        index=sub_service_default_index,
        key="user_experience_map_area",
    )

    area_key = (
        "underserved_area"
        if selected_sub_service == "교통소외지역"
        else "vulnerable_area"
    )
    area_config = st.secrets.get(area_key, "")

    col = st.columns((1.3, 1), gap="large")

    with col[0]:
        st.markdown("#### **|** 서비스 대기 시간 지도")

        reservation_options = {
            "사전 예약": 1,
            "실시간 예약": 2,
        }
        reservation_labels = list(reservation_options.keys())
        reservation_default_index = reservation_labels.index("사전 예약")
        selected_reservation_label = st.selectbox(
            f"🕒 현재 시간: {current_time}",
            reservation_labels,
            index=reservation_default_index,
            key="user_experience_reservation_type",
        )

        map_waiting_result = safe_data_call(
            return_waitings,
            current_time=current_time,
            days_interval=temp_interval,
            reserveType=selected_reservation_label,
            sevice_Type=selected_service_values,
        )

        if (
            isinstance(map_waiting_result, (tuple, list))
            and len(map_waiting_result) >= 5
        ):
            locations = map_waiting_result[4]
        else:
            locations = []

        waiting_df = pd.DataFrame(locations)
        required_columns = {"station", "weight"}

        if (
            waiting_df.empty
            or not required_columns.issubset(waiting_df.columns)
        ):
            st.info("No data")
        else:
            waiting_df = waiting_df[["station", "weight"]].copy()
            waiting_df["weight"] = pd.to_numeric(
                waiting_df["weight"],
                errors="coerce",
            )
            waiting_df = waiting_df.dropna(subset=["station", "weight"])

            if waiting_df.empty:
                st.info("No data")
            else:
                waiting_df = (
                    waiting_df.groupby("station")
                    .agg(
                        예약건수=("station", "count"),
                        평균대기시간=("weight", "mean"),
                    )
                    .reset_index()
                    .rename(
                        columns={
                            "station": "정류장 ID",
                            "평균대기시간": "(평균)대기시간 (분)",
                        }
                    )
                    .sort_values(
                        "(평균)대기시간 (분)",
                        ascending=False,
                    )
                    .reset_index(drop=True)
                )
                waiting_df.index = waiting_df.index + 1
                styled_df = style_frequency_table(
                    waiting_df,
                    "(평균)대기시간 (분)",
                )

                col_subs = st.columns((2, 1), gap="small")
                with col_subs[0]:
                    try:
                        map_html = markers_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            normalize_weights(locations),
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"],
                        )
                    except Exception:
                        map_html = default_map_html(
                            PAGES_URL,
                            kakao_api_key,
                            center=(area_config["lat"], area_config["lng"]),
                            level=area_config["level"],
                        )
                    components.html(map_html, height=700)
                with col_subs[1]:
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=700,
                    )

    with col[1]:
        st.markdown("#### **|** 실시간 운행 정보 - 30분 전후 포함")

        realtime_result = safe_data_call(
            return_realtime_operations,
            current_time,
            minutes_interval=30,
        )

        if isinstance(realtime_result, (tuple, list)) and len(realtime_result) >= 4:
            (
                temp_oper_info,
                temp_routes,
                temp_pickup_info,
                temp_dropoff_info,
            ) = realtime_result[:4]
        else:
            temp_oper_info = []
            temp_routes = []
            temp_pickup_info = []
            temp_dropoff_info = []

        operation_count = min(
            safe_length(temp_oper_info),
            safe_length(temp_routes),
            safe_length(temp_pickup_info),
        )

        if operation_count == 0:
            st.info("No data")
        else:
            def format_operation(index):
                try:
                    info = temp_oper_info[index]
                    return (
                        f"운행 #{index + 1} | 차량 : {info[0]}"
                        f" - 운행시간 : 총 {int(info[1])}분"
                        f" - 총 요청수 : {info[2]}개"
                        f" - 총 승객수 : {info[3]}"
                        f" - 총 휠체어수 : {info[4]}"
                    )
                except DATA_ERRORS:
                    return f"운행 #{index + 1}"

            selected_index = st.selectbox(
                f"🕒 현재 시간: {current_time}",
                range(operation_count),
                format_func=format_operation,
                key="user_experience_realtime_operation",
            )

            selected_routes = [temp_routes[selected_index]]
            selected_pickup_info = temp_pickup_info[selected_index]

            try:
                map_html = routes_map_html(
                    PAGES_URL,
                    kakao_api_key,
                    selected_routes,
                    selected_pickup_info,
                    center=(area_config["lat"], area_config["lng"]),
                    level=area_config["level"],
                )
            except Exception:
                map_html = default_map_html(
                    PAGES_URL,
                    kakao_api_key,
                    center=(area_config["lat"], area_config["lng"]),
                    level=area_config["level"],
                )
            components.html(map_html, height=700)
