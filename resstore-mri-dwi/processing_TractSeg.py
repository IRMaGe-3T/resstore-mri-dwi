"""
Functions to used TracSeg software:
    - run_tractseg

"""

from useful import check_file_ext, execute_command, verify_file
import os

EXT_NIFTI = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}
EXT_MIF = {"MIF": "mif"}


def run_tractseg(peaks, FA_map):
    """
    Run all the commands from TractSeg software.
    
    Parameters:
    peaks (str): Path to the peaks image in NIfTI format.
    FA_map (str): Path to the FA map, which can be in NIfTI or MIF format.
    
    Returns:
    tuple: A tuple containing a status code (1 for success, 0 for failure) 
           and a message indicating the result or error.
    """

    # Check if peaks has the right format
    valid_bool, in_ext, file_name = check_file_ext(peaks, EXT_NIFTI)
    if not valid_bool:
        msg = "\nInput image format is not recognized (NIfTI needed)...!"
        return 0, msg
    
    # Check if FA map has the right format (nifti)
    # If format is mif, convert it to (nifti)
    valid_bool, in_ext, file_name = check_file_ext(FA_map, EXT_NIFTI)
    if not valid_bool:
        print("\nInput FA_map is not nifti.\n")
        valid_bool, in_ext, file_name = check_file_ext(FA_map, EXT_MIF)
        if not valid_bool:
            msg = f"Cannot perform tractography, FA_map do not have the right format {result}"
            return 0, msg
        else: 
            print("\n FA is in mif format.\n")
            dir_name_FA = os.path.dirname(FA_map)
            FA_nii = dir_name_FA.replace(".mif", ".nii.gz")
            if not verify_file(FA_nii):
                cmd = ["mrconvert", FA_map, FA_nii]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"Can not convert mif to nii for FA_map: {result})"
                    return 0, msg
            else:
                print("\n FA  already exist in nii format, we'll use it.\n")

    # Run all usefull TractSeg commands
    cmd = ["TractSeg", "-i", peaks, "--output_type", "tract_segmentation"]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not run TractSeg tract_segmentation (exit code {result})"
        return 0, msg
    cmd = ["TractSeg", "-i", peaks, "--output_type", "endings_segmentation"]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not run TractSeg endings_segmentation (exit code {result})"
        return 0, msg
    cmd = ["TractSeg", "-i", peaks, "--output_type", "TOM"]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not run TractSeg TOM (exit code {result})"
        return 0, msg
    cmd = ["Tracking", "-i", peaks, "--tracking_format", "tck"]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not run TractSeg Tracking (exit code {result})"
        return 0, msg
    cmd = ["TractSeg", "-i", peaks, "--uncertainty"]
    result, stderrl, sdtoutl = execute_command(cmd)
    if result != 0:
        msg = f"Can not run TractSeg uncertainty (exit code {result})"
        return 0, msg
    
    # Run tractometry to create csv file
    dir_name = os.path.dirname(peaks)
    tractseg_out_dir=os.path.join(dir_name, "tractseg_output")
    TOM_trackings = os.path.join(tractseg_out_dir, "TOM_trackings")
    ending_segm= os.path.join(tractseg_out_dir, "endings_segmentation")
    if (os.path.exists(TOM_trackings) and os.path.exists(ending_segm)):
        tracto_csv = os.path.join(tractseg_out_dir, "tactometry.csv")
        if not verify_file(tracto_csv):
            cmd = ["Tractometry", "-i", TOM_trackings, "-o", tracto_csv, "-e", ending_segm, "-s", FA_nii]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"Can not run tractometry: {result})"
                return 0, msg

    msg = "Run TracSeg done"
    return 1, msg