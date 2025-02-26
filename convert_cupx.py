import csv
import os
import re
import shutil
import sys
from pathlib import Path

import binwalk

# Copied and adapted from https://github.com/lordfolken/xcsoar-cupx-converter. Many thank @lordfolken

DATA_DIR = 'data'
OUTPUT_DIR = 'output'
TEMP_DIR = 'temp'

def cpux2xcsoar(cupx_file):
    # generate temporary directory
    temp_dir = Path(__file__).resolve().parent / TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)

    # copy cupx file into temporary directory
    cupx_file_name = os.path.basename(cupx_file)
    cupx_file_path = os.path.join(temp_dir, cupx_file_name)
    shutil.copy(os.path.join(DATA_DIR, cupx_file_name), cupx_file_path)
    cupx_file_extracted_path = os.path.join(temp_dir.name, '_{}.extracted'.format(cupx_file_name))

    # binwalk cupx_file and extract all files
    binwalk.scan(cupx_file_path, quiet=True, signature=True, extract=True)

    # look for *.cup file without case sensitivity
    cup_file_name = None
    for filename in os.listdir(cupx_file_extracted_path):
        if re.search(r'\.cup$', filename, re.IGNORECASE):
            cup_file_name = filename
            break

    # Takes a CUP file in cupx format and converts it to a waypoints_details file.
    with open(os.path.join(cupx_file_extracted_path, cup_file_name), 'r') as cup_file:
        # convert to unix line format
        cup_file_content = cup_file.read().replace('\r\n', '\n').replace('\r', '\n')

    # create output directory
    os.makedirs('output', exist_ok=True)

    CUP_FILENAME = os.path.join(OUTPUT_DIR, '{}.cup'.format(cupx_file_name))
    with open(CUP_FILENAME, 'w') as cup_unix_file:
        cup_unix_file.write(cup_file_content)

    # create output sub directories
    for subdir in ['pics', 'docs']:
        os.makedirs(os.path.join(OUTPUT_DIR, subdir), exist_ok=True)

    # Create a corresponding waypoints_details file
    with open(CUP_FILENAME, 'r') as csv_in_file:
        csv_reader = csv.reader(csv_in_file)
        with open(csv_in_file.name.replace('.cupx.cup', '.wp_details.txt'), 'w') as output_file:
            for row in csv_reader:
                # skip the cup header: "name,code,country,lat,lon,elev,style,rwdir,rwlen,rwwidth,freq,desc,userdata,pics"
                if csv_reader.line_num == 1:
                    try:
                        pics_idx = row.index('pics')
                        code_idx = row.index('code')
                    except:
                        pics_idx = None
                    continue
                # bullet proofing: if the field "pics" does not exist skip the row
                if pics_idx is not None:
                    try:
                        output_file.write('[{}]\n'.format(row[code_idx]))
                        for item in row[pics_idx].split(';'):
                            for dir_ext in [['Pics', '.jpg'], ['Docs', '.pdf']]:
                                if item.endswith(dir_ext[1]):
                                    dir_ext_lc = dir_ext[0].lower()
                                    shutil.copy(os.path.join(cupx_file_extracted_path, dir_ext[0], item),
                                                os.path.join(OUTPUT_DIR, dir_ext_lc, ''))
                                    output_file.write('image={}\n'.format(os.path.join(dir_ext_lc, item)))
                    except:
                        print('Line not parsed:\n', row, 'in file', csv_in_file.name)
                        continue

    # delete temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    cpux2xcsoar(sys.argv[1]) if len(sys.argv > 0) else print('no cupx-file specified')
