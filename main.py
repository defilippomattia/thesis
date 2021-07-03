import pymongo
import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import altair as alt
import geopy.distance
#import requests
#import credentials
st.set_page_config(layout="wide")
#myclient = pymongo.MongoClient("mongodb://localhost:27017/")
#mydb = myclient["zavrsni_db"]

atlas_conn_str="#"
atlas_client = pymongo.MongoClient(atlas_conn_str)
atlas_db = atlas_client["zavrsni"]
stats_collection = atlas_db["stats"]
myclient = pymongo.MongoClient(
    host = "#",
    username = "#",
    password = "#"
)

mydb = myclient["automotive_data"]

drivers_collection = mydb["drivers"]
obd_data_collection = mydb["obd_data"]
trips_collection = mydb["trips"]

df = pd.DataFrame()



def select_driver():
    drivers = []
    drivers_id = []
    for driver in drivers_collection.find():
        drivers.append(driver)
    #options = drivers["androidId"]
    #values = drivers["vechile"]

    options = []
    values = []
    for driver in drivers:
        #print(driver)
        options.append(driver["androidId"])
        val = str(driver["age"])+ " - "+str(driver["gender"][0].upper() + " - " + str(driver["vehicle"]))
        values.append(val)

    dic = dict(zip(options, values))
    #driver_selected = st.sidebar.selectbox("Select driver",drivers)
    driver_selected = st.sidebar.selectbox("Select driver",options,format_func=lambda x: dic[x])
    #print(driver_selected)
    return driver_selected




def select_trip(driver_selected):
    filter_driver_trips = {
        "mobileDeviceInfo.androidId": {
            "$eq":driver_selected
        }
    }
    filtered_trips = trips_collection.find(filter_driver_trips)
    trips = []
    values = []
    for trip in filtered_trips:
        #print(trip)
        trips.append(trip["tripId"])
        val = trip["tripStartTimestamp"]
        a = pd.to_datetime(val,unit="ms").strftime("%d-%m-%Y at %H:%M")
        #print(a.strftime("%d-%m-%Y at %H:%M"))
        values.append(a)
        #print(type(trip["tripStartTimestamp"]))

    dic = dict(zip(trips, values))
    trip_selected = st.sidebar.selectbox("Select trip", trips,format_func=lambda x: dic[x])
    
    return trip_selected

def create_df(trip_id):
    global df

    trip_query = {
        "tripId": {
            "$eq":trip_id
        }
    }

    trips = obd_data_collection.find(trip_query).sort("timestamp",1)
    latutude_org_arr = []
    longitude_org_arr = []
    timestamp_org_arr = []
    vehicle_speed_org_arr = []
    free_flow_speed_org_arr = []
    current_speed_org_arr = []
    acc_pedal_position_D_arr =[]
    acc_pedal_position_E_arr =[]
    engine_rpm_arr = []
    engine_load_arr = []
    fuel_level_arr = []

    for trip in trips: 
        latitude_org_val = trip["locationData"]["latitude"]
        longidute_org_val = trip["locationData"]["longitude"]
        timestamp_org_val = trip['timestamp']
        datetime_time = timestamp_org_val
        
        try:
            vehicle_speed_org_val = int(trip["obdData"]["SPEED"])
        except Exception as e:
            vehicle_speed_org_val = None

        free_flow_speed_val = trip["trafficData"]["freeFlowSpeed"]
        current_speed_val = trip["trafficData"]["currentSpeed"]


        try:
            acc_pedal_position_E_val = float(trip["obdData"]["Accelerator Pedal Position E"].strip('%').replace(",","."))
            acc_pedal_position_E_val = round(acc_pedal_position_E_val,2)
        except Exception as e:
            acc_pedal_position_E_val = None
        try:
            acc_pedal_position_D_val = float(trip["obdData"]["Accelerator Pedal Position D"].strip('%').replace(",","."))
        except Exception as e:
            acc_pedal_position_D_val = None

        try:
            engine_rpm_val = float(trip["obdData"]["ENGINE_RPM"])
        except Exception as e:
            engine_rpm_val = None
        try:
            engine_load_val = float(trip["obdData"]["ENGINE_LOAD"].strip('%').replace(",","."))
        except Exception as e:
            engine_load_val = None 
        
        try:
            fuel_level_val = float(trip["obdData"]["FUEL_LEVEL"].strip('%').replace(",","."))
        except Exception as e:
            fuel_level_val = None 

        latutude_org_arr.append(latitude_org_val)
        longitude_org_arr.append(longidute_org_val)
        timestamp_org_arr.append(datetime_time)
        vehicle_speed_org_arr.append(vehicle_speed_org_val)
        free_flow_speed_org_arr.append(free_flow_speed_val)
        current_speed_org_arr.append(current_speed_val)

        acc_pedal_position_E_arr.append(acc_pedal_position_E_val)
        acc_pedal_position_D_arr.append(acc_pedal_position_D_val)

        engine_rpm_arr.append(engine_rpm_val)
        engine_load_arr.append(engine_load_val)
        fuel_level_arr.append(fuel_level_val)
        

    data_for_df = {
        'timestamp':timestamp_org_arr,
        'lat':latutude_org_arr,
        'lon':longitude_org_arr,
        'vehicle_speed (km/h)':vehicle_speed_org_arr,
        'free_flow_speed (km/h)':free_flow_speed_org_arr,
        'current_speed (km/h)':current_speed_org_arr,
        'acc_pedal_position_D (%)':acc_pedal_position_D_arr,
        'acc_pedal_position_E (%)':acc_pedal_position_E_arr,
        'engine_rpm':engine_rpm_arr,
        'engine_load (%)':engine_load_arr,
        'fuel_level':fuel_level_arr
    }
    df = pd.DataFrame(data_for_df,columns=[
        'timestamp','lat','lon','vehicle_speed (km/h)',
        'free_flow_speed (km/h)','current_speed (km/h)',
        'acc_pedal_position_D (%)','acc_pedal_position_E (%)',
        'engine_rpm','engine_load (%)','fuel_level'
    ])

    df["timestamp"]=(pd.to_datetime(df["timestamp"],unit='ms')) 
    #df

