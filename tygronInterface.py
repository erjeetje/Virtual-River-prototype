# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:25:35 2019

@author: HaanRJ
"""

import requests
import base64
import json
import random
import numpy as np
from shapely import geometry
from geojson import load
from scipy import interpolate
import gridMapping as gridmap
#from arcpy import NumPyArrayToRaster


def join_session(username, password, application_type="EDITOR",
                 api_endpoint=("https://engine.tygron.com/api/services/event/"
                               "IOServiceEventType/GET_MY_JOINABLE_SESSIONS/?"
                               "f=JSON")):
    """
    Login function to Tygron, returns api token on successful login (requires
    a Tygron session to run called 'virtual_river2').
    """
    sessions_data = requests.post(url=api_endpoint, json=[],
                                  auth=(username, password))
    session_id = -1
    sessions = sessions_data.json()
    for item in sessions:
        if item["name"] == "virtual_river2":
            session_id = item["id"]
            break
    if session_id > -1:
        join_url = ("https://engine.tygron.com/api/services/event/"
                    "IOServiceEventType/join/")
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
    except json.decoder.JSONDecodeError:
        print("JSON decode error")
        return None


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


def update_hexagons_tygron_id(api_key, hexagons):
    buildings_json = get_buildings(api_key)
    building_indices = {}
    for building in buildings_json:
        name = building["name"]
        tygron_id = building["id"]
        try:
            building_indices.update({int(name): tygron_id})
        except ValueError:
            print("faulty building name for building with ID " +
                  str(building["id"]))
            continue
    for feature in hexagons.features:
        tygron_id = building_indices.get(feature.id, None)
        feature.properties["tygron_id"] = tygron_id
    return hexagons


def set_function(api_key, hex_id, new_type,
                 api_endpoint=("https://engine.tygron.com/api/session/event/"
                               "EditorBuildingEventType/SET_FUNCTION/?")):
    """
    Function for setting the land use of each hexagon in Tygron. Updates the
    Building function in Tygron.
    """
    r = requests.post(url=api_endpoint+api_key, json=[hex_id, new_type])
    """try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("no content")
    """
    return


def set_function_value(api_key, building_id, value,
                       function_value="FLOOR_HEIGHT_M", 
                       api_endpoint=("https://engine.tygron.com/api/session/"
                                     "event/editorbuilding/"
                                     "set_function_value/?")):
    r = requests.post(url=api_endpoint+api_key, json=[building_id, function_value, value])
    return


def set_name(api_key, tygron_id, hex_id,
             api_endpoint=("https://engine.tygron.com/api/session/event/"
                           "EditorBuildingEventType/SET_NAME/?")):
    r = requests.post(url=api_endpoint+api_key, json=[tygron_id, str(hex_id)])
    return


def set_terrain_type(api_key, hexagons, terrain_type="land"):
    """
    Function that updates terrain in Tygron. Mainly, it updates terrain from
    land to water and visa versa. In case of water to land, first changes the
    hexagon terrain to water and then adds a building to it which is
    subsequently updated to a specific land use. In case of land to water,
    first removes any building (the land use) from the hexagon and then changes
    the terrain to water.
    """
    print("updating terrain")
    water = []
    land = []
    for feature in hexagons.features:
        shape = geometry.asShape(feature.geometry)
        if feature.properties["water"] & feature.properties["z_changed"]:
            shape = geometry.asShape(feature.geometry)
            water.append(shape)
            if feature.properties["tygron_id"] is not None:
                remove_polygon(api_key, feature.properties["tygron_id"], shape)
        elif feature.properties["land"] & feature.properties["z_changed"]:
            land.append(shape)
        else:
            continue
    water_multipolygon = geometry.MultiPolygon(water)
    land_multipolygon = geometry.MultiPolygon(land)
    becomes_water = geometry.mapping(water_multipolygon)
    becomes_land = geometry.mapping(land_multipolygon)
    r = update_terrain(api_key, becomes_water, terrain_type="water")
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("water terrain updated")
    r = update_terrain(api_key, becomes_land, terrain_type="land")

    for feature in hexagons.features:
        if feature.properties["land"]:
            if feature.properties["tygron_id"] is None:
                tygron_id = add_standard(api_key)
                feature.properties["tygron_id"] = tygron_id
                set_name(api_key, tygron_id, feature.id)
            shape = geometry.asShape(feature.geometry)
            add_polygon(api_key, feature.properties["tygron_id"], shape)
            set_function(api_key, feature.properties["tygron_id"], 0)
        else:
            continue
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("land terrain updated")
    return hexagons


def remove_polygon(api_key, hexagon_id, hexagon_shape,
                   api_endpoint=("https://engine.tygron.com/api/session/event/"
                                 "editorbuilding/remove_polygons/?")):
    """
    Function that removes a building (land use) from a hexagon in Tygron.
    """
    multi = geometry.MultiPolygon([hexagon_shape])
    remove = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, remove])
    return


def add_polygon(api_key, hexagon_id, hexagon_shape,
                api_endpoint=("https://engine.tygron.com/api/session/event/"
                              "editorbuilding/add_polygons/?")):
    """
    Function that adds a polygon to a building (land use) for a hexagon in
    Tygron.
    """
    multi = geometry.MultiPolygon([hexagon_shape])
    add = geometry.mapping(multi)
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_id, 1, add,
                                                      True])
    return


def add_standard(api_key,
                 api_endpoint=("https://engine.tygron.com/api/session/event/"
                               "EditorBuildingEventType/ADD_STANDARD/?")):
    r = requests.post(url=api_endpoint+api_key, json=[0])
    print("added standard " + str(r))
    return r.text


def add_section(api_key, hexagon_ids,
                api_endpoint=("https://engine.tygron.com/api/session/event/"
                              "EditorBuildingEventType/ADD_SECTION/?")):
    r = requests.post(url=api_endpoint+api_key, json=[hexagon_ids])
    print("added section " + str(r))
    return


def update_terrain(api_key, hexagons, terrain_type="land",
                   api_endpoint=("https://engine.tygron.com/api/session/event/"
                                 "editorterraintype/add_polygons/?")):
                   #api_endpoint=("https://engine.tygron.com/api/session/event/"
                   #              "EditorTerrainTypeEventType/"
                   #              "ADD_TERRAIN_POLYGONS/?")):
    """
    Function that changes the terrain of a hexagon in Tygron. Changes the
    terrain from land to water or from water to land.
    """
    if terrain_type == "water":
        terrain_id = 3
    else:
        terrain_id = 0
    r = requests.post(url=api_endpoint+api_key, json=[terrain_id,
                                                      hexagons, True])
    return r


def set_elevation(tiff_file, api_key, turn=0,
                  api_endpoint=("https://engine.tygron.com/api/session/"
                                "event/editorgeotiff/add/?")):
    """
    Function to update the elevation of the entire Tygron world. Uploads
    a new GeoTIFF and in case of the initiating the session, selects the
    GeoTIFF as the elevation map. On turn updates, selects the newly updated
    GeoTIFF as the new elevation map.
    """
    with open(tiff_file, 'rb') as f:
        heightmap = f.read()
    # the "True" value in below's if statement should be "start"
    json = elevation_json(turn, heightmap)
    r = requests.post(url=api_endpoint+api_key, json=json)
    try:
        heightmap_id = r.json()
    except ValueError:
        print("no heightmap id found")
    api_endpoint = ("https://engine.tygron.com/api/session/event/"
                    "editormap/set_height_geotiff/?")
    r = requests.post(url=api_endpoint+api_key, json=[heightmap_id])
    return heightmap_id


def update_elevation(tiff_file, api_key, heightmap_id, turn=0,
                     api_endpoint=("https://engine.tygron.com/api/session/"
                                   "event/editorgeotiff/set_geotiff/?")):
    json = elevation_json(heightmap_id, heightmap)
    json.append("")
    r = requests.post(url=api_endpoint+api_key, json=json)
    print(r)
    print(r.text)
    try:
        heightmap_id = r.json()
        print(heightmap_id)
    except ValueError:
        print("no content")
    return


def elevation_json(tiff_id, heightmap):
    tiff_base64 = base64.b64encode(heightmap).decode()
    uploader = "r.j.denhaan@utwente.nl"
    datapackage = [tiff_id, tiff_base64, uploader]
    return datapackage


def set_elevation3(tiff_file, api_key, turn=0, start=False):
    """
    Function to update the elevation of the entire Tygron world. Uploads
    a new GeoTIFF and in case of the initiating the session, selects the
    GeoTIFF as the elevation map. On turn updates, selects the newly updated
    GeoTIFF as the new elevation map.
    """
    with open(tiff_file, 'rb') as f:
        heightmap = f.read()
    # the "True" value in below's if statement should be "start"
    if start:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editorgeotiff/add/?")
    else:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editorgeotiff/set_geotiff/?")
    tiff_id = turn
    tiff_base64 = base64.b64encode(heightmap).decode()
    uploader = "r.j.denhaan@utwente.nl"
    r = requests.post(url=api_endpoint+api_key, json=[tiff_id, tiff_base64,
                                                      uploader])
    print(r)
    try:
        heightmap_id = r.json()
        print(heightmap_id)
    except ValueError:
        print("no content")
    # the "True" value in below's if statement should be "start"
    if False:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editormap/set_height_geotiff/?")
        r = requests.post(url=api_endpoint+api_key, json=[heightmap_id])
        return
    else:
        return heightmap_id


def set_elevation2(heightmap, api_key, turn=0, start=False):
    """
    Function to update the elevation of the entire Tygron world. Uploads
    a new GeoTIFF and in case of the initiating the session, selects the
    GeoTIFF as the elevation map. On turn updates, selects the newly updated
    GeoTIFF as the new elevation map.
    """
    """
    To fix: update heightmap from variable instead of from reading file. This
    may work with an approach as below, but installing arcpy will make many
    changes to packages (upgrades and downgrades), including numpy which cannot
    but upgraded until Fedor gives the green light to do so.
    """
    heightmap = NumPyArrayToRaster(heightmap, x_cell_size=1, y_cell_size=1)
    heightmap = heightmap.tostring()
    # the "True" value in below's if statement should be "start"
    if True:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editorgeotiff/add/?")
    else:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editorgeotiff/set_geotiff/?")
    tiff_id = turn
    tiff_base64 = base64.b64encode(heightmap).decode()
    uploader = "r.j.denhaan@utwente.nl"
    r = requests.post(url=api_endpoint+api_key, json=[tiff_id, tiff_base64,
                                                      uploader])
    print(r.text)
    try:
        heightmap_id = r.json()
    except ValueError:
        print("no content")
    # the "True" value in below's if statement should be "start"
    if True:
        api_endpoint = ("https://engine.tygron.com/api/session/event/"
                        "editormap/set_height_geotiff/?")
        r = requests.post(url=api_endpoint+api_key, json=[heightmap_id])
        print(r)
        return
    else:
        return heightmap_id


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
        if feature.properties["water"]:
            continue
        if feature.properties["landuse"] == 0:
            # built environment / farm / factory
            new_type = 936  # veehouderij
            """
            rand = random.randint(1, 3)
            if rand == 1:
                new_type = 936  # veehouderij
            elif rand == 2:
                new_type = 941  # Van Nelle Fabriek
            else: 
                new_type = 851  # Caballero Fabriek
            """
        elif feature.properties["landuse"] == 1:
            # agriculture; production meadow/crop field
            new_type = 1000000
            """
            rand = random.randint(1, 3)
            if rand == 1:
                new_type = 728  # maisveld
            elif rand == 2:
                new_type = 729  # graanveld
            else:
                new_type = 889  # koeienveld
            """
        elif feature.properties["landuse"] == 2:
            # natural grassland
            new_type = 1000001
            #new_type = 730  # grasland
        elif feature.properties["landuse"] == 3:
            # reed; 'ruigte'
            new_type = 1000003
            #new_type = 742  # riet
        elif feature.properties["landuse"] == 4:
            # shrubs; hard-/softwood
            new_type = 1000004
            #new_type = 898  # struikgewas
            """
            rand = random.randint(1, 2)
            if rand == 1:
                new_type = 753  # mangrovebos
            else:
                new_type = 898  # struikgewas
            """
        elif feature.properties["landuse"] == 5:
            # forest; hard-/softwood
            new_type = 1000005
            #new_type = 440  # loofbomen
            """
            rand = random.randint(1, 2)
            if rand == 1:
                new_type = 440  # loofbomen
            else:
                new_type = 888  # naaldbomen
            """
        elif feature.properties["landuse"] == 6:
            # mixtype class; mix between grass/reed/shrubs/forest
            new_type = 0
        # Note: Values 7 to 9 should not occur.
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
            new_type = 730
        set_function(api_key, feature.properties["tygron_id"], new_type)
    return


if __name__ == '__main__':
    with open('storing_files\\node_grid0.geojson', 'r') as f:
        grid = load(f)
    heightmap = gridmap.create_geotiff(grid)
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
        #set_function(api_key, 60, 1000001)
        #add_standard(api_key)
        #buildings_json = get_buildings(api_key)
        #print(buildings_json)
        #with open('waterbodies_tygron_transformed.geojson') as f:
        #    hexagons = geojson.load(f)
        #hexagons = update_hexagons_tygron_id(api_key, hexagons)
        #set_terrain_type(api_key, hexagons, terrain_type="water")
        #tiff_file = "grid_height_map0.tif"
        filename = 'test_grid_height_map0.tif'
        heightmap_id = set_elevation(filename, api_key)
        #print(heightmap_id)
        #time.sleep(5)
        #filename = 'test_grid_height_map.tif'
        #update_elevation(filename, api_key, heightmap_id)
        #set_function_value(api_key, 6, 12.0, function_value="FLOOR_HEIGHT_M")
        #set_elevation2(heightmap, api_key, start=True)
    """
    tiff_file = "test_grid_height_map0.tif"
    with open(tiff_file, 'rb') as f:
        heightmap = f.read()
    print(heightmap)
    """
