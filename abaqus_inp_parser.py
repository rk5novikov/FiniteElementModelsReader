'''
Module with functions for parsing (reading and writing)
of abaqus inp files
'''


import os
import re
from datetime import datetime

from .common_functions import sci_float


abaqus_elem_types = {'C3D4': 'tet',
                     'C3D6': 'wedge',
                     'C3D8': 'hex',
                     'C3D8I': 'hex',
                     'C3D8R': 'hex',
                     'C3D10': 'tet2',
                     'C3D15': 'wedge2',
                     'C3D20': 'hex2',
                     'C3D20R': 'hex2',
                     'C3D20RI': 'hex2',
                     'DC3D4': 'tet',
                     'DC3D6': 'wedge',
                     'DC3D8': 'hex',
                     'DC3D10': 'hex',
                     'DC3D15': 'tet2',
                     'DC3D20': 'wedge2',
                     'S3': 'tria',
                     'S3R': 'tria',
                     'S4': 'quad',
                     'S4R': 'quad',
                     'S6': 'tria2',
                     'STRI65': 'tria2',
                     'S8': 'quad2',
                     'S8R': 'quad2',
                     'CPS3': 'tria',
                     'CPS4': 'quad',
                     'CPS6': 'tria2',
                     'CPS8': 'quad2',
                     'CPS8R': 'quad2',
                     'CPE3': 'tria',
                     'CPE4': 'quad',
                     'CPE6': 'tria2',
                     'CPE8': 'quad2',
                     'CPE8R': 'quad2',
                     'CAX3': 'tria',
                     'CAX4': 'quad',
                     'CAX6': 'tria2',
                     'CAX8': 'quad2',
                     'CAX8R': 'quad2',
                     'B31': 'bar',
                     'B32': 'bar2',
                     'B32R': 'bar2'}

abaqus_elem_types_ = {'tet': 'C3D4',
                      'wedge': 'C3D6',
                      'hex': 'C3D8',
                      'tet2': 'C3D10',
                      'wedge2': 'C3D15',
                      'hex2': 'C3D20',
                      'tria': 'S3R',
                      'quad': 'S4R',
                      'bar': 'B31',
                      'tria2': 'STRI65',
                      'quad2': 'S8R',
                      'bar2': 'B32'}


def inp_rjust(num):
    return str(num).rjust(8)


def convert_out_to_inp_elem_list(nodes, elem_type):
    if elem_type == 'tet':
        return nodes
    elif elem_type == 'hex':
        return nodes
    elif elem_type == 'tria':
        return nodes
    elif elem_type == 'quad':
        return nodes
    elif elem_type == 'wedge':
        return nodes
    elif elem_type == 'bar':
        return nodes
    elif elem_type == 'hex2':
        return [*nodes[:12], *nodes[16:], *nodes[-8:-4]]
    elif elem_type == 'wedge2':
        return [*nodes[:9], *nodes[12:], *nodes[9:12]]
    elif elem_type == 'tet2':
        return nodes
    elif elem_type == 'quad2':
        return nodes
    elif elem_type == 'tria2':
        return nodes
    elif elem_type == 'bar2':
        return [nodes[0], nodes[2], nodes[1]]
    else:
        print('Type d\'element est inconnu!')
        raise TypeError


def is_node_block(block_str):
    return block_str.startswith('NODE\n')


def is_elem_block(block_str):
    return block_str.startswith('ELEMENT,')


def is_elset_block(block_str):
    return block_str.startswith('ELSET,')


def is_nset_block(block_str):
    return block_str.startswith('NSET,')


def read_inp(inp_in, read_nodes=1, read_elems=1, read_groups=1):

    float_expr = r"\-?\d+\.?\d*(?i:E\-?\+?\d+)*"
    elem_block_break = re.compile(',\n')

    nodes = {}
    elems = {}
    groups = {}
    dict_elem_types = {}
    elem_types = set()
    mesh_dict = {'nodes': {}, 'elems': {}, 'groups': {}}

    with open(inp_in, 'r') as f0:
        inp_str = '\n'.join([line.strip() for line in f0.readlines() if not line.startswith('**')])
        blocks = inp_str.split('*')
    blocks = inp_str.split('*')
    for block in blocks:
        if read_nodes and is_node_block(block):
            nodes_data = re.findall('(\d+),\s*({0}),\s*({0}),*\s*({0})*\n'.format(float_expr), block)
            nodes.update(
                {int(data[0]):  [float(val) if val else 0.0 for val in data[1:]] for data in nodes_data})
        elif read_elems and is_elem_block(block):
            abaqus_elem_type = re.findall('TYPE=([a-zA-z0-9]+)\s*\n', block)[0]
            if abaqus_elem_type in abaqus_elem_types:
                elem_type = abaqus_elem_types[abaqus_elem_type]
                if elem_type not in elem_types:
                    elem_types.add(elem_type)
                    elems[elem_type] = {}
                elem_block = block.split('\n', 1)[1]
                elem_block_clean = elem_block_break.sub(',', elem_block)
                elems_data = [[int(val_str.strip()) for val_str in line.split(
                    ',') if val_str.strip()] for line in elem_block_clean.split('\n') if line.strip()]
                #
                elems[elem_type].update({data[0]:  convert_out_to_inp_elem_list(
                    data[1:], elem_type) for data in elems_data})
                dict_elem_types.update({int(data[0]): elem_type for data in elems_data})
            else:
                print('Elément du type {0} a été ignoré'.format(abaqus_elem_type))
        elif read_groups and is_elset_block(block):
            gr_name = re.findall('ELSET=([\-_a-zA-z0-9]+)', block)[0]
            ents_str = block.split('\n', 1)[1]
            entities = [int(elem_id) for elem_id in re.findall('(\d+)', ents_str)]
            try:
                ent_elem_types = [dict_elem_types[elem_id] for elem_id in entities]
                pairs = list(zip(entities, ent_elem_types))
                groups[gr_name] = {elem_type: [e[0] for e in list(
                    filter(lambda el: el[1] == elem_type, pairs))] for elem_type in set(ent_elem_types)}
            except:
                print('N\'arrive pas de lire le contenu du groupe {}'.format(gr_name))
        elif read_groups and is_nset_block(block):
            gr_name = re.findall('NSET=([\-_a-zA-z0-9]+)', block)[0]
            ents_str = block.split('\n', 1)[1]
            entities = [int(elem_id) for elem_id in re.findall('(\d+)', ents_str)]
            groups[gr_name] = {'node': entities}
    mesh_dict['nodes'] = nodes
    mesh_dict['elems'] = elems
    mesh_dict['groups'] = groups
    return mesh_dict


