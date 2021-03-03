'''
Module with functions for parsing (reading and writing)
of Patran neutral files
'''


import os
import re
from datetime import datetime

from .common_functions import check_num, sci_float


patran_elem_types = {2: 'bar',
                     3: 'tria',
                     4: 'quad',
                     5: 'tet',
                     7: 'wedge',
                     8: 'hex',
                     -2: 'bar2',
                     -3: 'tria2',
                     -4: 'quad2',
                     -5: 'tet2',
                     -7: 'wedge2',
                     -8: 'hex2'}

patran_elem_size = {'bar': 2,
                    'tria': 3,
                    'quad': 4,
                    'tet': 4,
                    'wedge': 6,
                    'hex': 8}

patran_entity_types = {5: 'node',
                       6: 'bar',
                       7: 'tria',
                       8: 'quad',
                       9: 'tet',
                       11: 'wedge',
                       12: 'hex',
                       19: 'coords',
                       22: 'mpc',
                       106: 'bar2',
                       107: 'tria2',
                       108: 'quad2',
                       109: 'tet2',
                       111: 'wedge2',
                       112: 'hex2'}

patran_elem_types_ = {patran_elem_types[k]: k for k in patran_elem_types}
patran_entity_types_ = {patran_entity_types[k]: k for k in patran_entity_types}


def is_node_block(line):
    return line.startswith(' 1')


def is_elem_block(line):
    return line.startswith(' 2')


def is_group_block(line):
    return line.startswith('21')


def is_finish_line(line):
    return line.startswith('99')


def read_out(outin, read_nodes=True, read_elems=True, read_groups=True):

    nodes = {}
    elems = {}
    groups = {}
    elem_types = set()
    mesh_dict = {'nodes': {}, 'elems': {}, 'groups': {}}
    float_expr = r"\-?\d+\.?\d*(?i:E\-?\+?\d+)?"
    with open(outin, 'r', encoding="utf8") as f0:
        for line in f0:
            data = line.split()
            if data:
                if is_finish_line(line):
                    break
                if read_nodes and is_node_block(line):
                    node_id = int(line[2:11].strip())
                    coo_str = next(f0)
                    coords = re.findall(float_expr, coo_str)
                    nodes[node_id] = [float(coords[0]), float(coords[1]), float(coords[2])]
                    next(f0)
                if read_elems and is_elem_block(line):
                    next(f0)
                    elem_id = int(line[2:11].strip())
                    elem_type = patran_elem_types[int(line[11:18].strip())]
                    block_size = int(int(line[18:26].strip()))
                    elem_nodes = []
                    for i in range(block_size - 1):
                        cur_str = next(f0)
                        elem_nodes_cur = [int(cur_str[j*8:(j+1)*8].strip())
                                          for j in range(10) if check_num(cur_str[j*8:(j+1)*8].strip())]
                        elem_nodes.extend(elem_nodes_cur)
                    elem_nodes = [node for node in elem_nodes if node]
                    if len(elem_nodes) > patran_elem_size[elem_type]:
                        elem_type = elem_type + '2'
                    if elem_type not in elem_types:
                        elem_types.add(elem_type)
                        elems[elem_type] = {}
                    elems[elem_type][elem_id] = elem_nodes
                if read_groups and is_group_block(line):
                    block_size = int(data[3])
                    group_name = next(f0).strip()
                    groups[group_name] = {}
                    group_entity_types = set()
                    for i in range(block_size - 1):
                        cur_line = [int(s) for s in next(f0).split() if int(s) != 0]
                        for j in range(0, len(cur_line), 2):
                            try:
                                cur_type = patran_entity_types[cur_line[j]]
                                cur_ent = cur_line[j+1]
                                if cur_type not in group_entity_types:
                                    group_entity_types.add(cur_type)
                                    groups[group_name][cur_type] = []
                                groups[group_name][cur_type].append(cur_ent)
                            except Exception as e:
                                pass
    mesh_dict['nodes'] = nodes
    mesh_dict['elems'] = elems
    mesh_dict['groups'] = groups
    return mesh_dict


def count_lines(array, ncolumns):
    return len(array) // ncolumns + int(bool(len(array) % ncolumns))


def rest_columns(array, ncolumns):
    return ncolumns * int(bool(len(array) % ncolumns)) - len(array) % ncolumns


