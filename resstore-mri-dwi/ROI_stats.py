from useful import execute_command, verify_file
import os
import csv


def getFAstats (FA, ROI_mask, bundle):

    # Create a dictionnary
    d = {} 

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

def extract_roi_stats(analysis_directory, FA_MNI):
    # Directory definition
    Tract_dir = os.path.join(analysis_directory, "Tracto")
    tractseg_out_dir = os.path.join(Tract_dir, "tractseg_output")
    bundle = os.path.join(tractseg_out_dir, "bundle_segmentations")

    # All ROIs
    roi_files = [f for f in os.listdir(bundle) if f.endswith('.nii.gz')]
    roi_files.sort()
    roi_stats = []
    for roi_file in roi_files:
        ROI = os.path.join(bundle, roi_file)
        d = getFAstats(FA_MNI, ROI, bundle)
        roi_stats.append(d)

    return roi_stats

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
        return False  # Subject is already in the TSV file

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

    print("\nSubject successfully added to FA stats table.")

    return True  # Subject was added