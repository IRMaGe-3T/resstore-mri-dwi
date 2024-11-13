# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - get_dwifslpreproc_command
    - run_preproc_dwi: perform preprocessing and optional FOD 
"""

import os
from useful import check_file_ext, convert_mif_to_nifti, execute_command, verify_file, convert_nifti_to_mif
from termcolor import colored

EXT = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}


def get_dwifslpreproc_command(
    in_dwi, dwi_out, pe_dir, readout_time, qc_directory, b0_pair=None, rpe=None, shell=False
):
    """
    Get dwifslpreproc command

    Parameters: 
    - in_dwi: input file .mif format to be corrected
    - dwi_out: file that will contain the motion and distortion corrected images
    - pe_dir: phase encoding direction
    - readout_time: the time it takes to acquire the k-space data after the excitation pulse (s)
    - b0_pair: (optionnal) b0_pair file in .mif format 
    - rpe: (optionnal) ratio of partial echo = fraction of the k-space that are encoded
    - shell: (default:False) no info was given on the b-values

    Return:
    - command: to run the dwifslpreproc 
    """
    command = ["dwifslpreproc", in_dwi, dwi_out]
    if not rpe:
        command += [
            "-rpe_none",
            "-pe_dir", pe_dir,
            "-readout_time", readout_time,
            "-eddyqc_text", qc_directory
        ]
    elif rpe == "pair":
        command += [
            "-rpe_pair",
            "-se_epi", b0_pair,
            "-pe_dir", pe_dir,
            "-readout_time", readout_time,
            "-eddyqc_text", qc_directory
        ]
    elif rpe == "all":
        command += [
            "-rpe_all",
            "-pe_dir", pe_dir,
            "-readout_time", readout_time,
            "-eddyqc_text", qc_directory
        ]
    if shell:
        command += ["-eddy_options", "--slm=linear --data_is_shelled"]
    else:
        command += ["-eddy_options", "--slm=linear"]
    return command


def run_preproc_dwi(
    in_dwi, pe_dir, readout_time, shell=True, in_pepolar_PA=None, in_pepolar_AP=None
):
    """
    Run preproc for whole brain diffusion using MRtrix command and an optional FOD estimation 

    Parameters:
    - in_dwi: input file .mif format to be preprocessed
    - pe_dir: phase encoding direction
    - readout_time: the time it takes to acquire the k-space data after the excitation pulse (s)
    - shell: (default:True) info was given on the b-values
    - in_pepolar_PA: (optionnal), fmap PA in .mif format
    - in_pepolar_AP: (optionnal), fmap AP in .mif format

    Returns: 
    - int 1 success, 0 failure 
    - msg 
    - info_preproc
    """

    # Get files name
    info_prepoc = {}
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})

    # Denoise
    dwi_denoise = os.path.join(dir_name, file_name + "_denoise.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_denoise):
        cmd = ["dwidenoise", in_dwi, dwi_denoise]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch dwidenoise (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"\nDenoise completed. Output file: {dwi_denoise}")

    # DeGibbs / Unringing
    dwi_degibbs = dwi_denoise.replace("_denoise.mif", "_denoise_degibbs.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_degibbs):
        cmd = ["mrdegibbs", dwi_denoise, dwi_degibbs]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch mrdegibbs (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"\nUnringing completed. Output file: {dwi_degibbs}")

    # Motion and distortion correction
    dwi_preproc = dwi_degibbs.replace("_degibbs.mif", "_degibbs_preproc.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_preproc):
        # Create b0_pair if possible
        # and choose rpe option for dwifslpreproc cmd
        b0_pair = os.path.join(dir_name, "b0_pair.mif")
        # Check if the file already exists or not
        if not verify_file(b0_pair):
            # If pe_dir=PA (j) and fmap AP exist
            if pe_dir == "j" and in_pepolar_AP:
                rpe = "pair"
                # No fmap files in the encoding direction (PA) is given
                if in_pepolar_PA is None:
                    # Extract b0 (PA) from main dwi
                    in_pepolar_PA = in_dwi.replace(".mif", "_bzero.mif")
                    # Check if the file already exists or not
                    if not verify_file(in_pepolar_PA):
                        cmd = ["dwiextract", in_dwi, in_pepolar_PA, "-bzero"]
                        result, stderrl, sdtoutl = execute_command(cmd)
                        if result != 0:
                            msg = f"\nCannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("\nb0_PA successfully extracted")
                # Check dimension and average b0 if needed
                # All fmaps are averaged to ensure that dwifslpreproc will run correctly 
                # It can only run with even number of volumes in the fmaps
                cmd = ["mrinfo", "-ndim", in_pepolar_PA]
                result, stderrl, sdtoutl = execute_command(cmd)
                dim = int(sdtoutl.decode("utf-8").replace("\n", ""))
                in_pep_PA_mean = in_pepolar_PA.replace(".mif", "_mean.mif")
                if dim == 4:
                    cmd = ["mrmath", in_pepolar_PA, "mean", in_pep_PA_mean, "-axis", "3", "-force"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                else:
                    in_pep_PA_mean = in_pepolar_PA

                cmd = ["mrinfo", "-ndim", in_pepolar_AP]
                result, stderrl, sdtoutl = execute_command(cmd)
                dim = int(sdtoutl.decode("utf-8").replace("\n", ""))
                in_pep_AP_mean = in_pepolar_AP.replace(".mif", "_mean.mif")
                if dim == 4:
                    cmd = ["mrmath", in_pepolar_AP, "mean", in_pep_AP_mean, "-axis", "3", "-force"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                else:
                    in_pep_AP_mean = in_pepolar_AP

                # Concatenate both b0 images to create b0_pair
                cmd = ["mrcat", in_pep_PA_mean, in_pep_AP_mean, b0_pair]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch mrcat to create b0_pair (exit code {result})"
                    return 0, msg, info_prepoc
                else:
                    print(
                        f"\nB0_pair successfully created. Output file: {b0_pair}")
            # If pe_dir=AP (j-) and fmap PA exist
            elif pe_dir == "j-" and in_pepolar_PA:
                rpe = "pair"
                # Check for fmap files encoding direction (AP)
                if in_pepolar_AP is None:
                    # Extract b0 (AP) from dwi
                    in_pepolar_AP = in_dwi.replace(".mif", "_bzero.mif")
                    # Check if the file already exists or not
                    if not verify_file(in_pepolar_AP):
                        cmd = ["dwiextract", in_dwi, in_pepolar_AP, "-bzero"]
                        result, stderrl, sdtoutl = execute_command(cmd)
                        if result != 0:
                            msg = f"\nCannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("\nb0_AP successfully extracted")
                # Check dimension and average b0 if needed
                cmd = ["mrinfo", "-ndim", in_pepolar_AP]
                result, stderrl, sdtoutl = execute_command(cmd)
                dim = int(sdtoutl.decode("utf-8").replace("\n", ""))
                in_pep_AP_mean = in_pepolar_AP.replace(".mif", "_mean.mif")
                if dim == 4:
                    cmd = ["mrmath", in_pepolar_AP, "mean", in_pep_AP_mean, "-axis", "3", "-force"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                else:
                    in_pep_AP_mean = in_pepolar_AP

                cmd = ["mrinfo", "-ndim", in_pepolar_PA]
                result, stderrl, sdtoutl = execute_command(cmd)
                dim = int(sdtoutl.decode("utf-8").replace("\n", ""))
                in_pep_PA_mean = in_pepolar_PA.replace(".mif", "_mean.mif")
                if dim == 4:
                    cmd = ["mrmath", in_pepolar_PA, "mean", in_pep_PA_mean, "-axis", "3", "-force"]
                    result, stderrl, sdtoutl = execute_command(cmd)
                else:
                    in_pep_PA_mean = in_pepolar_PA

                # Concatenate both b0 images to create b0_pair
                cmd = ["mrcat", in_pep_AP_mean, in_pep_PA_mean, b0_pair]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch mrcat to create b0_pair (exit code {result})"
                    return 0, msg, info_prepoc
                else:
                    print(
                        f"\nB0_pair successfully created. Output file: {b0_pair}")
            # If no inverse fmap available (pe_dir AP or PA)
            else:
                rpe = None
                b0_pair = None
                print(
                    "\nfmap not available. Due to use of a single fixed phase encoding, "
                    "no EPI distortion correction can be applied in this case."
                )

        # fslpreproc (topup and Eddy)
        qc_directory = os.path.join(dir_name, "qc_text")
        if not os.path.exists(qc_directory):
            os.makedirs(qc_directory)
        cmd = get_dwifslpreproc_command(
            dwi_degibbs, dwi_preproc, pe_dir, readout_time, qc_directory, b0_pair, rpe, shell,
        )
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch dwifslpreproc (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(
                f"\nMotion and distortion correction completed. Output file: {dwi_preproc}")

    # Bias correction
    dwi_unbias = dwi_preproc.replace(
        "_degibbs_preproc.mif", "_degibbs_preproc_unbiased.mif")
    bias_output = dwi_preproc.replace(
        "_degibbs_preproc.mif", "_degibbs_preproc_bias.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_unbias) and not verify_file(bias_output):
        cmd = ["dwibiascorrect", "ants", dwi_preproc,
               dwi_unbias, "-bias", bias_output]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch bias correction (exit code {result})"
            return 0, msg
        else:
            print(
                f"\nBias correction completed. Output files: {dwi_unbias}, {bias_output}")

    # Brain mask, for FA
    dwi_mask = dwi_unbias.replace(
        "_degibbs_preproc_unbiased.mif", "_dwi_brain_mask.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_mask):
        cmd = ["dwi2mask", dwi_unbias, dwi_mask]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch mask (exit code {result})"
            return 0, msg
        else:
            print(f"\nBrain mask completed. Output file: {dwi_mask}")

    mask_nii = dwi_mask.replace(".mif", ".nii.gz")
    if not verify_file(mask_nii):
        convert_mif_to_nifti(dwi_mask, dir_name, diff=None)
    dwi_unbias_nii = dwi_unbias.replace(".mif", ".nii.gz")
    if not verify_file(dwi_unbias_nii):
        convert_mif_to_nifti(dwi_unbias, dir_name, diff=True)

    info_preproc = {"dwi_preproc": dwi_unbias, "dwi_preproc_nii": dwi_unbias_nii,
                    "brain_mask": dwi_mask, "brain_mask_nii": mask_nii}
    msg = "\nPreprocessing DWI done"
    print(colored(msg, "cyan"))
    return 1, msg, info_preproc
