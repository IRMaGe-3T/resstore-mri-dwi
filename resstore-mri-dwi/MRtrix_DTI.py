"""
Use MRTrix to fit Diffusion Tensor Imaging (DTI)
"""

import os
from useful import check_file_ext, execute_command, verify_file
from termcolor import colored


def mrtrix_DTI(in_dwi, mask, FA_dir):
    """
    Fit DTI using mrtrix
    """
    info = {}
    # Get files name
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    print(colored("\n~~FA_map starts~~", "cyan"))

    # Create path for tensor
    tensor = os.path.join(FA_dir, "tensor.mif")
    # Check if the file already exist or not
    if not verify_file(tensor):
        cmd = ["dwi2tensor", in_dwi, "-mask", mask, tensor]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch dwi2tensor (exit code {result})"
            return 0, msg, info
        else:
            print(
                f"\nDiffusion tensor succesfully created. Output file: {tensor}")

    # Create path to FA map
    FA_map = os.path.join(FA_dir, "FA_map.mif")
    ADC_map = os.path.join(FA_dir, "ADC_map.mif")
    RD_map = os.path.join(FA_dir,  "RD_map.mif")
    AD_map = os.path.join(FA_dir,  "AD_map.mif")
    vector = os.path.join(FA_dir,  "vector.mif")
    # Check if the file already exist or not
    if not (os.path.exists(FA_map) or os.path.exists(ADC_map) or os.path.exists(RD_map) or os.path.exists(AD_map)):
        cmd = ["tensor2metric", "-fa", FA_map, "-adc",
               ADC_map, "-rd", RD_map, "-ad", AD_map, "-vector", vector, "-mask", mask, tensor]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch tensor2metric (exit code {result})"
            return 0, msg, info
        else:
            print(f"\nFA map succesfully created. Output file: {FA_map}")
    else:
        print(colored(
            f"\nSkipping FA, ADC, AD and RD map creation step, at least one of them already exists.", "yellow"))

    info_fa = {"FA_map": FA_map}
    msg = "\nFA_map done"
    print(colored(msg, "cyan"))
    return 1, msg, info_fa
