import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Organize a DICOM dataset in BIDS. '
                    'Folders should be organized in one folder with one folder '
                    'per subject, and inside each subject folder, one folder per session.'
    )
    parser.add_argument(
        '-s', '--sourcedata', required=True, help='Directory with DICOM folders'
    )
    parser.add_argument(
        '-o', '--output', required=True, help='Output directory'
    )
    parser.add_argument(
        '-c', '--config_file', required=True, help='dcm2bids config file'
    )
    parser.add_argument(
        '-subject', required=True, help='Subject ID (e.g., 075 or 003)'
    )
    parser.add_argument(
        '-visit', required=True, help='Visit ID (e.g., 01 or 02)'
    )
    args = parser.parse_args()
    sourcedata = args.sourcedata
    output_directory = args.output
    config_file = args.config_file
    sub_id = args.subject
    visit_id = args.visit

    # Find the subject folder in the source directory
    subject_folder = os.path.join(sourcedata, f'subject-{sub_id}')
    if not os.path.isdir(subject_folder):
        print(f"Subject folder {subject_folder} does not exist.")
        exit(1)

    # Find the visit folder for the subject in the source directory
    visit_folder = os.path.join(subject_folder, f'visit-{visit_id}')
    if not os.path.isdir(visit_folder):
        print(f"Visit folder {visit_folder} for subject {sub_id} does not exist.")
        exit(1)

    # Check if the subject and session have already been processed
    output_subject_folder = os.path.join(output_directory, f'sub-{sub_id}')
    if os.path.isdir(output_subject_folder):
        output_visit_folder = os.path.join(output_subject_folder, f'ses-{visit_id}')
        if os.path.isdir(output_visit_folder):
            print(f"Session {visit_id} for subject {sub_id} has already been processed.")
            exit(1)

    # Construct the dcm2bids command
    cmd = f'dcm2bids -d {visit_folder} -p {sub_id} -s {visit_id} -c {config_file} -o {output_directory}'
    print('Command:', cmd)

    # Execute the command
    os.system(cmd)
