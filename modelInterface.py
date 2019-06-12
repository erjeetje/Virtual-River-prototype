# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:21:54 2019

@author: HaanRJ
"""


import time
import pathlib
import geojson
import bmi.wrapper
import mako.template
import matplotlib.pyplot as plt
import numpy as np
import gridMapping as gridmap
import updateRoughness as roughness
from copy import deepcopy


def initialize_model():
    model = bmi.wrapper.BMIWrapper('dflowfm')
    model.initialize(r'C:\Users\HaanRJ\Documents\GitHub\sandbox-fm\models\sandbox\Waal_schematic\waal_with_side.mdu')
    print('model initialized')
    return model


def run_model(model, filled_node_grid, face_grid, hexagons):
    model.get_var('s1')
    #numk = model.get_var('numk')
    #ndx = model.get_var('ndx')
    ndxi = model.get_var('ndxi')
    
    # points, nodes, vertices (corner points)
    xk = model.get_var('xk')
    yk = model.get_var('yk')
    
    # cell centers
    xzw = model.get_var('xzw')
    yzw = model.get_var('yzw')
    
    # on the nodes
    zk = model.get_var('zk')
    
    # on the faces/cells (including boundary points)
    s1 = model.get_var('s1')[:ndxi]
    ucx = model.get_var('ucx')[:ndxi]
    ucy = model.get_var('ucy')[:ndxi]

    s1_t0 = s1.copy()
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
    sc = axes[0].scatter(xzw, yzw, c=s1, edgecolor='none', vmin=0, vmax=6, cmap='jet')
    sc_zk = axes[1].scatter(xk, yk, c=zk, edgecolor='none', vmin=0, vmax=6, cmap='jet')

    plt.show()
    zk_new = np.array([feature.properties['z'] for feature in filled_node_grid['features']])
    for i in range(10):
        model.update()
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(ucx.copy())
        sc_zk.set_array(zk.copy())
        plt.draw()
        plt.pause(0.00001)
    qv = axes[1].quiver(xzw, yzw, ucx, ucy)
    changed = [
            feature
            for feature
            in filled_node_grid.features
            if feature.properties['changed']
    ]
    frcu = model.get_var('frcu')
    test = np.unique(deepcopy(frcu))
    print(test)
    """
    hexagons_by_id = {feature.id: feature for feature in hexagons.features}
    default_landuse = 8
    for feature in filled_node_grid.features:
        feature.properties["landuse"] = default_landuse
        if feature.properties["board"]:
            location = feature.properties["location"]
        else:
            continue
        hexagon = hexagons_by_id[location]
        landuse = hexagon.properties["landuse"]
        # for now use z
        if hexagon.properties['z'] == 0:
            landuse = 9
        else:
            landuse = 8
        feature.properties["landuse"] = landuse
    for feature in filled_node_grid.features:
        friction = landuse_to_friction(feature.properties['landuse'])
        frcu[feature.id] = friction
    """
    if True:
        for feature in changed:
            zk_new = np.array([feature.properties['z']], dtype='float64') * 1.5
            model.set_var_slice(
                    'zk',
                    [feature.id + 1],
                    [1],
                    zk_new
            )
    s0 = s1.copy()
    model.update(60)
    for i in range(50):
        model.update(3)
        axes[0].set_title("{:2f}".format(model.get_current_time()))
        sc.set_array(ucx.copy())
        sc_zk.set_array(zk.copy())
        qv.set_UVC(ucx.copy(), ucy.copy())
        plt.draw()
        plt.pause(0.00001)

    print(model.get_current_time())


def landuse_to_friction(landuse):
    if landuse == 9:
        friction = 1000
    else:
        friction = 1
    return friction

def set_crest_height(model, structure, height, weir_type="groyne"):
    #model.set_compound_field
    """
    subroutine get_compound_field


