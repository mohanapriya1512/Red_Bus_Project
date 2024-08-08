import mysql.connector
import pandas as pd

#Establish database connection
#pymysql.connect(host='127.0.0.1',user='root',passwd='********',database='redbusdb')
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="********",
        database="redbusdb"
    )

# Function to fetch route names from database
def get_route_names():
    conn = get_db_connection()
    query = "SELECT DISTINCT route_name FROM redbus_details"
    cursor = conn.cursor()
    cursor.execute(query)
    route_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return route_names

def fetch_filtered_data(route_name,bus_type,departing_time,price_range,star_rating):
    conn = get_db_connection()
    query = """
    SELECT *
    FROM redbus_details
    WHERE 1=1
    """
    
    params = []
    
    #filter by route name:
    if route_name:
        query += " AND route_name = %s"
        params.append(route_name)
        
    # Filter by bus type :
    if bus_type == "AC":
        query += " AND (bus_type LIKE %s OR bus_type LIKE %s) AND bus_type NOT LIKE %s AND bus_type NOT LIKE %s "
        params.append("%AC%")  # Matches all AC-related types
        params.append("%A/C%") # Also match "A/C" variations, if needed
        params.append("%NON AC%") # Explicitly exclude NON AC types
        params.append("%NON A/C%") # Explicitly exclude NON AC types
    elif bus_type == "NON AC":
        query += " AND bus_type LIKE %s"
        params.append("%NON AC%")  # Matches all NON AC-related types
    elif bus_type == "Seater":
        query += " AND bus_type LIKE %s"
        params.append("%Seater%")  # Matches all Seater types
    elif bus_type == "Sleeper":
        query += " AND bus_type LIKE %s"
        params.append("%Sleeper%")  # Matches all Sleeper types

    #Filter by departing time:
    if departing_time:
        time_conditions = {
            "Before 6am": "departing_time < '06:00:00'",
            "6am-12Pm": "departing_time BETWEEN '06:00:00' AND '12:00:00'",
            "12pm-6pm": "departing_time BETWEEN '12:00:00' AND '18:00:00'",
            "After 6pm": "departing_time > '18:00:00'"
        }
        query += f" AND {time_conditions[departing_time]}"

    #Filter by price_range
    if price_range:
        price_ranges = {
            '100-500': (100, 500),
            '501-1500': (501, 1500),
            '1501-3000': (1501, 3000),
            '3001-5000': (3001, 5000),
        }
        min_price, max_price = price_ranges[price_range]
        query += " AND fare_price BETWEEN %s AND %s"
        params.extend([min_price, max_price])

    #Filter by star_rating:
    if star_rating:
        min_rating, max_rating = star_rating
        query += " AND star_rating BETWEEN %s AND %s"
        params.extend([min_rating, max_rating])

    print(f"SQL Query: {query}")
    print(f"Parameters: {params}")
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    df =pd.DataFrame(data)
    
    #print("DataFrame Columns:", df.columns)  # Debug print to check columns
    #print(df.head())  # Print first few rows to verify data

    # Function to format the time duration
    def format_duration(duration):
        duration_obj = pd.to_timedelta(duration)
        hours, remainder = divmod(duration_obj.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
    
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    # Apply the formatting function
    df['departing_time'] = df['departing_time'].apply(format_duration)
    df['arrival_time'] = df['arrival_time'].apply(format_duration)
    #Print the data types to diagnose the issue
    #print(df.dtypes)
    #print(df)   
    return df


import streamlit as st

# Streamlit application
def main():
    # Streamlit app layout
    st.title('REDBUS Bus Details')
    st.header('Bus Details for the Selected Route Name')
    st.sidebar.write("Home :house:")

    # Display the sidebar selection boxes and slider
    # Fetch route names from the database
    route_names = get_route_names()
    # Route name selectbox
    route_name = st.sidebar.selectbox(
        "Select Route Name",
        options=["All"] + route_names)
    bus_type = st.sidebar.selectbox('Select Bus Type', ["AC", "NON AC","Seater","Sleeper"])
    price_range = st.sidebar.selectbox(
            "Select Price Range",
            ["None", "100-500", "501-1500", "1501-3000", "3001-5000"])
          
    departing_time = st.sidebar.selectbox(
             "Departure Time",
             ["Before 6am", "6am-12Pm", "12pm-6pm", "After 6pm"])
         
    star_rating = st.sidebar.slider(
        'Select Star Rating Range',
        1.0, 5.0, (2.0, 4.0), step=0.1)
    
    # Convert 'None' to None for filtering
    if price_range == "None":
        price_range = None
    if departing_time == "None":
         departing_time = None

    #Fetch and display data based on user inputs
    if st.sidebar.button("Search Bus"):
        #filtered_data = fetch_filtered_data(route_name,bus_type,departing_time,price_range,star_rating)
        try:
            filtered_data = fetch_filtered_data(route_name, bus_type, departing_time, price_range, star_rating)
            st.write("Filtered Results:")
            st.dataframe(filtered_data)
        
        except Exception as e:
            st.write("No results found.")
        
if __name__ == "__main__":
    main()
