"""
Use dipy library to fit Diffusion Tensor Imaging (DTI) and Diffusion Kurtosis Imaging (DKI) model
"""

import os
import dipy.reconst.dki as dki
import dipy.reconst.dti as dti
from dipy.io.image import load_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import fractional_anisotropy
from termcolor import colored
from useful import verify_file
import nibabel as nib


def dipy_DTI(dwi_unbias_mif, dwi_mask_nii, DTI_dir):
    """Fit DTI model with dipy"""

    dwi_unbias_nii = dwi_unbias_mif.replace(".mif", ".nii.gz")
    dwi_bval = dwi_unbias_nii.replace(".nii.gz", ".bval")
    dwi_bvec = dwi_unbias_nii.replace(".nii.gz", ".bvec")

    FA_file = os.path.join(DTI_dir, "dipy_dti_" + "FA" + ".nii.gz")
    print(colored("\n~~DTI dipy starts~~", "cyan"))

    if not verify_file(FA_file):
        print("\nDTI recontruction with dipy")
        data, affine = load_nifti(dwi_unbias_nii)
        bvals, bvecs = read_bvals_bvecs(dwi_bval, dwi_bvec)
        gtab = gradient_table(bvals, bvecs)
        dtimodel = dti.TensorModel(gtab, fit_method='WLS')
        mask, affine_mask = load_nifti(dwi_mask_nii)
        dtifit = dtimodel.fit(data, mask=mask)
        dti_metrics = {"FA": dtifit.fa,
                    "MD": dtifit.md,
                    "AD": dtifit.ad,
                    "RD": dtifit.rd, 
                    "FA2" :  fractional_anisotropy(dtifit.evals)
                    }

        for metric in list(dti_metrics.keys()):
            img = nib.Nifti1Image(dti_metrics[metric], affine)
            path = os.path.join(DTI_dir, "dipy_dti_" + metric + ".nii.gz")
            nib.save(img, path)

    info_DTI = {"FA_map": os.path.join(DTI_dir, "dipy_dti_FA.nii.gz")}
    msg = "\nDTI dipy done"
    print(colored(msg, "cyan"))
    print(info_DTI)
    return 1, msg, info_DTI


def dipy_DKI(dwi_unbias_mif, dwi_mask_nii, DKI_dir):
    """Fit DKI model with dipy"""

    dwi_unbias_nii = dwi_unbias_mif.replace(".mif", ".nii.gz")
    dwi_bval = dwi_unbias_nii.replace(".nii.gz", ".bval")
    dwi_bvec = dwi_unbias_nii.replace(".nii.gz", ".bvec")

    AD_file = os.path.join(DKI_dir, "dipy_dki_" + "AD" + ".nii.gz")
    print(colored("\n~~DKI starts~~", "cyan"))

    if not verify_file(AD_file):
        print("\nDKI recontruction with dipy")
        data, affine = load_nifti(dwi_unbias_nii)
        bvals, bvecs = read_bvals_bvecs(dwi_bval, dwi_bvec)
        gtab = gradient_table(bvals, bvecs)
        dkimodel = dki.DiffusionKurtosisModel(gtab)
        mask, affine_mask = load_nifti(dwi_mask_nii)
        dkifit = dkimodel.fit(data, mask=mask)
        dki_metrics = {"FA": dkifit.fa,
                       "MD": dkifit.md,
                       "AD": dkifit.ad,
                       "RD": dkifit.rd,
                       "MK": dkifit.mk(0, 3),
                       "AK": dkifit.ak(0, 3),
                       "RK": dkifit.rk(0, 3),
                       "kFA": dkifit.kfa
                       }

        for metric in list(dki_metrics.keys()):
            img = nib.Nifti1Image(dki_metrics[metric], affine)
            path = os.path.join(DKI_dir, "dipy_dki_" + metric + ".nii.gz")
            nib.save(img, path)

    info_DKI = {}
    msg = "\nDKI done"
    print(colored(msg, "cyan"))
    return 1, msg, info_DKI
