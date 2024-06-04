'''
Main code to launch to process RESSTORE diffusion data

python main.py --bids folder_bids_path 
--subjects 01001 01002 --sessions V2 V5 --asquisitions abcd hermes
'''

import argparse
import json
import os
import glob
import sys

from bids import BIDSLayout

from prepare_acquisitions import prepare_abcd_acquistions, prepare_hermes_acquistions
from useful import convert_nifti_to_mif, execute_command, get_shell
from preprocessing import run_preproc_dwi


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

    # Set path
    args = parser.parse_args()
    bids_path = args.bids
    subjects = args.subjects
    sessions = args.sessions
    acquisitions = args.acquisitions
    layout = BIDSLayout(bids_path)

    if subjects == ['all']:
        # Get all subjects in BIDS directory
        subjects = layout.get_subjects()

    if sessions == ['all']:
        # Get all sessions in BIDS directory
        sessions = layout.get_sessions()

    print(f'Subjects to process: {subjects}')
    print(f'Sessions to process: {sessions}')
    for sub in subjects:
        print('\n Subject: ', sub)
        for ses in sessions:
            print('Session: ', ses)
            # Check if sub / session exist
            check = layout.get(subject=sub, session=ses)
            if check == []:
                print(f'No data for {sub} for session {ses}')
                continue
            for acq in acquisitions:
                # Check if acquistion exist for this subject
                check = layout.get(subject=sub, session=ses, acquisition=acq)
                if check == []:
                    print(f'No data for {sub} for session {ses} for {acq}')
                    continue

                # Create analysis directory
                analysis_directory = os.path.join(
                    bids_path,
                    "derivatives",
                    "sub-" + sub,
                    "ses-" + ses,
                    "dwi-" + acq
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
                # TODO: add verification if only one T1w or several T1w
                if all_sequences_t1:
                    in_t1w_nifti = all_sequences_t1[0]
                    result, msg, in_t1w = convert_nifti_to_mif(
                        in_t1w_nifti, preproc_directory, diff=False
                    )
                    if result == 0: #I add this
                        print(msg)
                        sys.exit(1)
                else:
                    print(f"No T1w data found for subject {sub} in session {ses}. Proceeding without T1w data.")
                    in_t1w = None  #Until here

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

            print(f'Phase encoding dir: {pe_dir}')
            # Launch preprocessing

            # TODO: add function to launch preprocessing
            run_preproc_dwi(in_dwi, pe_dir, readout_time, rpe=None, shell=SHELL, in_pepolar_PA=in_pepolar_PA, in_pepolar_AP=in_pepolar_AP)
            # see what to put in rpe
            
            
            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/preprocessing.py#L59
            # adapt function to abdc acquistions (2 pepolar sequences)
            # Compare with Fabrice Hanneau code

            # Launch compute FA / ADC ..

            # TODO: add function to compute FA , ADC ..
            # Compare with Fabrice Hanneau code

            # Launch DWI response and FOD

            # TODO: add function to get FOD
            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/processing_fod.py
            # Compare with Fabrice Hanneau code
            
            # Launch TractSeg
            if info["user_imput_2"]  in ['yes', 'y']:
                tractogram(in_t1w, info["brain_mask"]) #Preguntar si podemos pasarlo al main
            else:
                print("No creation of a whole-brain tractogram")

            # TODO: add function to get the tract
            # Take inspiration : https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/processing_tractseg.py#L14
            # Compare with Fabrice Hanneau code
