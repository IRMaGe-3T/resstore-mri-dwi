""" FOD processing 
Function for FOD estimation:
    - Performs RF estimation using the dhollander algorithm
    - Estimates FOD using MSMT CSD
    - Converts the resulting FOD files into a volume fraction (VF) file
    - Normalizes the intensity of the FOD files

Parameters:
    in_dwi (str): Path to the input DWI file in MIF format.
    mask (str): Path to the brain mask file in MIF format. 

Files created:
    - voxels.mif
    - wm.txt, gm.txt, csf.txt
    - wmfod.mif, gmfod.mif, csffod.mif
    - wmfod_norm.mif, gmfod_norm.mif, csffod_norm.mif
"""

import os
from useful import check_file_ext, execute_command, verify_file
from termcolor import colored


def FOD(in_dwi, mask, acq, FOD_dir):

    info = {}
    # Get files name
    dir_name = os.path.dirname(in_dwi)
    valid_bool, in_ext, file_name = check_file_ext(in_dwi, {"MIF": "mif"})
    print(colored("\n~~FOD estimation starts~~", "cyan"))

    if acq == "abcd":
        # RF estimation
        voxels = os.path.join(FOD_dir, "voxels.mif")
        wm = os.path.join(FOD_dir, "wm.txt")
        gm = os.path.join(FOD_dir, "gm.txt")
        csf = os.path.join(FOD_dir, "csf.txt")
        if not verify_file(voxels):
            cmd = ["dwi2response", "dhollander",
                   in_dwi, wm, gm, csf, "-voxels", voxels]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not launch dwi2response hollander (exit code {result})"
                return 0, msg, info
            else:
                print(f"\nVoxels succesfully created. Output file: {voxels}")

        # FOD estimation
        vf = os.path.join(FOD_dir, "vf.mif")
        wmfod = os.path.join(FOD_dir, "wmfod.mif")
        gmfod = os.path.join(FOD_dir, "gmfod.mif")
        csffod = os.path.join(FOD_dir, "csffod.mif")
        if not verify_file(vf):
            if not (os.path.exists(wmfod) and os.path.exists(gmfod) and os.path.exists(csffod)):
                cmd = ["dwi2fod", "msmt_csd", in_dwi, "-mask",
                       mask, wm, wmfod, gm, gmfod, csf, csffod]
                result, stderrl, sdtoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCan not launch dwi2fod (exit code {result})"
                    return 0, msg, info
                else:
                    print(
                        f"\nFOD files succesfully created. Output file: {wmfod}, {gmfod}, {csffod}")
            interm_wm = os.path.join(FOD_dir, "interm_wm.mif")
            cmd = ["mrconvert", "-coord", "3", "0", wmfod, interm_wm]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not launch mrconvert (exit code {result})"
                return 0, msg, info
            else:
                print(
                    f"\nIntermediary files succesfully created. Output file: {interm_wm}")
            cmd = ["mrcat", csffod, gmfod, interm_wm, vf]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not launch mrcat (exit code {result})"
                return 0, msg, info
            else:
                print(f"\nVf files succesfully created. Output file: {vf}")
            cmd = ["rm", interm_wm]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not remove intermediary file (exit code {result})"
                return 0, msg, info
            else:
                print(
                    f"\nIntermediary files succesfully removed. Output file: {interm_wm}")

        # Intensity normalization
        wmfod_norm = os.path.join(FOD_dir, "wmfod_norm.mif")
        gmfod_norm = os.path.join(FOD_dir, "gmfod_norm.mif")
        csffod_norm = os.path.join(FOD_dir, "csffod_norm.mif")
        if not (os.path.exists(wmfod_norm) and os.path.exists(gmfod_norm) and os.path.exists(csffod_norm)):
            cmd = ["mtnormalise", wmfod, wmfod_norm, gmfod,
                   gmfod_norm, csffod, csffod_norm, "-mask", mask]
            result, stderrl, sdtoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCan not launch mtnormalize (exit code {result})"
                return 0, msg, info
            else:
                print(
                    f"\nIntensity normalization completed. Output file: {wmfod_norm}, {gmfod_norm}, {csffod_norm}")
        else:
            print(colored(f"\nIntensity normalization already done", "yellow"))

        # Extract peaks
        peaks = os.path.join(FOD_dir, "peaks.nii")
        if not verify_file(peaks):
            cmd = ["sh2peaks", wmfod_norm, peaks]
            result, stderrl, stdoutl = execute_command(cmd)
            if result != 0:
                msg = f"\nCannot launch sh2peaks (exit code {result})"
                return 0, msg, info
            else:
                print("\nsh2peaks done.")

        msg = f"\nPeaks Succesfully extracted. Output file: {peaks}"
        print(colored("\nFOD estimation ends", "cyan"))
        return 1, msg, peaks

    elif acq == "hermes":
        peaks_h = os.path.join(FOD_dir, "peaks.nii")
        if not verify_file(peaks_h):

            # dwi2response
            rf = os.path.join(FOD_dir, "rf.response")
            if not verify_file(rf):
                cmd = ["dwi2response", "tournier", in_dwi, rf, "-mask", mask]
                result, stderrl, stdoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch dwi2response (exit code {result})"
                    return 0, msg, info
                else:
                    print(
                        f"\nResponse estimation for FOD done. Output file: {rf}")

            # dwi2fod
            fod = os.path.join(FOD_dir, "FOD.mif")
            if not verify_file(fod):
                cmd = ["dwi2fod", "csd", in_dwi, rf, fod, "-mask", mask]
                result, stderrl, stdoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch dwi2fod (exit code {result})"
                    return 0, msg, info
                else:
                    print(f"\nFOD computation done. Output file: {fod}")

            # Extract peaks
                cmd = ["sh2peaks", fod, peaks_h]
                result, stderrl, stdoutl = execute_command(cmd)
                if result != 0:
                    msg = f"\nCannot launch sh2peaks (exit code {result})"
                    return 0, msg, info
                else:
                    print(f"\nsh2peaks done")

        msg = "Peaks successfully extracted"
        print(colored("\nFOD estimation ends", "cyan"))
        return 1, msg, peaks_h

    else:
        msg = "\nType of acquisition not recognized for FOD estimation."
        return 0, msg, None
