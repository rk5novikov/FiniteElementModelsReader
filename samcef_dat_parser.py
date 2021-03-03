'''
Module with functions for parsing (reading and writing)
of Samcef .dat files
'''


import re
from datetime import datetime
from .common_functions import sci_float, check_num


samcef_elem_types = {2: 'bar',
                     3: 'tria',
                     4: 'quad',
                     5: 'tet',
                     7: 'wedge',
                     9: 'hex',
                     -2: 'bar2',
                     -3: 'tria2',
                     -4: 'quad2',
                     -5: 'tet2',
                     -7: 'wedge2',
                     -9: 'hex2'}


def dat_cur_command(line, prev):
    if line.startswith('.'):
        return line[:4]
    elif line.startswith('!'):
        return 'comment'
    elif 'RETURN' in line:
        return 'RETURN'
    else:
        return prev


def read_dat(datin, read_nodes=1, read_elems=1, read_groups=1):

    exp_group_name = re.compile('"\w+"')

    nodes = {}
    elems = {}
    groups = {}
    dict_elem_types = {}
    set_elem_types = set()
    mesh_dict = {'nodes': {}, 'elems': {}, 'groups': {}}
    with open(datin, 'r', encoding="utf8") as f0:
        cur_command = 'start'
        for line in f0:
            cur_command = dat_cur_command(line, cur_command)
            if read_nodes and cur_command == '.NOE':
                line = next(f0)
                while cur_command == '.NOE':
                    data = list(filter(lambda cell: cell not in [
                                'I', 'X', 'Y', 'Z'], line.split()))
                    nodes[int(data[0])] = [float(data[1]), float(data[2]), float(data[3])]
                    line = next(f0)
                    cur_command = dat_cur_command(line, cur_command)
            if read_elems and cur_command == '.MAI':
                line = next(f0)
                while cur_command == '.MAI':
                    cur_deg = 1
                    while "$" in line:
                        line = line.replace("$", "")
                        line += next(f0)
                    if "-" in line:
                        cur_deg = 2
                    data = line.split()
                    elem_id = int(data[1])
                    elem_nodes = [int(node) for node in data[3:]]
                    if cur_deg == 1:
                        elem_type = samcef_elem_types[len(elem_nodes)]
                    else:
                        elem_nodes_filtered = set(filter(lambda n: n >= 0, elem_nodes))
                        elem_type = samcef_elem_types[-len(elem_nodes_filtered)]
                    dict_elem_types[elem_id] = elem_type
                    if elem_type not in set_elem_types:
                        set_elem_types.add(elem_type)
                        elems[elem_type] = {}
                    corner_nodes = [n_id for n_id in elem_nodes if n_id > 0]
                    mid_nodes = [abs(n_id) for n_id in elem_nodes if n_id < 0]
                    if elem_type == 'wedge2':
                        mid_nodes = mid_nodes[:3] + mid_nodes[6:] + mid_nodes[3:6]
                    if elem_type == 'hex2':
                        mid_nodes = mid_nodes[:4] + mid_nodes[8:] + mid_nodes[4:8]
                    elems[elem_type][elem_id] = corner_nodes + mid_nodes
                    line = next(f0)
                    cur_command = dat_cur_command(line, cur_command)
            if read_groups and cur_command == '.SEL':
                sel_lines = ''
                while cur_command == '.SEL':
                    sel_lines += line
                    line = next(f0)
                    cur_command = dat_cur_command(line, cur_command)
                sel_lines = sel_lines.replace('.SEL', '')
                sel_list = list(filter(lambda sel: not sel.isspace(), sel_lines.split('GROUP ')))
                for sel in sel_list:
                    info, str_entities = [s.strip() for s in sel.split('\n', 1)]
                    try:
                        what = info.split()[1]
                        find_name = exp_group_name.findall(info)
                    except:
                        find_name = ''
                    if find_name:
                        gr_name = find_name[0].split()[-1].strip('"')
                    else:
                        try:
                            gr_name = 'selection_{0:03d}'.format(int(info.split()[0]))
                            counter = int(info.split()[0])
                        except Exception:
                            gr_name = 'selection_{0:03d}'.format(counter+1)
                            counter += 1
                    if (what in ['NOEUDS', 'MAILLES', 'FACES']) and (str_entities.startswith('I') or str_entities.startswith('MAILLE')):
                        if what == 'NOEUDS':
                            groups[gr_name] = {'node': [int(entity) for entity in str_entities.split()[
                                1:] if entity != '$']}
                        else:
                            if what == 'MAILLES':
                                entities = [int(entity) for entity in str_entities.split()[
                                    1:] if entity != '$' and check_num(entity)]
                            else:
                                entities = [int(face.split()[1]) for face in str_entities.split(
                                    '\n') if check_num(face.split()[1])]
                            ent_elem_types = [dict_elem_types[elem_id] for elem_id in entities]
                            pairs = list(zip(entities, ent_elem_types))
                            groups[gr_name] = {elem_type: [e[0] for e in list(
                                filter(lambda el: el[1] == elem_type, pairs))] for elem_type in set(ent_elem_types)}
                    else:
                        print('N\'arrive pas de lire le contenu du groupe {}'.format(gr_name))
    mesh_dict['nodes'] = nodes
    mesh_dict['elems'] = elems
    mesh_dict['groups'] = groups
    return mesh_dict


