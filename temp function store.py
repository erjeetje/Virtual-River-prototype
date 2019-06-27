# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 09:46:06 2019

@author: HaanRJ
"""

if feature.id == 0 or feature.id == 1:
            edge = True
            west_edge = True
        else:
            left_hex = hexagons[feature.id - 2]
            shape = geometry.asShape(left_hex.geometry)
            y_hex_left = shape.centroid.y
        try:
            right_hex = hexagons[feature.id + 2]
            shape = geometry.asShape(right_hex.geometry)
            y_hex_right = shape.centroid.y
        except KeyError:
            edge = True
            east_edge = True
        if not edge:
            if y_hex < y_hex_left:
                hex_left_north = True
            else:
                hex_left_north = False
            if y_hex < y_hex_right:
                hex_right_north = True
            else:
                hex_right_north = False
        else:
            if west_edge:
                if y_hex < y_hex_right:
                    hex_left_north = False
                    hex_right_north = True
                else:
                    hex_left_north = True
                    hex_right_north = False
            if east_edge:
                if y_hex < y_hex_left:
                    hex_left_north = True
                    hex_right_north = False
                else:
                    hex_left_north = False
                    hex_right_north = True
        mid_point = [x_hex, y_hex]
        if hex_left_north and hex_right_north:
            # LTD shape: high to high: \_/
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            right_point = [x_top_left, y_top_left]
        elif hex_left_north and not hex_right_north:
            # LTD shape high to low: `-_
            x_top_left = x_hex - x_dist
            y_top_left = y_hex + y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex - y_dist
            right_point = [x_top_left, y_top_left]
        elif not hex_left_north and hex_right_north:
            # LTD shape low to high: _-`
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            y_top_left = y_hex + y_dist
            right_point = [x_top_left, y_top_left]
        else:
            # LTD shape low to high: /`\
            x_top_left = x_hex - x_dist
            y_top_left = y_hex - y_dist
            left_point = [x_top_left, y_top_left]
            x_top_left = x_hex + x_dist
            right_point = [x_top_left, y_top_left]
        line = geojson.LineString([left_point, mid_point, right_point])
        ltd = geojson.Feature(id="LTD" + str(feature.id).zfill(2),
                              geometry=line)
        ltd.properties["active"] = False
        ltd.properties["crest_level"] = 0.0
        structures.append(ltd)