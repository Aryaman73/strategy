import requests
import pandas as pd
import sys
import os.path

sys.path.append(os.path.dirname(__file__))

from config import API_KEY, BASE_URL 

def points_query_builder(waypoints: list, viawaypoints: list):
    """
    @param waypoints: List of dictionaries of waypoints.
        Each dictionary can only have 1 waypoint.
        Up to 25 dictionaries/elements in full list.
        Format as: [{lat1: long1}, {lat2: long2},... {latN: longN}]
    @param viawaypoints: List of dictionaries of viawaypoints. 
        Each dictionary can have up to 10 viawaypoints.
        Full list should be one element shorter than list of waypoints,
        to a maximum of 24 elements.
        Format as: [{lat1: long1,... latN: longN},...{lat1: long1,... latN: longN}]
    @return: a string of points for sending to API; pass to getter
    """
    counter = 0
    params = str()
    for index, waypoint in enumerate(waypoints):
        for key in waypoint.keys():
            params += 'wp.{}={},{}&'.format(counter, key, waypoint[key])
            counter += 1
        if index < len(waypoints) - 1:
            for points in viawaypoints[index]:
                for key in points.keys():
                    params += 'vwp.{}={},{}&'.format(counter, key, points[key])
                    counter += 1
         
    return params

def get_routing_data(points: str, route_attrs = 'routePath', dist_unit = 'km'):
    """
    Getting navigation data response from Bing Maps API.
    @param points: string of points formatted for requesting from Bing Maps API.
        Use points_query_builder method to build string correctly.
    @param dist_unit (optional): Either 'km' or 'mi,' default to km since
        we're Canadian, eh.
    @param route_attrs (optional): 
    @return: Requests.response object from API call
    """
    # adjust url for Route API request
    url = BASE_URL + 'Routes?'

    # add coordinates, route attribute option, distance unit, and API key
    # to url to be requested
    url += '{}routeAttributes={}&distanceUnit={}&key={}'.format(points, \
           route_attrs, dist_unit, API_KEY)
    
    # get and return response
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print("An error occured:", err, "\nMessage:", err.response.text)
        sys.exit()
    return response.json()    

def parse_routing_data(response: dict):
    """
    Parsing through Routes API call response.
    @param response: Requests.response object from API call
    @return: boolean
    """
    route = response    # headers are for csv, create DataFrame to write data into
    headers = ['Latitude', 'Longitude', 'Maneuver Instruction', 'Distance to Maneuver', 'Direction', 'Street']
    route_df = pd.DataFrame(columns=headers)

    # parse through each route leg returned in response
    try:
        for route_leg in route['resourceSets'][0]['resources'][0]['routeLegs']:
            # parse through the items in each route leg
            for item in route_leg['itineraryItems']:
                    # relevant info parsed below
                    lat = item['maneuverPoint']['coordinates'][0]
                    longit = item['maneuverPoint']['coordinates'][1]
                    instruction = item['instruction']['text']
                    dist = item['travelDistance']
                    direction = item['compassDirection']

                    # ensure street name is found
                    if len(item['details']) > 1:
                        street = item['details'][1].get('names')[0]
                    else:
                        street = item['details'][0].get('names')[0]
                    
                    # append data into dataframe
                    route_df = route_df.append({'Latitude': lat, 'Longitude': longit, 
                                                'Maneuver Instruction': instruction, 'Distance to Maneuver': dist, 
                                                'Direction': direction, 'Street': street}, ignore_index = True)
    except Exception as error:
        print(f'An error occurred: {error}')
        sys.exit()
    return route_df
