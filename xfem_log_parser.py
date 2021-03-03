'''
Module for parsing of Samcef Xfem log file
It's used to create graph and report based
on log file. This report is used to analyse
quality of results per step. Main metric is
value of ecart KIaux
'''


import re


float_expr = r"\-?\d+\.?\d*(?i:E\-?\+?\d+)?"
split_pattern = "Start STEP \d+"


keys = ["Front length = ",
        " width: ",
        "\nradius: ",
        " size_width: ",
        "size_radius: ",
        "MAXIMUM CRACK GROWTH INCREMENT=",

        "Number of elements after refinement: ",
        "NUMBER OF CLASSICAL DOF ",
        "NUMBER OF ENRICHMENT DOF",
        "TOTAL NUMBER OF DEGREES OF FREEDOM: ",

        "Step Time:",
        "TIME FOR CRACK PROJECTION ",
        "TIME FOR MESH REFINEMENT ",
        "TIME TO COMPUTE THE STRESS INTENSITY FACTORS ",

        "MATRIX COMPUTATION TIME ",
        "TIME TO GENERATE ELEMENTARY MATRIX:",
        "MATRIX GENERATION GLOBAL Time:",

        "norm:",
        "mode I:",
        "mode II:",
        "mode III:",
        "AVERAGE ENERGY RELEASE RATE: ",

        "PROBLEM SIZE: ",
        "TIME TO EXPORT FIELDS "]


labels = ["Step",
          "Front length (L)",
          "Width Remesh",
          "Radius Remesh",
          "Size Radius Remesh (ref_front)",
          "Size Width Remesh (ref_surf)",
          "MAX CRACK GROWTH INCREMENT da",
          "Number of Element after refinement",
          "NUMBER OF CLASSICAL DOF",
          "NUMBER OF ENRICHMENT DOF",
          "TOTAL NUMBER OF DEGREES OF FREEDOM",
          "Step Time",
          "TIME FOR CRACK PROJECTION",
          "TIME FOR MESH REFINEMENT",
          "TIME TO COMPUTE THE SIF",
          "MATRIX COMPUTATION TIME",
          "TIME TO GENERATE ELEMENTARY MATRIX",
          "MATRIX GENERATION GLOBAL Time",
          "Max_tot",
          "ModeI",
          "ModeII",
          "ModeIII",
          "AVERAGE ENERGY RELEASE RATE",
          "PROBLEM SIZE",
          "TIME TO EXPORT FIELDS"]


def write_log_report(report_path, log_file):
    _res_table = []
    _res_table.append(labels)

    with open(log_file, 'r') as f0:
        s = f0.read()

    blocks = re.split(split_pattern, s)[1:]
    for block in blocks:
        find_step = re.findall('End of step (\d+)', block)
        if not find_step:
            continue
        step = find_step[-1]
        cur_line = [step, ]
        for k in keys:
            search_key = "{}\s*{}".format(k, float_expr)
            find = re.findall(search_key, block)
            if find:
                val = re.findall(float_expr, find[-1])[-1]
            else:
                val = ''
            cur_line.append(val)
        _res_table.append(cur_line)

        res_table = []
        n_colums = len(_res_table[0])
        for i in range(n_colums):
            new_line = []
            for line in _res_table:
                new_line.append(line[i])
            res_table.append(new_line)

    tables = [res_table[:7],
              res_table[7:11],
              res_table[11:15],
              res_table[15:18],
              res_table[18:23],
              res_table[23:]]

    with open(report_path, 'w') as f1:
        for table in tables:
            for line in table:
                s = ';'.join(line) + '\n'
                f1.write(s)
            f1.write('\n\n')

    return report_path
