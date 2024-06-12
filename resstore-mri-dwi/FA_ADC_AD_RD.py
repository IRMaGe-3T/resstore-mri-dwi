"""
Create FA map 

"""

import os
from useful import check_file_ext, execute_command

def FA_ADC_AD_RD_maps(in_dwi, mask):

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
    ADC_map= os.path.join(dir_name, file_name + "_ADC_map.mif")
    RD_map= os.path.join(dir_name, file_name + "_RD_map.mif")
    AD_map= os.path.join(dir_name, file_name + "_AD_map.mif")
    # Check if the file already exist or not 
    if not (os.path.exists(FA_map) or os.path.exists(ADC_map) or os.path.exists(RD_map) or os.path.exists(AD_map)):
        cmd = ["tensor2metric", "-fa", FA_map, "-adc", ADC_map, "-rd", RD_map, "-ad", AD_map, tensor]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch tensor2metric (exit code {result})"
            return 0, msg, info
        else:
            print(f"FA map succesfully created. Output file: {FA_map}")
    else:
        print(f"Skipping FA, ADC, AD and RD map creation step, at least one of them already exists.")

    return FA_map