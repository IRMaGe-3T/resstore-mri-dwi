from useful import execute_command, verify_file
import os
import csv


def getFAstats (FA, ROI_mask, bundle):

    #Create directory for the grid files
    grid_dir = os.path.join(bundle, "grid")
    os.makedirs(grid_dir, exist_ok=True)

    # Create a dictionnary
    d = {} 
    
    # ROI_mask_grid = os.path.join(grid_dir, os.path.basename(ROI_mask).replace(".nii.gz", "_grid.nii.gz"))

    # if not verify_file(ROI_mask_grid):
    #     cmd = ["mrgrid", ROI_mask, "regrid", "-template", FA, ROI_mask_grid, "-interp", "nearest"]
    #     result, stderrl, sdtoutl = execute_command(cmd)

    cmd = ["mrstats", "-mask", ROI_mask, FA]
    result, stderrl, sdtoutl = execute_command(cmd)
    
    res = sdtoutl.split()    
       
    d['FA'] = FA
    d['ROI_mask'] = os.path.basename(ROI_mask).replace(".nii.gz", "")
    d[res[0]]=res[8].decode()
    d[res[1].decode()] = res[10].decode().replace('.', ',')
    d[res[2]]=res[11].decode()
    d[res[3]]=res[12].decode()
    d[res[4]]=res[13].decode()
    d[res[5]]=res[14].decode()
    d[res[6]]=res[15].decode()
    d['mean_FA'] = d[res[1].decode()] 

    return d

def create_or_update_tsv(subject_name, roi_stats, tsv_file):
    # Check if CSV exist
    file_exists = os.path.isfile(tsv_file)

    # Create headers
    roi_headers = [stat['ROI_mask'] for stat in roi_stats]
    roi_headers.sort()  # Sort the ROI headers alphabetically
    expected_headers = ["Subject"] + roi_headers

    # Check if content exist
    if file_exists:
        with open(tsv_file, mode='r') as file:
            reader = csv.reader(file, delimiter='\t')
            existing_data = list(reader)
            if existing_data:
                existing_headers = existing_data[0]
            else:
                existing_headers = []
    else:
        existing_data = []
        existing_headers = []

    # If the file does not have headers, write them
    if not existing_headers:
        existing_data.append(expected_headers)
        existing_headers = expected_headers

    # Match data with header
    if existing_headers != expected_headers:
        header_mapping = {header: index for index, header in enumerate(existing_headers)}
        existing_data[1:] = [
            [row[header_mapping[header]] if header in header_mapping else '' for header in expected_headers]
            for row in existing_data[1:]
        ]

    # Verify if subject is already on the list
    subjects_in_table = {row[0] for row in existing_data[1:]}
    if subject_name in subjects_in_table:
        return  # If there is the subject we skip

    # Create each file
    subject_data = [subject_name] + [stat['mean_FA'] for stat in roi_stats]

    # add subject data excluding headers
    existing_data.append(subject_data)
    
    # Name order of subject
    existing_data[1:] = sorted(existing_data[1:], key=lambda x: x[0])

    # Rewrite all data on the TSV file, by name order and with the proper headers
    with open(tsv_file, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows([expected_headers] + existing_data[1:])