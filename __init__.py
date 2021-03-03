import os
import re

from math import atan, sqrt, cos, sin

from .abaqus_inp_parser import read_inp
from .gmsh_pos_parser import read_pos_file, read_pos_field_options
from .patran_neutral_parser import read_out
from .samcef_dat_parser import read_dat

from .patran_results_parser import read_rpt
from .xfem_front_parser import read_sif_file, get_front_indices
from .xfem_log_parser import write_log_report

from .samres_results_reader import (get_group_names_from_file,
                                    start_extraction_reac_xfem,
                                    create_reac_report_xfem)


class FEMReader(object):

    ReaderFromMeshFormatDict = {'patran': read_out,
                                'samcef': read_dat,
                                'abaqus': read_inp,
                                'gmsh': read_pos_file}

    ReaderFromFileExtensionDict = {'.out': read_out,
                                   '.dat': read_dat,
                                   '.inp': read_inp,
                                   '.pos': read_pos_file}

    def __init__(self):
        super(FEMReader, self).__init__()

    def read_mesh_file(self, mesh_file, mesh_format=None, read_nodes=True, read_elems=True, read_groups=False):
        if mesh_format:
            reader_func = FEMReader.ReaderFromMeshFormatDict[mesh_format]
        else:
            file_extension = os.path.splitext(mesh_file)[-1]
            reader_func = FEMReader.ReaderFromFileExtensionDict[file_extension]
        mesh_dict = reader_func(mesh_file, read_nodes, read_elems, read_groups)
        return mesh_dict

    def read_mesh_result_file(self, mesh_result_file, xf_lips=False):
        file_extension = os.path.splitext(mesh_result_file)[-1]
        if file_extension == '.pos':
            dirname = os.path.dirname(mesh_result_file)
            pos_files = [mesh_result_file]
            # add levres files for xfem if needed
            if xf_lips:
                if os.path.basename(mesh_result_file) == 'DISPLACEMENT-1-0.pos':
                    levre_1 = os.path.join(dirname, 'DISPLACEMENT-1-1.pos')
                    levre_2 = os.path.join(dirname, 'DISPLACEMENT-1-2.pos')
                    pos_files.extend([levre_1, levre_2])
                elif os.path.basename(mesh_result_file) == 'STRESS-1-0.pos':
                    levre_1 = os.path.join(dirname, 'STRESS-1-1.pos')
                    levre_2 = os.path.join(dirname, 'STRESS-1-2.pos')
                    pos_files.extend([levre_1, levre_2])
            _pos_files = [p for p in pos_files if os.path.exists(p)]
            mesh_dict, _field_dict = read_pos_file(_pos_files, read_fields=True)
            field_type = list(_field_dict.keys())[0]
            field_dict = {0: _field_dict[field_type]}
            return mesh_dict, field_dict


class FieldReader(object):

    FieldFormatFromExtension = {'.pos': 'gmsh',
                                '.rpt': 'patran'}

    PosFieldsNamesDict = {'DISPLACEMENT-1-0.pos': 'Déplacements (peau, XFEM)',
                          'DISPLACEMENT-1-1.pos': 'Déplacements (peau, levre 1)',
                          'DISPLACEMENT-1-2.pos': 'Déplacements (peau, levre 2)',
                          'DISPLACEMENT-1-Full.pos': 'Déplacements (XFEM)',
                          'FEDISPLACEMENT-1-0.pos': 'Déplacements (peau, FEM)',
                          'FEDISPLACEMENT-1-Full.pos': 'Déplacements (FEM)',

                          'STRESS-1-0.pos': 'Contraintes (peau, XFEM)',
                          'STRESS-1-1.pos': 'Contraintes (peau, levre 1)',
                          'STRESS-1-2.pos': 'Contraintes (peau, levre 2)',
                          'STRESS-1-Full.pos': 'Contraintes (XFEM)',
                          'FESTRESS-1-0.pos': 'Contraintes (peau, FEM)',
                          'FESTRESS-1-Full.pos': 'Contraintes (FEM)',

                          'temp_xfe.pos': 'Température (XFEM)',
                          'Dtemp_xfe.pos': 'Décalage de température (XFEM)',
                          'tempsam.pos': 'Témperature (FEM)'}

    def __init__(self):
        super(FieldReader, self).__init__()

    def read_field_file(self, field_file, field_format=None, field_type='vector', xf_lips=False):
        if not field_format:
            file_extension = os.path.splitext(field_file)[-1]
            field_format = FieldReader.FieldFormatFromExtension[file_extension]
        if field_format == 'gmsh':
            dirname = os.path.dirname(field_file)
            pos_files = [field_file]
            if xf_lips:
                if os.path.basename(field_file) == 'DISPLACEMENT-1-0.pos':
                    levre_1 = os.path.join(dirname, 'DISPLACEMENT-1-1.pos')
                    levre_2 = os.path.join(dirname, 'DISPLACEMENT-1-2.pos')
                    pos_files.extend([levre_1, levre_2])
                elif os.path.basename(field_file) == 'STRESS-1-0.pos':
                    levre_1 = os.path.join(dirname, 'STRESS-1-1.pos')
                    levre_2 = os.path.join(dirname, 'STRESS-1-2.pos')
                    pos_files.extend([levre_1, levre_2])
            mesh_dict, _field_dict = read_pos_file(pos_files, read_fields=True)
            field_type = list(_field_dict.keys())[0]
            field_dict = {0: _field_dict[field_type]}
            return field_dict
        if field_format == 'patran':
            field_dict = read_rpt(field_file, field_type)
            return field_dict

    def get_pos_field_options(self, pos_file):
        return read_pos_field_options(pos_file)

    def get_pos_field_name(self, pos_file):
        file_name = os.path.basename(pos_file)
        if file_name in self.PosFieldsNamesDict:
            return self.PosFieldsNamesDict[file_name]
        else:
            return file_name

    def get_pos_mesh_name(self, pos_file):
        dir_name = os.path.dirname(pos_file)
        step_str_list = re.findall('step\d+', dir_name)
        if step_str_list:
            step_str = step_str_list[0]
            modele_name = os.path.basename(os.path.dirname(dir_name))
            mesh_name = '{0}_{1}'.format(modele_name, step_str)
        else:
            mesh_name = os.path.basename(pos_file)
        return mesh_name


