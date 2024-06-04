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

def tractogram(in_dwi, mask):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    
    
    return 