def out_elem_lines(nodes):
    return '\n'.join([''.join([str(node).rjust(8) for node in nodes[10*i:10*(i+1)]]) for i in range(count_lines(nodes, 10))])


def out_group_lines(pairs):
    return '\n'.join([''.join([str(pair[0]).rjust(8)+str(pair[1]).rjust(8) for pair in pairs[5*i:5*(i+1)]])
                      for i in range(count_lines(pairs, 5))]) + '0'.rjust(8)*2*(rest_columns(pairs, 5))


def write_out(outout, mesh_dict, write_nodes=True, write_elems=True, write_groups=True):

    n_nodes = len(mesh_dict['nodes'])
    n_elems = sum([len(mesh_dict['elems'][k]) for k in mesh_dict['elems'].keys()])
    date = str(datetime.now().strftime('%d-%m-%y')).ljust(12)
    time = str(datetime.now().strftime('%H:%M:%S')).ljust(12)
    ver = '3.0'.rjust(8)
    with open(outout, 'w') as f0:
        f0.write('25       0       0       1       0       0       0       0       0\n')
        f0.write('P3/PATRAN Neutral File from: {0}'.format(os.path.abspath(outout))[0:80] + '\n')
        f0.write('26       0       0       1{0}{1}{2}\n'.format(
            str(n_nodes).rjust(8), str(n_elems).rjust(8), '0'.rjust(8)*3))
        f0.write('{0}{1}{2}\n'.format(date, time, ver))
        if mesh_dict['nodes'] and write_nodes:
            node_ids = list(mesh_dict['nodes'].keys())
            node_ids.sort()
            for node_id in node_ids:
                f0.write(' 1{0}{1}{2}{3}\n'.format(str(node_id).rjust(
                    8), '0'.rjust(8), '2'.rjust(8), '0'.rjust(8)*5))
                f0.write(''.join([sci_float(coo, prec=9, exp_digits=1).rjust(16)
                                  for coo in mesh_dict['nodes'][node_id]]) + '\n')
                f0.write('1G       6       0       0  000000\n')
        if mesh_dict['elems'] and write_elems:
            elem_dict = {}
            for elem_type in mesh_dict['elems'].keys():
                elem_dict.update({k: (abs(patran_elem_types_[
                                 elem_type]), mesh_dict['elems'][elem_type][k]) for k in mesh_dict['elems'][elem_type].keys()})
            elem_ids = list(elem_dict.keys())
            elem_ids.sort()
            for elem_id in elem_ids:
                elem_type = elem_dict[elem_id][0]
                elem_nodes = elem_dict[elem_id][1]
                block_size = 1 + count_lines(elem_nodes, 10)
                f0.write(' 2{0}{1}{2}{3}\n'.format(str(elem_id).rjust(8), str(
                    abs(elem_type)).rjust(8), str(block_size).rjust(8), '0'.rjust(8)*5))
                f0.write('{0}{1}{2}\n'.format(str(len(elem_nodes)).rjust(8),
                                              '0'.rjust(8)*3, sci_float(0, prec=9, exp_digits=2).rjust(16)*3))
                f0.write('{0}\n'.format(out_elem_lines(elem_nodes)))
        if mesh_dict['groups'] and write_groups:
            i_gr = 1
            group_dict = mesh_dict['groups']
            groups = list(group_dict.keys())
            groups.sort()
            for group in groups:
                node_pairs = []
                elem_pairs = []
                for ent_type in group_dict[group].keys():
                    cur_pairs = [(patran_entity_types_[ent_type], entity)
                                 for entity in group_dict[group][ent_type]]
                    if ent_type == 'node':
                        node_pairs = cur_pairs
                    else:
                        elem_pairs.extend(cur_pairs)
                node_pairs.sort(key=lambda pair: pair[1])
                elem_pairs.sort(key=lambda pair: pair[1])
                pairs = node_pairs + elem_pairs
                block_size = 1 + count_lines(pairs, 5)
                f0.write('21{0}{1}{2}{3}\n'.format(str(i_gr).rjust(8), str(
                    2 * len(pairs)).rjust(8), str(block_size).rjust(8), '0'.rjust(8)*5))
                f0.write('{0}\n'.format(group))
                f0.write('{0}\n'.format(out_group_lines(pairs)))
                i_gr += 1
        f0.write('99       0       0       1       0       0       0       0       0\n')
