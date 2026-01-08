"""
Functions to do "JHU analysis" (registration to MNI):

"""

from useful import execute_command, verify_file
from termcolor import colored
import csv
import os
import pandas as pd
import urllib.request
from termcolor import colored


def register_to_MNI_using_T1w(in_t1, in_t1_brain, mean_b0, in_fa, out_dir):
    """
    FA registation to MNI (FSL MNI152_T1_2mm_brain) using T1w and b0.
    """
    fsl_dir = os.environ.get("FSLDIR")
    template = f"{fsl_dir}/data/standard/MNI152_T1_2mm_brain.nii.gz"
    jhu_labels = f"{fsl_dir}/data/atlases/JHU/JHU-ICBM-labels-2mm.nii.gz"
    jhu = f"{fsl_dir}/data/atlases/JHU/JHU-ICBM-FA-2mm.nii.gz"

    # 1. epi_reg b0 -> T1 (BBR)
    b0_to_T1 = os.path.join(out_dir, "b0_to_T1")
    b0_to_T1_mat = os.path.join(out_dir, "b0_to_T1.mat")
    if not verify_file(b0_to_T1_mat):
        cmd = [
            "epi_reg",
            f"--epi={mean_b0}",
            f"--t1={in_t1}",
            f"--t1brain={in_t1_brain}",
            f"--out={b0_to_T1}"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch epi_reg (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 2. Affine T1 -> MNI
    T1_to_MNI_affine_mat = os.path.join(out_dir, "T1_to_MNI_affine.mat")
    T1_affine_in_MNI =  os.path.join(out_dir, "T1_affine_in_MNI.nii.gz")
    if not verify_file(T1_affine_in_MNI):
        cmd = [
            "flirt",
            "-in", in_t1_brain,
            "-ref", template,
            "-omat", T1_to_MNI_affine_mat,
            "-dof", "12",
            "-cost", "corratio",
            "-out", T1_affine_in_MNI
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch flirt (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 3. FNIRT non-linear
    T12MNI_warp = os.path.join(out_dir, "T12MNI_warp.nii.gz")
    T1_in_MNI =  os.path.join(out_dir, "T1_in_MNI.nii.gz")
    if not verify_file(T1_in_MNI):
        cmd = [
            "fnirt",
            f"--in={in_t1}",
            f"--aff={T1_to_MNI_affine_mat}",
            f"--cout={T12MNI_warp}",
            f"--iout={T1_in_MNI}",
            f"--ref={template}",
            "--config=T1_2_MNI152_2mm"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch fnirt (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 4. Apply warp to FA
    out_fa = os.path.join(out_dir, "FA_in_MNI.nii.gz")
    if not verify_file(out_fa):
        cmd = [
            "applywarp",
            f"--in={in_fa}",
            f"--ref={template}",
            f"--warp={T12MNI_warp}",
            f"--premat={b0_to_T1_mat}",
            f"--out={out_fa}",
            "--interp=trilinear"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch apply warp (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 5. Invert T1->MNI warp
    MNI2T1_warp = os.path.join(out_dir, "MNI2T1_warp.nii.gz")
    if not verify_file(MNI2T1_warp):
        cmd = [
            "invwarp",
            f"--warp={T12MNI_warp}",
            f"--ref={in_t1}",
            f"--out={MNI2T1_warp}"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch inwarp (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 6. Invert linear transform b0->T1
    T1_to_b0_mat = os.path.join(out_dir, "T1_to_b0.mat")
    if not verify_file(T1_to_b0_mat):
        cmd = [
            "convert_xfm",
            "-omat", T1_to_b0_mat,
            "-inverse", b0_to_T1_mat
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch convert_xfm (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 7. Create MNI->FA warp
    MNI2FA_warp = os.path.join(out_dir, "MNI2FA_warp.nii.gz")
    if not verify_file(MNI2FA_warp):
        cmd = [
            "convertwarp",
            f"--ref={in_fa}",
            f"--warp1={MNI2T1_warp}",
            f"--postmat={T1_to_b0_mat}",
            f"--out={MNI2FA_warp}"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch convertwarp (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 8. Warp JHU FA template to subject FA space
    jhu_fa = os.path.join(out_dir, "JHU_in_FAspace.nii.gz")
    if not verify_file(jhu_fa):
        cmd = [
            "applywarp",
            f"--in={jhu}",
            f"--ref={in_fa}",
            f"--warp={MNI2FA_warp}",
            f"--out={jhu_fa}",
            "--interp=trilinear"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch applywarp (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    # 9. Warp JHU labels to subject FA space
    jhu_labels_fa = os.path.join(out_dir, "JHU_labels_in_FAspace.nii.gz")
    if not verify_file(jhu_labels_fa):
        cmd = [
            "applywarp",
            f"--in={jhu_labels}",
            f"--ref={in_fa}",
            f"--warp={MNI2FA_warp}",
            f"--out={jhu_labels_fa}",
            "--interp=nn"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch applywarp (exit code {result}): {stderrl}"
            print(msg)
            return 0, msg

    info_mni = {
        "FA_MNI": out_fa, 
        "T12MNI_warp": T12MNI_warp, 
        "b0_to_T1_mat": b0_to_T1_mat,
        "MNI2FA_warp": MNI2FA_warp
    }
    msg = "\nMNI space step done"
    print(colored("\nMNI step ends", 'cyan'))
    return 1, msg, info_mni


def map_in_MNI_applywarp(map_to_register, T12MNI_warp, b0_to_T1_mat, out_dir):
    """
    Aligning maps in the MNI space

    Parameters:
    - map_to_register: path to the map to register in MNI
    - warp: path to warp
    - out_dir: output directory path 

    """
    _, map_name = os.path.split(map_to_register)
    map_name = map_name.replace(".nii.gz", "_in_MNI.nii.gz")
    map_name = map_name.replace("fit_", "").replace("dipy_", "")
    map_mni = os.path.join(out_dir, map_name)

    fsl_dir = os.environ.get("FSLDIR")
    template = f"{fsl_dir}/data/standard/MNI152_T1_2mm_brain.nii.gz"

    if not verify_file(map_mni):
        cmd = [
            "applywarp",
            f"--in={map_to_register}",
            f"--ref={template}",
            f"--warp={T12MNI_warp}",
            f"--premat={b0_to_T1_mat}",
            f"--out={map_mni}",
            "--interp=trilinear"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            print(f"\nCan not pass map in the MNI space (exit code {result}): {stderrl}")

