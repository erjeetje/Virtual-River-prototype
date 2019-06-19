import numpy as np

def dflowfm_compute(data):
    """compute variables that are missing/buggy/not available"""
    numk = data['zk'].shape[0]
    data['numk'] = numk
    # fix shapes
    for var_name in dflowfm_vars:
        arr = data[var_name]
        if arr.shape[0] == data['numk']:
            data[var_name] = arr[:data['numk']]
        elif arr.shape[0] == data['ndx']:
            "should be of shape ndx"
            # ndxi:ndx are the boundary points
            # (See  netcdf write code in unstruc)
            data[var_name] = arr[:data['ndxi']]
            # data should be off consistent shape now
        elif arr.shape[0] == data['ndxi']:
            # this is ok
            pass
        else:
            msg = "unexpected data shape %s for variable %s" % (
                arr.shape,
                var_name
            )
            raise ValueError(msg)
        # compute derivitave variables, should be consistent shape now.
    data['is_wet'] = data['s1'] > data['bl']

def update_height_dflowfm(idx, height_nodes_new, data, model):
    nn = 0
    for i in np.where(idx)[0]:
        # Only update model where the bed level changed (by compute_delta_height)
        if height_nodes_new[i] < data['bedlevel_update_maximum'] and np.abs(height_nodes_new[i] - data['HEIGHT_NODES'][i]) > data['bedlevel_update_threshold']:
            nn += 1
            model.set_var_slice('zk', [int(i+1)], [1], height_nodes_new[i:i + 1])
    print('Total bed level updates', nn)

#  a list of mappings of variables
# variables are not named consistently between models and between netcdf files and model
dflowfm = {
    "initial_vars": [
        'xzw',
        'yzw',
        'xk',
        'yk',
        'zk',
        'ndx',
        'ndxi',             # number of internal points (no boundaries)
        'flowelemnode'
    ],
    "vars": ['bl', 'ucx', 'ucy', 's1', 'zk'],
    "mapping": dict(
        X_NODES="xk",
        Y_NODES="yk",
        X_CELLS="xzw",
        Y_CELLS="yzw",
        HEIGHT_NODES="zk",
        HEIGHT_CELLS="bl",
        WATERLEVEL="s1",
        U="ucx",
        V="ucy"
    ),
    "compute": dflowfm_compute,
    "update_nodes": update_height_dflowfm
}
dflowfm["reverse_mapping"] = {value: key for key, value in dflowfm["mapping"].items()}


dflowfm_nc = {
    "initial_vars": [
        'mesh2d_face_x',
        'mesh2d_face_y',
        'mesh2d_node_x',
        'mesh2d_node_y',
        'mesh2d_node_z',
        'time'
    ],
    "vars": ['mesh2d_flowelem_bl', 'mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_s1', 'mesh2d_node_z'],
    "mapping": dict(
        X_NODES="mesh2d_node_x",
        Y_NODES="mesh2d_node_y",
        X_CELLS="mesh2d_face_x",
        Y_CELLS="mesh2d_face_y",
        HEIGHT_NODES="mesh2d_node_z",
        HEIGHT_CELLS="mesh2d_flowelem_bl",
        WATERLEVEL="mesh2d_s1",
        U="mesh2d_ucx",
        V="mesh2d_ucy"
    ),
    "compute": lambda x: x,
    "update_nodes": lambda x: x
}
dflowfm_nc["reverse_mapping"] = {value: key for key, value in dflowfm["mapping"].items()}

available = {
    "dflowfm": dflowfm,       # from memory
    "dflowfm_nc": dflowfm_nc  # from file
}