def draw_trip():
    st.map(df)
    st.title("")
    st.title("")


def calculate_speed_stats():
    avg_speed = df["vehicle_speed (km/h)"].mean()
    avg_speed = round(avg_speed,2)
    avg_speed_excluded_zeros = df["vehicle_speed (km/h)"]
    avg_speed_excluded_zeros = avg_speed_excluded_zeros[avg_speed_excluded_zeros!=0].mean()
    avg_speed_excluded_zeros = round(avg_speed_excluded_zeros,2)
    median_speed = df["vehicle_speed (km/h)"].median()
    max_speed = df["vehicle_speed (km/h)"].max()


    return avg_speed, avg_speed_excluded_zeros, median_speed, max_speed

def calculate_trip_distance():
    suma = 0
    df2 = df[df.index % 5 == 0]  # Selects every 3rd raw starting from 0
    for ind in df2.index:

        if(ind > len(df)-5):
            break
        cords1 = (df2["lat"][ind],df2["lon"][ind])
        cords2 = (df2["lat"][ind+5],df2["lon"][ind+5])
        suma = suma + geopy.distance.distance(cords1, cords2).km

    return suma


    

def general_info(avg_speed, avg_speed_excluded_zeros, median_speed, max_speed):
    trip_started = df["timestamp"][0]
    trip_started_str = trip_started
    
    trip_started_str = trip_started_str.strftime("%d-%m-%Y at %H:%M")
    trip_ended = df["timestamp"][len(df.index)-1]
    trip_ended_str = trip_ended
    trip_ended_str = trip_ended_str.strftime("%d-%m-%Y at %H:%M")
    number_of_points = len(df.index)
    trip_time = trip_ended - trip_started
    trip_time_str = trip_time
    trip_time_str = str(trip_time_str.components.hours)+":"+str(trip_time_str.components.minutes)+":"+str(trip_time_str.components.seconds)

    trip_duration_in_hours = trip_time / pd.Timedelta('1 hour')

    #trip_distance = trip_duration_in_hours * avg_speed
    #trip_distance = round(trip_distance,2) #3.23KM
    trip_distance = round(calculate_trip_distance(),2)

    st.title("General info")
    st.write(
        """In the table below you can find various informations about speed (mean, mean (with 0s excluded), median and max) and trip (date of the trip, its duration, number of points and the distance).
        """
    )

    
    c1,c2= st.beta_columns((2))

    with c1:
        st.header("Speed info")
        st.title("")
        st.markdown(f'''
        **Mean speed:** {avg_speed:,} km/h
        
        ---
        **Mean speed (non 0):** {avg_speed_excluded_zeros:,} km/h

        ---
        **Median speed:** {median_speed:,} km/h

        ---
        **Max speed:** {max_speed:,} km/h

    ''')
    with c2:
        st.header("Trip info")
        st.title("")
        st.markdown(f'''
        **Trip time:** (start) {trip_started_str:} - (end) {trip_ended_str:}

        ---
        **Trip duration:** {trip_time_str:} (hours:min:sec)

        ---
        **Number of points:** {number_of_points:}
        
        ---
        **Trip distance:** {(trip_distance):} km

    ''')
    st.title("")

def vechile_free_flow_current():
    global df
    st.title("Vehicle, current and free flow speed")
    st.write(
        """In the chart below you can find data about vehicle, current and free flow speed. You can also toggle between them and draw only the speed you want displayed.
        """
    )

    default_columns = ['vehicle_speed (km/h)','free_flow_speed (km/h)','current_speed (km/h)']
    st_ms = st.multiselect("", ['vehicle_speed (km/h)','free_flow_speed (km/h)','current_speed (km/h)'], default=default_columns)

    chart = alt.Chart(df).transform_fold(
        st_ms,
        as_=["direction","km/h"]
    ).mark_line().encode(
        alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M",tickCount=5)),
        y ="km/h:Q",
        color="direction:N"
    )  

    st.altair_chart(chart.properties(width=1300, height=400))
    #st.altair_chart(chart)
    st.title("")
    

