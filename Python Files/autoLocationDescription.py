import pandas as pd
import pyperclip
import shutil
import os
import re
import math
import sqlite3
import sys

# db_path = r"C:\Users\asset\OneDrive - Asset Inspect\AI Shared Folder\Administration\Programs\Databases\special_location_descriptions.db"

base_dir = os.path.dirname(__file__)
db_path = os.path.join(base_dir, "Databases", "special_location_descriptions.db")

table_name = "descriptions"

state_mapping = {
    "QLD": "Queensland",
    "NSW": "New South Wales",
    "SA": "South Australia",
    "NT": "Northern Territory",
    "VIC": "Victoria",
    "TAS": "Tasmania",
    "WA": "Western Australia",
    "ACT": "Australian Capital Territory"
}

state_capital_mapping = {
    "QLD": "Brisbane",
    "NSW": "Sydney",
    "SA": "Adelaide",
    "NT": "Darwin",
    "VIC": "Melbourne",
    "TAS": "Hobart",
    "WA": "Perth",
    "ACT": "Canberra"
}

city_lng_lat = {
    "Brisbane": (-27.4705, 153.0260),
    "Sydney": (-33.8688, 151.2093),
    "Adelaide": (-34.9285, 138.6007),
    "Darwin": (-12.4637, 130.8444),
    "Melbourne": (-37.8136, 144.9631),
    "Hobart": (-42.8826, 147.3257),
    "Perth": (-31.9514, 115.8617),
    "Canberra": (35.2802, 149.1310)
}

def haversine_distance_and_direction(lat1, lon1, lat2, lon2):
    """
    Calculates the distance and approximate direction between two points on Earth's surface.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        tuple: A tuple containing the distance in kilometers and the direction.
    """

    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    distance = R * c

    # Determine direction
    bearing = math.atan2(math.sin(dlon) * math.cos(lat2),
                      math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon))
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360

    if 337.5 <= bearing or bearing < 22.5:
        direction = "North"
    elif 22.5 <= bearing < 67.5:
        direction = "North-East"
    elif 67.5 <= bearing < 112.5:
        direction = "East"
    elif 112.5 <= bearing < 157.5:
        direction = "South-East"
    elif 157.5 <= bearing < 202.5:
        direction = "South"
    elif 202.5 <= bearing < 247.5:
        direction = "South-West"
    elif 247.5 <= bearing < 292.5:
        direction = "West"
    elif 292.5 <= bearing < 337.5:
        direction = "North-West"
    else:
        print(bearing)

    return distance, direction

def get_population(suburb_name, file1, file2, statesLs):
    # Read the two CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    exact_matches = df1[df1['SAL_NAME_2021'] == suburb_name]

    if not exact_matches.empty:
        code = exact_matches['SAL_CODE_2021'].values[0]
        state = exact_matches['STATE_CODE_2021'].values[0]
    else:
        # Find partial matches
        partial_matches = df1[df1['SAL_NAME_2021'].str.startswith(suburb_name)]

        if not partial_matches.empty:
            print("Multiple matches found:")
            x = 1
            for i, row in partial_matches.iterrows():
                print(f"{x}. {row['SAL_NAME_2021']}")
                x += 1

            choice = int(input("Please select a match: "))
            suburb_name = partial_matches.iloc[choice-1]['SAL_NAME_2021']
            code = partial_matches.iloc[choice-1]['SAL_CODE_2021']
            state = partial_matches.iloc[choice-1]['STATE_CODE_2021']
        else:
            print(f"Suburb '{suburb_name}' not found.")
            return

    stateName = statesLs[int(state)-1]

    # Find the population for the code in the second file
    population = df2[df2['SAL_CODE_2021'] == 'SAL'+code]['Tot_P_P'].values[0]

    return population, suburb_name, stateName

