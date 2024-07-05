# RESSTORE MRI-DWI Processing

This project is a processing pipeline for MRI diffusion data of the RESSTORE study. This repository contains the code to process MRI diffusion data using the BIDS (Brain Imaging Data Structure) format.

## Getting Started

To begin, make sure your data are in BIDS format and that they have been organized with dcm2bids_scaffold method. This means your data should look like this:

├── BIDS  
│ ├── code  
│ ├── derivatives  
│ ├── sourcedata  
│ └── sub-001  
│       └── ses-01  
│               ├── anat  
│               ├── dwi  
│               ├── fmap  
│               └── ...  
│       └── ses-02  
│               ├── anat  
│               ├── dwi  
│               ├── fmap  
│               └── ...  
│ └── sub-002  
│       └── ses-01  
│       └── ses-02  
│ └── sub-003  
│       └── ses-01  
│       └── ses-02  
│ ├── CHANGES  
│ ├── dataset_description.json  
│ ├── ...  

To use this code, open the `restorre-mri-dwi` directory in your terminal and run the following command:
```
python3 main.py --bids <folder_bids_path> --subjects <subject_ids> --sessions <session_ids> --acquisitions <acquisition_ids>
```
Replace `<folder_bids_path>` with the path to your BIDS dataset folder, `<subject_ids>` with the IDs of the subjects you want to process, `<session_ids>` with the IDs of the sessions you want to process, and `<acquisition_ids>` with the IDs of the acquisitions you want to process (ex. hermes or abcd).

**Example Command**
```
python3 main.py --bids 'path/to/OUTPUT_DIR' --subjects 003 --sessions 02 --acquisitions hermes
```

## What does the program do

The program creates different ressources that are organize as follow in the `derivatives` directory:

├── sub-001
│ └── ses-01
│ 	└── dwi-abcd
│ 		├── AMICO: NODDI maps (ODI, NDI, FWF,...)
│ 		├── DKI: DKI maps (AK, MK, RK, ...) --> only for multishell data
│ 		├── FA: FA maps and others (FA, ADC, RD, AD)
│ 		├── FOD: all files linked to FOD estimations
│ 		├── preprocessing: preprocessed data from each step 
│ 		├── preprocessing_MNI: processed data passed in the MNI space (DWI, FA, NODDI, DKI, ...)
│ 		├── Tracto: all files related to tractography and some postprocessed data (graphs)
│ 		└── FA_2_MNI.mat
└── FA_stats: tsv file containing stats for mean FA in all subjects

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

