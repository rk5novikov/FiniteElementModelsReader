'''
Module with functions for writing of Patran .els files
'''


from .common_functions import check_num, sci_float


def read_rpt(rptin, rpt_type='scalar'):
    rpt_list = rptin.split(' ')
    res_all_dict = {}
    insts = []
    i = 0
    for rpt in rpt_list:
        with open(rpt, 'r') as f0:
            for line in f0:
                if 'Load Case:' in line:
                    if 'Time step' in line or ' Pas ' in line:
                        inst = float((line.split(':')[-1]).split(r'{')[0])
                        insts.append(inst)
                    elif ' Load case ' in line or ' Cas de charges ' in line:
                        inst = float(line.split(':')[1].split()[-1])
                    else:
                        inst = float(i)
                    while inst in insts:
                        inst += 0.00001
                    insts.append(inst)
                else:
                    data = line.split()
                    check = len(data) > 1 and all([check_num(s) for s in data])
                    if not check:
                        continue
                    entity, res = int(data[0]), [float(s) for s in data[1:]]
                    if rpt_type == 'scalar':
                        res_all_dict[inst][entity] = res[0]
                    else:
                        res_all_dict[inst][entity] = res
    return res_all_dict


def write_template(ifile, tmpl_type='scalar', column='1', pri='MAXRES', sec=''):
    str_path = ifile
    with open(str_path, 'w') as f:
        if tmpl_type == 'scalar':
            f.write('KEYLOC = 0\nTYPE = {0}\nCOLUMN = {1}\nPRI = {2}\nSEC ={3}\nTYPE = END\n'.format(
                tmpl_type, column, pri, sec))
        elif tmpl_type == 'vector':
            f.write('KEYLOC = 0\nTYPE = {0}\nCOLUMN = 1,2,3\nPRI = {2}\nSEC ={3}\nCTYPE = GLOBAL\nTYPE = END\n'.format(
                tmpl_type, column, pri, sec))
        elif tmpl_type == 'tensor':
            f.write('KEYLOC = 0\nTYPE = {0}\nCOLUMN = 1,2,3,4,5,6\nPRI = {2}\nSEC ={3}\nCTYPE = GLOBAL\nTYPE = END\n'.format(
                tmpl_type, column, pri, 'Components'))


def write_ses(ifile, resfile_name, entity='E', tmplfile_name='template.res_tmpl', mode='w'):
    str_path = ifile
    with open(str_path, mode) as f:
        f.write(
            r'resold_import_results("{0}", "{1}", 1E-006, "{2}")'.format(resfile_name, entity, tmplfile_name) + '\n')


def write_res(ifile, entity_type, lc_name, tmpl_type, entities, res_dict):
    str_path = ifile
    with open(str_path, 'w') as f:
        if tmpl_type == 'scalar':
            if entity_type.lower() == 'n':
                f.write('{0}\n       2       0    0.000000E+0       0       1\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    f.write('{0}{1}\n'.format(str(entity).rjust(8),
                                              sci_float(res_dict[entity], prec=5).rjust(13)))
            else:
                f.write('{0}\n1\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    f.write('{0}0\n{1}\n'.format(str(entity).ljust(
                        18), sci_float(res_dict[entity], prec=5)))
        elif tmpl_type == 'vector':
            if entity_type.lower() == 'n':
                f.write('{0}\n       2       0    0.000000E+0       0       3\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    vals_str = ''.join([sci_float(val, prec=5).rjust(13)
                                        for val in res_dict[entity]])
                    f.write('{0}{1}\n'.format(str(entity).rjust(8), vals_str))
            else:
                f.write('{0}\n3\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    vals_str = ''.join([sci_float(val, prec=5).rjust(13)
                                        for val in res_dict[entity]])
                    f.write('{0}0\n{1}\n'.format(str(entity).ljust(18), vals_str))
        elif tmpl_type == 'tensor':
            if entity_type.lower() == 'n':
                f.write('{0}\n       2       0    0.000000E+0       0       6\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    vals_str_1 = ''.join([sci_float(val, prec=5).rjust(13)
                                          for val in res_dict[entity][:5]])
                    vals_str_2 = ''.join([sci_float(val, prec=5).rjust(13)
                                          for val in res_dict[entity][5:]])
                    f.write('{0}{1}\n{2}\n'.format(str(entity).rjust(8), vals_str_1, vals_str_2))
            else:
                f.write('{0}\n6\nX\nNONE\n'.format(lc_name))
                for entity in entities:
                    vals_str_1 = ''.join([sci_float(val, prec=5).rjust(13)
                                          for val in res_dict[entity][:5]])
                    vals_str_2 = ''.join([sci_float(val, prec=5).rjust(13)
                                          for val in res_dict[entity][5:]])
                    f.write('{0}0\n{1}\n{2}\n'.format(
                        str(entity).ljust(18), vals_str_1, vals_str_2))