def get_location(suburb_name, file, state):
    citylat, citylong = city_lng_lat[state_capital_mapping[state]]

    df = pd.read_csv(file)

    exact_matches = df[df['suburb'] == suburb_name]

    if len(exact_matches) == 0:
        print('Cant find the suburb')
        exit()

    if len(exact_matches) != 1:
        exact_matches = exact_matches[exact_matches['state'] == state]
        if len(exact_matches) != 1:
            print("Multiple matches found in same state:")
            x=1
            for i, row in exact_matches.iterrows():
                print(f"{x}. {row['suburb']}, {row['local_goverment_area']}")
                x += 1
            choice = int(input("Please select a match: "))
            suburbRow = exact_matches.iloc[choice-1]
        else:
            suburbRow = exact_matches.iloc[0]
    else:
        suburbRow = exact_matches.iloc[0]

    lga = suburbRow['local_goverment_area']
    lng = suburbRow['lng']
    lat = suburbRow['lat']

    distance, direction = haversine_distance_and_direction(citylat, citylong, lat, lng)

    return distance, direction, lga

def search_specials(location, lga):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query the database for the given Location and LGA
    cursor.execute(f"""
        SELECT Description FROM {table_name}
        WHERE Location = ? AND LGA = ?
    """, (location, lga))

    result = cursor.fetchone()  # Fetch a single result

    conn.close()

    if result:
        return result[0]  # Return the description
    else:
        return None  # No matching entry found
    
def updateSpecial(suburb_name, lga, description):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the entry exists
    cursor.execute(f"""
        SELECT 1 FROM {table_name} WHERE Location = ? AND LGA = ?
    """, (suburb_name, lga))

    if cursor.fetchone():
        # Update existing entry
        cursor.execute(f"""
            UPDATE {table_name}
            SET Description = ?
            WHERE Location = ? AND LGA = ?
        """, (description, suburb_name, lga))
    else:
        # Insert new entry
        cursor.execute(f"""
            INSERT INTO {table_name} (Location, LGA, Description)
            VALUES (?, ?, ?)
        """, (suburb_name, lga, description))

    conn.commit()
    conn.close()

    print(f"Entry updated/inserted for {suburb_name}, {lga}.")

statesLs = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']

file1 = r"c:\Users\asset\OneDrive\Desktop\Automation Stuff\RI-Code\ABS Stats\SAL_2021_AUST.csv"
file2 = r"c:\Users\asset\OneDrive\Desktop\Automation Stuff\RI-Code\ABS Stats\2021Census_G01_AUST_SAL.csv"
file3 = r"c:\Users\asset\OneDrive\Desktop\Automation Stuff\RI-Code\ABS Stats\suburbs.csv"

def main():
    while True:
        editing = False

        suburb_name = input().strip()

        if suburb_name == 'e': exit()

        if suburb_name[0] == '#':
            editing = True
            suburb_name = suburb_name[1:]

        population, suburb_name_long, state = get_population(suburb_name, file1, file2, statesLs)
        distance, direction, lga = get_location(suburb_name, file3, state)

        distance = round(distance)

        lga = lga.split("(")[0].strip()

        special = search_specials(suburb_name, lga)

        if editing:
            print("Current description:")

        if special:
            description = special

        else:
            if distance < 60:
                if suburb_name not in lga:
                    description = f"The subject property is located in {suburb_name}, a suburb of {state_capital_mapping[state]}, {state_mapping[state]}. {suburb_name} has a current population of {population:,} and is located {distance}km {direction.lower()} of {state_capital_mapping[state]} CBD in the {lga} local government area."
                else:
                    description = f"The subject property is located in {suburb_name}, a suburb of {state_capital_mapping[state]}, {state_mapping[state]}. {suburb_name} has a current population of {population:,} and is located {distance}km {direction} of {state_capital_mapping[state]} CBD."
            else:
                if suburb_name not in lga:
                    description = f"The subject property is located in {suburb_name}, a town in {state_mapping[state]}. {suburb_name} has a current population of {population:,} and is located {distance}km {direction.lower()} of {state_capital_mapping[state]} in the {lga} local government area."
                else:
                    description = f"The subject property is located in {suburb_name}, a town in {state_mapping[state]}. {suburb_name} has a current population of {population:,} and is located {distance}km {direction.lower()} of {state_capital_mapping[state]}."

        print(description)
        
        if editing:
            print("Copy and paste the updated description. Then enter>ctrl-z>enter.")
            newDesc = sys.stdin.read().strip()
            updateSpecial(suburb_name, lga, newDesc)

        else:
            pyperclip.copy(description)

        

main()