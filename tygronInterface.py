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
        r = requests.post(url = join_url, json = [session_id, application_type, "Virtual River application script"], auth=(username, password))
    else:
        print("no session to join")
    try:
        pastebin_url = r.json()
        #print(pastebin_url["apiToken"])
    except ValueError:
        print("no content")
    return pastebin_url["apiToken"]


def set_function(hex_id, new_type, api_key, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/SET_FUNCTION/?"):
    """
    Functie voor type landgebruik in te vullen/updaten. Werkt per zeshoek
    """
    #data = {'0': hex_id, '1': new_type} #alles in dict format versturen
    data = [hex_id, new_type]
    r = requests.post(url = api_endpoint+api_key, json=data)
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")

 
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
    r = requests.post(url = api_endpoint+api_key, json=[tiff_id, tiff_base64, uploader])
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")
    if start:
        api_endpoint = "https://engine.tygron.com/api/session/event/EditorMapEventType/SELECT_HEIGHT_MAP/?"
        r = requests.post(url = api_endpoint+api_key, json=[tiff_id])
    else:
        return


def set_terrain_type_backup(api_key, hexagons, terrain_type="land", api_endpoint="https://engine.tygron.com/api/session/event/EditorTerrainTypeEventType/ADD_TERRAIN_POLYGONS/?"):
    if terrain_type == "water":
        terrain_id = 3
    else:
        terrain_id = 0
    polygons = []
    """
    Deze methode opdelen in twee delen:
    
    Deel 1: polygon verwijderen/toevoegen, krijgt mee: id, coordinaten, water/land.
    Op basis van water of land polygon verwijderen (water) of toevoegen (land)
    en dat komt overeen met building_remove_polygons en building_add_polygons
    
    Deel 2: Krijgt mee terrain_type & geojson file of file name. Maakt
    multipolygons geheel water, danwel land.
    """
    api_url = "https://engine.tygron.com/api/session/event/EditorBuildingEventType/BUILDING_REMOVE_POLYGONS/?"
    for feature in hexagons.features:
        #data = requests.get(api_quick+str(feature.id)+"?f=JSON&"+api_key)
        #tygron_buildings = feature.id
        shape = geometry.asShape(feature.geometry)
        polygons.append(shape)
        multi = geometry.MultiPolygon([shape])
        #print(multi)
        remove = geometry.mapping(multi)
        r = requests.post(url = api_url+api_key, json=[feature.id, 1, remove])
    #for feature_id in tygron_buildings:   
    #print(tygron_buildings)
    multipolygon = geometry.MultiPolygon(polygons)
    waterbodies = geometry.mapping(multipolygon)
    r = requests.post(url = api_endpoint+api_key, json=[terrain_id, waterbodies, True])
    print(r, r.text)
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("waterbodies updated")


def set_terrain_type(api_key, terrain_type="land"):
    with open('waterbodies.geojson') as f:
        hexagons = geojson.load(f)
    polygons = []
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
        print("waterbodies updated")


def remove_polygon(api_key, hexagon_id, hexagon_shape, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/BUILDING_REMOVE_POLYGONS/?"):
    multi = geometry.MultiPolygon([hexagon_shape])
    remove = geometry.mapping(multi)
    r = requests.post(url = api_endpoint+api_key, json=[hexagon_id, 1, remove])
    return


def add_polygon(api_key, hexagon_id, hexagon_shape, api_endpoint="https://engine.tygron.com/api/session/event/EditorBuildingEventType/BUILDING_ADD_POLYGONS/?"):
    multi = geometry.MultiPolygon([hexagon_shape])
    remove = geometry.mapping(multi)
    r = requests.post(url = api_endpoint+api_key, json=[hexagon_id, 1, remove])
    return


def update_polygon(api_key, hexagons, terrain_type="land", api_endpoint="https://engine.tygron.com/api/session/event/EditorTerrainTypeEventType/ADD_TERRAIN_POLYGONS/?"):
    if terrain_type == "water":
        terrain_id = 3
    else:
        terrain_id = 0
    r = requests.post(url = api_endpoint+api_key, json=[terrain_id, hexagons, True])
    return r
    

if __name__ == '__main__':
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    api_key = join_session(username, password)
    api_key = "token="+api_key
    print(api_key)
    set_function(60, 0, api_key)
    buildings_json = get_buildings(api_key)
    #print(buildings_json)
    set_terrain_type(api_key, terrain_type="water")
