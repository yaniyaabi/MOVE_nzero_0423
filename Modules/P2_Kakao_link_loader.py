import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import datetime as dt
import itertools
import json
import pymysql
import geopandas as gpd
import ast
from collections import Counter
import yaml
import os
from pathlib import Path
import streamlit as st

HERE = Path(__file__).resolve().parent        # .../MOVE/Modules
ROOT = HERE.parent                            # .../MOVE
sejong_gdf = gpd.read_file(ROOT / st.secrets.get("sejong_Station", ""))
daejeon_gdf = gpd.read_file(ROOT / st.secrets.get("daejeon_Station", ""))

gdf = pd.concat([sejong_gdf, daejeon_gdf]).reset_index(drop=True)
gdf['pickupStationID'] = gdf['StationID']

def parse_onboarding_time(t):
    try:
        t_str = str(int(t)).zfill(12)
        return datetime.strptime(t_str, "%Y%m%d%H%M")
    except:
        return np.nan

current_mode = st.secrets.get("mode", "static")

if current_mode == "dynamic":
    current_db_config = st.secrets.get("database")

    # import reservation request table
    con = pymysql.connect(
        user=current_db_config['user'],
        passwd=current_db_config['passwd'],
        host=current_db_config['host'],
        port=current_db_config['port'],
        db=current_db_config['db'],
        charset=current_db_config['charset'],
        use_unicode=current_db_config['use_unicode']
    )
    mycursor = con.cursor()
    query = """
        select * from reservation_request;
    """
    mycursor.execute(query)
    data = mycursor.fetchall()
    con.close()
    request_df = pd.DataFrame(data, columns=["requestID", "passengerID", "messageTime", "pickupStationID", "dropoffStationID", "serviceType", "reserveType", "dispatchID", "responseStatus", "confirmCheck", "passengerCount", "wheelchairCount", "failInfoList", "pickupTimeRequest"])

    # import dispatch table
    con = pymysql.connect(
        user=current_db_config['user'],
        passwd=current_db_config['passwd'],
        host=current_db_config['host'],
        port=current_db_config['port'],
        db=current_db_config['db'],
        charset=current_db_config['charset'],
        use_unicode=current_db_config['use_unicode']
    )
    mycursor = con.cursor()
    query = """
        select * from dispatch;
    """
    mycursor.execute(query)
    data = mycursor.fetchall()
    con.close()
    dispatch_df = pd.DataFrame(data, columns=["dispatchID", "messageTime", "passengerID", "requestID", "routeIDs", "pickupStationName", "dropoffStationName", "reserveType", "onboardingTime", "dropoffTime", "linkIDs", "pickupStationID", "dropoffStationID", "tripID", "operationID", "vehicleID"])

    # import operation table
    con = pymysql.connect(
        user=current_db_config['user'],
        passwd=current_db_config['passwd'],
        host=current_db_config['host'],
        port=current_db_config['port'],
        db=current_db_config['db'],
        charset=current_db_config['charset'],
        use_unicode=current_db_config['use_unicode']
    )
    mycursor = con.cursor()
    query = """
        select * from operation;
    """
    mycursor.execute(query)
    data = mycursor.fetchall()
    con.close()
    operation_df = pd.DataFrame(data, columns=["operationID", "vehicleID", "StationIDs", "routeIDs", "startTime", "endTime", "VehicleType", "operationServiceType"])

    # import route table
    con = pymysql.connect(
        user=current_db_config['user'],
        passwd=current_db_config['passwd'],
        host=current_db_config['host'],
        port=current_db_config['port'],
        db=current_db_config['db'],
        charset=current_db_config['charset'],
        use_unicode=current_db_config['use_unicode']
    )
    mycursor = con.cursor()
    query = """
        select * from route;
    """
    mycursor.execute(query)
    data = mycursor.fetchall()
    con.close()
    route_df = pd.DataFrame(data, columns=["routeID", "routeSeq", "operationID", "vehicleID", "routeInfo", "linkIDs", "updatedLinkIDs", "NodeIDs", "updatedNodeIDs", "originStationID", "originDeptTime", "destStationID", "destArrivalTime", "onboardingNum", "dispatchIDs", "lon", "updatedLon", "lat", "updatedLat", "originBoardingPxIDs", "originGetoffPxIDs", "destBoardingPxIDs", "destGetoffPxIDs", "routeCode", "StationIDs"])

