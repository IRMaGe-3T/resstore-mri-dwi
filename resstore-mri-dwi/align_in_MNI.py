# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - doswnload_template: template for aligning in the MNI space
    - run_register_mni: get the matrices and align dwi images in the mni
    - map_in_MNI: align any map in the MNI space
"""

import os
import urllib.request
from useful import verify_file, execute_command, check_file_ext, convert_mif_to_nifti, convert_nifti_to_mif




def download_template(dir_name):
    """
    Function to download the template file if it doesn't exist

    Parameters:
    - dir_name: directory where the template will be downloaded

    Returns: 
    - template_path
    """

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





def map_in_MNI(map, MNI_dir, NODDI_dir, DKI_dir):
    """
    Aligning NODDI and DKI maps in the MNI space

    Parameters:
    - map: path to the map
    - MNI_dir: path to MNI directory
    - NODDI_dir
    - DKI_dir
    """
        
    map_dir = os.path.dirname(map) # Either NODDI or DKI path
    _, map_name = os.path.split(map)
    map_name = map_name.replace(".nii.gz", "_MNI.nii.gz")
    template = os.path.join(MNI_dir, "MNI_FA_template.nii.gz")
    if not os.path.exists(template):
        template = download_template(MNI_dir)
    if map_dir == NODDI_dir:
        MNI_NODDI_dir = os.path.join(MNI_dir, "NODDI_MNI")
        if not os.path.exists(MNI_NODDI_dir):
            os.mkdir(MNI_NODDI_dir)
        map_mni = os.path.join(MNI_NODDI_dir, map_name)
    if map_dir == DKI_dir:
        MNI_DKI_dir = os.path.join(MNI_dir, "DKI_MNI")
        if not os.path.exists(MNI_DKI_dir):
            os.mkdir(MNI_DKI_dir)
        map_mni = os.path.join(MNI_DKI_dir, map_name)

    if not verify_file(map_mni):
        cmd = [
            "flirt",
            "-ref", template, 
            "-in", map,
            "-out", map_mni,
            "-omat", "FA_2_MNI.mat",
            "-dof", "6",
            "-cost", "mutualinfo",
            "-searchcost", "mutualinfo"
        ]
        result, stderr, stdout = execute_command(cmd)
        if result != 0:
            print(f"\nCan not pass map in the MNI space (exit code {result}): {stderr}")