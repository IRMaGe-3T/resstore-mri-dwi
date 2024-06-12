# RESSTORE MRI-DWI Processing

This project is a processing pipeline for MRI diffusion data of the RESSTORE study. This repository contains the code to process MRI diffusion data using the BIDS (Brain Imaging Data Structure) format.

**Getting Started**

To use this code, open the `restorre-mri-dwi` directory in your terminal and run the following command:
```
python3 main.py --bids <folder_bids_path> --subjects <subject_ids> --sessions <session_ids> --acquisitions <acquisition_ids>
```
Replace `<folder_bids_path>` with the path to your BIDS dataset folder, `<subject_ids>` with the IDs of the subjects you want to process, `<session_ids>` with the IDs of the sessions you want to process, and `<acquisition_ids>` with the IDs of the acquisitions you want to process (ex. hermes or abcd).

**Example Command**
```
python3 main.py --bids 'OUTPUT_DIR' --subjects 003 --sessions 02 --acquisitions hermes
```
**Visualization of tractography results**

If you choose to create a brain tractogram, you'll have a folder in `derivatives/sub-XXX/ses-XX/acq/preprocessing` named `tractseg_output`. It contains all the data created by TractSeg.

	1) FA histogram along specific tracks
	
Download the 'subjects.txt' template from this git repository. Open the files and complete it following the instructions given in the file. Then, from the terminal launch the command:
```
plot_tractometry_results -i <path_subjects.txt> -o <path_tractseg_output/results.png> --mc
```
This command create a file `results.png` in the `tractseg_output` folder. It represents the evolution of the FA values along certain tracts specified in the `subjects.txt` file.

	2) Visualize the tracks with mrview

To see the tracks you can use mrview. Launch mrview from the terminal. Open the preprocessed diffusion image which is named `sub-XXX_ses-XX_..._denoise_degibbs_prproc_unbiased.mif`. Then with `Tools` add `tractography`. Then open the track that you want to vizualize from `TOM_trackings` folder. To visualize only the track click on `View` and `Hide main image`.  


**Important Notes**

* Make sure you have the BIDS files in the `OUTPUT_DIR` folder.
* The processed output will be stored in the `derivatives` directory.
* **Respect the BIDS format**: Ensure that your input files are in the correct BIDS format, as incorrect formatting may cause errors or incorrect results.

