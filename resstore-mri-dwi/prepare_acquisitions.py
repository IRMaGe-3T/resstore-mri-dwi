''' 
Functions to get sequences and prepare 
sequences for processing:
    - prepare_abcd_acquistions
    - prepare_hermes_acquistions

'''
import sys
import os

from bids import BIDSLayout

from useful import convert_nifti_to_mif, execute_command, get_shell


def prepare_abcd_acquistions(bids_directory, sub, ses, preproc_directory):
    '''
    Get acquistions to process for abdc protocol 
    and do some preprocessings

    :param bids_directory: file name (a string)
    :param sub: subject name (a string)
    :param ses: session name (a string)
    :param preproc_directory: out directory (a string)

    :returns:
        - dwi: main diffusion to use for next steps (.mif)
        - dwi_json: diffusion json (.json) 
        - pepolar_ap: pepolar AP sequence to use for next steps (.mif)
        - pepolar_pa: pepolar PA sequence to use for next steps (.mif)
    '''

    layout = BIDSLayout(bids_directory)
    acq = 'abcd'
    # For ABCD, 2 DWI
    acq1 = acq + "1"
    all_sequences_dwi1 = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='dwi', acquisition=acq1, return_type='filename'
    )
    dwi_1_nifti = all_sequences_dwi1[0]
    acq2 = acq + "2"
    all_sequences_dwi2 = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='dwi', acquisition=acq2, return_type='filename'
    )
    dwi_2_nifti = all_sequences_dwi2[0]

    result, msg, dwi_1 = convert_nifti_to_mif(
        dwi_1_nifti, preproc_directory, diff=True
    )
    if result == 0:
        print(msg)
        sys.exit(1)

    result, msg, dwi_2 = convert_nifti_to_mif(
        dwi_2_nifti, preproc_directory, diff=True
    )
    if result == 0:
        print(msg)
        sys.exit(1)
    # Merge DTI1 and DTI2
    dwi = dwi_1.replace(f"acq-{acq1}", "acq-abcd")
    if not os.path.exists(dwi):
        cmd = ["dwicat", dwi_1, dwi_2, dwi]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch dwicat (exit code {result})"
        else:
                print("Extraction successfull")
    else:
        print(f"File already exists: {dwi}")
    # Use DTI1 to get info
    dwi_json = dwi_1_nifti.replace("nii.gz", "json")

    # Get both pepolar sequences
    all_sequences_pepolar_ap = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='AP',
        return_type='filename'
    )
    pepolar_ap_nifti = all_sequences_pepolar_ap[0]
    result, msg, pepolar_ap = convert_nifti_to_mif(
        pepolar_ap_nifti, preproc_directory, diff=False
    )
    if result == 0:
        print(msg)
        sys.exit(1)

    all_sequences_pepolar_pa = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='PA',
        return_type='filename'
    )
    pepolar_pa_nifti = all_sequences_pepolar_pa[0]
    result, msg, pepolar_pa = convert_nifti_to_mif(
        pepolar_pa_nifti, preproc_directory, diff=False
    )
    if result == 0:
        print(msg)
        sys.exit(1)

    return dwi, dwi_json, pepolar_ap, pepolar_pa


def prepare_hermes_acquistions(bids_directory, sub, ses, preproc_directory):
    '''
    Get acquistions to process for hermes protocol 
    and do some preprocessings

    :param bids_directory: file name (a string)
    :param sub: subject name (a string)
    :param ses: session name (a string)
    :param preproc_directory: out directory (a string)

    :returns:
        - dwi: main diffusion to use for next steps (.mif)
        - dwi_json: diffusion json (.json) 
        - pepolar_ap: pepolar AP sequence to use for next steps (.mif)
        - pepolar_pa: pepolar PA sequence to use for next steps (.mif)
    '''

    layout = BIDSLayout(bids_directory)
    acq = 'hermes'
    # Get DWI
    all_sequences_dwi = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='dwi', acquisition=acq, return_type='filename'
    )
    dwi_nifti = all_sequences_dwi[0]
    dwi_json = dwi_nifti.replace("nii.gz", "json")
    result, msg, dwi = convert_nifti_to_mif(
        dwi_nifti, preproc_directory, diff=True
    )
    if result == 0:
        print(msg)
        sys.exit(1)
    # Get both pepolar sequences
    all_sequences_pepolar_ap = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='AP',
        return_type='filename'
    )
    pepolar_ap_nifti = all_sequences_pepolar_ap[0]
    result, msg, pepolar_ap = convert_nifti_to_mif(
        pepolar_ap_nifti, preproc_directory, diff=True
    )
    if result == 0:
        print(msg)
        sys.exit(1)

    all_sequences_pepolar_pa = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='PA',
        return_type='filename'
    )
    pepolar_pa_nifti = all_sequences_pepolar_pa[0]
    result, msg, pepolar_pa = convert_nifti_to_mif(
        pepolar_pa_nifti, preproc_directory, diff=True
    )
    if result == 0:
        print(msg)
        sys.exit(1)

    # For HERMES, pepolar sequences contains b100
    # Extract only b0
    pepolar_ap_bzero=pepolar_ap.replace('.mif', '_bzero.mif')
    if not os.path.exists(pepolar_ap_bzero):
        cmd = ["dwiextract", pepolar_ap, pepolar_ap_bzero, '-bzero']
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch dwicat (exit code {result})"
        else:
            print("Extraction successfull")
    else:
        print(f"File already exists: {pepolar_ap_bzero}")
    
    pepolar_pa_bzero=pepolar_pa.replace('.mif', '_bzero.mif')
    if not os.path.exists(pepolar_pa_bzero):
        cmd = ["dwiextract", pepolar_pa, pepolar_pa.replace(
            '.mif', '_bzero.mif'), '-bzero']
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"Can not lunch dwicat (exit code {result})"
        else:
            print("Extraction successfull")
    else:
        print(f"Skipping exctraction step, file alreeady exists: {pepolar_pa_bzero}")
        
    return dwi, dwi_json, pepolar_ap, pepolar_pa
