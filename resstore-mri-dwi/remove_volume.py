import os
from useful import delete_directory

def remove_volumes(input_file, output_file, volumes_to_remove):
    """
    Remove specific volumes from a MRtrix image file (.mif).

    Args:
        input_file (str): Path to the input MRtrix image file (.mif).
        output_file (str): Path to save the output MRtrix image file (.mif).
        volumes_to_remove (list): Text file (.txt) containing the list of volumes to remove.

    Returns:
        None
    """
    # Create a temporary directory
    dir = os.path.dirname(input_file)
    temp_dir = os.path.join(dir, "_temp")
    os.mkdir(temp_dir)
    
    # List to store paths of remaining volumes
    remaining_volumes = []
    volume_idx = 0

    # Loop to extract volumes
    while True:
        temp_volume_file = os.path.join(temp_dir, f'volume_{volume_idx}.mif')
        result = os.system(f'mrconvert {input_file} -coord 3 {volume_idx} {temp_volume_file}')
        if result != 0:  # Break the loop if mrconvert fails (indicating no more volumes)
            print("\n No more volumes to extract")
            break
        if str(volume_idx) not in volumes_to_remove:
            remaining_volumes.append(temp_volume_file)
        volume_idx += 1
    
    # Concatenate remaining volumes into a single output .mif file
    remaining_volumes = ' '.join(remaining_volumes)
    os.system(f'mrcat {remaining_volumes} -axis 3 {output_file}')
    
    # Clean up temporary files
    delete_directory(temp_dir)
    
    print(f"Volumes removed and image saved to '{output_file}'")
