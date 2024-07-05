import os
from useful import execute_command, convert_mif_to_nifti, verify_file

def run_preproc_t1(in_t1_nifti, in_dwi):
    """
    Coregister T1w to DWI

    Parameters:
    -----------
    in_t1_nifti : str
        Path to the T1-weighted image in NIfTI format.
    in_dwi : str
        Path to the diffusion-weighted image (DWI) in MIF format.

    Returns:
    --------
    tuple
        A tuple containing the execution status (0 if an error occurred, 1 otherwise),
        a message describing the execution result, and an information dictionary (info).
        If the status is 1, info will contain the path to the coregistered T1 image.
    """

    # Get name directory and create info 
    info = {}
    MNI_dir = os.path.dirname(in_dwi)
    
    # Extract b0 from dwi
    in_dwi_b0 = in_dwi.replace(".mif", "_bzero.mif")
    if not verify_file(in_dwi_b0):
        cmd = ["dwiextract", in_dwi, in_dwi_b0, "-bzero"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch dwiextract (exit code {result})"
            return 0, msg, info
        
    # Convert preprocessed dwi back to nifti
    in_dwi_b0_nii = in_dwi_b0.replace(".mif", ".nii.gz")
    if not verify_file(in_dwi_b0_nii):
        result, msg, in_dwi_b0_nii = convert_mif_to_nifti(
            in_dwi_b0, MNI_dir, diff=False
        )

    # Creating tissue boundaries
    tissue_type = os.path.join(MNI_dir, "5tt.nii.gz")
    if not verify_file(tissue_type):
        cmd = ["5ttgen", "fsl", in_t1_nifti, tissue_type]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch 5ttgen (exit code {result})"
            return 0, msg, info

    # Extract gm info 
    grey_matter = tissue_type.replace(".nii.gz", "_gm.nii.gz")
    if not verify_file(grey_matter):
        cmd = ["fslroi", tissue_type, grey_matter, "0", "1"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch fslroi (exit code {result})"
            return 0, msg, info


    # Coregistration of T1 with DWI
    # Get transfo matrix to go from dwi to gm 
    transfo_mat = os.path.join(MNI_dir, "diff2struct_fsl.mat")
    if not verify_file(transfo_mat):
        cmd = [
            "flirt",
            "-in",
            in_dwi_b0_nii,
            "-ref",
            grey_matter,
            "-interp",
            "nearestneighbour",
            "-dof",
            "6",
            "-omat",
            transfo_mat,
        ]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch flirt (exit code {result})"
            return 0, msg, info


    # Convert the matrix (dwi --> gm) to the right format (diff2struct.txt) for the next step
    diff2struct = os.path.join(MNI_dir, "diff2struct_mrtrix.txt")
    if not verify_file(diff2struct):
        cmd = [
            "transformconvert",
            transfo_mat,
            in_dwi_b0_nii,
            tissue_type,
            "flirt_import",
            diff2struct,
        ]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch transformconvert (exit code {result})"
            return 0, msg, info

    # Apply inverse transfo to t1 (gm --> dwi)
    # Then t1_coreg is align on dwi image
    in_t1_coreg = tissue_type.replace("_5tt.nii.gz", "_t1_correg.mif")
    if not verify_file(in_t1_coreg):
        cmd = [
            "mrtransform",
            in_t1_nifti,
            "-linear",
            diff2struct,
            "-inverse",
            in_t1_coreg,
        ]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = "\nCan not lunch mrtransform (exit code {result})"
            return 0, msg, info

    # Apply inverse transfo to tissue type (gm --> dwi)
    # Then tissue_type_correg is aligned on dwi
    tissue_type_coreg = tissue_type.replace(".nii.gz", "_coreg_dwi.mif")
    if not verify_file(tissue_type_coreg):
        cmd = [
            "mrtransform",
            tissue_type,
            "-linear",
            diff2struct,
            "-inverse",
            tissue_type_coreg,
        ]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = "\nCan not lunch mrtransform (exit code {result})"
            return 0, msg, info

    # Create seed
    seed_boundary = os.path.join(MNI_dir, "gmwmSeed_coreg_dwi.mif")
    if not verify_file(seed_boundary):
        cmd = ["5tt2gmwmi", tissue_type_coreg, seed_boundary]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not lunch 5tt2gmwmi (exit code {result})"
            return 0, msg, info
        info = {"in_t1_coreg": in_t1_coreg}
        msg = "\nPreprocessing T1 done"
        return 1, msg, info