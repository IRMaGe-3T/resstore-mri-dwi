Table of contents
1. [Overview](#overview)
2. [Diffusion MRI protocol](#mriprotocol)
3. [Installation and configuration](#installation)
4. [How it works](#how-it-works)


<a name="overview"></a>
# Overview
This repository contains the diffusion MRI protocol and processing pipeline for [RESSTORE (Regenerative Stem Cell Therapy for Stroke in Europe)](https://doi.org/10.3389/fstro.2024.1416490), a multicenter randomized controlled trial evaluating intravenous allogeneic adipose-derived stem cells in subacute ischemic stroke. 

Within the context of RESSTORE, a clinically compatible four-shell diffusion MRI protocol has been implemented. The pipeline provided here enables processing of the acquired data.

The MRI protocol, processing pipeline, and validation (test–retest on healthy volunteers and feasibility in stroke patients) are described in a submitted MethodsX article.

## What this repository provides

- A clinically validated diffusion MRI acquisition protocol
- A complete processing pipeline for multi-shell diffusion data
- Quantitative outputs including DTI, DKI, NODDI, and tract-based analysis

<a name="mriprotocol"></a>
# Diffusion MRI protocol

- Philips MRI scanner:

  Diffusion adapted from the ABCD framework (Casey et al., 2018; Cetin-Karayumak et al., 2023) and optimized for clinical feasibility on a Philips system.  Diffusion data were acquired using two runs of 51 directions each. Reversed phase-encoded b=0 images were acquired. Protocol is available in `resources`

- GE and Siemens MRI scanner:

   Diffusion protocol derived from the ABCD framework (Casey et al., 2018; Cetin-Karayumak et al., 2023) used. 


<a name="installation"></a>
# Installation

## Clone the repository
```
git clone https://github.com/IRMaGe-3T/resstore-mri-dwi.git
cd resstore-mri-dwi
```

## Create a Python virtual environment

We recommend using a virtual environment to avoid dependency conflicts.

```
python3 -m venv resstore-env
source resstore-env/bin/activate
```

## Install Python dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
``` 

## External dependencies

The following tools must be installed separately (not included in requirements.txt):

- MRtrix (tested with 3.0.4)
- FSL (tested with 6.0.7.11)
- ANTs (tested with 2.5.2)
- TractSeg (tested with 2.9)
- Xvfb

Make sure these tools are available in your system PATH.


<a name="how-it-works"></a>
# How it works

## Data organization 

The data should be organized following the BIDS format. 
To do so, you can follow the tutorial available in `resources/data_conversion`.

**Example of data organization for Philips data:**
```
/BIDS_FOLDER_PATH
├── dataset_description.json
├── derivatives
├── sub-013
│   ├── ses-02
│   │   ├── anat
│   │   │   ├── sub-013_ses-02_T1w.json
│   │   │   ├── sub-013_ses-02_T1w.nii.gz
│   │   ├── dwi
│   │   │   ├── sub-013_ses-02_acq-abcd1_dir-PA_dwi.bval
│   │   │   ├── sub-013_ses-02_acq-abcd1_dir-PA_dwi.bvec
│   │   │   ├── sub-013_ses-02_acq-abcd1_dir-PA_dwi.json
│   │   │   ├── sub-013_ses-02_acq-abcd1_dir-PA_dwi.nii.gz
│   │   │   ├── sub-013_ses-02_acq-abcd2_dir-PA_dwi.bval
│   │   │   ├── sub-013_ses-02_acq-abcd2_dir-PA_dwi.bvec
│   │   │   ├── sub-013_ses-02_acq-abcd2_dir-PA_dwi.json
│   │   │   └── sub-013_ses-02_acq-abcd2_dir-PA_dwi.nii.gz
│   │   ├── fmap
│   │   │   ├── sub-013_ses-02_acq-abcd_dir-AP_epi.json
│   │   │   ├── sub-013_ses-02_acq-abcd_dir-AP_epi.nii.gz
│   │   │   ├── sub-013_ses-02_acq-abcd_dir-PA_epi.json
│   │   │   └── sub-013_ses-02_acq-abcd_dir-PA_epi.nii.gz

```

## Launch analysis
To use the analysis pipeline, open the `restorre-mri-dwi` directory in your terminal and run the following command:
```
python main.py --bids <folder_bids_path> --subjects <subject_ids> --sessions <session_ids> --acquisitions <acquisition_ids>
```
Arguments: 
- --bids: Path to the BIDS dataset
- --subjects: List of subject IDs (without "sub-")
- --sessions: List of session IDs (without "ses-")
- --acquisitions: Acquisition type (abcd or hermes)

**Example Command**
```
python main.py --bids /BIDS_FOLDER_PATH --subjects 013 014 --sessions 02 --acquisitions abcd
```

## Workflow description

The pipeline includes the following steps:

1) Data preparation(conversion to .mif format, data concatenation, fmap preparation)
2) Denoising 
3) Unringing
4) Motion and distortion correction 
5) Bias field correction
6) Diffusion Tensor Imaging (DTI) (MRtrix and DIPY)
7) NODDI (AMICO)
8) Diffusion Kurtosis Imaging (DKI) (DIPY)
9) TractSeg analysis
    - Align diffusion and metric maps in the MNI space using FA template
    - FOD estimation 
    - Tractography (TractSeg)
    - Tractometry (TractSeg)
10) JHU analysis
    - Align diffusion and metric maps in the JHU space (MNI space)
    - Warp JHU atlas to subject space

## Outputs

Main outputs include:

- **DTI metrics**: FA, MD, AD, RD
- **DKI metrics**: MK, AK, RK
- **NODDI metrics**: ODI, NDI, FWF
- **TractSeg results**: bundle segmentation and tractometry
- **JHU analysis**: atlas-based metrics

Each step also generates intermediate files for quality control.

All the outputs are stored in the `derivatives` directory:

- sub-XX
  - ses-XX
    - dwi-abcd
        - AMICO: NODDI maps (ODI, NDI, FWF,...) --> only for multishell data
        - analysis_jhu: results from JHU analysis
        - analysis_tractseg: results from TractSeg analysis
        - DKI: DKI maps (AK, MK, RK, ...)       --> only for multishell data
        - DTI_dipy: DTI maps created using DIPY
        - DTI_mrtrix: DTI maps created using MRTrix
        - preprocessing: preprocessed data from each step 


## Optional: Removing corrupted volumes

To improve data quality, you may remove corrupted volumes.

### Steps

1. Create a text file containing the indices of volumes to remove (space-separated)
2. Run the pipeline with:


```
python main.py --bids /BIDS_FOLDER_PATH --subjects 003 --sessions 02 --acquisitions hermes --volumes 'path/to/volumes_to_remove.txt'
```

Warning: Removing volumes may affect downstream modeling (especially multi-shell methods like NODDI).
Use this option carefully.


### How to choose which volumes to remove

Once you've run the program completely for the subject with all the volumes, open the pdf file located in: `preprocessing/qc_text/quad/qc.pdf`. On the 6th page you'll see a chart indicating the number of outliers in each volume. A good idea is to suppress the volumes having too many outliers (high peaks on top of the chart).
You can also visualize by hand the volumes by typing in the terminal `mrview path/to/img.mif` and decide which volume to remove.  
Volumes where the head is tilted or that contain dark bands are good candidates for removal.





