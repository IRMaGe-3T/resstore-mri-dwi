# RESSTORE MRI-DWI Processing

The RESSTORE project is a processing pipeline for MRI diffusion data. This repository contains the code to process MRI diffusion data using the BIDS (Brain Imaging Data Structure) format.

**Getting Started**

To use this code, open the `restorre-mri-dwi` directory in your terminal and run the following command:
```
python3 main.py --bids <folder_bids_path> --subjects <subject_ids> --sessions <session_ids> --acquisitions <acquisition_ids>
```
Replace `<folder_bids_path>` with the path to your BIDS dataset folder, `<subject_ids>` with the IDs of the subjects you want to process, `<session_ids>` with the IDs of the sessions you want to process, and `<acquisition_ids>` with the IDs of the acquisitions you want to process (ex. hermes or abcd).

**Example Command**
```
python3 main.py --bids '/media/admin/e9890200-5ce6-441f-b56b-385d71d440f5/data/resstore_1b/GITHUB_DATA/OUTPUT_DIR' --subjects 003 --sessions 02 --acquisitions hermes
```
**Important Notes**

* Make sure you have the BIDS files in the `OUTPUT_DIR` folder.
* The processed output will be stored in the `derivatives` directory.
* **Respect the BIDS format**: Ensure that your input files are in the correct BIDS format, as incorrect formatting may cause errors or incorrect results.

