"""
Create FA map 

"""

import os
from useful import check_file_ext, execute_command

def FA_map(in_dwi, mask):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})

    # Create path for tensor 
    tensor = os.path.join(dir_name, file_name + "_tensor.mif")
    # Check if the file already exist or not 
    if not os.path.exists(tensor):
        cmd = ["dwi2tensor", in_dwi, "-mask", mask, tensor]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch dwi2tensor (exit code {result})"
            return 0, msg, info
        else:
            print(f"Diffusion tensor succesfully created. Output file: {tensor}")
    else:
        print(f"Skipping RF estimation step, {tensor} already exists.")

    # Create path to FA map
    FA_map = os.path.join(dir_name, file_name + "_FA_map.mif")
    # Check if the file already exist or not 
    if not os.path.exists(FA_map):
        cmd = ["tensor2metric", "-fa", FA_map, tensor]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch tensor2metric (exit code {result})"
            return 0, msg, info
        else:
            print(f"FA map succesfully created. Output file: {FA_map}")
    else:
        print(f"Skipping FA map creation step, {FA_map} already exists.")

    return 
