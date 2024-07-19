import argparse
import glob
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Organise a DICOM dataset in BIDS. '
        'Folders should be organized in one folder with one folder '
        'by subject with inside one folder by session'
    )
    parser.add_argument(
        '-s', '--sourcedata', required=True, help='directory with DICOM folders'
    )
    parser.add_argument(
        '-o', '--output', required=True, help='output directory'
    )
    parser.add_argument(
        '-c', '--config_file', required=True, help='dcm2bids config file'
    )
    args = parser.parse_args()
    sourcedata = args.sourcedata
    output_directory = args.output
    config_file = args.config_file

    # Trouver tous les dossiers de sujets dans fichier source
    all_subject_folders = glob.glob(os.path.join(sourcedata, 'subject-*'))
    # Trouver tous les dossiers de sujets dans fichier out
    all_subject_folders_out = glob.glob(os.path.join(output_directory, 'sub-*'))

    # Vérifier s'il existe des dossiers sujets dans le fichier source
    if not all_subject_folders:
        print("Aucun dossier de sujet trouvé dans le répertoire source.")
        exit(1)

    # Vérifier s'il existe des dossiers sujets dans le fichier output
    if not all_subject_folders_out:
        print("Aucun dossier de sujet trouvé dans le répertoire output. Traitement de tous les sujets du répertoire source.")
        all_subject_folders_out = []

    # Parcours des dossiers sujets dans fichier source
    for subject_folder in all_subject_folders:
        print(f"\nTraitement du dossier du sujet : {subject_folder}")

        # Vérifier si le répertoire sujet est valide
        if os.path.isdir(subject_folder):

            # Récupère le numéro du sujet 
            id_sub = os.path.basename(subject_folder).split('subject-')[-1]
            print('\nIdentifiant du sujet :', id_sub)
            
            # Trouver tous les dossiers de visite pour ce sujet dans le fichier source 
            visit_folders = glob.glob(os.path.join(subject_folder, 'visit-*'))

            # Verfier si le fichier source contient des visites pour ce sujet
            if not visit_folders:
                print(f"Aucun dossier de visite trouvé pour le sujet {id_sub}.")
                continue

            # Parcours des dossiers visites
            for visit_folder in visit_folders:

                # Vérfier si le repertoire est valide 
                if os.path.isdir(visit_folder):

                    # Recupère le numéro de le session
                    id_ses = os.path.basename(visit_folder).split('visit-')[-1]

                    # Si le dossier de sortie est vide, on traite directement les visites
                    if not all_subject_folders_out:
                        # Construire la commande dcm2bids
                        cmd = f'dcm2bids -d {visit_folder} -p {id_sub} -s {id_ses} -c {config_file} -o {output_directory}'
                        print('Commande :', cmd)

                        # Exécuter la commande
                        os.system(cmd)
                        continue

                    # Ici on a un dossier patient-visite valide on va vérifier s'il a déjà été traité ou non 
                    # Parcours de tous les dossiers output
                    for subject_folder_out in all_subject_folders_out:

                        # Vérifier si le répertoire est valide
                        if os.path.isdir(subject_folder_out):

                            # Trouver tous les dossiers de visite pour ce sujet dans le fichier source 
                            visit_folders_out = glob.glob(os.path.join(subject_folder_out, 'ses-*'))

                            # Parcours des dossiers visites out
                            for visit_folder_out in visit_folders_out:

                                # Vérifier si le répertoire est valide
                                if os.path.isdir(visit_folder_out):
                    
                                    # Vérifier si le dossier de session correspond à l'identifiant id_ses
                                    if visit_folder_out.startswith(f'ses-{id_ses}'):
                                        continue

                            # Arrivé ici cela signifie que le fichier visite n'a pas encore été traité donc on le fait  
                            # Construire la commande dcm2bids
                            cmd = f'dcm2bids -d {visit_folder} -p {id_sub} -s {id_ses} -c {config_file} -o {output_directory}'
                            print('Commande :', cmd)
                                            
                            # Exécuter la commande
                            os.system(cmd)
