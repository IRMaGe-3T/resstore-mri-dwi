"""
Useful functions :

    - check_file_ext
    - execute_command
    - convert_mif_to_nifti
    - convert_nifti_to_mif
    - get_shell
    -download_subjects_txt
"""

import os
import subprocess
import shutil
import urllib.request

EXT_NIFTI = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"}
EXT_MIF = {"MIF": "mif"}






def check_file_ext(in_file, ext_dic):
    """Check file extension
    
    Parameters:
    - in_file: file name (a string)
    - ext_dic: dictionary of the valid extensions for the file
                    (dictionary, ex:
                    EXT = {"NIFTI_GZ": "nii.gz", "NIFTI": "nii"})
    Returns:
    - valid_bool: True if extension is valid (a boolean)
    - in_ext: file extension (a string)
    - file_name: file name without extension (a string)
    """
    # Get file extension
    valid_bool = False
    ifile = os.path.split(in_file)[-1]
    file_name, in_ext = ifile.rsplit(".", 1)
    if in_ext == "gz":
        (file_name_2, in_ext_2) = file_name.rsplit(".", 1)
        in_ext = in_ext_2 + "." + in_ext
        file_name = file_name_2

    valid_ext = list(ext_dic.values())

    if in_ext in valid_ext:
        valid_bool = True

    return valid_bool, in_ext, file_name

def verify_file(file_path):
    if os.path.exists(file_path):
        print(f"\nFile {file_path} already exists. Verifying contents...")
        return True
    else:
        return False


