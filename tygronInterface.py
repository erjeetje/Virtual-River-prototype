# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:25:35 2019

@author: HaanRJ
"""

import requests
import base64
import geojson
from shapely import geometry


def join_session(username, password, application_type = "EDITOR", api_endpoint="https://engine.tygron.com/api/services/event/IOServiceEventType/GET_MY_JOINABLE_SESSIONS/?f=JSON"):
    sessions_data = requests.post(url = api_endpoint, json = [], auth=(username, password))
    session_id = -1
    sessions = sessions_data.json()
    for item in sessions:
        if item["name"] == "rivercare_hex":
            session_id = item["id"]
            break
    if session_id > -1:
        join_url = "https://engine.tygron.com/api/services/event/IOServiceEventType/JOIN_SESSION/?f=JSON"
        r = requests.post(url=join_url, json=[session_id, application_type, "Virtual River application script"], auth=(username, password))
    else:
        print("no session to join")
    try:
        pastebin_url = r.json()
        #print(pastebin_url["apiToken"])
    except ValueError:
        print("no content")
    return pastebin_url["apiToken"]


def set_function(api_key, hex_id, new_type, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/SET_FUNCTION/?"):
    """
    Functie voor type landgebruik in te vullen/updaten. Werkt per zeshoek
    """
    r = requests.post(url=api_endpoint+api_key, json=[hex_id, new_type])
    print(r.text)
    """try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")
    """
    return


def get_buildings(api_key, api_endpoint="https://engine.tygron.com/api/session/items/buildings/?f=JSON&"):
    """
    Ophalen alle gebouwen uit Tygron engine
    """
    data = requests.get(api_endpoint+api_key)
    buildings_json = data.json()
    return buildings_json


def set_elevation(tiff_file, api_key, start=False):
    """
    GeoTIFF maken --> stackoverflow afzoeken
    Inladen komt Rudolf op terug
    """
    if start:
        api_endpoint = "https://engine.tygron.com/api/session/event/EditorGeoTiffEventType/ADD/?"
    else:
        api_endpoint = "https://engine.tygron.com/api/session/event/EditorGeoTiffEventType/UPDATE/?"
    tiff_id = 1
    tiff_base64 = base64.b64encode(tiff_file)
    uploader = "r.j.denhaan@utwente.nl"
    r = requests.post(url=api_endpoint+api_key, json=[tiff_id, tiff_base64, uploader])
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")
    if start:
        api_endpoint = "https://engine.tygron.com/api/session/event/EditorMapEventType/SELECT_HEIGHT_MAP/?"
        r = requests.post(url=api_endpoint+api_key, json=[tiff_id])
    else:
        return


def set_terrain_type(api_key, hexagons, terrain_type="land"):
    polygons = []
    if terrain_type == "water":
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            polygons.append(shape)
            remove_polygon(api_key, feature.id, shape)
        multipolygon = geometry.MultiPolygon(polygons)
        hexagons2change = geometry.mapping(multipolygon)
        r = update_terrain(api_key, hexagons2change, terrain_type=terrain_type)
        try:
            pastebin_url = r.json()
            print(pastebin_url)
        except ValueError:
            print("test")
    else:
        """
        to do: see if only one for loop can be used
        """
        hexagon_ids = []
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            hexagon_ids.append(feature.id)
            polygons.append(shape)
        multipolygon = geometry.MultiPolygon(polygons)
        hexagons2change = geometry.mapping(multipolygon)
        r = update_terrain(api_key, hexagons2change, terrain_type=terrain_type)
        add_section(api_key, hexagon_ids)
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            add_polygon(api_key, feature.id, shape)
            set_function(api_key, feature.id, 0)
        try:
            pastebin_url = r.json()
            print(pastebin_url)
        except ValueError:
            print("land terrain updated")
    """
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        polygons.append(shape)
        if terrain_type == "water":
            remove_polygon(api_key, feature.id, shape)
        else:
            add_polygon(api_key, feature.id, shape)
    multipolygon = geometry.MultiPolygon(polygons)
    hexagons2change = geometry.mapping(multipolygon)
    r = update_polygon(api_key, hexagons2change, terrain_type=terrain_type)
    print(r, r.text)
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        if terrain_type == "water":
            print("waterbodies updated")
        else:
            print("land terrain updated")
    """


def remove_polygon(api_key, hexagon_id, hexagon_shape, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/BUILDING_REMOVE_POLYGONS/?"):
    multi = geometry.MultiPolygon([hexagon_shape])
    remove = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, remove])
    print(r.text)
    return


def add_polygon(api_key, hexagon_id, hexagon_shape, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/BUILDING_ADD_POLYGONS/?"):
    multi = geometry.MultiPolygon([hexagon_shape])
    add = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, add])
    print(r.text)
    return

"""
def add_standard(api_key, hexagon_id, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/ADD_STANDARD/?"):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id])
    print(r, r.text)
    return


def add_building(api_key, hexagon_id, hexagon_shape, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/ADD_BUILDING_COLLECTION/?"):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, hexagon_shape])
    print(r, r.text)
    return r
"""

def add_section(api_key, hexagon_ids, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/ADD_SECTION/?"):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_ids])
    print(r.text)
    return


def update_terrain(api_key, hexagons, terrain_type="land", api_endpoint="https://engine.tygron.com/api/session/event/EditorTerrainTypeEventType/ADD_TERRAIN_POLYGONS/?"):
    if terrain_type == "water":
        terrain_id = 3
    else:
        terrain_id = 0
    r = requests.post(url=api_endpoint+api_key, json=[terrain_id, hexagons, True])
    return r
    

if __name__ == '__main__':
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    api_key = join_session(username, password)
    api_key = "token="+api_key
    print(api_key)
    set_function(api_key, 60, 0)
    buildings_json = get_buildings(api_key)
    print(buildings_json)
    with open('waterbodies.geojson') as f:
        hexagons = geojson.load(f)
    set_terrain_type(api_key, hexagons, terrain_type="water")
