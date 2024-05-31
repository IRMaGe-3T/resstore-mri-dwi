# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - get_dwifslpreproc_command
    - run_preproc_dwi

"""

import logging
import os

from useful import check_file_ext, convert_mif_to_nifti, execute_command

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
    in_dwi, pe_dir, readout_time, rpe=None, shell=True, in_pepolar=None
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
    cmd = ["dwidenoise", in_dwi, dwi_denoise]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not lunch mrdegibbs (exit code {result})"
        return 0, msg, info

    # DeGibbs / Unringing
    dwi_degibbs = dwi_denoise.replace("_denoise.mif", "_denoise_degibbs.mif")
    cmd = ["mrdegibbs", dwi_denoise, dwi_degibbs]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not lunch mrdegibbs (exit code {result})"
        return 0, msg, info

    # # Create b0 pair for motion distortion correction
    # if in_pepolar:
    #     # Average b0 pepolar
    #     in_pepolar_mean = in_pepolar.replace(".mif", "_mean.mif")
    #     cmd = ["mrmath", in_pepolar, "mean", in_pepolar_mean, "-axis", "3"]
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Can not lunch mrmath (exit code {result})"
    #         return 0, msg, info
    #     # Extract b0 from dwi and average data
    #     in_dwi_b0 = in_dwi.replace(".mif", "_bzero.mif")
    #     cmd = ["dwiextract", in_dwi, in_dwi_b0, "-bzero"]
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Can not lunch dwiextract (exit code {result})"
    #         return 0, msg, info
    #     in_dwi_b0_mean = in_dwi_b0.replace(".mif", "_mean.mif")
    #     cmd = ["mrmath", in_dwi_b0, "mean", in_dwi_b0_mean, "-axis", "3"]
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Can not lunch mrmath (exit code {result})"
    #         return 0, msg, info
    #     # Concatenate both b0 mean
    #     b0_pair = os.path.join(dir_name, "b0_pair.mif")
    #     cmd = ["mrcat", in_dwi_b0_mean, in_pepolar_mean, b0_pair]
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Can not lunch mrcat (exit code {result})"
    #         return 0, msg, info

    # Motion distortion correction
    # if rpe == "all":
    #     # In this case issue with dwifslpreproc
    #     # use directly corrected image for in_dwi
    #     dwi_out = in_dwi
    #     mylog.info("Motion distorsion correction not done")
    # else:
    #     # fslpreproc (topup and Eddy)
    #     dwi_out = dwi_degibbs.replace(".mif", "_fslpreproc.mif")
    #     if in_pepolar:
    #         cmd = get_dwifslpreproc_command(
    #             dwi_degibbs, dwi_out, pe_dir, readout_time, b0_pair, rpe, shell
    #         )
    #     else:
    #         cmd = get_dwifslpreproc_command(
    #             dwi_degibbs,
    #             dwi_out,
    #             pe_dir,
    #             readout_time,
    #             b0_pair=None,
    #             rpe=rpe,
    #             shell=shell,
    #         )
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Can not lunch dwifslpreproc (exit code {result})"
    #         return 0, msg, info

    # # Bias correction
    # dwi_unbias = os.path.join(dir_name, dwi_out.replace(".mif", "_unbias.mif"))
    # cmd = ["dwibiascorrect", "ants", dwi_out, dwi_unbias]
    # result, stderrl, sdtoutl = execute_command(cmd)
    # if result != 0:
    #     msg = f"Can not lunch bias correction (exit code {result})"
    #     return 0, msg

    # # Brain mask
    # dwi_mask = os.path.join(dir_name, "dwi_brain_mask.mif")
    # cmd = ["dwi2mask", dwi_unbias, dwi_mask]
    # result, stderrl, sdtoutl = execute_command(cmd)
    # if result != 0:
    #     msg = "Can not lunch mask (exit code {result})"
    #     return 0, msg

    # info = {"dwi_preproc": dwi_unbias, "brain_mask": dwi_mask}
    # msg = "Preprocessing DWI done"
    # mylog.info(msg)
    # return 1, msg, info


