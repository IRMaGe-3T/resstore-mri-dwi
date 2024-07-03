# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - get_dwifslpreproc_command
    - run_preproc_dwi: perform preprocessing and optional FOD 
    - download_template: Dowload a MNI_FA template
    - run_register_MNI: Aligning image to MNI space
"""

import os
import urllib.request

from useful import check_file_ext, convert_mif_to_nifti, execute_command, verify_file, convert_nifti_to_mif

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
    in_dwi, pe_dir, readout_time, rpe=None, shell=True, in_pepolar_PA=None, in_pepolar_AP=None
):
    """
    Run preproc for whole brain diffusion using MRtrix command and an optional FOD estimation 

    Parameters:
    - in_dwi: input file .mif format to be preprocessed
    - pe_dir: phase encoding direction
    - readout_time: the time it takes to acquire the k-space data after the excitation pulse (s)
    - rpe: (optionnal) ratio of partial echo = fraction of the k-space that are encoded
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
    if not os.path.exists(dwi_denoise):
        cmd = ["dwidenoise", in_dwi, dwi_denoise]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch dwidenoise (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"\nDenoise completed. Output file: {dwi_denoise}")
    else:
        print(f"\nSkipping denoise step, {dwi_denoise} already exists.")

    # DeGibbs / Unringing
    dwi_degibbs = dwi_denoise.replace("_denoise.mif", "_denoise_degibbs.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_degibbs):
        cmd = ["mrdegibbs", dwi_denoise, dwi_degibbs]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch mrdegibbs (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"\nUnringing completed. Output file: {dwi_degibbs}")
    else:
        print(f"\nSkipping unringing step, {dwi_degibbs} already exists.")

    # Motion and distortion correction
    dwi_preproc = dwi_degibbs.replace("_degibbs.mif", "_degibbs_preproc.mif")
    b0_pair = os.path.join(dir_name, "b0_pair.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_preproc):

        # Create b0_pair 
        # Check if the file already exists or not
        if not os.path.exists(b0_pair):
            # Create command for b0_pair creation if pe_dir=PA
            if pe_dir == "j" and in_pepolar_AP:
                # Check for fmap files encoding direction (PA)
                if in_pepolar_PA is None:
                    # Extract b0 (PA) from dwi 
                    in_pepolar_PA = in_dwi.replace(".mif", "_bzero.mif")
                    # Check if the file already exists or not
                    if not os.path.exists(in_pepolar_PA):
                        cmd = ["dwiextract", in_dwi, in_pepolar_PA, "-bzero"]
                        result, stderrl, sdtoutl = execute_command(cmd)
                        if result != 0:
                            msg = f"\nCannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("\nb0_PA successfully extracted")
                    else:
                        print("\nSkipping b0_PA extraction, file already exists")
                # Create command for concatenation
                cmd = ["mrcat", in_pepolar_PA, in_pepolar_AP, b0_pair]
            # Create command for b0_pair creation if pe_dir=AP
            if pe_dir == "j-" and in_pepolar_PA:
                # Check for fmap files encoding direction (AP)
                if in_pepolar_AP is None:
                # Extract b0 (AP) from dwi 
                    in_pepolar_AP = in_dwi.replace(".mif", "_bzero.mif")
                    # Check if the file already exists or not
                    if not os.path.exists(in_pepolar_AP):
                        cmd = ["dwiextract", in_dwi, in_pepolar_AP, "-bzero"]
                        result, stderrl, sdtoutl = execute_command(cmd)
                        if result != 0:
                            msg = f"\nCannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("\nb0_AP successfully extracted")
                    else:
                        print("\nSkipping b0_AP extraction, file already exists")
                        
                # Create command for concatenation
                cmd = ["mrcat", in_pepolar_AP, in_pepolar_PA, b0_pair]
                # Concatenate both b0 images to create b0_pair     
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch mrcat to create b0_pair (exit code {result})"
                    return 0, msg, info_prepoc
                else:
                    print(f"\nB0_pair successfully created. Output file: {b0_pair}")
        else:
            print(f"\nSkipping b0_pair creation step, {b0_pair} already exists.")
            
        # fslpreproc (topup and Eddy)
        qc_directory = os.path.join(dir_name, "qc_text")
        if not os.path.exists(qc_directory):
            os.makedirs(qc_directory)
        if b0_pair:
            cmd = get_dwifslpreproc_command(
                dwi_degibbs, dwi_preproc, pe_dir, readout_time, qc_directory, b0_pair, rpe, shell,
            )
        else:
            cmd = get_dwifslpreproc_command(
                dwi_degibbs,
                dwi_preproc,
                pe_dir,
                readout_time,
                qc_directory,
                b0_pair=None,
                rpe=rpe,
                shell=shell,
            )
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch dwifslpreproc (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"\nMotion and distortion correction completed. Output file: {dwi_preproc}")
            
    else:
        print(f"\nSkipping motion correction step, {dwi_preproc} already exists.")


    # Bias correction
    dwi_unbias = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_unbiased.mif")
    bias_output = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_bias.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_unbias) and not os.path.exists(bias_output):
        cmd = ["dwibiascorrect", "ants", dwi_preproc, dwi_unbias, "-bias", bias_output]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch bias correction (exit code {result})"
            return 0, msg
        else:
            print(f"\nBias correction completed. Output files: {dwi_unbias}, {bias_output}")
    else:
       print(f"\nSkipping bias correction step, {dwi_unbias} and/or {bias_output} already exists.")

    # Brain mask, for FA
    dwi_mask = dwi_unbias.replace("_degibbs_preproc_unbiased.mif", "_dwi_brain_mask.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_mask):
        cmd = ["dwi2mask", dwi_unbias, dwi_mask]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch mask (exit code {result})"
            return 0, msg
        else:
            print(f"\nBrain mask completed. Output file: {dwi_mask}")
    else:
       print(f"\nSkipping brain mask step, {dwi_mask} already exists.")

    mask_nii = dwi_mask.replace('.mif', '.nii.gz')
    if not verify_file(mask_nii):
        convert_mif_to_nifti(dwi_mask, dir_name, diff=None)
        
    info_preproc = {"dwi_preproc": dwi_unbias,"brain_mask": dwi_mask, "brain_mask_nii": mask_nii}
    msg = "\nPreprocessing DWI done"
    print(msg)
    return 1, msg, info_preproc

# Function to download the template file if it doesn't exist
def download_template(dir_name):
    github_repo_url = "https://github.com/IRMaGe-3T/resstore-mri-dwi/raw/1f0fbd5ff4809cf0f89be36548d1c4b7bc2c5f04/resstore-mri-dwi/resources/MNI_FA_template.nii.gz"
    template_filename = "MNI_FA_template.nii.gz"
    template_path = os.path.join(dir_name, template_filename)
    
    # Check if the template file already exists
    if not verify_file(template_path):
        try:
            print("\nDownloading MNI_FA_template.nii.gz...")
            urllib.request.urlretrieve(github_repo_url, template_path)
            print("\nTemplate file downloaded successfully.")
        except Exception as e:
            print(f"\nFailed to download the template file: {e}")
            return None
    
    return template_path

def run_register_MNI(in_dwi, in_fa, NODDI_dir, DKI_dir, MNI_dir):
    """
    Aligning image to MNI space

    Parameters:
    - in_dwi: input file .mif format to be preprocessed, mif format.
    - in_fa: input Fractional Anisotropy Map to be preprocessed, mif format.

    Returns: 
    - int 1 success, 0 failure 
    - msg 
    - info_mni
    """

    # Get files name
    info_mni = {}
    preproc_dir = os.path.dirname(in_dwi)
    FA_dir = os.path.dirname(in_fa)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})

    # Download the template file
    template_path = download_template(MNI_dir)

    # Convert MIF to NIfTI
    #Diffusion
    dwi_nii_return, dwii_nii_msg,in_dwi_nii=convert_mif_to_nifti(in_dwi,preproc_dir)
    #FA
    fa_nii_return, fa_nii_msg,in_fa_nii=convert_mif_to_nifti(in_fa,FA_dir, False)

    # Linear registration of FA
    fa_mni = os.path.join(MNI_dir, "FA_MNI.nii.gz")
    if not verify_file(fa_mni):
        cmd = [
            "flirt",
            "-ref", template_path, 
            "-in", in_fa_nii,
            "-out", fa_mni,
            "-omat", "FA_2_MNI.mat",
            "-dof", "6",
            "-cost", "mutualinfo",
            "-searchcost", "mutualinfo"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch flirt for FA (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"\nLinear registration of FA completed. Output file: {fa_mni}")

    # Linear registration of NODDI maps
    if NODDI_dir is not None:
        for file_name in os.listdir(NODDI_dir):
            if file_name.endswith(".nii.gz"):
                map_path = os.path.join(NODDI_dir, file_name)
                MNI_NODDI_dir = os.path.join(MNI_dir, "NODDI")
                if not os.path.exists(MNI_NODDI_dir):
                    os.mkdir(MNI_NODDI_dir)
                map_mni = os.path.join(MNI_NODDI_dir, file_name.replace(".nii.gz", "_MNI.nii.gz"))
                if not verify_file(map_mni):
                    cmd = [
                        "flirt",
                        "-ref", template_path, 
                        "-in", map_path,
                        "-out", map_mni,
                        "-omat", "FA_2_MNI.mat",
                        "-dof", "6",
                        "-cost", "mutualinfo",
                        "-searchcost", "mutualinfo"
                    ]
                    result, stderr, stdout = execute_command(cmd)
                    if result != 0:
                        msg = f"\nCan not launch flirt for NODDI map {file_name} (exit code {result}): {stderr}"
                        return 0, msg, info_mni
                    
    # Linear registration of DKI maps
    if DKI_dir is not None:
        for file_name in os.listdir(DKI_dir):
            if file_name.endswith(".nii.gz"):
                map_path = os.path.join(DKI_dir, file_name)
                MNI_DKI_dir = os.path.join(MNI_dir, "DKI")
                if not os.path.exists(MNI_DKI_dir):
                    os.mkdir(MNI_DKI_dir)
                map_mni = os.path.join(MNI_DKI_dir, file_name.replace(".nii.gz", "_MNI.nii.gz"))
                if not verify_file(map_mni):
                    cmd = [
                        "flirt",
                        "-ref", template_path, 
                        "-in", map_path,
                        "-out", map_mni,
                        "-omat", "FA_2_MNI.mat",
                        "-dof", "6",
                        "-cost", "mutualinfo",
                        "-searchcost", "mutualinfo"
                    ]
                    result, stderr, stdout = execute_command(cmd)
                    if result != 0:
                        msg = f"\nCan not launch flirt for NODDI map {file_name} (exit code {result}): {stderr}"
                        return 0, msg, info_mni

    # Linear registration of DWI
    diffusion_mni = os.path.join(MNI_dir, "dwi_MNI.nii.gz")
    if not verify_file(diffusion_mni):
        cmd = [
            "flirt",
            "-ref", template_path,
            "-in", in_dwi_nii,
            "-out", diffusion_mni,
            "-applyxfm",
            "-init", "FA_2_MNI.mat",
            "-dof", "6"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch flirt for DWI (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"\nLinear registration of DWI completed. Output file: {diffusion_mni}")
    
    # Rotating BVECs
    bvecs = in_dwi_nii.replace(".nii.gz", ".bvec")
    bvecs_mni = diffusion_mni.replace(".nii.gz", ".bvec")
    if not verify_file(bvecs_mni):
        cmd = [
            "rotate_bvecs",
            "-i", bvecs,  
            "-t", "FA_2_MNI.mat",
            "-o", bvecs_mni
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch rotate_bvecs (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"\nRotating BVECs completed. Output file: {bvecs_mni}")

    # Copy/Rename BVALs
    bval = in_dwi_nii.replace(".nii.gz", ".bval")
    bvals_mni = diffusion_mni.replace(".nii.gz", ".bval")
    if not verify_file(bvals_mni):
        cmd = ["cp", bval, bvals_mni]  
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot copy bvals (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"\nCopy/Rename BVALs completed. Output file: {bvals_mni}")

    # Convert normalized DWI to MIF
    mni_mif_return, mni_mif_msg, diffusion_mni_mif = convert_nifti_to_mif(diffusion_mni, MNI_dir)

    # Brain mask, change after the MNI
    dwi_mask = diffusion_mni_mif.replace(".mif", "_mask_MNI.mif")
    # Check if the file already exists or not
    if not verify_file(dwi_mask):
        cmd = ["dwi2mask", diffusion_mni_mif, dwi_mask] #To try i put this one bad
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch mask (exit code {result})"
            return 0, msg
        else:
            print(f"\nBrain mask completed. Output file: {dwi_mask}")
    

    info_mni = {"dwi_preproc_mni": diffusion_mni_mif,"dwi_mask_mni": dwi_mask, "FA_MNI": fa_mni}
    msg = "\nMNI space step done"
    print(msg)
    return 1, msg, info_mni