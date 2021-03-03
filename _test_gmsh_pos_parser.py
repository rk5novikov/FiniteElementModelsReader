import os
import glob

from gmsh_pos_parser import number_of_values_dict, read_pos_file
from patran_neutral_parser import write_out, patran_elem_types
from patran_results_parser import write_template, write_ses, write_res


def convert_pos_data_to_patran(pos_name, mesh_dict, field_dict, work_dir=''):
    if not work_dir:
        work_dir = os.getcwd()
    dir_for_files = os.path.join(work_dir, 'pos_to_patran')
    if not os.path.exists(dir_for_files):
        os.mkdir(dir_for_files)
    #
    out_name_abs = os.path.join(dir_for_files, '{0}_mesh.out'.format(pos_name))
    print('Création du {0}_mesh.out à partir des données du fichier .pos . . .'.format(pos_name))
    try:
        write_out(out_name_abs, mesh_dict, write_nodes=True, write_elems=True, write_groups=False)
    except KeyError:
        print('Certains types d’éléments ne sont pas pris en charge et ne seront pas enregistrés dans {0}_mesh.out'.format(
            pos_name))
        elems_filtered = {}
        for elem_type, elems_dict in mesh_dict['elems'].items():
            if elem_type in patran_elem_types:
                elems_filtered[elem_type] = elems_dict
        mesh_dict_filtered = {'nodes': mesh_dict['nodes'],
                              'elems': elems_filtered,
                              'groups': mesh_dict['groups']}
        write_out(out_name_abs, mesh_dict_filtered, write_nodes=True,
                  write_elems=True, write_groups=False)
    #
    for field_type, field in field_dict.items():
        print('Écrire des fichiers de résultats pour patran. Maillage de référence: {0}_mesh.out'.format(pos_name))
        entities = sorted(list(field.keys()))
        sc_name = '{0}_{1}'.format(pos_name, field_type)
        ses_name = 'load_{0}_{1}.ses'.format(pos_name, field_type)
        tmpl_name = '{0}.res_tmpl'.format(field_type)
        n_comps = number_of_values_dict[field_type.upper()]
        column_str = ','.join([str(i) for i in range(1, n_comps+1)])
        #
        sc_name_abs = os.path.join(dir_for_files, sc_name)
        ses_name_abs = os.path.join(dir_for_files, ses_name)
        tmpl_name_abs = os.path.join(dir_for_files, tmpl_name)
        #
        write_res(sc_name_abs, 'n', pos_name, field_type, entities, field)
        write_ses(ses_name_abs, sc_name, 'N', tmpl_name, mode='w')
        write_template(tmpl_name_abs, tmpl_type=field_type,
                       column=column_str, pri='USER_RES', sec=field_type)


def test_all_files():
    pos_files = glob.glob('tests_data/step0/*.pos')
    for pos_file in pos_files:
        pos_name = os.path.splitext(os.path.basename(pos_file))[0]
        mesh_dict, field_dict = read_pos_file(pos_file)
        convert_pos_data_to_patran(pos_name, mesh_dict, field_dict)


def test_read_tensor():
    pos_files = glob.glob('tests_data/step0/*STRESS*.pos')
    for pos_file in pos_files:
        pos_name = os.path.splitext(os.path.basename(pos_file))[0]
        mesh_dict, field_dict = read_pos_file(pos_file)
        convert_pos_data_to_patran(pos_name, mesh_dict, field_dict)


if __name__ == '__main__':
    print('Start tests...')
    test_all_files()
