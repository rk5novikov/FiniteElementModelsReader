'''
Module with functions for parsing (reading and writing)
of Gmsh pos binary files
'''

import os
import struct


# Gmsh-style data keys
keys_names = ['SCALAR_POINTS',
              'VECTOR_POINTS',
              'TENSOR_POINTS',
              'SCALAR_LINES',
              'VECTOR_LINES',
              'TENSOR_LINES',
              'SCALAR_TRIANGLES',
              'VECTOR_TRIANGLES',
              'TENSOR_TRIANGLES',
              'SCALAR_QUADRANGLES',
              'VECTOR_QUADRANGLES',
              'TENSOR_QUADRANGLES',
              'SCALAR_TETRAHEDRA',
              'VECTOR_TETRAHEDRA',
              'TENSOR_TETRAHEDRA',
              'SCALAR_HEXAHEDRA',
              'VECTOR_HEXAHEDRA',
              'TENSOR_HEXAHEDRA',
              'SCALAR_PRISMS',
              'VECTOR_PRISMS',
              'TENSOR_PRISMS',
              'SCALAR_PYRAMIDS',
              'VECTOR_PYRAMIDS',
              'TENSOR_PYRAMIDS',
              'SCALAR_LINES2',
              'VECTOR_LINES2',
              'TENSOR_LINES2',
              'SCALAR_TRIANGLES2',
              'VECTOR_TRIANGLES2',
              'TENSOR_TRIANGLES2',
              'SCALAR_QUADRANGLES2',
              'VECTOR_QUADRANGLES2',
              'TENSOR_QUADRANGLES2',
              'SCALAR_TETRAHEDRA2',
              'VECTOR_TETRAHEDRA2',
              'TENSOR_TETRAHEDRA2',
              'SCALAR_HEXAHEDRA2',
              'VECTOR_HEXAHEDRA2',
              'TENSOR_HEXAHEDRA2',
              'SCALAR_PRISMS2',
              'VECTOR_PRISMS2',
              'TENSOR_PRISMS2',
              'SCALAR_PYRAMIDS2',
              'VECTOR_PYRAMIDS2',
              'TENSOR_PYRAMIDS2']

number_of_values_dict = {'SCALAR': 1,
                         'VECTOR': 3,
                         'TENSOR': 9}

number_of_nodes_dict = {'POINTS': 1,
                        'LINES': 2,
                        'TRIANGLES': 3,
                        'QUADRANGLES': 4,
                        'TETRAHEDRA': 4,
                        'HEXAHEDRA': 8,
                        'PRISMS': 6,
                        'PYRAMIDS': 5,
                        'LINES2': 3,
                        'TRIANGLES2': 6,
                        'QUADRANGLES2': 8,
                        'TETRAHEDRA2': 10,
                        'HEXAHEDRA2': 20,
                        'PRISMS2': 15,
                        'PYRAMIDS2': 13}

# Dictionary for convert gmsh-style element type key to module 'mesh.py' element type key
gmsh_type_to_mesh_type = {'LINES': 'bar',
                          'TRIANGLES': 'tria',
                          'QUADRANGLES': 'quad',
                          'TETRAHEDRA': 'tet',
                          'HEXAHEDRA': 'hex',
                          'PRISMS': 'wedge',
                          'LINES2': 'bar2',
                          'TRIANGLES2': 'tria2',
                          'QUADRANGLES2': 'quad2',
                          'TETRAHEDRA2': 'tet2',
                          'HEXAHEDRA2': 'hex2',
                          'PRISMS2': 'wedge2'}


def tensor_from_full_to_sym(tensor):
    return [tensor[j] for j in [0, 4, 8, 1, 5, 2]]


