import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import numpy as np
import pandas as pd
from Modules.P3_Kakao_population_loader import (
    return_last_population_df,
    return_last_past_population_df,
)
from utils.maps import polygons_map_html, default_map_html


DATA_ERRORS = (
    IndexError,
    KeyError,
    TypeError,
    ValueError,
    AttributeError,
    ZeroDivisionError,
    OverflowError,
    UnboundLocalError,
    StopIteration,
)


def safe_data_call(func, *args, **kwargs):
    """빈 데이터 처리 과정에서 발생하는 일반적인 오류를 빈 결과로 변환합니다."""
    try:
        return func(*args, **kwargs)
    except DATA_ERRORS:
        return None


def is_valid_number(value):
    try:
        return np.isfinite(float(value))
    except DATA_ERRORS:
        return False


def to_dataframe(data):
    try:
        return pd.DataFrame(data).copy()
    except DATA_ERRORS:
        return pd.DataFrame()


def has_required_data(data, required_columns):
    if data is None:
        return False

    try:
        return (
            not data.empty
            and set(required_columns).issubset(data.columns)
        )
    except DATA_ERRORS:
        return False


def result_values_are_valid(result_list, indexes):
    try:
        values = [result_list[index] for index in indexes]
        return all(is_valid_number(value) for value in values)
    except DATA_ERRORS:
        return False


