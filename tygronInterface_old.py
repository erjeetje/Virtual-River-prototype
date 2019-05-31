# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:25:35 2019

@author: HaanRJ
"""

import requests
import base64
import json
import geojson
from shapely import geometry


def join_session(username, password, application_type="EDITOR",
                 api_endpoint=("https://engine.tygron.com/api/services/event/"
                               "IOServiceEventType/GET_MY_JOINABLE_SESSIONS/?"
                               "f=JSON")):
    """
    Login function to Tygron, returns api token on successful login (requires
    a Tygron session to run called 'rivercare_hex').
    """
    sessions_data = requests.post(url=api_endpoint, json=[],
                                  auth=(username, password))
    session_id = -1
    sessions = sessions_data.json()
    for item in sessions:
        if item["name"] == "rivercare_hex":
            session_id = item["id"]
            break
    if session_id > -1:
        join_url = ("https://engine.tygron.com/api/services/event/"
                    "IOServiceEventType/JOIN_SESSION/?f=JSON")
        r = requests.post(url=join_url, json=[session_id, application_type,
                          "Virtual River application script"],
                          auth=(username, password))
    else:
        print("no session to join")
    try:
        pastebin_url = r.json()
        return pastebin_url["apiToken"]
    except UnboundLocalError:
        print("no content")
        return None


def set_function(api_key, hex_id, new_type,
                 api_endpoint=("https://engine.tygron.com/api/session/event/"
                               "EditorBuildingEventType/SET_FUNCTION/?")):
    """
    Function for setting the land use of each hexagon in Tygron. Updates the
    Building function in Tygron.
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


def set_name(api_key, tygron_id, hex_id,
             api_endpoint=("https://engine.tygron.com/api/session/event/"
                           "EditorBuildingEventType/SET_NAME/?")):
    r = requests.post(url=api_endpoint+api_key, json=[tygron_id, str(hex_id)])
    return


def get_buildings(api_key, api_endpoint=("https://engine.tygron.com/api/"
                                         "session/items/buildings/?f=JSON&")):
    """
    Function to retrieve all building information from Tygron.
    """
    data = requests.get(api_endpoint+api_key)
    buildings_json = data.json()
    with open('buildings.json', 'w') as f:
        json.dump(buildings_json, f, sort_keys=True, indent=2)
    return buildings_json


def set_elevation(tiff_file, api_key, start=False):
    """
    Function to update the elevation of the entire Tygron world. Uploads
    a new GeoTIFF and in case of the initiating the session, selects the
    GeoTIFF as the elevation map. On turn updates, selects the newly updated
    GeoTIFF as the new elevation map.

    Placeholder: GeoTIFF maken --> stackoverflow afzoeken, inladen komt Rudolf
    op terug.
    """
    if start:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "EditorGeoTiffEventType/ADD/?")
    else:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "EditorGeoTiffEventType/UPDATE/?")
    tiff_id = 1
    tiff_base64 = base64.b64encode(tiff_file)
    uploader = "r.j.denhaan@utwente.nl"
    r = requests.post(url=api_endpoint+api_key, json=[tiff_id, tiff_base64,
                                                      uploader])
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")
    if start:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "EditorMapEventType/SELECT_HEIGHT_MAP/?")
        r = requests.post(url=api_endpoint+api_key, json=[tiff_id])
    else:
        return


def update_hexagons_tygron_id(api_key, hexagons):
    buildings_json = get_buildings(api_key)
    building_names = {}
    for building in buildings_json:
        name = building["name"]
        tygron_id = building["id"]
        try:
            building_names.update({int(name): tygron_id})
        except ValueError:
            print("faulty building name for building with ID " +
                  str(building["id"]))
            continue
    for feature in hexagons.features:
        tygron_id = building_names.get(feature.id, None)
            if tygron_id == None:
                tygron_id = add_standard(api_key)
                feature.properties["tygron_id"] = tygron_id
                set_name(api_key, tygron_id, feature.id)
            else:
                feature.properties["tygron_id"] = tygron_id
    return hexagons


