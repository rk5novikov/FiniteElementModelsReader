'''
Module with functions for use of Samres.exe.
This functions allow easily create queries for
Samcef results binary files (des/fac). In IDEFIX
these functions are used for creation of reaction
reports
'''


import os
import re
import subprocess

from math import sqrt


def read_group_file(group_file, groups=[]):
    group_dict = {}
    with open(group_file, 'r') as f:
        file_str = f.read()
    if file_str[0] == '$':
        blocks = file_str.split('$')[1:]
    else:
        default_block = 'default_group\n' + file_str
        blocks = [default_block, ]
    for block in blocks:
        name = block.split('\n', 1)[0]
        if groups and name not in groups:
            continue
        nodes = [int(s) for s in re.findall('\d+', block)]
        group_dict[name] = nodes
    return group_dict


def read_dat_node_sel(dat_path, groups=[]):
    if groups:
        group_pattern = '{}'.format('|'.join(groups))
    else:
        group_pattern = '\S+'

    pattern = '(.SEL GROUP \d+ NOEUDS NOM "({})"\n[I0-9\$\s]+)'.format(group_pattern)

    with open(dat_path, 'r') as f0:
        s = f0.read()
    raw_blocks = re.findall(pattern, s)

    group_dict = {}
    for raw_block in raw_blocks:
        block = raw_block[0]
        info, group = block.split('\n', 1)
        group_name = re.findall('"\S+"', info)[0].strip('"')
        nodes_str = group.strip()
        nodes_ids = nodes_str[1:].replace('$', ' ')
        ids = [int(_id) for _id in nodes_ids.split()]
        group_dict[group_name] = ids

    return group_dict


def read_out_node_sel(out_path, groups=[]):
    if groups:
        group_pattern = '{}'.format('|'.join(groups))
    else:
        group_pattern = '\S+'

    content_pattern = r"(\s+5\s*\d+)*"

    pattern = '\n21\s+\d+\s+\d+\s+\d+\s+0\s+0\s+0\s+0\s+0\n({})\n({})'.format(group_pattern, content_pattern)

    with open(out_path, 'r') as f0:
        s = f0.read()

    raw_blocks = re.findall(pattern, s)

    group_dict = {}
    for raw_block in raw_blocks:
        group_name, group, _ = raw_block
        node_ids = re.findall('       5\s*(\d+)\s+', group)
        ids = [int(_id) for _id in node_ids]
        group_dict[group_name] = ids

    return group_dict


def read_groups(mesh_file, group_names=[]):
    group_dict = {}

    ext = os.path.splitext(mesh_file)[-1]
    if ext == '.txt':
        group_dict = read_group_file(mesh_file, group_names)
    elif ext == '.dat':
        group_dict = read_dat_node_sel(mesh_file, group_names)
    elif ext == '.out':
        group_dict = read_out_node_sel(mesh_file, group_names)

    return group_dict


def get_group_names_from_file(mesh_file):

    with open(mesh_file, 'r') as f:
        s = f.read()

    ext = os.path.splitext(mesh_file)[-1]
    if ext == '.txt':
        pattern = '\$(\S+)\n'
    elif ext == '.dat':
        pattern = '.SEL GROUP \d+ NOEUDS NOM "(\S+)"\n'
    elif ext == '.out':
        pattern = '\n21\s+\d+\s+\d+\s+\d+\s+0\s+0\s+0\s+0\s+0\n(\S+)'
    else:
        return []

    group_names = re.findall(pattern, s)

    return group_names


# code = 163, 221, 223, 120, 1411, 3431 etc.
# region='All Nodes', 'Group 32', 'Group [BRIDE_1]' or list of nodes
def write_request_file(folder, name, code=221, region='All Nodes'):
    request_path = os.path.join(folder, name)
    if type(region) == list:
        s_list = ['$$GET_VALUE "Code {0}" " " "{1}" " " " "'.format(code, n_id) for n_id in region]
        s = '\n'.join(s_list)
    else:
        s = '$$GET_VALUE "Code {0}" " " "{1}" " " " "'.format(code, region)
    with open(request_path, 'w') as f:
        f.write(s)

    return request_path


def write_request_comands(folder, name, des_files, request_files, answer_files, sam_exe, sam_zone, use_sdb=False):
    if use_sdb:
        sam_bossdb = 'ONLY'
    else:
        sam_bossdb = 'NONE'

    s = ''
    s += 'set SAM_EXE=' + sam_exe
    s += '\nset SAM_ZONE=' + str(sam_zone)
    s += '\nset SAM_BOSSDB=' + sam_bossdb
    s += '\nset SAM_EXE_SAMRES=%SAM_EXE%'
    s += '\nset SAM_SAMPROC=\%SAM_EXE%\samcef.proc'
    s += '\nset SAM_HOME=\%SAM_EXE%'

    for des_file, request_file, answer_file in zip(des_files, request_files, answer_files):
        res_dir = os.path.dirname(des_file)
        basename = os.path.basename(des_file)
        res_name = os.path.splitext(basename)[0][:-3]
        res_file = os.path.join(res_dir, res_name)
        s += '\n%SAM_EXE%/samres NOM={} LCP=as < {} > {} &\n'.format(res_file, request_file, answer_file)

    start_path = os.path.join(folder, name)
    with open(start_path, 'w') as f0:
        f0.write(s)

    return start_path


