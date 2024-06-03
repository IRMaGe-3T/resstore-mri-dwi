# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - get_dwifslpreproc_command
    - run_preproc_dwi

"""

import logging
import os

from FOD import FOD
from useful import check_file_ext, convert_mif_to_nifti, execute_command

# Set up logging, to check
logging.basicConfig(level=logging.INFO)
mylog = logging.getLogger(__name__)

EXT = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}


def get_dwifslpreproc_command(
    in_dwi, dwi_out, pe_dir, readout_time, b0_pair=None, rpe=None, shell=False
):
    """
    Get dwifslpreproc command.
    """
    command = ["dwifslpreproc", in_dwi, dwi_out]

    if not rpe:
        command += [
            "-rpe_none",
            "-pe_dir",
            pe_dir,
            "-readout_time",
            readout_time,
        ]
    elif rpe == "pair":
        command += [
            "-rpe_pair",
            "-se_epi",
            b0_pair,
            "-pe_dir",
            pe_dir,
            "-readout_time",
            readout_time,
        ]
    elif rpe == "all":
        command += [
            "-rpe_all",
            "-pe_dir",
            pe_dir,
            "-readout_time",
            readout_time,
        ]
    if shell is True:
        command += ["-eddy_options", "--slm=linear --data_is_shelled"]
    else:
        command += ["-eddy_options", "--slm=linear "]
    return command


def run_preproc_dwi(
    in_dwi, pe_dir, readout_time, rpe=None, shell=True, in_pepolar_PA=None, in_pepolar_AP=None
):
    """
    Run preproc for whole brain diffusion using MRtrix command
    """
    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})

    # Denoise
    dwi_denoise = os.path.join(dir_name, file_name + "_denoise.mif")
    if not os.path.exists(dwi_denoise):
        cmd = ["dwidenoise", in_dwi, dwi_denoise]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch mrdegibbs (exit code {result})"
            return 0, msg, info
        else:
            print(f"Denoise completed. Output file: {dwi_denoise}")
    else:
        print(f"Skipping denoise step, {dwi_denoise} already exists.")

    # DeGibbs / Unringing
    dwi_degibbs = dwi_denoise.replace("_denoise.mif", "_denoise_degibbs.mif")
    if not os.path.exists(dwi_degibbs):
        cmd = ["mrdegibbs", dwi_denoise, dwi_degibbs]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch mrdegibbs (exit code {result})"
            return 0, msg, info
        else:
            print(f"Unringing completed. Output file: {dwi_degibbs}")
    else:
        print(f"Skipping unringing step, {dwi_degibbs} already exists.")

    # Motion and distortion correction
    dwi_preproc = dwi_degibbs.replace("_degibbs.mif", "_degibbs_preproc.mif")
    if not os.path.exists(dwi_preproc):

        # Create b0_pair 
        b0_pair = os.path.join(dir_name, "b0_pair.mif")
        if not os.path.exists(b0_pair):
            # Create command for b0_pair creation if pe_dir=PA
            if pe_dir=="j" and in_pepolar_AP:
                # Check for fmap files encoding direction (PA)
                if in_pepolar_PA==None:
                    # Extract b0 (PA) from dwi 
                    in_pepolar_PA = in_dwi.replace(".mif", "_bzero.mif")
                    cmd = ["dwiextract", in_dwi, in_pepolar_PA, "-bzero"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                    if result != 0:
                        msg = f"Can not launch dwiextract (exit code {result})"
                        return 0, msg, info
                # Create command for concatenation
                cmd = ["mrcat", in_pepolar_PA, in_pepolar_AP, b0_pair]
            # Create command for b0_pair creation if pe_dir=AP
            if pe_dir=="j-" and in_pepolar_PA:
                # Check for fmap files encoding direction (AP)
                if in_pepolar_AP==None:
                # Extract b0 (AP) from dwi 
                    in_pepolar_AP = in_dwi.replace(".mif", "_bzero.mif")
                    cmd = ["dwiextract", in_dwi, in_pepolar_AP, "-bzero"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                    if result != 0:
                        msg = f"Can not launch dwiextract (exit code {result})"
                        return 0, msg, info
                # Create command for concatenation
                cmd = ["mrcat", in_pepolar_AP, in_pepolar_PA, b0_pair]
            # Concatenate both b0 images to create b0_pair     
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"Can not launch mrcat to create b0_pair (exit code {result})"
                return 0, msg, info
            else:
                print(f"B0_pair succesfully created. Output file: {b0_pair}")
        else:
            print(f"Skipping b0_pair creation step, {b0_pair} already exists.")
            
        # Motion distortion correction
        # fslpreproc (topup and Eddy)
        if b0_pair:
            cmd = get_dwifslpreproc_command(
                dwi_degibbs, dwi_preproc, pe_dir, readout_time, b0_pair, rpe, shell
            )
        else:
            cmd = get_dwifslpreproc_command(
                dwi_degibbs,
                dwi_preproc,
                pe_dir,
                readout_time,
                b0_pair=None,
                rpe=rpe,
                shell=shell,
            )
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch dwifslpreproc (exit code {result})"
            return 0, msg, info
        else:
            print(f"Motion and distortion correction completed. Output file: {dwi_preproc}")
            
    else:
        print(f"Skipping motion correction step, {dwi_preproc} already exists.")

    # Bias correction
    dwi_unbias = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_unbiased.mif")
    bias_output = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_bias.mif")
    if not os.path.exists(dwi_unbias) and not os.path.exists(bias_output):
        cmd = ["dwibiascorrect", "ants", dwi_preproc, dwi_unbias,"-bias", bias_output]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch bias correction (exit code {result})"
            return 0, msg
        else:
            print(f"Bias correction completed. Output files: {dwi_unbias}, {bias_output}")#good detail to add
    else:
       print(f"Skipping bias correction step, {dwi_unbias} and/or {bias_output} already exists.")


    # Brain mask
    dwi_mask = dwi_unbias.replace("_degibbs_preproc_unbiased.mif", "_dwi_brain_mask.mif")
    if not os.path.exists(dwi_mask):
        cmd = ["dwi2mask", dwi_unbias, dwi_mask]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = "Can not lunch mask (exit code {result})"
            return 0, msg
        else:
            print(f"Brain mask completed. Output file: {dwi_mask}")
    else:
       print(f"Skipping brain mask step, {dwi_mask} already exists.")

    user_input = input(f"Do you want to perform FOD estimation? (yes/no): ").strip().lower()
    if user_input in ['yes', 'y']:
        FOD(dwi_preproc, dwi_mask)
    else:
        print("No FOD done")
        
    info = {"dwi_preproc": dwi_unbias, "brain_mask": dwi_mask}
    msg = "Preprocessing DWI done"
    print(msg)
    return 1, msg, info

    