def get_inp_elem_line(elem_type, elem_id, nodes):
    _nodes = [node_id for node_id in nodes if node_id]
    if elem_type == 'tet':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'hex':
        return '{0},{1},\n{2}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes[:6]]),
                                        ','.join([inp_rjust(node_id) for node_id in _nodes[6:]]))
    elif elem_type == 'tria':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'quad':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'wedge':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'bar':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'hex2':
        return '{0},{1},\n{2},{3},\n{4}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes[:7]]),
                                                  ','.join([inp_rjust(node_id)
                                                            for node_id in _nodes[7:12]]),
                                                  ','.join([inp_rjust(node_id)
                                                            for node_id in _nodes[16:19]]),
                                                  ','.join([inp_rjust(_nodes[19])] +
                                                           [inp_rjust(node_id) for node_id in _nodes[12:15]] +
                                                           [inp_rjust(_nodes[15]), ]))
    elif elem_type == 'wedge2':
        return '{0},{1},\n{2},{3},{4}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes[:7]]),
                                                ','.join([inp_rjust(node_id)
                                                          for node_id in _nodes[7:9]]),
                                                ','.join([inp_rjust(node_id)
                                                          for node_id in _nodes[12:15]]),
                                                ','.join([inp_rjust(node_id) for node_id in _nodes[9:12]]))
    elif elem_type == 'tet2':
        return '{0},{1},\n{2}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes[:7]]),
                                        ','.join([inp_rjust(node_id) for node_id in nodes[7:]]))
    elif elem_type == 'quad2':
        return '{0},{1},\n{2}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes[:6]]),
                                        ','.join([inp_rjust(node_id) for node_id in _nodes[6:]]))
    elif elem_type == 'tria2':
        return '{0},{1}\n'.format(inp_rjust(elem_id), ','.join([inp_rjust(node_id) for node_id in _nodes]))
    elif elem_type == 'bar2':
        return '{0},{1},{2},{3}\n'.format(inp_rjust(elem_id), inp_rjust(_nodes[0]), inp_rjust(_nodes[2]), inp_rjust(_nodes[1]))
    else:
        print('Type d\'element est inconnu!')
        raise TypeError


def write_inp(outinp, mesh_dict, write_nodes=1, write_elems=1, write_groups=1):
    node_dict = mesh_dict['nodes']
    elem_dict = mesh_dict['elems']
    group_dict = mesh_dict['groups']
    #
    cur_time = str(datetime.now().strftime('%H%M%S %Y%m%d'))
    with open(outinp, 'w') as f0:
        f0.write('*HEADING\n')
        f0.write('{0}  6 (creation time, creation date, unitsys)\n'.format(cur_time))
        f0.write('** if you modify the *HEADING, please modify from the second line and leave the first line\n')
        f0.write('**\n')
        f0.write('** ABAQUS input file is written by mesh.py from smartec python library\n')
        f0.write('** ABAQUS solver add-in version 18,2017,101,1\n')
        f0.write("** JOBNAME IS '{0}'\n".format(os.path.basename(outinp)))
        f0.write('**\n')
        f0.write('**---------------------------------------\n')
        f0.write('** Topology\n')
        f0.write('**---------------------------------------\n')
        # nodes block
        if write_nodes:
            f0.write('*NODE\n')
            n_lines = []
            for node_id in sorted(list(node_dict.keys())):
                str_nodes = [sci_float(node_dict[node_id][i], prec=9).rjust(20) for i in range(3)]
                line = '{0},{1},{2},{3}\n'.format(str(node_id).rjust(8), *str_nodes)
                n_lines.append(line)
            f0.write(''.join(n_lines))
        # elems block
        if write_elems:
            for elem_type in elem_dict.keys():
                cur_elem_dict = elem_dict[elem_type]
                abaqus_elem_type = abaqus_elem_types_[elem_type]
                f0.write('*ELEMENT, TYPE={0}\n'.format(abaqus_elem_type))
                for elem_id in sorted(list(cur_elem_dict.keys())):
                    f0.write(get_inp_elem_line(elem_type, elem_id, cur_elem_dict[elem_id]))
        # group block
        if write_groups:
            for gr_name in sorted(group_dict.keys()):
                for ent_type in group_dict[gr_name].keys():
                    entities = group_dict[gr_name][ent_type]
                    if ent_type == 'node':
                        str_ent_1 = 'NSET'
                    else:
                        str_ent_1 = 'ELSET'
                    f0.write('*{0}, {0}={1}\n'.format(str_ent_1, gr_name))
                    el_lines = [str(ent_id) + ', ' + '\n' * int(bool(not (i+1) % 10)) for i, ent_id in enumerate(entities)]
                    f0.write(''.join(el_lines)[:-2].strip(',') + '\n')
