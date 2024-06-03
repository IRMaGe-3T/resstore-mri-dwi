"""
Function for FOD estimation:
    - Performs RF estimation using the dhollander algorithm
    - Estimates FOD using MSMT CSD
    - Converts the resulting FOD files into a volume fraction (VF) file
    - Normalizes the intensity of the FOD files

Parameters:
    in_dwi (str): Path to the input DWI file in MIF format.
    mask (str): Path to the brain mask file.

Returns:
    tuple: (status, message, info) where status is 0 for failure and 1 for success,
            message is a string describing the result, and info is a dictionary with file paths.
"""

import os
from useful import check_file_ext, convert_mif_to_nifti, execute_command

def FOD(in_dwi, mask):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    
    # RF estimation 
    voxels = os.path.join(dir_name, "voxels.mif")
    wm = os.path.join(dir_name, "wm.txt")
    gm = os.path.join(dir_name, "gm.txt")
    csf = os.path.join(dir_name, "csf.txt")
    if not os.path.exists(voxels):
        cmd = ["dwi2response", "dhollander", in_dwi, wm, gm, csf, "-voxels", voxels]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch dwi2response hollander (exit code {result})"
            return 0, msg, info
        else:
            print(f"Voxels succesfully created. Output file: {voxels}")
    else:
        print(f"Skipping RF estimation step, {voxels} already exists.")

    # FOD estimation 
    vf = os.path.join(dir_name, "vf.mif")
    wmfod = os.path.join(dir_name, "wmfod.mif")
    gmfod = os.path.join(dir_name, "gmfod.mif")
    csffod = os.path.join(dir_name, "csffod.mif")
    if not os.path.exists(vf) :
        if not (os.path.exists(wmfod) and os.path.exists(gmfod) and os.path.exists(csffod)):
            cmd = ["dwi2fod", "msmt_csd", in_dwi, "-mask", mask, wm, wmfod, gm, gmfod, csf, csffod]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"Can not launch dwi2fod (exit code {result})"
                return 0, msg, info
            else:
                print(f"FOD files succesfully created. Output file: {wmfod}, {gmfod}, {csffod}")
        interm_wm = os.path.join(dir_name, "interm_wm.mif")
        cmd = ["mrconvert", "-coord", "3", "0", wmfod, interm_wm]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch mrconvert (exit code {result})"
            return 0, msg, info
        else:
            print(f"Intermediary files succesfully created. Output file: {interm_wm}")
        cmd = ["mrcat", csffod, gmfod, interm_wm, vf]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch mrcat (exit code {result})"
            return 0, msg, info
        else:
            print(f"Vf files succesfully created. Output file: {vf}")
        cmd = ["rm", interm_wm]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not remove intermediary file (exit code {result})"
            return 0, msg, info
        else:
            print(f"Intermediary files succesfully removed. Output file: {interm_wm}")
    else: 
        print(f"Skipping FOD estimation step, {vf} already exists.")

    # Intensity normalization
    wmfod_norm = os.path.join(dir_name, "wmfod_norm.mif")
    gmfod_norm = os.path.join(dir_name, "gmfod_norm.mif")
    csffod_norm = os.path.join(dir_name, "csffod_norm.mif")
    if not (os.path.exists(wmfod_norm) and os.path.exists(gmfod_norm) and os.path.exists(csffod_norm)):
        cmd = ["mtnormalise", wmfod, wmfod_norm, gmfod, gmfod_norm, csffod, csffod_norm, "-mask", mask]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch mtnormalize (exit code {result})"
            return 0, msg, info
        else:
            print(f"Intensity normalization completed. Output file: {wmfod_norm}, {gmfod_norm}, {csffod_norm}")
    else:
        print("Intensity normalization already done")

    return 