class XfemFrontReader(object):

    SifName = 'sifs-1.txt'
    SifSmoothName = 'smoothsifs-1.txt'
    InfoPropaName = 'InfoPropa.txt'

    FrontFiles = [SifName,
                  SifSmoothName,
                  InfoPropaName]

    def __init__(self):
        super(XfemFrontReader, self).__init__()

    def read_front_file(self, front_file, dk_coef=1.0, new_curv_coords=None):
        mesh, fields = read_sif_file(front_file, dk_coef, new_curv_coords)
        return mesh, fields

    def read_fronts_for_step(self, step_folder, dk_coef, mu=0.3):
        front_files = [os.path.join(step_folder, name) for name in self.FrontFiles]

        mesh = {}
        fields = {}
        curv_coord = {}

        for front_file in front_files:
            if not os.path.exists(front_file):
                continue

            basename = os.path.basename(front_file)
            if curv_coord and basename == self.InfoPropaName:
                _mesh, _fields = read_sif_file(front_file, dk_coef, new_curv_coords=curv_coord)
            else:
                _mesh, _fields = read_sif_file(front_file, dk_coef)

            if not mesh:
                mesh = _mesh

            for front in _fields:
                if front not in fields:
                    fields[front] = {}
                fields[front].update(_fields[front])

            if 'curv.coord.' in list(_fields.values())[0]:
                curv_coord = {front: _fields[front]['curv.coord.'] for front in _fields}

        for front in fields:
            for coo in ('x', 'y', 'z'):
                fields[front].pop(coo, None)

        for front, cur_fields in fields.items():
            vars_needed = ('K1_smooth', 'K2_smooth', 'K3_smooth')
            if all([k in cur_fields for k in vars_needed]):
                K1 = cur_fields['K1_smooth']
                K2 = cur_fields['K2_smooth']
                K3 = cur_fields['K3_smooth']

                Keqv = []
                Theta_p = []
                for _K1, _K2, _K3 in zip(K1, K2, K3):
                    _Theta_p = 2 * atan((_K1 - sqrt(_K1 ** 2 + 8 * _K2 ** 2)) / (4 * _K2))
                    t2 = _Theta_p / 2
                    _Keqv = sqrt(((_K1 * cos(t2) ** 3) - (3 * _K2 * cos(t2) ** 2) * sin(t2)) ** 2 + (_K3 ** 2) / (1 - mu))
                    Theta_p.append(_Theta_p)
                    Keqv.append(_Keqv)

                _Keqv_moy = sum(Keqv) / len(Keqv)
                Keqv_moy = [_Keqv_moy for i in range(len(Keqv))]

                fields[front]['Keqv (smooth)'] = Keqv
                fields[front]['Theta_p (smooth)'] = Theta_p
                fields[front]['Keqv (smooth-moyenne)'] = Keqv_moy

        return mesh, fields

    def get_front_indices(self, step_folder):
        sif_1 = os.path.join(step_folder, 'sifs-1.txt')
        n_fronts = get_front_indices(sif_1)
        return n_fronts


class SamresReader(object):

    def __init__(self, parent):
        super(SamresReader, self).__init__()
        self.parent = parent

    def get_group_names(self, mesh_file):
        groups = get_group_names_from_file(mesh_file)
        return groups

    def start_extraction_reac_xfem(self, des_files, folder_to_dump, sam_exe, sam_zone):
        return start_extraction_reac_xfem(des_files, folder_to_dump, sam_exe, sam_zone)

    def create_reac_report_xfem(self, folder_to_dump, nom_etude, answer_files, mesh_file, group_names):
        return create_reac_report_xfem(folder_to_dump, nom_etude, answer_files, mesh_file, group_names)
