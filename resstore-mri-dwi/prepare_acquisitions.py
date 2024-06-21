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
    # For ABCD, 1 DWI
    all_sequences_dwi_concatenated = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='dwi', acquisition=acq, return_type='filename'
    )
    if all_sequences_dwi_concatenated:
        dwi_nifti = all_sequences_dwi_concatenated[0]
        result, msg, dwi = convert_nifti_to_mif(
            dwi_nifti, preproc_directory, diff=True
        )
        if result == 0:
            print(msg)
            sys.exit(1)
        print("\nDWI processing successful")
        dwi_json = dwi_nifti.replace("nii.gz", "json")
    else:
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
                msg = f"\nCan not lunch dwicat (exit code {result})"
            else:
                    print("\nExtraction successfull")
        else:
            print(f"\nFile already exists: {dwi}")
        # Use DTI1 to get info
        dwi_json = dwi_1_nifti.replace("nii.gz", "json")

    # Get both pepolar sequences
    all_sequences_pepolar_ap = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='AP',
        return_type='filename'
    )
    if len(all_sequences_pepolar_ap)!=0:
        pepolar_ap_nifti = all_sequences_pepolar_ap[0]
        result, msg, pepolar_ap = convert_nifti_to_mif(
            pepolar_ap_nifti, preproc_directory, diff=False
        )
        if result == 0:
            print(msg)
            sys.exit(1)
    else:
        pepolar_ap_nifti=None
        pepolar_ap=None

    all_sequences_pepolar_pa = layout.get(
        subject=sub, session=ses, extension='nii.gz',
        suffix='epi', acquisition=acq, direction='PA',
        return_type='filename'
    )

    if len(all_sequences_pepolar_pa)!=0:
        pepolar_pa_nifti = all_sequences_pepolar_pa[0]
        result, msg, pepolar_pa = convert_nifti_to_mif(
            pepolar_pa_nifti, preproc_directory, diff=False
        )
        if result == 0:
            print(msg)
            sys.exit(1)
    else:
        pepolar_pa_nifti=None
        pepolar_pa=None

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

    # For HERMES, pepolar sequences may contain b1000 and b0
    # Check if pepolar contain only b0 or not 
    _, msg, shell_ap = get_shell(pepolar_ap)
    _, msg, shell_pa = get_shell(pepolar_pa)
    print(f'\nShell pepolar AP: {shell_ap}')
    print(f'\nShell pepolar PA: {shell_pa}')
    shell_ap = [bval for bval in shell_ap if bval != "0" and bval != ""]
    shell_pa = [bval for bval in shell_pa if bval != "0" and bval != ""]
    print(f'\nShell pepolar AP: {shell_ap}')
    print(f'\nShell pepolar PA: {shell_pa}')
    pepolar_ap_bzero=pepolar_ap.replace('.mif', '_bzero.mif')
    pepolar_pa_bzero=pepolar_pa.replace('.mif', '_bzero.mif')

    # If pepolar contain b0 and b1000, extract b0
    if (len(shell_pa) > 0 and len(shell_ap) > 0):
        print('\n Hermes fmaps contain b1000 and b0. b0 must be extracted')

        # Extraction b0 AP
        if not os.path.exists(pepolar_ap_bzero):
            cmd = ["dwiextract", pepolar_ap, pepolar_ap_bzero, '-bzero']
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not launch dwicat (exit code {result})"
            else:
                print("\nExtraction successfull")
        else:
            print(f"\nFile already exists: {pepolar_ap_bzero}")
        
        # Extraction b0 PA
        if not os.path.exists(pepolar_pa_bzero):
            cmd = ["dwiextract", pepolar_pa, pepolar_pa.replace(
                '.mif', '_bzero.mif'), '-bzero']
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not lunch dwicat (exit code {result})"
            else:
                print("\nExtraction successfull")
        else:
            print(f"\nSkipping exctraction step, file alreeady exists: {pepolar_pa_bzero}")

    # If pepolar contain only b0, rename the file
    else:
        print('\n Hermes fmaps contain only b0.')
        cmd = ["mv", pepolar_pa, pepolar_pa_bzero]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not rename pepolar_pa images (exit code {result})"

        cmd = ["mv", pepolar_ap, pepolar_ap_bzero]
        result, stderrl, sdtoutl = execute_command(cmd)
        if result != 0:
            msg = f"\nCan not rename pepolar_ap images (exit code {result})"
            

    return dwi, dwi_json, pepolar_ap_bzero, pepolar_pa_bzero