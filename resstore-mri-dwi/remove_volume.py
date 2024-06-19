import os
from useful import delete_directory

def remove_volumes_dwi(input_file, output_file, volumes_to_remove_file):
    # Créer un répertoire temporaire
    dir = os.path.dirname(input_file)
    temp_dir = os.path.join(dir, "_temp")
    os.mkdir(temp_dir)
    
    with open(volumes_to_remove_file, 'r') as file:
        data=file.read()
        volumes_to_remove = data.split()

    print(f'\n   Vol to rm: {volumes_to_remove}')

    # Liste pour stocker les chemins des volumes restants
    remaining_volumes = []
    volume_idx = 0

    # Boucle pour extraire les volumes
    while True:
        temp_volume_file = os.path.join(temp_dir, f'volume_{volume_idx}.mif')
        result = os.system(f'mrconvert {input_file} -coord 3 {volume_idx} {temp_volume_file}')
        if result != 0:  # Break the loop if mrconvert fails (indicating no more volumes)
            print("\n No more volumes to extract")
            break
        if str(volume_idx) not in volumes_to_remove:
            remaining_volumes.append(temp_volume_file)
        volume_idx += 1
    
    # Concaténer les volumes restants en un seul fichier .mif de sortie
    remaining_volumes = ' '.join(remaining_volumes)
    os.system(f'mrcat {remaining_volumes} -axis 3 {output_file}')
    
    # Nettoyer les fichiers temporaires
    
    delete_directory(temp_dir)
    
    print(f"Volumes retirés et image sauvegardée sous '{output_file}'")