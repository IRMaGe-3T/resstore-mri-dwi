'''
Main code to launch to process RESSTORE diffusion data

python main.py --bids folder_bids_path 
--subjects 01001 01002 --sessions V2 V5 --acquisitions abcd hermes
'''

import argparse
import json
import os
import sys

from bids import BIDSLayout

from prepare_acquisitions import prepare_abcd_acquistions, prepare_hermes_acquistions
from useful import convert_nifti_to_mif, execute_command, get_shell, verify_file
from preprocessing import run_preproc_dwi, run_register_MNI
from FOD import FOD
from FA_ADC_AD_RD import FA_ADC_AD_RD_maps
from T1_preproc import run_preproc_t1  
from processing_TractSeg import run_tractseg
from remove_volume import remove_volumes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process RESSTORE diffusion data'
    )
    parser.add_argument(
        '--bids', required=True, help='bids directory'
    )
    parser.add_argument(
        '--subjects', required=True, nargs='+',
        help='subjects to proces, if you want to process all subjects use --subjects all'
    )
    parser.add_argument(
        '--sessions', required=True,  nargs='+',
        help='sessions to process, if you want to process all sessions use --sessions all'
    )
    parser.add_argument(
        '--acquisitions', required=True,  nargs='+',
        help='diffusion acquisition to process (abcd, hermes)'
    )
    parser.add_argument(
        '--volumes', required=None, 
        help='list of volumes to remove (.txt)'
    )

    # Set path
    args = parser.parse_args()
    bids_path = args.bids
    subjects = args.subjects
    sessions = args.sessions
    acquisitions = args.acquisitions
    volumes = args.volumes
    layout = BIDSLayout(bids_path)

    # Ask user for processing
    user_input_1 = input(f"\nDo you want to create an FA, ADC, AD and RD maps of the brain? (yes/no): ").strip().lower()
    if user_input_1 in ['yes', 'y']:
        user_input_2 = input(f"Do you want to align image to the MNI space? (yes/no): ").strip().lower()
        if user_input_2 in ['yes', 'y']:
            user_input_3 = input(f"Do you want to perform FOD estimation? (yes/no): ").strip().lower()
            if user_input_3 in ['yes', 'y']:
                user_input_4 = input(f"Do you want to create a whole-brain tractogram? (yes/no): ").strip().lower()
            else:
                user_input_4 = 'no'
        else:
            user_input_3 = 'no'
            user_input_4 = 'no'
    else:
        user_input_2 = 'no'
        user_input_3 = 'no'
        user_input_4 = 'no'

    
    if subjects == ['all']:
        # Get all subjects in BIDS directory
        subjects = layout.get_subjects()

    if sessions == ['all']:
        # Get all sessions in BIDS directory
        sessions = layout.get_sessions()

    print(f'\nSubjects to process: {subjects}')
    print(f'Sessions to process: {sessions}')
    print("\n \n===== PREPARATION OF ACQUISITIONS =====\n")
    for sub in subjects:
        print('\nSubject: ', sub)
        for ses in sessions:
            print('Session: ', ses)
            # Check if sub / session exist
            check = layout.get(subject=sub, session=ses)
            if check == []:
                print(f'\nNo data for {sub} for session {ses}')
                continue
            for acq in acquisitions:
                # Check if acquistion exist for this subject
                check = layout.get(subject=sub, session=ses, acquisition=acq)
                if check == []:
                    print(f'\nNo data for {sub} for session {ses} for {acq}')
                    continue

                if volumes==None:
                    # Create analysis directory
                    analysis_directory = os.path.join(
                        bids_path,
                        "derivatives",
                        "sub-" + sub,
                        "ses-" + ses,
                        "dwi-" + acq
                    )
                else:
                    # Create analysis directory
                    analysis_directory = os.path.join(
                        bids_path,
                        "derivatives",
                        "sub-" + sub,
                        "ses-" + ses,
                        "dwi-" + acq + "_removed_volumes",
                    )



                preproc_directory = os.path.join(
                    analysis_directory, "preprocessing"
                )
                if not os.path.exists(analysis_directory):
                    os.makedirs(analysis_directory)
                if not os.path.exists(preproc_directory):
                    os.makedirs(preproc_directory)

                # Change working directory
                # (mrtriw will create temp directory in it)
                os.chdir(analysis_directory)

                session_path = os.path.join(
                    bids_path, "sub-" + sub, "ses-" + ses
                )

                # Get T1w and convert to MIF
                all_sequences_t1 = layout.get(
                    subject=sub, session=ses,
                    extension='nii.gz', suffix='T1w', return_type='filename')
                if all_sequences_t1:
                    in_t1w_nifti = all_sequences_t1[0]
                    result, msg, in_t1w = convert_nifti_to_mif(
                        in_t1w_nifti, preproc_directory, diff=False
                    )
                    if result == 0: 
                        print(msg)
                        sys.exit(1)
                else:
                    print(f"\nNo T1w data found for subject {sub} in session {ses}. Proceeding without T1w data.")
                    in_t1w = None  

                # Get DWI and pepolar, convert to MIF, merge DWI and get info
                if "abcd" in acq:
                    in_dwi, in_dwi_json, in_pepolar_AP, in_pepolar_PA = prepare_abcd_acquistions(
                        bids_path, sub, ses, preproc_directory)

                elif "hermes" in acq:
                    in_dwi, in_dwi_json, in_pepolar_AP, in_pepolar_PA = prepare_hermes_acquistions(
                        bids_path, sub, ses, preproc_directory)

                # Get info fot future processing
                # Get readout time
                with open(in_dwi_json, encoding="utf-8") as my_json:
                    data = json.load(my_json)
                    try:
                        readout_time = str(data["TotalReadoutTime"])
                    except Exception:
                        # For Philips data
                        readout_time = str(data["EstimatedTotalReadoutTime"])
                    pe_dir = str(data["PhaseEncodingDirection"])
                # Check if it is multishell data
                result, msg, shell = get_shell(in_dwi)
                shell = [bval for bval in shell if bval != "0" and bval != ""]
                if len(shell) > 1:
                    SHELL = True
                else:
                    SHELL = False

            print(f'\nPhase encoding dir: {pe_dir}')
            print("\n \n===== PREPROCESSING =====\n")

            if not volumes==None:
                in_dwi_rm_vol = in_dwi.replace(".mif", "_removed_vol.mif")
                remove_volumes(in_dwi, in_dwi_rm_vol, volumes)
                cmd = ["mv",in_dwi_rm_vol, in_dwi]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCan not move dwi_rm_vol file (exit code {result})"
                cmd = ["rm",in_dwi_rm_vol]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCan not delete dwi_rm_vol file (exit code {result})"

            # Launch preprocessing
            main_return, main_msg, info_preproc =run_preproc_dwi(in_dwi, pe_dir, readout_time, rpe=None, shell=SHELL, in_pepolar_PA=in_pepolar_PA, in_pepolar_AP=in_pepolar_AP)

            print("\n \n===== PROCESSING =====\n")

            # Launch FA map creation if needed
            if user_input_1 in ['yes', 'y']:
                FA_dir = os.path.join(analysis_directory, "FA")
                if not os.path.exists(FA_dir):
                    os.mkdir(FA_dir)
                fa_return, fa_msg, info_fa = FA_ADC_AD_RD_maps(info_preproc["dwi_preproc"], info_preproc["brain_mask"],FA_dir) 
            else:
                print("\nNo creation of FA_map")

            # Aligning image to MNI space
            if user_input_2 in ['yes', 'y']:
                MNI_dir = os.path.join(analysis_directory, "preprocessing_MNI")
                if not os.path.exists(MNI_dir):
                    os.mkdir(MNI_dir)
                mni_return, mni_msg, info_mni = run_register_MNI(info_preproc["dwi_preproc"], info_fa["FA_map"],MNI_dir) 
            else:
                print("\nNo MNI space alignment")

            # Launch FOD estimation if wanted 
            if user_input_3 in ['yes', 'y']:
                FOD_dir = os.path.join(analysis_directory, "FOD")
                if not os.path.exists(FOD_dir):
                    os.mkdir(FOD_dir)
                _,msg,peaks = FOD(info_mni["dwi_preproc_mni"], info_mni["dwi_mask_mni"],acq, FOD_dir)
            else:
                print("\nNo FOD done")  

            # For tractography
            # Launch T1_preproc
            if user_input_4 in ['yes', 'y']:
                Tract_dir = os.path.join(analysis_directory, "Tracto")
                if not os.path.exists(Tract_dir):
                    os.mkdir(Tract_dir)
                run_preproc_t1(in_t1w_nifti,info_mni["dwi_preproc_mni"])
                print("run_preproc_t1w done")
                run_tractseg(peaks,info_fa["FA_map"],Tract_dir)
                print("\nTractSeg successfully used")
            else:
                print("\nNo tractography done")

            print("\n \n===== THE END =====\n\n")
                   
            
            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/preprocessing.py#L59
            # adapt function to abdc acquistions (2 pepolar sequences)
 
            # Compare with Fabrice Hanneau code

            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/processing_fod.py            