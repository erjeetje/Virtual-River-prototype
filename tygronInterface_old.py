# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 11:25:35 2019

@author: HaanRJ
"""

import os
import requests
import base64
import json
from shapely import geometry
from geojson import FeatureCollection


def join_session(username, password, application_type="EDITOR",
                 api_endpoint=("https://engine.tygron.com/api/event/io/get_my_joinable_sessions/?f=JSON")):
    """
    Login function to Tygron, returns api token on successful login (requires
    a Tygron session to run called 'virtual_river2').
    """
    try:
        sessions_data = requests.post(url=api_endpoint, json=[],
                                      auth=(username, password))
    except requests.exceptions.ConnectionError:
        print("There appears to be no internet connection.")
        return None
    session_id = -1
    print(sessions_data)
    sessions = sessions_data.json()
    for item in sessions:
        if item["name"] == "virtual_river_salti":
            session_id = item["id"]
            break
    print(session_id)
    if session_id > -1:
        join_url = ("https://engine.tygron.com/api/event/io/join/?f=JSON")
        """
        r = requests.post(url=join_url, json=[session_id, application_type,
                          "Virtual River application script"],
                          auth=(username, password))
        """
        r = requests.post(url=join_url, json=[session_id, application_type,
                          "Virtual River application script"],
                          auth=(username, password))
    try:
        pastebin_url = r.json()
        return pastebin_url["apiToken"]
    except UnboundLocalError:
        print("LOGIN FAILED: Received no content from Tygron.")
        return None
    except json.decoder.JSONDecodeError:
        print("LOGIN FAILED: Received faulty response from Tygron.")
        return None


def get_buildings(api_key, api_endpoint=("https://engine.tygron.com/api/"
                                         "session/items/buildings/?f=JSON&"),
            save=False):
    """
    Function to retrieve all building information from Tygron.
    """
    data = requests.get(api_endpoint+api_key)
    buildings_json = data.json()
    if save:
        with open('buildings.json', 'w') as f:
            json.dump(buildings_json, f, sort_keys=True, indent=2)
    return buildings_json


def update_hexagons_tygron_id(api_key, hexagons):
    """
    Function to update the tygron ids of the hexagons.
    
    NOTE: this works now as the name of the hexagons are numbered. Could cause
    problems when adding the groynes and LTDs to tygron, which may not have
    numbers as names to distinguish.
    
    PROPOSED FIX: int(name) --> name and feature.id --> str(feature.id) (test!)
    """
    buildings_json = get_buildings(api_key)
    building_indices = {}
    for building in buildings_json:
        name = building["name"]
        tygron_id = building["id"]
        try:
            building_indices.update({int(name): tygron_id})
        except ValueError:
            print("ERROR: Faulty hexagon name for hexagon with ID " +
                  str(building["id"]) + ". Unable to match hexagon to Tygron" +
                  " id.")
            continue
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
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
    """
    Function to update the values of a function, e.g. the height of trees. This
    should not be necessary to call --> set functions correctly in Tygron.
    """
    r = requests.post(url=api_endpoint+api_key, json=[building_id, function_value, value])
    return


def set_name(api_key, tygron_id, hex_id,
             api_endpoint=("https://engine.tygron.com/api/session/event/"
                           "EditorBuildingEventType/SET_NAME/?")):
    """
    Function to set the name of a hexagon to the correct name (number).
    """
    r = requests.post(url=api_endpoint+api_key, json=[tygron_id, str(hex_id)])
    return


def set_terrain_type(api_key, hexagons):
    """
    Function that updates terrain in Tygron. Mainly, it updates terrain from
    land to water and visa versa. In case of water to land, first changes the
    hexagon terrain to water and then adds a building to it which is
    subsequently updated to a specific land use. In case of land to water,
    first removes any building (the land use) from the hexagon and then changes
    the terrain to water.
    """
    print("Updating terrain in Tygron.")
    water = []
    land = []
    new_land_hexagons = []
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (feature.properties["water"] and feature.properties["z_changed"]):
            shape = geometry.asShape(feature.geometry)
            water.append(shape)
            if feature.properties["tygron_id"] is not None:
                remove_polygon(api_key, feature.properties["tygron_id"], shape)
        elif (feature.properties["land"] and feature.properties["z_changed"]):
            shape = geometry.asShape(feature.geometry)
            land.append(shape)
            new_land_hexagons.append(feature)
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
        print("Water terrain updated in Tygron.")
    r = update_terrain(api_key, becomes_land, terrain_type="land")

    new_land_hexagons = FeatureCollection(new_land_hexagons)
    for feature in new_land_hexagons.features:
        if feature.properties["tygron_id"] is None:
            tygron_id = add_standard(api_key)
            feature.properties["tygron_id"] = tygron_id
            set_name(api_key, tygron_id, feature.id)
        shape = geometry.asShape(feature.geometry)
        add_polygon(api_key, feature.properties["tygron_id"], shape)
        set_function(api_key, feature.properties["tygron_id"], 0)
    try:
        pastebin_url = r.json()
        print(pastebin_url)
    except ValueError:
        print("Land terrain updated in Tygron.")
    return


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
    """
    Obsolete function, may be removed when we are sure it will not be used.
    """
    r = requests.post(url=api_endpoint+api_key, json=[0])
    print("Added standard " + str(r) + " in Tygron.")
    return r.text


def add_section(api_key, hexagon_ids,
                api_endpoint=("https://engine.tygron.com/api/session/event/"
                              "EditorBuildingEventType/ADD_SECTION/?")):
    """
    Obsolete function, may be removed when we are sure it will not be used.
    """
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
        print("UPLOAD FAILED: Received no heightmap id from Tygron.")
    api_endpoint = ("https://engine.tygron.com/api/session/event/"
                    "editormap/set_height_geotiff/?")
    r = requests.post(url=api_endpoint+api_key, json=[heightmap_id])
    return heightmap_id


def update_elevation(tiff_file, api_key, heightmap_id, turn=0,
                     api_endpoint=("https://engine.tygron.com/api/session/"
                                   "event/editorgeotiff/set_geotiff/?")):
    """
    This function should override the initial geotiff and therefore update the
    elevation in tygron. Doesn't seem to work. Workaround right now is to
    upload new geotiffs and set these (this method is therefore not called).
    """
    json = elevation_json(heightmap_id, tiff_file)
    json.append("")
    r = requests.post(url=api_endpoint+api_key, json=json)
    print(r)
    print(r.text)
    try:
        heightmap_id = r.json()
        print(heightmap_id)
    except ValueError:
        print("UPLOAD FAILED: Received no heightmap id from Tygron.")
    return


def set_indicator(score, api_key, indicator="budget", index=0, value=0,
                       api_endpoint=("https://engine.tygron.com/api/session/"
                                     "event/editorindicator/set_attribute/?")):
    if indicator == "flood":
        indicator_id = 0
        excel_id = 1000026
        value_input = ["RED", "YELLOW", "GREEN"]
        for i, count in enumerate(value):
            try:
                r = requests.post(
                        url=api_endpoint+api_key,
                        json=[indicator_id, value_input[i], value[i]])
            except IndexError:
                print("faulty length of values to be sent to the flood safety "
                      "indicator")
                continue
    elif indicator == "biodiversity":
        indicator_id = 1
        excel_id = 1000028
        value_input = ["POTTAX_INI", "POTTAX_UPDATE"]
        for i, count in enumerate(value):
            try:
                r = requests.post(
                        url=api_endpoint+api_key,
                        json=[indicator_id, value_input[i], value[i]])
            except IndexError:
                print("faulty length of values to be sent to the biodiversity "
                      "indicator")
                continue
    else:
        indicator_id = 2
        excel_id = 1000029
        value_input = "COSTS"
        r = requests.post(
                url=api_endpoint+api_key,
                json=[indicator_id, value_input, value])
    score_input = "SCORE_INPUT_" + str(index)
    score_index = "SCORE_INPUT_INDEX"
    r = requests.post(
            url=api_endpoint+api_key, json=[indicator_id, score_input, score])
    r = requests.post(
            url=api_endpoint+api_key, json=[indicator_id, score_index, index])
    """
    # below code was a test, but seems it is not necessary to push a "hard" update.
    if indicator == "biodiversity":
        html = '<img src="http://localhost:8000/biodiversity_score1.png" height="240" width="320">'
        link = "IMAGE_LINK"
        r = requests.post(url=api_endpoint+api_key, json=[indicator_id, link, html])
    """
    api_endpoint=("https://engine.tygron.com/api/session/event/"
                  "editorindicator/set_excel/?")
    r = requests.post(url=api_endpoint+api_key, json=[indicator_id, excel_id])
    return


def set_turn_tracker(turn, api_key,
                       api_endpoint=("https://engine.tygron.com/api/session/"
                                     "event/editorindicator/set_attribute/?")):
    indicator_id = 3
    excel_id = 1000000
    score_input = "TURN"
    r = requests.post(
            url=api_endpoint+api_key, json=[indicator_id, score_input, turn])
    api_endpoint=("https://engine.tygron.com/api/session/event/"
                  "editorindicator/set_excel/?")
    r = requests.post(url=api_endpoint+api_key, json=[indicator_id, excel_id])
    return


def set_indicator_text(string, api_key, indicator="flood",
                       api_endpoint=("https://engine.tygron.com/api/session/"
                                     "event/editorindicator/"
                                     "set_description/?")):
    if indicator == "biodiversity":
        indicator_id = 1
    elif indicator == "budget":
        indicator_id = 2
    else:
        indicator_id = 0
    r = requests.post(url=api_endpoint+api_key, json=[indicator_id, string])
    return


def elevation_json(tiff_id, heightmap):
    """
    Function that creates a base64 string for the geotiff that can be sent to
    tygron to set the elevation.
    """
    tiff_base64 = base64.b64encode(heightmap).decode()
    uploader = "r.j.denhaan@utwente.nl"
    datapackage = [tiff_id, tiff_base64, uploader]
    return datapackage


def hex_to_terrain(api_key, hexagons, updated_hex=[]):
    """
    Function that sets the terrain of the hexagons in tygron.
    
    landuse range between 0 and 9, with a subdivision for 0:
    0: built environment
    1: agriculture; production meadow/crop field
    2: natural grassland
    3: reed; 'ruigte'
    4: shrubs; hard-/softwood
    5: forest; hard-/softwood
    6: mixtype class; mix between grass/reed/shrubs/forest
    7: water body; sidechannel (connected to main channel) or lake
    8: main channel; river bed with longitudinal training dams
    9: main channel; river bed with groynes
    10: dike
    """
    for feature in hexagons.features:
        if feature.properties["ghost_hexagon"]:
            continue
        if (not feature.properties["landuse_changed"] or
            feature.id not in updated_hex):
            continue
        if feature.properties["water"]:
            continue
        if feature.properties["landuse"] == 0:
            # built environment / farm / factory
            # this value should be changed to something that fits better, or a
            # new function based on this type.
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
            # this value should be changed to something that fits better.
            new_type = 730
        set_function(api_key, feature.properties["tygron_id"], new_type)
    print("Updated all land uses in Tygron.")
    return


def main():
    #with open('storing_files\\node_grid0.geojson', 'r') as f:
    #    grid = load(f)
    #heightmap = gridmap.create_geotiff(grid)
    with open(r'C:\Users\HaanRJ\Documents\Storage\username.txt', 'r') as f:
        username = f.read()
    with open(r'C:\Users\HaanRJ\Documents\Storage\password.txt', 'r') as g:
        password = g.read()
    api_key = join_session(username, password)
    if api_key is None:
        print("logging in to Tygron failed, unable to make changes in Tygron")
    else:
        api_key = "token="+api_key
        root_dir = os.path.dirname(os.path.realpath(__file__))
        web_dir = os.path.join(root_dir, 'webserver')
        os.chdir(web_dir)
        set_indicator(0.6, api_key, indicator="biodiversity", index=2)
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
        #filename = 'test_grid_height_map0.tif'
        #heightmap_id = set_elevation(filename, api_key)
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
    return


if __name__ == '__main__':
    main()