def draw_pedal_position():
    st.title("Pedal position")
    st.write(
        """The pedal position (in %) is shown in the chart below. You can switch between them and show only the ones that you want displayed. 
        """
    )
    #global df
    default_columns = ['acc_pedal_position_D (%)','acc_pedal_position_E (%)']
    st_ms = st.multiselect("", ['acc_pedal_position_D (%)','acc_pedal_position_E (%)'], default=default_columns)

    chart = alt.Chart(df).transform_fold(
        st_ms,
        as_=["Pedal position","Pedal position (%)"]
    ).mark_line().encode(
        alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M",tickCount=5)),
        #alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M", tickCount=3)),
        #x="timestamp:T",
        y ="Pedal position (%):Q",
        color="Pedal position:N"
    )  
    st.altair_chart(chart.properties(width=1300, height=400))
    st.title("")

def draw_engine_rpm_load():

    st.title("Engine load and RPM")
    st.write(
        """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et 
        dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
        commodo consequat. 
        """
    )
    st.title("")
    base = alt.Chart(df).encode(
        alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M", tickCount=5)),
    )

    line2 = base.mark_line(stroke='#5276A7', interpolate='monotone').encode(
        alt.Y('engine_load (%)',
            axis=alt.Axis(title='Engine load (%)', titleColor='#5276A7'))
    )

    line1 = base.mark_line(stroke='#F17720', interpolate='monotone').encode(
        alt.Y('engine_rpm',
            axis=alt.Axis(title='Engine rpm', titleColor='#F17720'))
    )

    chart = alt.layer(line1, line2).resolve_scale(y = 'independent')

    st.altair_chart(chart.properties(width=1300, height=400))



    # default_columns = ['fuel_level','engine_load (%)']
    # st_ms = st.multiselect("", ['fuel_level','engine_load (%)'], default=default_columns)

    # chart = alt.Chart(df).transform_fold(
    #     st_ms,
    #     as_=["Pedal position","Pedal position (%)"]
    # ).mark_line().encode(
    #     alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M",tickCount=5)),
    #     #alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M", tickCount=3)),
    #     #x="timestamp:T",
    #     y ="Pedal position (%):Q",
    #     color="Pedal position:N"
    # )  
    # st.altair_chart(chart.properties(width=700, height=400))
    # st.title("")

def draw_engine_rpm():
        st.title("Engine RPM")
        st.write(
            """In the chart below you can find how did the RPM change over time.
            """
        )

        default_columns = ['vehicle_speed (km/h)','free_flow_speed (km/h)','current_speed (km/h)']
        #st.line_chart("engine_rpm")
        chart = alt.Chart(df).mark_line().encode(
            alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M",tickCount=5)),
            y="engine_rpm:Q"
        )
        st.altair_chart(chart.properties(width=1300, height=400))


def draw_engine_load():
        st.title("Engine load")
        st.write(
            """In the chart below you can find how did the RPM load (in %) change over time. 
            """
        )

        default_columns = ['vehicle_speed (km/h)','free_flow_speed (km/h)','current_speed (km/h)']
        #st.line_chart("engine_rpm")
        chart = alt.Chart(df).mark_line().encode(
            alt.X('timestamp:T', axis=alt.Axis(title=None,format="%H:%M",tickCount=5)),
            y="engine_load (%):Q"
        )
        st.altair_chart(chart.properties(width=1300, height=400))





def all_stats(driver_selected):
    result = stats_collection.aggregate([
    {
        '$match': {
            'androidId': driver_selected
        }
    }
    ])
    for r in result:
        # print(r["avg_speed"])
        # print(r["avg_rpm"])
        # print(r["number_of_trips"])
        avg_speed = r["avg_speed"]
        avg_rpm = r["avg_rpm"]
        number_of_trips = r["number_of_trips"]
    st.sidebar.title("All trips stats")
    st.sidebar.subheader("Number of trips: " + str(number_of_trips))
    st.sidebar.subheader("Average speed: " + str(round(avg_speed, 2)) + " km/h")
    st.sidebar.subheader("Average RPM: " + str(int(avg_rpm)))

    
driver_selected = select_driver()


trip_selected = select_trip(driver_selected)
#print(trip_selected)
create_df(trip_selected)
draw_trip()
all_stats(driver_selected)
avg_speed, avg_speed_excluded_zeros, median_speed, max_speed = calculate_speed_stats()
general_info(avg_speed, avg_speed_excluded_zeros, median_speed, max_speed)

vechile_free_flow_current()
draw_pedal_position()

#draw_engine_rpm_load()

draw_engine_rpm()
draw_engine_load()
