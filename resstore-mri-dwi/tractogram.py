"""
Function for tractogram estimation:
    - 

Parameters:
    - 

Returns:
    -
"""

import os
from useful import check_file_ext, execute_command

def tractogram(in_dwi, mask, t1_raw, b0_pair):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    
    # Generate 5-tissue tissue model

    # Create the nocoreg file
    five_tissue = os.path.join(dir_name, '5tt_nocoreg.mif')
    if not os.path.exists(five_tissue):
        cmd = ["5ttgen", "fsl", in_dwi, five_tissue]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not launch 5ttgen (exit code {result})"
            return 0, msg, info
        else:
            print(f"5-tissue tissue model succesfully generated. Output file: {five_tissue}")
    else:
        print(f"Skipping 5-tissue generation step, {five_tissue} already exists.")

    # Convert mean B0 image to NIfTI format
    b0_nifti= b0_pair.replace('.mif', '.nii.gz')
    # Check if the file already exists or not
    if not os.path.exists(b0_nifti):
        cmd = ["mrconvert", b0_pair, b0_nifti]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in mrconvert (B0): {stderr}")
            return
    else:
        print(f"Skipping B0 conversion to NIfTI, {b0_nifti} already exists.")

    # Convert T1 image to NIfTI format
    t1_nii = t1_raw.replace('.mif', '.nii.gz')
    # Check if the file already exists or not
    if not os.path.exists(t1_nii):
        cmd = ["mrconvert", t1_raw, t1_nii]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in mrconvert (T1): {stderr}")
            return
    else:
        print(f"Skipping T1 conversion to NIfTI, {t1_nii} already exists.")

    # Register mean B0 image to T1 image using FSL's FLIRT
    diff2struct_fsl_mat = os.path.join(dir_name, "diff2struct_fsl.mat")
    # Check if the file already exists or not
    if not os.path.exists(diff2struct_fsl_mat):
        cmd = ["flirt", "-in", b0_nifti, "-ref", t1_nii, "-dof", "6", "-omat", diff2struct_fsl_mat]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in flirt: {stderr}")
            return
    else:
        print(f"Skipping FLIRT registration, {diff2struct_fsl_mat} already exists.")

    # Convert FLIRT transformation matrix to MRtrix format
    diff2struct_mrtrix_txt = os.path.join(dir_name, "diff2struct_mrtrix.txt")
    # Check if the file already exists or not
    if not os.path.exists(diff2struct_mrtrix_txt):
        cmd = ["transformconvert", "diff2struct_fsl.mat", b0_nifti, t1_raw, "flirt_import", diff2struct_mrtrix_txt]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in transformconvert b0: {stderr}")
            return
    else:
        print(f"Skipping transformconvert, {diff2struct_mrtrix_txt} already exists.")

    # Apply the inverse transformation to T1 image
    t1_coreg_mif = os.path.join(dir_name, "T1_coreg.mif")
    if not os.path.exists(t1_coreg_mif):
        cmd = ["mrtransform", t1_raw, "-linear", diff2struct_mrtrix_txt, "-inverse", t1_coreg_mif]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in mrtransform (T1): {stderr}")
            return
    else:
        print(f"Skipping T1 inverse transformation, {t1_coreg_mif} already exists.")

    # Apply the inverse transformation to the 5TT image
    five_tissue_coreg = os.path.join(dir_name, "5tt_coreg.mif")
    if not os.path.exists(five_tissue_coreg):
        cmd = ["mrtransform", five_tissue, "-linear", diff2struct_mrtrix_txt, "-inverse", five_tissue_coreg]
        result, stdout, stderr = execute_command(cmd)
        if result != 0:
            print(f"Error in mrtransform (5TT): {stderr}")
            return
    else:
        print(f"Skipping 5TT inverse transformation, {five_tissue_coreg} already exists.")

    print("All processing steps completed successfully.")

    return 