!> Sets the value for a specific field for a specific item in a set-variable of compound values.
!!
!! For example, all pumping stations in a model may be collected in a single compound variable set, named 'pumps',
!! a single pump selected by its name, and the actual data by its field name.
!!
!! The input value enters as a generic pointer, and will be converted to the required data type, e.g., double.
!! If necessary, use get_compound_field_type and get_compound_field_shape to determine which input is expected.
subroutine set_compound_field(c_var_name, c_item_name, c_field_name, xptr) bind(C, name="set_compound_field")
  !DEC$ ATTRIBUTES DLLEXPORT :: set_compound_field
  use iso_c_binding, only: c_double, c_char, c_loc, c_f_pointer
  use iso_c_utils
  use unstruc_messages
  use m_strucs
  use m_wind

  character(kind=c_char), intent(in) :: c_var_name(*)   !< Name of the set variable, e.g., 'pumps'
  character(kind=c_char), intent(in) :: c_item_name(*)  !< Name of a single item's index/location, e.g., 'Pump01'
  character(kind=c_char), intent(in) :: c_field_name(*) !< Name of the field to get, e.g., 'capacity'
  type(c_ptr), value,     intent(in) :: xptr            !< Pointer (by value) to the C-compatible value data to be set.

  real(c_double), pointer :: x_0d_double_ptr

  integer :: item_index
  integer :: iostat

  ! The fortran name of the attribute name
  character(len=MAXSTRLEN) :: var_name
  character(len=MAXSTRLEN) :: item_name
  character(len=MAXSTRLEN) :: field_name
  ! Store the name
  var_name   = char_array_to_string(c_var_name)
  item_name  = char_array_to_string(c_item_name)
  field_name = char_array_to_string(c_field_name)
   ! Debugging printing only: guess that it's a scalar double value, for now.
   call c_f_pointer(xptr, x_0d_double_ptr)
   write(msgbuf, '(6a,f20.6,a)', iostat=iostat) 'set_compound_field for ', trim(var_name), '(', trim(item_name), ')::', trim(field_name), ', will be set to value = ', x_0d_double_ptr, '.'
   call dbg_flush()
  ! TODO: AvD: include "bmi_set_compound_field.inc"
  select case(var_name)
  ! PUMPS
  case("pumps")
     call getStructureIndex('pumps', item_name, item_index)
     if (item_index == 0) then
         return
     endif
     select case(field_name)
     case("capacity")
         call c_f_pointer(xptr, x_0d_double_ptr)
         qpump(item_index) = x_0d_double_ptr
        return
     end select

  ! WEIRS
  case("weirs")
     call getStructureIndex('weirs', item_name, item_index)
     if (item_index == 0) then
         return
     endif
     select case(field_name)
     case("crest_level", "CrestLevel")
         call c_f_pointer(xptr, x_0d_double_ptr)
         zcgen((item_index-1)*3+1) = x_0d_double_ptr
         return
     case("lat_contr_coeff")
         ! TODO: RTC: AvD: set this in weir params
         return
     end select
     call update_zcgen_widths_and_heights()
    """
    """
    use get_compound_field_type to determine the correct data type.
    subroutine get_compound_field(c_var_name, c_item_name, c_field_name, x) bind(C, name="get_compound_field")
    
    character(kind=c_char), intent(in) :: c_var_name(*)   !< Name of the set variable, e.g., 'pumps'
    character(kind=c_char), intent(in) :: c_item_name(*)  !< Name of a single item's index/location, e.g., 'Pump01'
    character(kind=c_char), intent(in) :: c_field_name(*) !< Name of the field to get, e.g., 'capacity'
    type(c_ptr),            intent(inout) :: x            !< Pointer (by reference) to requested value data, NULL if not available.
    
    integer :: item_index
    
    case("weirs")
    call getStructureIndex('weirs', item_name, item_index)
    if (item_index == 0) then
        return
    endif
    if (item_index <= ncgensg) then 
        ! DFlowFM type structures
        select case(field_name)
        case("crest_level", "CrestLevel")
            x = c_loc(zcgen((item_index-1)*3+1))
            return
        case("lat_contr_coeff")
            ! TODO: RTC: AvD: get this from weir params
            return
        end select
    else
        ! DFlowFM1D type structures
        item_index = item_index - ncgensg
        select case(field_name)
        case("crest_level", "CrestLevel")
            x = get_crest_level_c_loc(network%sts%struct(item_index))  
            return
        case("lat_contr_coeff")
            ! TODO: RTC: AvD: get this from weir params (also for 1d?) 
            return
        end select
    endif
    """
    return


def geojson2pli(collection, name="groyne"):
    """
    convert geojson input (FeatureCollection of linestring features) to a pli file
    """
    structures_template_text = '''
%for feature in features:
[structure]
type                  = weir                # Type of structure
id                    = ${feature.id}              # Name of the structure
polylinefile          = ${feature.properties["pli_path"]}          # *.pli; Polyline geometry definition for 2D structure
crest_level           = ${feature.properties["crest_level"]}            # Crest height in [m]
crest_width           = 
lat_contr_coeff       = 1                   # Lateral contraction coefficient in 
%endfor
    '''
    for feature in collection.features:
        path = pathlib.Path(feature.id)
        pli_path = path.with_suffix('.pli').relative_to(path.parent)
        create_pli(feature, pli_path)
        feature.properties["pli_path"] = pli_path
    structures_template = mako.template.Template(structures_template_text)
    path = pathlib.Path(name)
    structures_path = path.with_suffix('.ini').relative_to(path.parent)
    with structures_path.open('w') as f:
        rendered = structures_template.render(features=collection.features)
        f.write(rendered)


def create_pli(feature, pli_path):
    pli_template_text = '''
${structure_id}
${len(coordinates)} 2
%for point in coordinates:
${point[0]} ${point[1]}
%endfor
'''
    pli_template = mako.template.Template(pli_template_text)
    with pli_path.open('w') as f:
        rendered = pli_template.render(structure_id=feature.id,
                                       coordinates=feature.geometry.coordinates)
        f.write(rendered)


if __name__ == "__main__":
    save = False
    turn = 0
    plt.interactive(True)
    calibration = gridmap.read_calibration()
    t0 = time.time()
    hexagons = gridmap.read_hexagons(filename='storing_files\\hexagons0.geojson')
    for feature in hexagons.features:
        feature.properties["z_changed"] = True
        feature.properties["landuse_changed"] = True
    t1 = time.time()
    print("Read hexagons: " + str(t1 - t0))
    model = initialize_model()
    node_grid = gridmap.read_node_grid()
    face_grid = gridmap.read_face_grid(model)
    t2 = time.time()
    print("Load grid: " + str(t2 - t1))
    node_grid = gridmap.index_node_grid(hexagons, node_grid)
    face_grid = gridmap.index_face_grid(hexagons, face_grid)
    t3 = time.time()
    print("Index grid: " + str(t3 - t2))
    node_grid = gridmap.interpolate_node_grid(hexagons, node_grid)
    hexagons, face_grid = roughness.hex_to_points(model, hexagons, face_grid)
    with open('node_grid_before%d.geojson' % turn, 'w') as f:
        geojson.dump(node_grid, f, sort_keys=True,
                     indent=2)
    t4 = time.time()
    print("Interpolate grid: " + str(t4 - t3))
    filled_node_grid = deepcopy(node_grid)
    filled_hexagons = deepcopy(hexagons)
    filled_hexagons = gridmap.hexagons_to_fill(filled_hexagons)
    t5 = time.time()
    print("Hexagons to fill: " + str(t5 - t4))
    filled_node_grid = gridmap.update_node_grid(filled_hexagons,
                                                filled_node_grid,
                                                fill=True)
    t6 = time.time()
    print("Nodes to fill: " + str(t6 - t5))
    filled_node_grid = gridmap.interpolate_node_grid(filled_hexagons,
                                                     filled_node_grid,
                                                     turn=turn)
    t7 = time.time()
    print("Interpolated filled grid: " + str(t7 - t6))
    if save:
        with open('node_grid_after%d.geojson' % turn, 'w') as f:
            geojson.dump(node_grid, f, sort_keys=True,
                         indent=2)
        with open('filled_node_grid%d.geojson' % turn, 'w') as f:
            geojson.dump(filled_node_grid, f, sort_keys=True,
                         indent=2)
    t8 = time.time()
    if save:
        print("Saved both grids: " + str(t8 - t7))
    gridmap.create_geotiff(node_grid)
    t9 = time.time()
    print("Created geotiff: " + str(t9 - t8))
    run_model(model, filled_node_grid, face_grid, hexagons)
