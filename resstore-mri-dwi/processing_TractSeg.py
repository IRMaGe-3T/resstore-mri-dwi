"""
Functions to used TracSeg software:
    - run_tractseg

"""

from useful import check_file_ext, execute_command, verify_file, download_subjects_txt, plot_cst_data
import os

EXT_NIFTI = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}
EXT_MIF = {"MIF": "mif"}


def run_tractseg(peaks, FA_map, Tract_dir):
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
    FA_nii = FA_map.replace(".mif", ".nii.gz")
    if not valid_bool:
        print("\nInput FA_map is not nifti.\n")
        valid_bool, in_ext, file_name = check_file_ext(FA_map, EXT_MIF)
        if not valid_bool:
            msg = f"\nCannot perform tractography, FA_map do not have the right format {result}"
            return 0, msg
        else: 
            print("\n FA is in mif format.\n")
            if not verify_file(FA_nii):
                cmd = ["mrconvert", FA_map, FA_nii]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCan not convert mif to nii for FA_map: {result})"
                    return 0, msg
            else:
                print("\n FA  already exist in nii format, we'll use it.\n")

    # Copy peaks into the tracto directory
    peaks_tracto = os.path.join(Tract_dir, "peaks.nii")
    if not verify_file(peaks_tracto):
        cmd = ["cp", peaks, peaks_tracto]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not copy peaks in the tracto directory: {result})"
            return 0, msg

    # Run all usefull TractSeg commands
    tractseg_out_dir=os.path.join(Tract_dir, "tractseg_output")
    bundle = os.path.join(tractseg_out_dir, "bundle_segmentations")
    ending_segm= os.path.join(tractseg_out_dir, "endings_segmentations")
    uncertainty = os.path.join(tractseg_out_dir, "bundle_uncertainties")
    TOM = os.path.join(tractseg_out_dir, "TOM")
    TOM_trackings = os.path.join(tractseg_out_dir, "TOM_trackings")

    if not verify_file(bundle):
        cmd = ["TractSeg", "-i", peaks_tracto, "--output_type", "tract_segmentation"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not run TractSeg tract_segmentation (exit code {result})"
            return 0, msg
    
    print(f'\n    end: {ending_segm}')
    if not verify_file(ending_segm):
        cmd = ["TractSeg", "-i", peaks_tracto, "--output_type", "endings_segmentation"]
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
    
    # Run tractometry to create csv file
    if (os.path.exists(TOM_trackings) and os.path.exists(ending_segm)):
        tracto_csv = os.path.join(tractseg_out_dir, "tractometry.csv")
        if not verify_file(tracto_csv):
            cmd = ["Tractometry", "-i", TOM_trackings, "-o", tracto_csv, "-e", ending_segm, "-s", FA_nii]
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
        
    #Download subjects.txt template
    subjects_txt = download_subjects_txt(tractseg_out_dir)

    if verify_file(tracto_csv):
        # Read the content of the .txt file
        with open(subjects_txt, 'r') as file:
            lines = file.readlines()
        # Modify the first line
        lines[0] = f"# tractometry_path={tracto_csv}\n"
        # Write the modified content back to the .txt file
        with open(subjects_txt, 'w') as file:
            file.writelines(lines)
        print(f"\nUpdated the first line of {subjects_txt} with the path to the CSV file.\n")

    FA_graphs = os.path.join(tractseg_out_dir, "FA_graphs_TractSeg")
    if not verify_file(FA_graphs):
        cmd = ["plot_tractometry_results", "-i", subjects_txt, "-o", FA_graphs, "--mc"]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not create FA plots with TractSeg: {result})"
            return 0, msg

    plot_cst_data(tracto_csv)

    msg = "\nRun TracSeg done"
    return 1, msg