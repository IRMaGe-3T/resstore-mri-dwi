"""
Functions to do TractSeg analysis (registration to MNI + run tractseg):
    - run_tractseg
    - replace_dots_with_commas
    - tractometry_postprocess
    - download_template: template for aligning in the MNI space
    - register_to_MNI_FA: align FA and DWI to MNI using TractSeg Template
    - map_in_MNI_flirt: align any map in the MNI space

"""

from useful import check_file_ext, execute_command, verify_file, download_subjects_txt, plot_cst_data, convert_mif_to_nifti, convert_nifti_to_mif
from termcolor import colored
import csv
import os
import pandas as pd
import urllib.request
from termcolor import colored

EXT_NIFTI = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}
EXT_MIF = {"MIF": "mif"}


def run_tractseg(peaks, Tract_dir):
    """
    Run all the commands from TractSeg software.

    Parameters:
    peaks (str): Path to the peaks image in NIfTI format.

    Returns:
    tuple: A tuple containing a status code (1 for success, 0 for failure)
           and a message indicating the result or error.
    """

    # Check if peaks has the right format
    valid_bool, in_ext, file_name = check_file_ext(peaks, EXT_NIFTI)
    print(colored("\n~~TractSeg running~~", "cyan"))
    if not valid_bool:
        msg = "\nInput image format is not recognized (NIfTI needed)...!"
        return 0, msg

    # Copy peaks into the tracto directory
    peaks_tracto = os.path.join(Tract_dir, "peaks.nii")
    tractseg_out_dir = os.path.join(Tract_dir, "tractseg_output")
    bundle = os.path.join(tractseg_out_dir, "bundle_segmentations")
    if not verify_file(bundle):
        if not verify_file(peaks_tracto):
            cmd = ["cp", peaks, peaks_tracto]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not copy peaks in the tracto directory: {result})"
                return 0, msg

    # Run all usefull TractSeg commands
    tractseg_out_dir = os.path.join(Tract_dir, "tractseg_output")
    bundle = os.path.join(tractseg_out_dir, "bundle_segmentations")
    ending_segm = os.path.join(tractseg_out_dir, "endings_segmentations")
    uncertainty = os.path.join(tractseg_out_dir, "bundle_uncertainties")
    TOM = os.path.join(tractseg_out_dir, "TOM")
    TOM_trackings = os.path.join(tractseg_out_dir, "TOM_trackings")

    if not verify_file(bundle):
        cmd = ["TractSeg", "-i", peaks_tracto,
               "--output_type", "tract_segmentation"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg tract_segmentation (exit code {result})"
            return 0, msg

    print(f"\n    end: {ending_segm}")
    if not verify_file(ending_segm):
        cmd = ["TractSeg", "-i", peaks_tracto,
               "--output_type", "endings_segmentation"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg endings_segmentation (exit code {result})"
            return 0, msg

    if not verify_file(TOM):
        cmd = ["TractSeg", "-i", peaks_tracto, "--output_type", "TOM"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg TOM (exit code {result})"
            return 0, msg

    if not verify_file(TOM_trackings):
        cmd = ["Tracking", "-i", peaks_tracto, "--tracking_format", "tck"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg Tracking (exit code {result})"
            return 0, msg

    if not verify_file(uncertainty):
        cmd = ["TractSeg", "-i", peaks_tracto, "--uncertainty"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg uncertainty (exit code {result})"
            return 0, msg

    msg = "\nRun TracSeg done"
    print(colored(msg, "cyan"))
    return 1, msg


# def replace_dots_with_commas(value):
#     if isinstance(value, str):
#         return value.replace('.', ',')
#     return value

def tractometry_postprocess(map, Tract_dir):
    """
    Tractometry

    """

    # Check if FA map has the right format (nifti)
    # If format is mif, convert it to (nifti)
    valid_bool, in_ext, file_name = check_file_ext(map, EXT_NIFTI)
    map_nii = map.replace(".mif", ".nii.gz")
    if not valid_bool:
        print("\nInput map is not nifti.\n")
        valid_bool, in_ext, file_name = check_file_ext(map, EXT_MIF)
        if not valid_bool:
            msg = f"\nCannot perform tractography, map do not have the right format {result}"
            return 0, msg
        else:
            print("\n FA is in mif format.\n")
            if not verify_file(map_nii):
                cmd = ["mrconvert", map, map_nii]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCan not convert mif to nii for input map: {result})"
                    return 0, msg
            else:
                print("\n map already exist in nii format.\n")

    # Create paths
    tractseg_out_dir = os.path.join(Tract_dir, "tractseg_output")
    ending_segm = os.path.join(tractseg_out_dir, "endings_segmentations")
    TOM_trackings = os.path.join(tractseg_out_dir, "TOM_trackings")
    peaks_tracto = os.path.join(Tract_dir, "peaks.nii")

    # Run tractometry to create csv file
    if (os.path.exists(TOM_trackings) and os.path.exists(ending_segm)):
        _, map_name_ext = os.path.split(map_nii)
        map_name, _ = os.path.splitext(map_name_ext)
        map_name, _ = os.path.splitext(map_name)
        map_name = map_name.replace("fit_", "")
        map_name = map_name.replace("dipy_", "")
        tracto_csv = os.path.join(
            tractseg_out_dir, "tractometry_" + map_name + ".csv")
        if not verify_file(tracto_csv):
            cmd = ["Tractometry", "-i", TOM_trackings, "-o",
                   tracto_csv, "-e", ending_segm, "-s", map_nii]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not run tractometry: {result})"
                return 0, msg


    if verify_file(peaks_tracto):
        cmd = ["rm", peaks_tracto]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not delete peaks copy in the tracto directory: {result})"
            return 0, msg

    # Download subjects.txt template
    subjects_txt = download_subjects_txt(tractseg_out_dir)

    if verify_file(tracto_csv):
        # Read the content of the .txt file
        with open(subjects_txt, "r") as file:
            lines = file.readlines()
        # Modify the first line
        lines[0] = f"# tractometry_path={tracto_csv}\n"
        # Write the modified content back to the .txt file
        with open(subjects_txt, "w") as file:
            file.writelines(lines)
        print(
            f"\nUpdated the first line of {subjects_txt} with the path to the CSV file.\n")

    FA_graphs = os.path.join(
        tractseg_out_dir, map_name + "_graphs_TractSeg.png")
    if not verify_file(FA_graphs):
        cmd = ["plot_tractometry_results", "-i",
               subjects_txt, "-o", FA_graphs, "--mc"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not create plots with TractSeg: {result})"
            return 0, msg

    plot_cst_data(tracto_csv, map_name)

    # df = pd.read_csv(tracto_csv)
    # df = df.applymap(replace_dots_with_commas)
    # df.to_csv(tracto_csv, index=False)


    # # Read the CSV file and process it line by line
    # with open(tracto_csv, 'r', newline='', encoding='utf-8') as csvfile:
    #     reader = csv.reader(csvfile)
    #     lines = list(reader)

    # # Write the processed lines to a TSV file
    # with open(tsv_file_path, 'w', newline='', encoding='utf-8') as tsvfile:
    #     writer = csv.writer(tsvfile, delimiter='\t')
    #     writer.writerows(lines)

    # # Remove the original CSV file
    # os.remove(tracto_csv)


    msg = "\nRun postprocessing for tractometry done"
    print(colored(msg, "cyan"))
    return 1, msg


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


def register_to_MNI_FA(in_dwi, in_fa, MNI_dir):
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
    print(colored("\n~~MNI step starts~~", 'cyan'))

    # Download the template file
    template_path = download_template(MNI_dir)

    # Convert MIF to NIfTI
    # Diffusion
    dwi_nii_return, dwii_nii_msg, in_dwi_nii = convert_mif_to_nifti(
        in_dwi, preproc_dir)
    # FA
    if ".mif" in in_fa:
        fa_nii_return, fa_nii_msg, in_fa_nii = convert_mif_to_nifti(
            in_fa, FA_dir, False)
    else:
        in_fa_nii = in_fa

    # Linear registration of FA
    fa_mni = os.path.join(MNI_dir, "FA_MNI.nii.gz")
    omat = os.path.join(MNI_dir,  "FA_2_MNI.mat")
    if not verify_file(fa_mni):
        cmd = [
            "flirt",
            "-ref", template_path,
            "-in", in_fa_nii,
            "-out", fa_mni,
            "-omat", omat,
            "-dof", "6",
            "-cost", "mutualinfo",
            "-searchcost", "mutualinfo"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not launch flirt for FA (exit code {result})"
            return 0, msg, info_mni
        else:
            print(
                f"\nLinear registration of FA completed. Output file: {fa_mni}")

    # Linear registration of DWI
    diffusion_mni = os.path.join(MNI_dir, "dwi_MNI.nii.gz")
    if not verify_file(diffusion_mni):
        cmd = [
            "flirt",
            "-ref", template_path,
            "-in", in_dwi_nii,
            "-out", diffusion_mni,
            "-applyxfm",
            "-init", omat,
            "-dof", "6"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch flirt for DWI (exit code {result})"
            return 0, msg, info_mni
        else:
            print(
                f"\nLinear registration of DWI completed. Output file: {diffusion_mni}")

    # Rotating BVECs
    bvecs = in_dwi_nii.replace(".nii.gz", ".bvec")
    bvecs_mni = diffusion_mni.replace(".nii.gz", ".bvec")
    if not verify_file(bvecs_mni):
        cmd = [
            "rotate_bvecs",
            "-i", bvecs,
            "-t", omat,
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
    mni_mif_return, mni_mif_msg, diffusion_mni_mif = convert_nifti_to_mif(
        diffusion_mni, MNI_dir)

    # Brain mask, change after the MNI
    dwi_mask = diffusion_mni_mif.replace(".mif", "_MNI_mask.mif")
    dwi_mask_nii = dwi_mask.replace(".mif", ".nii.gz")
    bzeros_MNI =  diffusion_mni.replace(".nii.gz","_bzero.nii.gz")
    bzeros_MNI_mean =  diffusion_mni.replace(".nii.gz","_bzero_mean.nii.gz")
    # Check if the file already exists or not
    if not verify_file(dwi_mask):
        # cmd = ["dwi2mask", diffusion_mni_mif, dwi_mask]
        # result, stderrl, sdtoutl = execute_command(cmd)
        # if result != 0:
        #     msg = f"\nCannot launch mask (exit code {result})"
        #     return 0, msg
        # else:
        #     print(f"\nBrain mask completed. Output file: {dwi_mask}")

        if not verify_file(bzeros_MNI_mean):
            cmd = [
                "dwiextract", diffusion_mni_mif, bzeros_MNI, "-bzero"

            ]
            result, stderrl, stdoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCannot launch dwiextract (exit code {result})"
                return 0, msg

            cmd = [
                "mrmath", bzeros_MNI, "mean",  bzeros_MNI_mean,  "-axis",  "3"
            ]
            result, stderrl, stdoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCannot launch mrmaths (exit code {result})"
                return 0, msg

        cmd = [
            "bet", bzeros_MNI_mean, dwi_mask_nii.replace("_mask.nii.gz",""),  "-m", "-n"
        ]
        result, stderrl, stdoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCannot launch bet (exit code {result})"
            return 0, msg
        if not verify_file(dwi_mask):
            convert_nifti_to_mif(dwi_mask_nii, MNI_dir, diff=False)    


    info_mni = {"dwi_preproc_mni": diffusion_mni_mif,
                "dwi_mask_mni": dwi_mask, "FA_MNI": fa_mni}
    msg = "\nMNI space step done"
    print(colored("\nMNI step ends", 'cyan'))
    return 1, msg, info_mni


def map_in_MNI_flirt_applyxfm(map_to_register, out_dir, MNI_dir):
    """
    Aligning maps in the MNI space

    Parameters:
    - map_to_register: path to the map to register in MNI
    - out_dir: output directory path
    - MNI_dir: directory with the template for MNI registration

    """
    _, map_name = os.path.split(map_to_register)
    map_name = map_name.replace(".nii.gz", "_MNI.nii.gz")
    map_name = map_name.replace("fit_", "")
    map_name = map_name.replace("dipy_", "")
    map_mni = os.path.join(out_dir, map_name)
    template = os.path.join(MNI_dir, "MNI_FA_template.nii.gz")
    omat = os.path.join(MNI_dir,  "FA_2_MNI.mat")
    if not os.path.exists(template):
        template = download_template(MNI_dir)

    if not verify_file(map_mni):
        cmd = [
            "flirt",
            "-ref", template,
            "-in", map_to_register,
            "-out", map_mni,
            "-applyxfm",
            "-init", omat,
            "-dof", "6"
        ]
        result, stderr, stdout = execute_command(cmd)
        if result != 0:
            print(f"\nCan not pass map in the MNI space (exit code {result}): {stderr}")
