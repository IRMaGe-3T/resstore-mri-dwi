from useful import execute_command, verify_file
import os
import csv


def getFAstats (FA, ROI_mask, bundle):

    #Create directory for the grid files
    grid_dir = os.path.join(bundle, "grid")
    os.makedirs(grid_dir, exist_ok=True)

    # Create a dictionnary
    d = {} 
    
    ROI_mask_grid = os.path.join(grid_dir, os.path.basename(ROI_mask).replace(".nii.gz", "_grid.nii.gz"))

    if not verify_file(ROI_mask_grid):
        cmd = ["mrgrid", ROI_mask, "regrid", "-template", FA, ROI_mask_grid, "-interp", "nearest"]
        result, stderrl, sdtoutl = execute_command(cmd)

    
    cmd = ["mrstats", "-mask", ROI_mask_grid, FA]
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

    # Si el archivo no tiene encabezado, escribir el encabezado
    if not existing_headers:
        existing_data.append(expected_headers)
        existing_headers = expected_headers
        
    # Asegurarse de que los datos coincidan con el orden de los encabezados
    if existing_headers != expected_headers:
        header_mapping = {header: index for index, header in enumerate(existing_headers)}
        existing_data[1:] = [
            [row[header_mapping[header]] if header in header_mapping else '' for header in expected_headers]
            for row in existing_data[1:]
        ]

    # Verificar si el sujeto ya está en la tabla
    subjects_in_table = {row[0] for row in existing_data[1:]}
    if subject_name in subjects_in_table:
        return  # Si el sujeto ya está presente, no agregar datos adicionales

    # Create each file
    subject_data = [subject_name] + [stat['mean_FA'] for stat in roi_stats]

    # Añadir los datos del sujeto actual a los datos existentes, excluyendo encabezado
    existing_data.append(subject_data)
    
    # Ordenar los datos por el nombre del sujeto (excluyendo el encabezado para la ordenación)
    existing_data[1:] = sorted(existing_data[1:], key=lambda x: x[0])

    # Escribir de nuevo todos los datos en el archivo TSV, ordenados y alineados
    with open(tsv_file, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows([expected_headers] + existing_data[1:])