def execute_command(command):
    """Execute command

    Parameters:
    - command: command to execute (a list)

    Examples:
    - command = ['cd', 'path']
    """
    print("\n", command)
    p = subprocess.Popen(
        command,
        shell=False,
        bufsize=-1,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    print("--------->PID:", p.pid)

    (sdtoutl, stderrl) = p.communicate()
    if str(sdtoutl) != "":
        print("sdtoutl: ", sdtoutl.decode())
    if str(stderrl) != "":
        print("stderrl: ", stderrl.decode())

    result = p.wait()

    return result, stderrl, sdtoutl





def convert_mif_to_nifti(in_file, out_directory, diff=True):
    """
    Convert NIfTI into MIF format

    Parameters: 
    - in_file: file in .mif format
    - out_directory: path to the directory that should store the .mif file 
    - diff: by default set to True to take the bvec and bval files 

    Returns:
    - int: 1 problem, 0 success
    - msg 
    - in_file_niftii: converted file in .nii format
    """

    in_file_nifti = None
    # Check inputs files and get files name
    valid_bool, ext, file_name = check_file_ext(in_file, EXT_MIF)
    if not valid_bool:
        msg = "\nInput image format is not " "recognized (mif needed)...!"
        return 0, msg, in_file_nifti

    # Convert diffusions into ".mif" format (mrtrix format)
    in_file_nifti = os.path.join(out_directory, file_name + ".nii.gz")
    if not verify_file(in_file_nifti):
        if diff:
            bvec = in_file.replace(ext, "bvec")
            bval = in_file.replace(ext, "bval")
            cmd = [
                "mrconvert",
                in_file,
                in_file_nifti,
                "-export_grad_fsl",
                bvec,
                bval,
            ]
        else:
            cmd = ["mrconvert", in_file, in_file_nifti]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Issue during conversion of {in_file} to nifti format"
            return 0, msg, in_file_nifti
        msg = f"Conversion of {in_file} to nifti format done"
    else:
        msg= None
    print(msg)
    return 1, msg, in_file_nifti






def convert_nifti_to_mif(in_file, out_directory, diff=True):
    """Convert NIfTI into MIF format
    
    Parameters:
    - in_file: file in .nii format 
    - out_directory: path to the directory that should store the .mif file 
    - diff: by default set to True to take the bvec and bval files 

    Returns:
    - int: 1 problem, 0 success
    - msg 
    - in_file_mif: converted file in .mif format
    """
    in_file_mif = None
    
    # Check inputs files and get files name
    valid_bool, ext, file_name = check_file_ext(in_file, EXT_NIFTI)
    if not valid_bool:
        msg = (
            "\nInput image format is not "
            "recognized (nii or nii.gz needed)...!"
        )
        return 0, msg, in_file_mif
    
    # Check if output MIF file already exists
    in_file_mif = os.path.join(out_directory, file_name + ".mif")
    if os.path.exists(in_file_mif):
        print(f"\nSkipping conversion of {in_file} to MIF format as MIF file already exists.")
        return 1, "", in_file_mif

    # Convert diffusions into ".mif" format (mrtrix format)
    #in_file_mif = os.path.join(out_directory, file_name + ".mif")
    if diff:
        bvec = in_file.replace(ext, "bvec")
        bval = in_file.replace(ext, "bval")
        cmd = ["mrconvert", in_file, in_file_mif, "-fslgrad", bvec, bval]
    else:
        cmd = ["mrconvert", in_file, in_file_mif]

    result, stderrl, sdtoutl = execute_command(cmd)

    if result != 0:
        msg = f"\nIssue during conversion of {in_file} to MIF format"
        return 0, msg, in_file_mif

    msg = f"\nConversion of {in_file} to MIF format done"

    return 1, msg, in_file_mif






def get_shell(in_file):
    """Get shell info (b values)
    
    Parameters: 
    - in_file: input file in .mif format 
    
    Returns: 
    - int 1 success, 0 failure
    - msg
    - shell: list of strings containing the b-values
    """
    shell = []
    # Check inputs files and get files name
    valid_bool, ext, file_name = check_file_ext(in_file, EXT_MIF)
    if not valid_bool:
        msg = "\nInput image format is not " "recognized (mif needed)...!"
        return 0, msg, shell

    cmd = ["mrinfo", in_file, "-shell_bvalues"]
    result, stderrl, sdtoutl = execute_command(cmd)

    if result != 0:
        msg = f"\nCan not get info for {in_file}"
        return 0, msg, shell
    shell = sdtoutl.decode("utf-8").replace("\n", "").split(" ")
    msg = f"\nShell found for {in_file}"

    return 1, msg, shell

# Function to download the subjects.txt file if it doesn't exist
def download_subjects_txt(dir_name):
    github_repo_url = "https://github.com/IRMaGe-3T/resstore-mri-dwi/raw/525fa8803e8c6fd1cfa2886e90e52163e9e5e12c/resstore-mri-dwi/resources/subjects.txt"
    template_filename = "subjects.txt"
    template_path = os.path.join(dir_name, template_filename)
    
    # Check if the template file already exists
    if not verify_file(template_path):
        try:
            print("Downloading subjects.txt...")
            urllib.request.urlretrieve(github_repo_url, template_path)
            print("\subjects.txt file downloaded successfully.")
        except Exception as e:
            print(f"\nFailed to download the subjects.txt file: {e}")
            return None
    
    return template_path

def delete_directory(dir):
    """
    Remove a directory and all its contents recursively.

    Args:
    - dir (str): Path to the directory to be deleted.

    Returns:
    - None

    Raises:
    - OSError: If the directory or any of its contents cannot be removed.

    This function attempts to delete the specified directory and all its contents.
    It first checks if the directory exists, and if so, proceeds to delete all files
    and subdirectories within it recursively. Finally, it removes the directory itself.
    Any errors encountered during the deletion process are caught and printed as an error message.
    """
    try:
        # Check if the directory exists
        if os.path.exists(dir):
            # Delete all files inside the directory
            for fichier in os.listdir(dir):
                file_path = os.path.join(dir, fichier)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
            
            # Delete the directory itself
            shutil.rmtree(dir)
            print(f"Directory '{dir}' and its contents have been successfully deleted.")
        else:
            print(f"Directory '{dir}' does not exist.")
    except Exception as e:
        print(f"Error deleting directory '{dir}': {e}")