"""
Function for tractogram estimation:
    - 

Parameters:
    - 

Returns:
    -
"""

import os
from useful import check_file_ext, execute_command

def tractogram(in_dwi, mask):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    
    # Generate 5-tissue tissue model
    five_tissue = os.path.join(dir_name, '5tt_nocoreg.mif')
    if not os.path.exists(five_tissue):
        cmd = ["5ttgen", "fsl", in_dwi, five_tissue]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch 5ttgen (exit code {result})"
            return 0, msg, info
        else:
            print(f"5-tissue tissue model succesfully generated. Output file: {five_tissue}")
    else:
        print(f"Skipping 5-tissue generation step, {five_tissue} already exists.")
        
    return 