def read_values_block(values_block, block_type, block_size, start_node_id=1, start_elem_id=1):
    offset = 12
    data_type = block_type.split('_')[0]
    data_type_key = data_type.lower()
    elem_type = block_type.split('_')[1]
    #
    num_values = number_of_values_dict[data_type]
    num_nodes = number_of_nodes_dict[elem_type]
    #
    if elem_type in gmsh_type_to_mesh_type:
        mesh_elem_type = gmsh_type_to_mesh_type[elem_type]
    else:
        print("Attention! Des éléments de type {0} ont été trouvés dans le fichier .pos.".format(elem_type))
        print("Ce type n'est pas supporté pour l'importation vers patran!")
        mesh_elem_type = elem_type.lower()
    #
    vals_in_row = num_nodes * 3 + num_nodes * num_values
    nodes = {}
    elems = {mesh_elem_type: {}}
    field_dict = {data_type_key: {}}
    node_id = start_node_id
    elem_id = start_elem_id
    #
    for i in range(block_size):
        line_binary = values_block[8 * i * vals_in_row + offset: 8 * (i + 1) * vals_in_row + offset]
        line_doubles = struct.unpack('d' * vals_in_row, line_binary)
        #
        xs = line_doubles[:num_nodes]
        ys = line_doubles[num_nodes:2 * num_nodes]
        zs = line_doubles[2 * num_nodes:3 * num_nodes]
        #
        elems[mesh_elem_type][elem_id] = list(range(node_id, node_id + num_nodes))
        elem_id += 1
        for i_res, coords in enumerate(zip(xs, ys, zs)):
            nodes[node_id] = coords
            start_index = 3 * num_nodes + i_res * num_values
            end_index = 3 * num_nodes + (i_res + 1) * num_values
            cur_field = line_doubles[start_index:end_index]
            if len(cur_field) == 1:
                field_dict[data_type_key][node_id] = cur_field[0]
            elif len(cur_field) == 9:
                # field_dict[data_type_key][node_id] = tensor_from_full_to_sym(cur_field)
                field_dict[data_type_key][node_id] = cur_field
            else:
                field_dict[data_type_key][node_id] = cur_field
            node_id += 1
    mesh_dict = {'nodes': nodes, 'elems': elems, 'groups': {}}
    return mesh_dict, field_dict, node_id, elem_id


def read_pos_file(pos_files, read_nodes=True, read_elems=True, read_groups=True, read_fields=False):
    if type(pos_files) is str:
        _pos_files = (pos_files, )
    else:
        _pos_files = pos_files

    mesh_dict = {'nodes': {}, 'elems': {}, 'groups': {}}
    field_dict = {}

    start_node_id = 1
    start_elem_id = 1

    cur_node_id = start_node_id
    cur_elem_id = start_elem_id

    for pos_file in _pos_files:
        folder = os.path.dirname(pos_file)
        name = os.path.basename(pos_file)
        print('Lecture du fichier {0}/{1}.'.format(folder, name))
        with open(pos_file, 'rb') as f0:
            content = f0.read()
        data_blocks = content.split(b'\n', 5)
        keys_block = data_blocks[-2]
        keys_block_str = str(keys_block).strip('\'\"')
        all_keys_list = [int(val.strip()) for val in keys_block_str.split()[-28:]]
        existing_keys_list = [(k, v) for k, v in zip(keys_names, all_keys_list) if v]

        if not len(existing_keys_list):
            print('Fichier vide!')
            return None

        i_block = 0
        for block_type, block_size in existing_keys_list:
            print('Lecture de la partie du type {0} en cours.'.format(block_type))
            values_block = data_blocks[5 + i_block]
            _mesh_dict, _field_dict, max_node_id, max_elem_id = read_values_block(values_block,
                                                                                  block_type,
                                                                                  block_size,
                                                                                  cur_node_id,
                                                                                  cur_elem_id)
            # updating mesh . . .
            if read_nodes:
                mesh_dict['nodes'].update(_mesh_dict['nodes'])
            if read_elems:
                for mesh_elem_type in _mesh_dict['elems']:
                    if mesh_elem_type in mesh_dict['elems']:
                        mesh_dict['elems'][mesh_elem_type].update(_mesh_dict['elems'][mesh_elem_type])
                    else:
                        mesh_dict['elems'][mesh_elem_type] = _mesh_dict['elems'][mesh_elem_type]
            if read_fields:
                # updating fields . . .
                for field_type, field in _field_dict.items():
                    if field_type in field_dict:
                        field_dict[field_type].update(field)
                    else:
                        field_dict[field_type] = field
            cur_node_id = max_node_id + 1
            cur_elem_id = max_elem_id + 1
            i_block += 1
    if read_fields:
        return mesh_dict, field_dict
    else:
        return mesh_dict


def read_pos_field_options(pos_file, only_first=True):
    with open(pos_file, 'rb') as f0:
        content = f0.read()
    data_blocks = content.split(b'\n', 5)
    keys_block = data_blocks[-2]
    keys_block_str = str(keys_block).strip('\'\"')
    all_keys_list = [int(val.strip()) for val in keys_block_str.split()[-28:]]
    existing_keys_list = [(k, v) for k, v in zip(keys_names, all_keys_list) if v]
    if only_first:
        return existing_keys_list[0]
    else:
        return existing_keys_list
