# -*- coding: utf-8 -*-
"""
Functions for preprocessing DWI data:
    - get_dwifslpreproc_command
    - run_preproc_dwi: perform preprocessing and optional FOD 
"""

import os
import urllib.request

from useful import check_file_ext, convert_mif_to_nifti, execute_command, verify_file

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
            msg = f"Cannot launch dwidenoise (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"Denoise completed. Output file: {dwi_denoise}")
    else:
        print(f"Skipping denoise step, {dwi_denoise} already exists.")

    # DeGibbs / Unringing
    dwi_degibbs = dwi_denoise.replace("_denoise.mif", "_denoise_degibbs.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_degibbs):
        cmd = ["mrdegibbs", dwi_denoise, dwi_degibbs]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot launch mrdegibbs (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"Unringing completed. Output file: {dwi_degibbs}")
    else:
        print(f"Skipping unringing step, {dwi_degibbs} already exists.")

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
                            msg = f"Cannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("b0_PA successfully extracted")
                    else:
                        print("Skipping b0_PA extraction, file already exists")
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
                            msg = f"Cannot launch dwiextract (exit code {result})"
                            return 0, msg, info_prepoc
                        else:
                            print("b0_AP successfully extracted")
                    else:
                        print("Skipping b0_AP extraction, file already exists")
                        
                # Create command for concatenation
                cmd = ["mrcat", in_pepolar_AP, in_pepolar_PA, b0_pair]
            # Concatenate both b0 images to create b0_pair     
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"Cannot launch mrcat to create b0_pair (exit code {result})"
                return 0, msg, info_prepoc
            else:
                print(f"B0_pair successfully created. Output file: {b0_pair}")
        else:
            print(f"Skipping b0_pair creation step, {b0_pair} already exists.")
            
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
            msg = f"Cannot launch dwifslpreproc (exit code {result})"
            return 0, msg, info_prepoc
        else:
            print(f"Motion and distortion correction completed. Output file: {dwi_preproc}")
            
    else:
        print(f"Skipping motion correction step, {dwi_preproc} already exists.")


    # Bias correction
    dwi_unbias = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_unbiased.mif")
    bias_output = dwi_preproc.replace("_degibbs_preproc.mif", "_degibbs_preproc_bias.mif")
    # Check if the file already exists or not
    if not os.path.exists(dwi_unbias) and not os.path.exists(bias_output):
        cmd = ["dwibiascorrect", "ants", dwi_preproc, dwi_unbias, "-bias", bias_output]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot launch bias correction (exit code {result})"
            return 0, msg
        else:
            print(f"Bias correction completed. Output files: {dwi_unbias}, {bias_output}")
    else:
       print(f"Skipping bias correction step, {dwi_unbias} and/or {bias_output} already exists.")

    # # Brain mask, change after the MNI
    # dwi_mask = dwi_unbias.replace("_degibbs_preproc_unbiased.mif", "_dwi_brain_mask.mif")
    # # Check if the file already exists or not
    # if not os.path.exists(dwi_mask):
    #     cmd = ["dwi2mask", dwi_unbias, dwi_mask]
    #     result, stderrl, sdtoutl = execute_command(cmd)
    #     if result != 0:
    #         msg = f"Cannot launch mask (exit code {result})"
    #         return 0, msg
    #     else:
    #         print(f"Brain mask completed. Output file: {dwi_mask}")
    # else:
    #    print(f"Skipping brain mask step, {dwi_mask} already exists.")


        
    info_preproc = {"dwi_preproc": dwi_unbias,"b0_pair": b0_pair}
    msg = "Preprocessing DWI done"
    print(msg)
    return 1, msg, info_preproc

# Function to download the template file if it doesn't exist
def download_template(in_dir):
    github_repo_url = "https://github.com/your_username/your_repository/raw/main/resources/MNI_FA_template.nii.gz"
    template_filename = "MNI_FA_template.nii.gz"
    template_path = os.path.join(in_dir, template_filename)
    
    # Check if the template file already exists
    if not os.path.exists(template_path):
        try:
            print("Downloading MNI_FA_template.nii.gz...")
            urllib.request.urlretrieve(github_repo_url, template_path)
            print("Template file downloaded successfully.")
        except Exception as e:
            print(f"Failed to download the template file: {e}")
            return None
    
    return template_path

def run_register_MNI(in_dwi, in_fa):
    """
    Run preproc for whole brain diffusion using MRtrix command and an optional FOD estimation 

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
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    in_dwi_nii = in_dwi
    in_fa_nii = in_fa

    # Download the template file
    template_path = download_template(in_dwi)

    voxels = os.path.join(dir_name + "_voxels.mif")

    # Linear registration of FA
    fa_mni = os.path.join(dir_name, "FA_MNI.nii.gz")
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
            msg = f"Can not launch flirt for FA (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"Successfully created FA_MNI.nii.gz. Output file: {fa_mni}")

    # Linear registration of DWI
    diffusion_mni = os.path.join(dir_name, "Diffusion_MNI.nii.gz")
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
            msg = f"Cannot launch flirt for DWI (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"Linear registration of DWI completed. Output file: {diffusion_mni}")
    
    # Rotating BVECs
    bvecs_mni = os.path.join(dir_name, "Diffusion_MNI.bvecs")
    if not verify_file(bvecs_mni):
        cmd = [
            "rotate_bvecs",
            "-i", "bvecs",  #Preguntar de donde vienen estos bvecs
            "-t", "FA_2_MNI.mat",
            "-o", bvecs_mni
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot launch rotate_bvecs (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"Rotating BVECs completed. Output file: {bvecs_mni}")

    # Copy/Rename BVALs
    bvals_mni = os.path.join(dir_name, "Diffusion_MNI.bvals")
    if not verify_file(bvals_mni):
        cmd = ["cp", "bvals", bvals_mni]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot copy bvals (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"Copy/Rename BVALs completed. Output file: {bvals_mni}")

    # Convert normalized DWI to MIF
    diffusion_mni_mif = os.path.join(dir_name, "Diffusion_MNI.mif")
    if not verify_file(diffusion_mni_mif):
        cmd = [
            "mrconvert",
            diffusion_mni,
            diffusion_mni_mif,
            "-fslgrad", bvecs_mni, bvals_mni
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"Cannot convert DWI to MIF (exit code {result})"
            return 0, msg, info_mni
        else:
            print(f"Convert normalized DWI to MIF completed. Output file: {diffusion_mni_mif}")

    # Brain mask, change after the MNI
        dwi_mask = dwi_unbias.replace("_degibbs_preproc_unbiased.mif", "_dwi_brain_mask.mif")
        # Check if the file already exists or not
        if not os.path.exists(dwi_mask):
            cmd = ["dwi2mask", dwi_unbias, dwi_mask]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"Cannot launch mask (exit code {result})"
                return 0, msg
            else:
                print(f"Brain mask completed. Output file: {dwi_mask}")
        else:
        print(f"Skipping brain mask step, {dwi_mask} already exists.")

    
    # Write average response to file
    average_response_path = os.path.join(i['path'], "average-response.txt")
    with open(average_response_path, "w+") as f:
        f.write('768.08558 -327.24084 72.15579 -11.15219 1.28727')
    print(f"Successfully wrote average response to {average_response_path}") #test