else:
    dispatch_df = pd.read_csv(ROOT/"data"/"dispatch_df.csv")
    operation_df = pd.read_csv(ROOT/"data"/"operation_df.csv")
    route_df = pd.read_csv(ROOT/"data"/"route_df.csv")
    request_df = pd.read_csv(ROOT/"data"/"request_df.csv")

dispatch_df['onboarding_datetime'] = dispatch_df['onboardingTime'].apply(parse_onboarding_time)
dispatch_df['dropoff_datetime'] = dispatch_df['dropoffTime'].apply(parse_onboarding_time)

operation_df['startTime_datetime'] = operation_df['startTime'].apply(parse_onboarding_time)
operation_df['endTime_datetime'] = operation_df['endTime'].apply(parse_onboarding_time)

route_df['originDeptTime_datetime'] = route_df['originDeptTime'].apply(parse_onboarding_time)
route_df['destArrivalTime_datetime'] = route_df['destArrivalTime'].apply(parse_onboarding_time)


# def return_link_frequency(current_time, day_interval):

#     temp_route_df = route_df[(route_df['destArrivalTime_datetime'] <= current_time) & (route_df['originDeptTime_datetime'] >= current_time - dt.timedelta(days=day_interval))].reset_index(drop=True)

#     link_list = []

#     for idx, row in temp_route_df.iterrows():
#         lons = ast.literal_eval(row['lon'])
#         lats = ast.literal_eval(row['lat'])

#         for i in range(len(lons) - 1):
#             link = ((lons[i], lats[i]), (lons[i+1], lats[i+1]))
#             link_list.append(link)

#     link_counter = Counter(link_list)

#     link_df = pd.DataFrame([
#         {'start_lon': s[0], 'start_lat': s[1],
#         'end_lon': e[0], 'end_lat': e[1],
#         'count': count}
#         for ((s, e), count) in link_counter.items()
#     ])

#     return link_df, pd.to_datetime(temp_route_df.sort_values('destArrivalTime_datetime')['destArrivalTime_datetime'].values[-1]).to_pydatetime()

def return_link_frequency(current_time, day_interval):

    temp_route_df = route_df[
        (route_df['destArrivalTime_datetime'] <= current_time) &
        (route_df['originDeptTime_datetime'] >= current_time - dt.timedelta(days=day_interval))
    ].reset_index(drop=True)

    link_list = []

    for idx, row in temp_route_df.iterrows():
        lons = ast.literal_eval(row['lon'])
        lats = ast.literal_eval(row['lat'])
        link_ids = ast.literal_eval(row['linkIDs'])

        # lon/lat로 만들어지는 링크 개수와 link_id 개수가 맞는지 확인
        n_links = min(len(lons) - 1, len(link_ids))

        for i in range(n_links):
            link = (
                (lons[i], lats[i]),
                (lons[i + 1], lats[i + 1]),
                link_ids[i]
            )
            link_list.append(link)

    link_counter = Counter(link_list)

    link_df = pd.DataFrame([
        {
            'start_lon': s[0],
            'start_lat': s[1],
            'end_lon': e[0],
            'end_lat': e[1],
            'linkID': link_id,
            'count': count
        }
        for ((s, e, link_id), count) in link_counter.items()
    ])

    return link_df, pd.to_datetime(temp_route_df.sort_values('destArrivalTime_datetime')['destArrivalTime_datetime'].values[-1]).to_pydatetime()
