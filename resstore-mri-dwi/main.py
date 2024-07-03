'''
Main code to launch to process RESSTORE diffusion data

python main.py --bids folder_bids_path 
--subjects 01001 01002 --sessions V2 V5 --acquisitions abcd hermes
'''

import argparse
import json
import os
import sys
import csv

from bids import BIDSLayout

from prepare_acquisitions import prepare_abcd_acquistions, prepare_hermes_acquistions
from useful import convert_nifti_to_mif, execute_command, get_shell, verify_file
from preprocessing import run_preproc_dwi, run_register_MNI
from FOD import FOD
from FA_ADC_AD_RD import FA_ADC_AD_RD_maps
from T1_preproc import run_preproc_t1  
from processing_TractSeg import run_tractseg
from remove_volume import remove_volumes
from ROI import getFAstats, create_or_update_tsv, extract_roi_stats
from dipy_dti_dki import DIPY_DTI
from NODDI import NODDI

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
                    in_t1w_nifti = None

                # Get DWI and pepolar, convert to MIF, merge DWI and get info
                if "abcd" in acq:
                    in_dwi, in_dwi_json, in_pepolar_AP, in_pepolar_PA = prepare_abcd_acquistions(
                        bids_path, sub, ses, preproc_directory)

                elif "hermes" in acq:
                    in_dwi, in_dwi_json, in_pepolar_AP, in_pepolar_PA = prepare_hermes_acquistions(
                        bids_path, sub, ses, preproc_directory)
                    
                # Remove volume from dwi if needed
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

            # Launch preprocessing
            main_return, main_msg, info_preproc =run_preproc_dwi(in_dwi, pe_dir, readout_time, rpe=None, shell=SHELL, in_pepolar_PA=in_pepolar_PA, in_pepolar_AP=in_pepolar_AP)

            print("\n \n===== PROCESSING =====\n")

            # FA map
            FA_dir = os.path.join(analysis_directory, "FA")
            if not os.path.exists(FA_dir):
                os.mkdir(FA_dir)
            fa_return, fa_msg, info_fa = FA_ADC_AD_RD_maps(info_preproc["dwi_preproc"], info_preproc["brain_mask"],FA_dir)
            # NODDI maps
            mask_nii = info_preproc["brain_mask_nii"]
            if acq=="abcd":
                AMICO_dir = os.path.join(analysis_directory, "AMICO_dir")
                if not os.path.exists(AMICO_dir):
                    dwi_preproc = info_preproc["dwi_preproc"]
                    bval = dwi_preproc.replace(".mif", ".bval")
                    bvec = dwi_preproc.replace(".mif", ".bvec")
                    NODDI_dir = NODDI(dwi_preproc, bval, bvec, mask_nii)
            else:
                NODDI_dir = None
            # DKI maps
            if acq=="abcd":
                DKI_dir = os.path.join(analysis_directory, "DKI")
                if not os.path.exists(DKI_dir):
                    os.mkdir(DKI_dir)
                DKI_return, DKI_msg, info_DKI = DIPY_DTI(info_preproc["dwi_preproc"], info_preproc["brain_mask_nii"],DKI_dir)
            else:
                DKI_dir=None
            # Aligning in the MNI space
            MNI_dir = os.path.join(analysis_directory, "preprocessing_MNI")
            if not os.path.exists(MNI_dir):
                os.mkdir(MNI_dir)
            mni_return, mni_msg, info_mni = run_register_MNI(info_preproc["dwi_preproc"], info_fa["FA_map"], NODDI_dir, DKI_dir, MNI_dir) 
            # Doing FOD estimations
            FOD_dir = os.path.join(analysis_directory, "FOD")
            if not os.path.exists(FOD_dir):
                os.mkdir(FOD_dir)
            _,msg, peaks = FOD(info_mni["dwi_preproc_mni"], info_mni["dwi_mask_mni"], acq, FOD_dir)
            # Tractography
            Tract_dir = os.path.join(analysis_directory, "Tracto")
            if not os.path.exists(Tract_dir):
                os.mkdir(Tract_dir)
            if in_t1w_nifti is not None:
                run_preproc_t1(in_t1w_nifti,info_mni["dwi_preproc_mni"])
                print("run_preproc_t1w done")
            run_tractseg(peaks, info_mni["FA_MNI"], Tract_dir)
            print("\nTractSeg successfully used")

            # ROI extraction
            tsv_file = os.path.join(bids_path, "derivatives", "FA_stats.tsv")
            subject_name = analysis_directory.split('/')[-3] + '-' + analysis_directory.split('/')[-2] + '-' + analysis_directory.split('/')[-1]
            # Check if the subject is already in the TSV file or there is not such a file
            if not os.path.isfile(tsv_file) or subject_name not in {row[0] for row in csv.reader(open(tsv_file), delimiter='\t')}:
                # Extract ROI stats and update the TSV file
                roi_stats = extract_roi_stats(analysis_directory, info_mni["FA_MNI"])
                create_or_update_tsv(subject_name, roi_stats, tsv_file)
            else:
                print("\nFile already on the FA stats table.")

            print("\n \n===== THE END =====\n\n")
                   
            
            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/preprocessing.py#L59
 
            # Compare with Fabrice Hanneau code

            # Take inspiration from https://github.com/IRMaGe-3T/mri_dwi_cluni/blob/master/mri_dwi_cluni/processing_fod.py            