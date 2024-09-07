import requests


def fetch_data():

    url = f"https://api.solcast.com.au/data/live/radiation_and_weather?latitude=43.4643&longitude=80.5204&hours=12&output_parameters=air_temp%2Cghi%2Cgti%2Cclearsky_ghi%2Cclearsky_gti%2Cdewpoint_temp%2Cprecipitation_rate%2Crelative_humidity%2Cwind_direction_10m%2Cwind_speed_10m&array_type=fixed&terrain_shading=true&format=csv&api_key="
    response = requests.get(url)
    return response.content


data = fetch_data()
print(data)