def render_static_rate(
    title,
    metric_label,
    numerator,
    denominator,
    delta,
    comparison_text,
    numerator_description,
    denominator_description,
    unit,
):
    st.markdown(f"#### **|** {title}")

    if (
        not is_valid_number(numerator)
        or not is_valid_number(denominator)
        or float(denominator) <= 0
    ):
        st.info("No data")
        return

    numerator_value = float(numerator)
    denominator_value = float(denominator)
    percentage = int(numerator_value / denominator_value * 100)

    col_sub = st.columns((0.3, 1), gap="small")
    with col_sub[0]:
        st.metric(
            label=metric_label,
            value=percentage,
            delta=delta,
            label_visibility="hidden",
        )
        st.markdown(f"###### {comparison_text}")
    with col_sub[1]:
        st.markdown(
            "<div style='height:28px;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style='font-size: 16px; color: gray;'>
                {denominator_description}: {denominator_value:,.0f} {unit}<br>
                {numerator_description}: {numerator_value:,.0f} {unit}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_population_rate(
    title,
    metric_label,
    last_df,
    past_df,
    result_list,
    current_result_index,
    past_result_index,
    value_column,
    y_axis_title,
    area_color,
    temp_interval,
):
    st.markdown(f"#### **|** {title}")

    last_frame = to_dataframe(last_df)
    past_frame = to_dataframe(past_df)
    required_columns = {"day", value_column}

    if (
        not has_required_data(last_frame, required_columns)
        or not has_required_data(past_frame, required_columns)
        or not result_values_are_valid(
            result_list,
            [current_result_index, past_result_index],
        )
    ):
        st.info("No data")
        return

    temp_last_df = last_frame[["day", value_column]].copy()
    temp_past_df = past_frame[["day", value_column]].copy()

    for dataframe in (temp_last_df, temp_past_df):
        dataframe["day"] = pd.to_numeric(
            dataframe["day"],
            errors="coerce",
        )
        dataframe[value_column] = pd.to_numeric(
            dataframe[value_column],
            errors="coerce",
        )
        dataframe.dropna(
            subset=["day", value_column],
            inplace=True,
        )

    if temp_last_df.empty or temp_past_df.empty:
        st.info("No data")
        return

    merged_df = (
        pd.concat(
            [temp_past_df, temp_last_df],
            ignore_index=True,
        )
        .sort_values("day")
        .reset_index(drop=True)
    )

    if merged_df.empty or merged_df[value_column].dropna().empty:
        st.info("No data")
        return

    window_size = max(
        1,
        int(np.round(len(temp_last_df) / 2, 0)),
    )
    merged_df["이동평균"] = (
        merged_df[value_column]
        .iloc[::-1]
        .rolling(window=window_size, min_periods=1)
        .mean()
        .iloc[::-1]
    )
    moving_avg_df = merged_df[
        merged_df["day"].isin(temp_last_df["day"])
    ].copy()

    if moving_avg_df.empty or moving_avg_df["이동평균"].dropna().empty:
        st.info("No data")
        return

    current_value = float(result_list[current_result_index])
    past_value = float(result_list[past_result_index])

    col_sub = st.columns((0.3, 1), gap="small")
    with col_sub[0]:
        st.metric(
            label=metric_label,
            value=int(current_value),
            delta=int(current_value - past_value),
            label_visibility="hidden",
        )
        st.markdown(f"###### 지난 {temp_interval}일 평균")
    with col_sub[1]:
        area = (
            alt.Chart(temp_last_df)
            .mark_area(opacity=0.7, color=area_color)
            .encode(
                x=alt.X(
                    "day:Q",
                    title="Day",
                    scale=alt.Scale(nice=True),
                    axis=alt.Axis(format=".0f"),
                ),
                y=alt.Y(
                    f"{value_column}:Q",
                    title=y_axis_title,
                ),
            )
        )
        line = (
            alt.Chart(moving_avg_df)
            .mark_line(
                color="#ED553B",
                strokeWidth=3,
                strokeDash=[4, 2],
                point=alt.OverlayMarkDef(
                    filled=True,
                    fill="#ED553B",
                    stroke="#ED553B",
                    strokeWidth=0.5,
                    size=50,
                ),
            )
            .encode(
                x=alt.X(
                    "day:Q",
                    title="Day",
                    scale=alt.Scale(nice=True),
                    axis=alt.Axis(format=".0f"),
                ),
                y=alt.Y("이동평균:Q"),
            )
        )
        chart = (area + line).properties(height=200)
        st.altair_chart(chart, use_container_width=True)


def render_population_map(
    population_df,
    value_column,
    PAGES_URL,
    kakao_api_key,
):
    required_columns = {value_column, "geometry"}

    if not has_required_data(population_df, required_columns):
        st.info("No data")
        return

    try:
        valid_values = pd.to_numeric(
            population_df[value_column],
            errors="coerce",
        ).dropna()
        valid_geometry = population_df["geometry"].dropna()
    except DATA_ERRORS:
        st.info("No data")
        return

    if valid_values.empty or valid_geometry.empty:
        st.info("No data")
        return

    try:
        map_html = polygons_map_html(
            PAGES_URL,
            kakao_api_key,
            population_df,
            value_column,
        )
    except Exception:
        map_html = default_map_html(PAGES_URL, kakao_api_key)

    components.html(map_html, height=750)


def render(current_time, temp_interval, PAGES_URL, kakao_api_key):
    st.header("♿ MOVE / 서비스 접근성")
    st.markdown("##### MOVE (Mobility On-demand for Vulnerable & Elderly)")
    st.markdown("---")

    service_population = st.secrets.get("service_population")
    odd_population = st.secrets.get("ODD_population")
    service_area = st.secrets.get("service_area")
    odd_area = st.secrets.get("ODD_area")

    col = st.columns((1, 1, 1), gap="large")
    with col[0]:
        render_static_rate(
            title="서비스 수혜율 (%)",
            metric_label="서비스 수혜율",
            numerator=odd_population,
            denominator=service_population,
            delta=3.6,
            comparison_text="지난 1년 대비",
            numerator_description="ODD 범위권 인구수",
            denominator_description="서비스 지역 인구수",
            unit="명",
        )

    with col[1]:
        render_static_rate(
            title="서비스 커버리지 (%)",
            metric_label="서비스 커버리지",
            numerator=odd_area,
            denominator=service_area,
            delta=2.1,
            comparison_text="지난 1년 대비",
            numerator_description="ODD 범위권 면적",
            denominator_description="서비스 지역 면적",
            unit="m²",
        )

    st.markdown("---")

    total_people_count = st.secrets.get("total_people_count")
    total_disabled_count = st.secrets.get("total_diabled_count")
    total_older_adults_count = st.secrets.get("total_olderadults_count")

    if all(
        is_valid_number(value)
        for value in (
            total_people_count,
            total_disabled_count,
            total_older_adults_count,
        )
    ):
        history_result = safe_data_call(
            return_last_past_population_df,
            current_time,
            temp_interval,
            total_people_count,
            total_disabled_count,
            total_older_adults_count,
        )
    else:
        history_result = None

    if isinstance(history_result, (tuple, list)) and len(history_result) >= 3:
        last_df, past_df, result_list = history_result[:3]
    else:
        last_df = pd.DataFrame()
        past_df = pd.DataFrame()
        result_list = []

    col = st.columns((1, 1, 1), gap="large")
    with col[0]:
        render_population_rate(
            title="서비스 이용률 (%)",
            metric_label="서비스 이용률(%)",
            last_df=last_df,
            past_df=past_df,
            result_list=result_list,
            current_result_index=0,
            past_result_index=1,
            value_column="total_count",
            y_axis_title="서비스 이용률 (%)",
            area_color="#173F5F",
            temp_interval=temp_interval,
        )

    with col[1]:
        render_population_rate(
            title="장애인 이용률 (%)",
            metric_label="장애인 이용률(%)",
            last_df=last_df,
            past_df=past_df,
            result_list=result_list,
            current_result_index=2,
            past_result_index=3,
            value_column="disabled_count",
            y_axis_title="장애인 이용률 (%)",
            area_color="#3CAEA3",
            temp_interval=temp_interval,
        )

    with col[2]:
        render_population_rate(
            title="고령자 이용률 (%)",
            metric_label="고령자 이용률(%)",
            last_df=last_df,
            past_df=past_df,
            result_list=result_list,
            current_result_index=4,
            past_result_index=5,
            value_column="older_adults_count",
            y_axis_title="고령자 이용률 (%)",
            area_color="#F6D55C",
            temp_interval=temp_interval,
        )

    st.markdown("---")

    options = {
        "최근 1일": 1,
        "최근 3일": 3,
        "최근 7일": 7,
        "최근 14일": 14,
    }
    option_labels = list(options.keys())
    default_index = option_labels.index("최근 14일")
    selected_label = st.selectbox(
        f"🕒 현재 시간: {current_time} ",
        option_labels,
        index=default_index,
        key="service_accessibility_population_days",
    )
    selected_days = options[selected_label]

    population_df = safe_data_call(
        return_last_population_df,
        current_time=current_time,
        days_interval=selected_days,
    )

    col = st.columns((1, 1, 1), gap="large")
    with col[0]:
        st.markdown("#### **|** 서비스 이용률 지도")
        render_population_map(
            population_df,
            "total_percent",
            PAGES_URL,
            kakao_api_key,
        )

    with col[1]:
        st.markdown("#### **|** 장애인 이용률 지도")
        render_population_map(
            population_df,
            "disabled_percent",
            PAGES_URL,
            kakao_api_key,
        )

    with col[2]:
        st.markdown("#### **|** 고령자 이용률 지도")
        render_population_map(
            population_df,
            "olderadults_percent",
            PAGES_URL,
            kakao_api_key,
        )
