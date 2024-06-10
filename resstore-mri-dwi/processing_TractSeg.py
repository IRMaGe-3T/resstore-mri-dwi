"""
Functions to used TracSeg software:
    - run_tractseg

"""

from useful import check_file_ext, execute_command, verify_file

EXT_NIFTI = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}


def run_tractseg(peaks):
    """
    Run all the command from TractSeg sofware.
    Peaks image should be in NIfTI format
    """

    valid_bool, in_ext, file_name = check_file_ext(peaks, EXT_NIFTI)
    if not valid_bool:
        msg = "\nInput image format is not recognized (NIfTI needed)...!"
        return 0, msg

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
    msg = "Run TracSeg done"
    return 1, msg