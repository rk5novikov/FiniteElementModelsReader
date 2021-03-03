'''
Module for parsing of Samcef Xfem front results files
InfoPropa.txt, sifs.txt, smoothsifs-1.txt
'''


import os

from .utilities import vector_len, vector, lin_interp


smoothing_used_vars = ['J', 'K1', 'K2', 'K3', 'I1', 'I2', 'I3']
coord_vars = ['x', 'y', 'z']
sif_vars = ['DKeq', 'K1', 'K2', 'K3', 'K1_smooth', 'K2_smooth', 'K3_smooth']


def read_sif_file(sif_file, dk_coef=1.0, new_curv_coords=None):
    smooth = 'smoothsifs' in os.path.basename(sif_file)
    smooth_key = '_smooth' if smooth else ''

    print('Lecture du fichier "{}"'.format(sif_file))

    with open(sif_file, 'r') as f0:
        lines = f0.readlines()
    init_labels = lines[0][1:].split()

    labels = []
    for label in init_labels:
        if 'front' in label:
            continue
        if label in smoothing_used_vars:
            _label = label + smooth_key
        else:
            _label = label
        labels.append(_label)

    val_lines = [line for line in lines[1:] if line.strip()]
    table = []
    for line in val_lines:
        vals = [float(val) for val in line.split()]
        table.append(vals)

    n_front_list = sorted(list(set([int(val_line[0]) for val_line in table])))

    cur_mesh = {}
    cur_fields = {}
    for front in n_front_list:
        cur_mesh[front] = {'nodes': {}, 'elems': {}}
        cur_fields[front] = {k: [] for k in labels}

    for val_line in table:
        front = int(val_line[0])
        vals = val_line[1:]
        for label, val in zip(labels, vals):
            if label in sif_vars:
                val = dk_coef * val
            cur_fields[front][label].append(val)

    if 'curv.coord.' not in labels:
        for front, fields in cur_fields.items():
            xs = fields['x']
            ys = fields['y']
            zs = fields['z']
            points = list(zip(xs, ys, zs))
            curv_coord = [0.0, ]
            for i in range(0, len(points) - 1):
                current_coord = curv_coord[-1] + vector_len(vector(points[i], points[i + 1]))
                curv_coord.append(current_coord)
            cur_fields[front]['curv.coord.'] = curv_coord

    if new_curv_coords:
        for front, field in cur_fields.items():
            old_curv_coords = cur_fields[front]['curv.coord.']
            for label, vals in field.items():
                if label in coord_vars:
                    continue
                old_field = list(zip(old_curv_coords, vals))
                new_field = [lin_interp(coo, old_field) for coo in new_curv_coords[front]]
                cur_fields[front][label] = new_field
            cur_fields[front]['curv.coord.'] = new_curv_coords[front]

    for front, fields in cur_fields.items():
        xs = fields['x']
        ys = fields['y']
        zs = fields['z']
        node_id = 0
        nodes = {}
        elems = {}
        for x, y, z in zip(xs, ys, zs):
            nodes[node_id] = (x, y, z)
            node_id += 1
        elem_id = 0
        for elem_id in range(0, len(nodes) - 1):
            elems[elem_id] = [elem_id, elem_id + 1]
        cur_mesh[front]['nodes'] = nodes
        cur_mesh[front]['elems'] = {'bar': elems}

    return cur_mesh, cur_fields


def get_front_indices(sif_file):
    with open(sif_file, 'r') as f0:
        lines = f0.readlines()

    val_lines = [line for line in lines[1:] if line.strip()]

    fronts = []
    for line in val_lines:
        fronts.append(int(line.split()[0]))

    n_front_list = sorted(list(set(fronts)))

    return n_front_list
