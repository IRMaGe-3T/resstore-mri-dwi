# RESSTORE MRI-DWI Processing

This project is a processing pipeline for MRI diffusion data of the RESSTORE study. This repository contains the code to process MRI diffusion data using the BIDS (Brain Imaging Data Structure) format.

## Getting Started

To use this code, open the `restorre-mri-dwi` directory in your terminal and run the following command:
```
python3 main.py --bids <folder_bids_path> --subjects <subject_ids> --sessions <session_ids> --acquisitions <acquisition_ids>
```
Replace `<folder_bids_path>` with the path to your BIDS dataset folder, `<subject_ids>` with the IDs of the subjects you want to process, `<session_ids>` with the IDs of the sessions you want to process, and `<acquisition_ids>` with the IDs of the acquisitions you want to process (ex. hermes or abcd).

**Example Command**
```
python3 main.py --bids 'path/to/OUTPUT_DIR' --subjects 003 --sessions 02 --acquisitions hermes
```


## Visualization of tractography results

If you choose to create a brain tractogram, you'll have a folder in `derivatives/sub-XXX/ses-XX/acq/preprocessing` named `tractseg_output`. It contains all the data created by TractSeg.

1. FA histogram along specific tracks
	
Download the 'subjects.txt' template from this git repository. Open the files and complete it following the instructions given in the file. Then, from the terminal launch the command:
```
plot_tractometry_results -i <path_subjects.txt> -o <path_tractseg_output/results.png> --mc
```
This command create a file `results.png` in the `tractseg_output` folder. It represents the evolution of the FA values along certain tracts specified in the `subjects.txt` file.

2. Visualize the tracks with mrview

To see the tracks you can use mrview. Launch mrview from the terminal. Open the preprocessed diffusion image which is named `sub-XXX_ses-XX_..._denoise_degibbs_prproc_unbiased.mif`. Then with 'Tools' add 'tractography'. Then open the track that you want to vizualize from `TOM_trackings` folder. To visualize only the track click on 'View' and 'Hide main image'.  


## Removing volumes

If you want to remove some volumes of your images to increase the quality of the processing, here's how you can do:
	- Create a text file in which you write the indices of the volumes that you want to remove. Each index must be separated from the other with a space. You can find an example in `ressources`. 
	- Run the same command as in the 'Getting started' section but add an option `--volumes` followed by the path to the text file that you just created. The program will create a new folder: `dwi-acq_removed_volumes` where you can find the results of the pre and post processing on the image with removed volumes.
	
**Example command**	
```
python3 main.py --bids 'path/to/OUTPUT_DIR' --subjects 003 --sessions 02 --acquisitions hermes --volumes 'path/to/volumes_to_remove.txt'
```


## How to choose which volumes to remove

Open the pdf file located in: `preprocessing/qc_text/quad/qc.pdf`. On the 6th page you'll see a chart indicating the number of outlier in each volume. A good idea is to supress the volumes having too many outliers (high peaks on top of the chart).
You can also visualize by hand the volumes by typing in the terminal `mrview path/to/img.mif` and decide which volume to remove. The ones where the head is tilted and the ones featuring dark bands are good to remove.


## Important Notes

* Make sure you have the BIDS files in the `OUTPUT_DIR` folder.
* The processed output will be stored in the `derivatives` directory.
* **Respect the BIDS format**: Ensure that your input files are in the correct BIDS format, as incorrect formatting may cause errors or incorrect results.