def start_extraction_reac_xfem(des_files, folder_to_dump, sam_exe, sam_zone=550000000, use_sdb=False):
    request_file = write_request_file(folder_to_dump, 'request_reac_all_nodes.in')
    request_files = [request_file for i in range(len(des_files))]

    answer_files = []
    for des_file in des_files:
        step = os.path.basename(os.path.dirname(des_file))
        answer_file = os.path.join(folder_to_dump, 'reac_all_nodes_{}.out'.format(step))
        answer_files.append(answer_file)

    bat_name = 'start.bat'
    write_request_comands(folder_to_dump, bat_name, des_files, request_files, answer_files, sam_exe, sam_zone, use_sdb)

    p = subprocess.Popen(bat_name, cwd=folder_to_dump, shell=True)
    stdout, stderr = p.communicate()

    return answer_files


# region = 'all nodes', 'group', 'selected nodes'
def read_samres_out(out_path, out_type='vector', region='all nodes'):
    result_dict = {}
    with open(out_path, 'r') as f0:
        lines = f0.readlines()
    if out_type == 'vector' and region == 'all nodes':
        print(lines[3].strip())
        n_ids = int(lines[3].strip())
        ids_block = lines[5:n_ids + 5]
        vals_block = lines[n_ids + 5:]
        _ids = [int(ids_block[i].strip()) for i in range(0, n_ids, 3)]
        for i, _id in enumerate(_ids):
            rx = float(vals_block[i * 3].strip())
            ry = float(vals_block[i * 3 + 1].strip())
            rz = float(vals_block[i * 3 + 2].strip())
            result_dict[_id] = [rx, ry, rz]
    else:
        print('SAMRES result reader: Reading of type {} and region {} not implemented yet'.format(out_type, region))

    return result_dict


def create_reac_report_xfem(folder, etude_name, answer_files, mesh_file=None, group_names=[]):
    comp_table = []
    module_table = []

    group_dict = {}
    if mesh_file:
        group_dict = read_groups(mesh_file, group_names)
    group_names = sorted(list(group_dict.keys()))
    if not group_names:
        group_names = ['default_group']

    comp_titre = ['INDEX', 'STEP']
    module_titre = ['INDEX', 'STEP']
    for gr_name in group_names:
        module_titre.append(gr_name)
        comp_titre.append(gr_name + '.fx')
        comp_titre.append(gr_name + '.fy')
        comp_titre.append(gr_name + '.fz')

    comp_table.append(comp_titre)
    module_table.append(module_titre)

    for i, answer_file in enumerate(answer_files):
        step_name = os.path.basename(answer_file)
        find_step_number = re.findall('step\d+', step_name)
        if find_step_number:
            step = find_step_number[-1]
        else:
            step = i

        comp_line = [i, step]
        module_line = [i, step]
        res_dict = read_samres_out(answer_file)
        for gr_name in group_names:
            sum_rx, sum_ry, sum_rz = 0.0, 0.0, 0.0
            if group_dict:
                node_ids = group_dict[gr_name]
            else:
                node_ids = sorted(list(res_dict.keys()))
            for node_id in node_ids:
                rx, ry, rz = res_dict[node_id]
                sum_rx += rx
                sum_ry += ry
                sum_rz += rz
            total_comps = [sum_rx, sum_ry, sum_rz]
            module = sqrt(sum([c * c for c in total_comps]))

            comp_line.extend(total_comps)
            module_line.append(module)

        comp_table.append(comp_line)
        module_table.append(module_line)

    comp_file = os.path.join(folder, etude_name + '_comp.csv')
    module_file = os.path.join(folder, etude_name + '_module.csv')

    files = (comp_file, module_file)
    tables = (comp_table, module_table)

    for file, table in zip(files, tables):
        with open(file, 'w') as f:
            for line in table:
                s = ';'.join([str(s) for s in line]) + '\n'
                f.write(s)


# if False:
#     res_folder = '\\\\ws81/home/CALCUL/sr00031/ICE_2019_00338_ECM-REV0_ZOOM_fissuration_LCF_XFEM15_DEG2'
#     folder_to_dump = 'e:/usr/Sr00031/PRJ/___XFEM_pour_MCM2/RES/test_script'
#     # mesh_file = '\\\\ws81/home/CALCUL/sr00031/ICE_2019_00338_ECM-REV0_ZOOM_fissuration_LCF_XFEM15_DEG2.dat'
#     mesh_file = '\\\\ws81/home/CALCUL/sr00031/ICE_2019_00338_ECM-REV0_ZOOM_fissuration_LCF_XFEM15_DEG2.dat'

#     sam_exe = os.environ['SAM_EXE']
#     answer_files = start_extraction_reac_xfem(res_folder, folder_to_dump, sam_exe)
#     create_reac_report_xfem(folder_to_dump, 'analyse_reaction', answer_files, mesh_file)
