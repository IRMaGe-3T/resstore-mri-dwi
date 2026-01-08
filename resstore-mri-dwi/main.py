"""
Main code to launch to process RESSTORE diffusion data

python main.py --bids folder_bids_path 
--subjects 01001 01002 --sessions V2 V5 --acquisitions abcd hermes
"""

import argparse
import json
import os
import sys
import csv

from bids import BIDSLayout
from termcolor import colored
from prepare_acquisitions import prepare_abcd_acquistions, prepare_hermes_acquistions
from useful import convert_nifti_to_mif, convert_mif_to_nifti, execute_command, get_shell, verify_file
from preprocessing import run_preproc_dwi
from MRtrix_FOD import FOD
from MRtrix_DTI import mrtrix_DTI
from T1_preproc import t1_bet
from TractSeg_processing import run_tractseg, tractometry_postprocess, map_in_MNI_flirt_applyxfm, register_to_MNI_FA
from JHU_analysis import register_to_MNI_using_T1w, map_in_MNI_applywarp
from remove_volume import remove_volumes
from DIPY_DKI_DTI import dipy_DKI, dipy_DTI
from AMICO_NODDI import NODDI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process RESSTORE diffusion data"
    )
    parser.add_argument(
        "--bids", required=True, help="bids directory"
    )
    parser.add_argument(
        "--subjects", required=True, nargs="+",
        help="subjects to proces, if you want to process all subjects use --subjects all"
    )
    parser.add_argument(
        "--sessions", required=True,  nargs="+",
        help="sessions to process, if you want to process all sessions use --sessions all"
    )
    parser.add_argument(
        "--acquisitions", required=True,  nargs="+",
        help="diffusion acquisition to process (abcd, hermes)"
    )
    parser.add_argument(
        "--volumes", required=None,
        help="list of volumes to remove (.txt)"
    )

    # Set path
    args = parser.parse_args()
    bids_path = args.bids
    subjects = args.subjects
    sessions = args.sessions
    acquisitions = args.acquisitions
    volumes = args.volumes
    layout = BIDSLayout(bids_path)

    if subjects == ["all"]:
        # Get all subjects in BIDS directory
        subjects = layout.get_subjects()

    if sessions == ["all"]:
        # Get all sessions in BIDS directory
        sessions = layout.get_sessions()

    print(colored(f"\nSubjects to process: {subjects}", "magenta"))
    print(colored(f"Sessions to process: {sessions}", "magenta"))
    print(colored("\n \n===== PREPARATION OF ACQUISITIONS =====\n", "cyan"))
    for sub in subjects:
        print(colored("\nSubject: " + sub, "magenta"))
        # print("\nSubject: ", sub)
        for ses in sessions:
            print(colored("Session: " + ses, "magenta"))
            # Check if sub / session exist
            check = layout.get(subject=sub, session=ses)
            if check == []:
                print(f"\nNo data for {sub} for session {ses}")
                continue
            for acq in acquisitions:
                # Check if acquistion exist for this subject
                check = layout.get(subject=sub, session=ses, acquisition=acq)
                if check == []:
                    print(f"\nNo data for {sub} for session {ses} for {acq}")
                    continue

                if volumes is None:
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
                    extension="nii.gz", suffix="T1w", return_type="filename")
                if all_sequences_t1:
                    in_t1w_nifti = all_sequences_t1[0]
                    result, msg, in_t1w = convert_nifti_to_mif(
                        in_t1w_nifti, preproc_directory, diff=False
                    )
                    if result == 0:
                        print(msg)
                        sys.exit(1)
                else:
                    print(
                        f"\nNo T1w data found for subject {sub} in session {ses}."
                        "Proceeding without T1w data."
                    )
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
                if volumes:
                    in_dwi_rm_vol = in_dwi.replace(".mif", "_removed_vol.mif")
                    remove_volumes(in_dwi, in_dwi_rm_vol, volumes)
                    cmd = ["mv", in_dwi_rm_vol, in_dwi]
                    result, stderrl, sdtoutl = execute_command(cmd)
                    if result != 0:
                        msg = f"\nCan not move dwi_rm_vol file (exit code {result})"
                    cmd = ["rm", in_dwi_rm_vol]
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
                result, msg, shell_res = get_shell(in_dwi)
                shell = [bval for bval in shell_res if float(bval) >= 5 and bval != ""]
                print("Shell: ", shell)
                if len(shell) > 1:
                    SHELL = True
                else:
                    SHELL = False

                print(f"\nMain phase encoding dir: {pe_dir}")

                print(colored("\n \n===== PREPROCESSING =====\n", "cyan"))

                # Launch preprocessing
                main_return, main_msg, info_preproc = run_preproc_dwi(
                    in_dwi, pe_dir,
                    readout_time,
                    shell=SHELL,
                    in_pepolar_PA=in_pepolar_PA,
                    in_pepolar_AP=in_pepolar_AP
                )

                print(colored("\n \n===== PROCESSING =====\n", "cyan"))

                # Compute FA map (mtrix)
                FA_dir = os.path.join(analysis_directory, "FA")
                if not os.path.exists(FA_dir):
                    os.mkdir(FA_dir)
                fa_return, fa_msg, info_fa = mrtrix_DTI(
                    info_preproc["dwi_preproc"], info_preproc["brain_mask"], FA_dir)
                
                # Compute FA map dipy
                DTI_dir = os.path.join(analysis_directory, "DTI_dipy")
                if not os.path.exists(DTI_dir):
                    os.mkdir(DTI_dir)
                DTI_return, DTI_msg, info_DTI = dipy_DTI(
                    info_preproc["dwi_preproc"], info_preproc["brain_mask_nii"], DTI_dir)

                # NODDI maps, only valid for multishell data
                if SHELL:
                    mask_nii = info_preproc["brain_mask_nii"]
                    AMICO_dir = os.path.join(analysis_directory, "AMICO")
                    print(colored("\n~~NOODI starts~~", "cyan"))
                    if not verify_file(AMICO_dir):
                        dwi_preproc_nii = info_preproc["dwi_preproc_nii"]
                        NODDI_dir = NODDI(dwi_preproc_nii, mask_nii)
                    else:
                        base_dir = os.path.dirname(os.path.dirname(mask_nii))
                        NODDI_dir = os.path.join(base_dir, "AMICO", "NODDI")
                        print(colored("\nNOODI ends", "cyan"))
                else:
                    AMICO_dir = None
                    NODDI_dir = None

                # DKI maps, (requires 3 b values)
                if SHELL:
                    DKI_dir = os.path.join(analysis_directory, "DKI")
                    if not os.path.exists(DKI_dir):
                        os.mkdir(DKI_dir)
                    DKI_return, DKI_msg, info_DKI = dipy_DKI(
                        info_preproc["dwi_preproc"], info_preproc["brain_mask_nii"], DKI_dir)
                else:
                    DKI_dir = None
                
                ## Tractseg analysis
                # Aligning in the MNI space for tractseg
                tractseg_dir = os.path.join(analysis_directory, "analysis_tractseg")
                if not os.path.exists(tractseg_dir):
                    os.mkdir(tractseg_dir)
                MNI_dir = os.path.join(tractseg_dir, "Results_MNI")
                if not os.path.exists(MNI_dir):
                    os.mkdir(MNI_dir)
                mni_return, mni_msg, info_mni = register_to_MNI_FA(
                    info_preproc["dwi_preproc"], info_DTI["FA_map"], MNI_dir)
                
                # MD in MNI
                map_md = info_DTI["FA_map"].replace("FA", "MD")
                if ".mif" in map_md:
                    nii_return, nii_msg, map_md_nii = convert_mif_to_nifti(map_md, FA_dir, diff=False)
                else:
                    map_md_nii = map_md
                map_in_MNI_flirt_applyxfm(map_md_nii, MNI_dir, MNI_dir)
                if SHELL:
                    # NODDI and DKI maps in the MNI
                    NODDI_MNI = os.path.join(MNI_dir, "NODDI_MNI")
                    DKI_MNI = os.path.join(MNI_dir, "DKI_MNI")
                    if not os.path.exists(NODDI_MNI):
                        os.mkdir(NODDI_MNI)
                    if not os.path.exists(DKI_MNI):
                        os.mkdir(DKI_MNI)
                    print(colored("\n~~Map in MNI step starts~~", "cyan"))
                    for file_name in os.listdir(NODDI_dir):
                        if file_name.endswith(".nii.gz"):
                            map_noddi = os.path.join(NODDI_dir, file_name)
                            map_in_MNI_flirt_applyxfm(map_noddi, NODDI_MNI, MNI_dir)
                    for file_name in os.listdir(DKI_dir):
                        if file_name.endswith(".nii.gz"):
                            map_dki = os.path.join(DKI_dir, file_name)
                            map_in_MNI_flirt_applyxfm(map_dki, DKI_MNI, MNI_dir)
                print(colored("\nMap in MNI step ends", "cyan"))

                # Doing FOD estimations
                FOD_dir = os.path.join(tractseg_dir, "FOD")
                if not os.path.exists(FOD_dir):
                    os.mkdir(FOD_dir)
                _, msg, peaks = FOD(
                    info_mni["dwi_preproc_mni"], info_mni["dwi_mask_mni"], FOD_dir, multishell=SHELL)

                # Tractography
                Tract_dir = os.path.join(tractseg_dir, "Tracto")
                if not os.path.exists(Tract_dir):
                    os.mkdir(Tract_dir)
                run_tractseg(peaks, Tract_dir)

                # Tractometry (map must be in the MNI space)
                map_path = info_mni["FA_MNI"]
                print(colored("\n~~Tractometry starts~~", "cyan"))
                tractometry_postprocess(map_path, Tract_dir)
                map_path_MD =  info_mni["FA_MNI"].replace("FA_MNI", "dti_MD_MNI")
                tractometry_postprocess(map_path_MD, Tract_dir)
                if SHELL:
                    map_path_ODI = os.path.join(NODDI_MNI, "ODI_MNI.nii.gz")
                    map_path_NDI = os.path.join(NODDI_MNI, "NDI_MNI.nii.gz")
                    map_path_KFA = os.path.join(DKI_MNI, "dki_kFA_MNI.nii.gz")
                    map_path_MK = os.path.join(DKI_MNI, "dki_MK_MNI.nii.gz")
                    tractometry_postprocess(map_path_NDI, Tract_dir)
                    tractometry_postprocess(map_path_KFA, Tract_dir)
                    tractometry_postprocess(map_path_MK, Tract_dir)
                    tractometry_postprocess(map_path_ODI, Tract_dir)
                else:
                    map_path_KFA = None
                    map_path_MK = None
                    map_path_NDI = None
                    map_path_ODI = None
                print(colored("\nTractometry done.", "cyan"))

                ## Jhu analysis (registration to MNI space)
                jhu_dir = os.path.join(analysis_directory, "analysis_jhu")
                if not os.path.exists(jhu_dir):
                    os.mkdir(jhu_dir)
                bet_return, bet_msg, info_bet = t1_bet(in_t1w_nifti, jhu_dir)
                fa_nii = info_DTI["FA_map"]
                mni_jhu_return, mni_jhu_msg, info_mni_jhu = register_to_MNI_using_T1w(
                    in_t1w_nifti, info_bet["t1_brain"], 
                    info_preproc["mean_b0"], fa_nii, jhu_dir
                )
        
                print(colored("\n~~Map in MNI step starts~~", "cyan"))
                map_in_MNI_applywarp(map_md_nii, info_mni_jhu["T12MNI_warp"], info_mni_jhu["b0_to_T1_mat"], jhu_dir)
                for file_name in os.listdir(NODDI_dir):
                    if file_name.endswith(".nii.gz"):
                        map_noddi = os.path.join(NODDI_dir, file_name)
                        map_in_MNI_applywarp(map_noddi, info_mni_jhu["T12MNI_warp"], info_mni_jhu["b0_to_T1_mat"], jhu_dir)
                for file_name in os.listdir(DKI_dir):
                    if file_name.endswith(".nii.gz"):
                        map_dki = os.path.join(DKI_dir, file_name)
                        map_in_MNI_applywarp(map_dki, info_mni_jhu["T12MNI_warp"], info_mni_jhu["b0_to_T1_mat"], jhu_dir)
                print(colored("\nMap in MNI step ends", "cyan"))


            print(colored("\n \n===== THE END =====\n\n", "cyan"))
