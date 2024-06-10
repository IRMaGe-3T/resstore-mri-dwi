""" FOD processing 
Function for FOD estimation:
    - Performs RF estimation using the dhollander algorithm
    - Estimates FOD using MSMT CSD
    - Converts the resulting FOD files into a volume fraction (VF) file
    - Normalizes the intensity of the FOD files

Parameters:
    in_dwi (str): Path to the input DWI file in MIF format.
    mask (str): Path to the brain mask file in MIF format. 

Files created:
    - voxels.mif
    - wm.txt, gm.txt, csf.txt
    - wmfod.mif, gmfod.mif, csffod.mif
    - wmfod_norm.mif, gmfod_norm.mif, csffod_norm.mif
"""

import os
from useful import check_file_ext, execute_command, verify_file





def FOD(in_dwi, mask):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    
    # RF estimation 
    voxels = os.path.join(dir_name, file_name + "_voxels.mif")
    wm = os.path.join(dir_name, file_name + "_wm.txt")
    gm = os.path.join(dir_name, file_name + "_gm.txt")
    csf = os.path.join(dir_name, file_name + "_csf.txt")
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
    vf = os.path.join(dir_name, file_name + "_vf.mif")
    wmfod = os.path.join(dir_name, file_name + "_wmfod.mif")
    gmfod = os.path.join(dir_name, file_name + "_gmfod.mif")
    csffod = os.path.join(dir_name, file_name + "_csffod.mif")
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
    wmfod_norm = os.path.join(dir_name, file_name + "_wmfod_norm.mif")
    gmfod_norm = os.path.join(dir_name, file_name + "_gmfod_norm.mif")
    csffod_norm = os.path.join(dir_name, file_name + "_csffod_norm.mif")
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

    # Extract peaks
    peaks = os.path.join(dir_name, "peaks.mif")
    if not verify_file(peaks):
        cmd = ["sh2peaks", wmfod_norm, peaks]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot launch sh2peaks (exit code {result})"
            return 0, msg, info
        else:
            print(f"Peaks Succesfully extracted. Output file: {peaks}")

    return 1, peaks