def write_dat_elem(elem_type, nodes):
    if elem_type == 'tet':
        return 'N {0:d} {1:d} {2:d} 0 {3:d}'.format(*nodes)
    elif elem_type == 'hex':
        return 'N {0:d} {1:d} {2:d} {3:d} 0 {4:d} {5:d} {6:d} {7:d}'.format(*nodes)
    elif elem_type == 'tria':
        return 'N {0:d} {1:d} {2:d}'.format(*nodes)
    elif elem_type == 'quad':
        return 'N {0:d} {1:d} {2:d} {3:d}'.format(*nodes)
    elif elem_type == 'wedge':
        return 'N {0:d} {1:d} {2:d} 0 {3:d} {4:d} {5:d}'.format(*nodes)
    elif elem_type == 'bar':
        return 'N {0:d} {1:d}'.format(*nodes)
    elif elem_type == 'hex2':
        return 'N {0:d} {2:d} {4:d} {6:d} {8:d} {10:d} {12:d} {14:d} 0 -{1:d} -{3:d} -{5:d} -{7:d} -{16:d} -{17:d} -{18:d} -{19:d} 0 -{9:d} 0 -{11:d} 0 -{13:d} 0 -{15:d}'.format(*nodes)
    elif elem_type == 'wedge2':
        return 'N {0:d} {2:d} {4:d} {6:d} {8:d} {10:d} 0 -{1:d} -{3:d} -{5:d} -{12:d} -{13:d} -{14:d} 0 -{7:d} 0 -{9:d} 0 -{11:d}'.format(*nodes)
    elif elem_type == 'tet2':
        return 'N {0:d} {2:d} {4:d} {6:d} -{1:d} -{3:d} 0 -{5:d} 0 -{7:d} 0 -{8:d} 0 -{9:d}'.format(*nodes)
    elif elem_type == 'quad2':
        return 'N {0:d} {2:d} {4:d} {6:d} -{1:d} -{3:d} -{5:d} -{7:d}'.format(*nodes)
    elif elem_type == 'tria2':
        return 'N {0:d} {2:d} {4:d} -{1:d} -{3:d} -{5:d}'.format(*nodes)
    elif elem_type == 'bar2':
        return 'N {0:d} {2:d} -{1:d}'.format(*nodes)
    else:
        print('Type d\'element est inconnu!')
        raise TypeError


def write_dat(outdat, mesh_dict, write_nodes=1, write_elems=1, write_groups=1):

    node_dict = mesh_dict['nodes']
    elem_dict = mesh_dict['elems']
    group_dict = mesh_dict['groups']
    elem_pairs = [(elem_id, write_dat_elem(elem_type, elem_dict[elem_type][elem_id]))
                  for elem_type in elem_dict.keys() for elem_id in elem_dict[elem_type].keys()]
    elem_pairs.sort(key=lambda pair: pair[0])
    #
    date = str(datetime.now().strftime('%d-%m-%y')).ljust(12)
    time = str(datetime.now().strftime('%H:%M:%S')).ljust(12)
    #
    with open(outdat, 'w') as f0:
        f0.write('.INIT &\n')
        f0.write('! DAT is written by mesh.py from smartec python library\n')
        f0.write('! date / time:  {0}{1}\n'.format(date, time))
        f0.write('! LINEAR STATIC (ASEF)\n')
        f0.write('! {0}\n'.format('-' * 40))
        f0.write('.ASEF &\n')
        f0.write('!\n! LINEAR STATIC (ASEF)\n!\n')
        f0.write('MODE I 0 LECT 132 M 1 ECHO 1\n')
        f0.write('!{0}\n! Topology\n!{1}\n'.format('-'*40, '-'*40))
        if write_nodes:
            f0.write('.NOE\n' + '\n'.join(['     I {0:d} X {1} Y {2} Z {3}'.format(node, *[sci_float(
                node_dict[node][i]) for i in range(3)]) for node in sorted(list(node_dict.keys()))]))
            f0.write('\n')
        if write_elems:
            f0.write(
                '.MAI\n' + '\n'.join(['     I {0:d} {1}'.format(e[0], e[1]) for e in elem_pairs]))
            f0.write('\n')
        if write_groups:
            i_gr = 1
            for gr_name in sorted(group_dict.keys()):
                for ent_type in group_dict[gr_name].keys():
                    entities = group_dict[gr_name][ent_type]
                    n = len(entities) + 1
                    if ent_type == 'node':
                        str_ent_1 = 'NOEUDS'
                        str_ent_2 = '_n'
                    else:
                        str_ent_1 = 'MAILLES'
                        str_ent_2 = '_e'
                    f0.write('.SEL GROUP {0:d} {1} NOM "{2}"\n'.format(
                        i_gr, str_ent_1, gr_name+str_ent_2))
                    str_entities = ' '.join(['{0:d}{1}'.format(ent_id, (' $'*int(bool(i % 160)) + '\n')*int(
                        not bool(i % 8))) for ent_id, i in zip(entities, range(1, n))]).rstrip('\n')
                    f0.write(' I ' + str_entities.rstrip('$') + '\n')
                    i_gr += 1
        f0.write('RETURN\n')