def set_terrain_type(api_key, hexagons, terrain_type="land"):
    """
    Function that updates terrain in Tygron. Mainly, it updates terrain from
    land to water and visa versa. In case of water to land, first changes the
    hexagon terrain to water and then adds a building to it which is
    subsequently updated to a specific land use. In case of land to water,
    first removes any building (the land use) from the hexagon and then changes
    the terrain to water.
    """

    # to do: add tygron update polygon method (run at start-up) to update all
    # feature.properties["tygron_id"].
    # Here, check if building exists (can be a list version again),
    # otherwise create.

    polygons = []
    """
    building_names = {}
    buildings_json = get_buildings(api_key)
    for building in buildings_json:
        name = building["name"]
        tygron_id = building["id"]
        try:
            building_names.update({int(name): tygron_id})
        except ValueError:
            print("faulty building name for building with ID " +
                  str(building["id"]))
            continue
    """
    if terrain_type == "water":
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            polygons.append(shape)
            #tygron_id = building_names.get(feature.id)
            remove_polygon(api_key, tygron_id, shape)
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
        to do: see if only one for loop can be used --> do this after steps for
        updating are clear, question is currently with Rudolf.
        """
        hexagon_ids = []
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            hexagon_ids.append(feature.id)
            polygons.append(shape)
            tygron_id = building_names.get(feature.id, None)
            if tygron_id == None:
            #if feature.id not in building_names:
            #if not building_names.get(feature.id):
                tygron_id = add_standard(api_key)
                feature.properties["tygron_id"] = tygron_id
                set_name(api_key, tygron_id, feature.id)
            else:
                feature.properties["tygron_id"] = tygron_id
        multipolygon = geometry.MultiPolygon(polygons)
        hexagons2change = geometry.mapping(multipolygon)
        r = update_terrain(api_key, hexagons2change, terrain_type=terrain_type)
        #add_section(api_key, hexagon_ids)
        for feature in hexagons.features:
            shape = geometry.asShape(feature.geometry)
            #building = geojson.GeometryCollection(feature.geometry)
            #add_building(api_key, feature.id, building)
            add_polygon(api_key, feature.properties["tygron_id"], shape)
            set_function(api_key, feature.properties["tygron_id"], 0)
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


def remove_polygon(api_key, hexagon_id, hexagon_shape,
                   api_endpoint=("https://engine.tygron.com/api/session/event/"
                                 "EditorBuildingEventType/"
                                 "BUILDING_REMOVE_POLYGONS/?")):
    """
    Function that removes a building (land use) from a hexagon in Tygron.
    """
    multi = geometry.MultiPolygon([hexagon_shape])
    remove = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, remove])
    #print(r.text)
    return


def add_polygon(api_key, hexagon_id, hexagon_shape,
                api_endpoint=("https://engine.tygron.com/api/session/event/"
                              "EditorBuildingEventType/"
                              "BUILDING_ADD_POLYGONS/?")):
    """
    Function that adds a polygon to a building (land use) for a hexagon in
    Tygron.
    """
    multi = geometry.MultiPolygon([hexagon_shape])
    add = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, add])
    #print(r, r.text)
    return


def add_standard(api_key,
                 api_endpoint=("https://engine.tygron.com/api/session/event/"
                               "EditorBuildingEventType/ADD_STANDARD/?")):
    r = requests.post(url=api_endpoint+api_key, json=[0])
    #print(r, r.text)
    return r.text


"""
def add_building(api_key, hexagon_id, hexagon_shape,
                 api_endpoint=("https://engine.tygron.com/api/session/event/"
                               "EditorBuildingEventType/"
                               "ADD_BUILDING_COLLECTION/?")):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id,
                                                      hexagon_shape])
    print(r, r.text)
    return r
"""


def add_section(api_key, hexagon_ids,
                api_endpoint=("https://engine.tygron.com/api/session/event/"
                              "EditorBuildingEventType/ADD_SECTION/?")):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_ids])
    #print(r.text)
    return


def update_terrain(api_key, hexagons, terrain_type="land",
                   api_endpoint=("https://engine.tygron.com/api/session/event/"
                                 "EditorTerrainTypeEventType/"
                                 "ADD_TERRAIN_POLYGONS/?")):
    """
    Function that changes the terrain of a hexagon in Tygron. Changes the
    terrain from land to water or from water to land.
    """
    if terrain_type == "water":
        terrain_id = 3
    else:
        terrain_id = 1
    r = requests.post(url=api_endpoint+api_key, json=[terrain_id,
                                                      hexagons, True])
    return r


def hex_to_terrain(api_key, hexagons):
    # landuse range between 0 and 9, with a subdivision for 0:
    # 0: built environment
    # 1: agriculture; production meadow/crop field
    # 2: natural grassland
    # 3: reed; 'ruigte'
    # 4: shrubs; hard-/softwood
    # 5: forest; hard-/softwood
    # 6: mixtype class; mix between grass/reed/shrubs/forest
    # 7: water body; sidechannel (connected to main channel) or lake
    # 8: main channel; river bed with longitudinal training dams
    # 9: main channel; river bed with groynes
    # 10: dike
    for feature in hexagons.features:
        if not feature.properties["landuse_changed"]:
            continue
        if feature.properties["z"] < 2:
            continue
        if feature.properties["landuse"] == 0:
            # built environment / farm / factory
            new_type = 0
        elif feature.properties["landuse"] == 1:
            # agriculture; production meadow/crop field
            new_type = 0
        elif feature.properties["landuse"] == 2:
            # natural grassland
            new_type = 0
        elif feature.properties["landuse"] == 3:
            # reed; 'ruigte'
            new_type = 0
        elif feature.properties["landuse"] == 4:
            # shrubs; hard-/softwood
            new_type = 0
        elif feature.properties["landuse"] == 5:
            # forest; hard-/softwood
            new_type = 0
        elif feature.properties["landuse"] == 6:
            # mixtype class; mix between grass/reed/shrubs/forest
            new_type = 0
        """
        Values 7 to 9 should not occur.
        """
        elif feature.properties["landuse"] == 7:
            # water body; sidechannel (connected to main channel) or lake
            new_type = 0
        elif feature.properties["landuse"] == 8:
            # main channel; river bed with longitudinal training dams
            new_type = 0
        elif feature.properties["landuse"] == 9:
            # main channel; river bed with groynes
            new_type = 0
        elif feature.properties["landuse"] == 10:
            # dike
            new_type = 0
        set_function(api_key, feature.properties["tygron_id"], new_type)
    return


if __name__ == '__main__':
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    api_key = join_session(username, password)
    if api_key is None:
        print("logging in to Tygron failed, unable to make changes in Tygron")
    else:
        api_key = "token="+api_key
        #print(api_key)
        #set_function(api_key, 60, 0)
        #add_standard(api_key)
        buildings_json = get_buildings(api_key)
        #print(buildings_json)
        with open('waterbodies_tygron_transformed.geojson') as f:
            hexagons = geojson.load(f)
        set_terrain_type(api_key, hexagons, terrain_type="water")
