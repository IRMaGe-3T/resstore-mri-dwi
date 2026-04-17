# How to convert dicom to BIDS for RESSTORE

## Prerequisites
- Have python
- Installe  [dcm2niix](https://github.com/rordenlab/dcm2niix/releases)
- Download [add_data_subject.py](./[add_data_subject.py)
- Install Python dependencies [dcm2bids](https://unfmontreal.github.io/Dcm2Bids/3.2.0/) (version >= 3.0.0)
- Create a dcm2bids configuration file corresponding to your data or download one [here](./dcm2bids_config_files)


## Sourcedata (DICOM) organization 
Organize your sourcedata folder containing  your DICOM as described below.
- Create folders for each subject (subject-XXX).
- Inside each subject folder, create subfolders for each visit (visit-XX).

```
├──DICOM_sourcedata/
|   ├──subject-001/
|   |   ├──visitit-02/
|   |   |  ├──DICOM/ (folder with DICOM for subject 001 for visit 02)
|   |   ├──visitit-05/
|   |   |  ├──DICOM/ (folder with DICOM for subject 001 for visit 05)
|   ├──subject-002/
|   |   ├──visitit-02/
|   |   |  ├──DICOM/ (folder with DICOM for subject 002 for visit 02)
|   |   ├──visitit-05/
|   |   |  ├──DICOM/ (folder with DICOM for subject 002 for visit 05)
```

## BIDS directory 
Create your output directory (BIDS_directory) and, before to add your first subject, organize it following bids structure, using dcm2bids: 

```
dcm2bids_scaffold -o BIDS_directory
```

## Add data in your BIDS directory

Run the add_data_subject.py script: 

```
python add_data_subject.py -s /path/to/sourcedata/ -o /path/to/BIDS_directory -c /path/to/dcm2bids_config.json -subject 01 -visit 02
```
It’s important to check the pairing at the end. If the output message indicates ‘no pairing’ for a useful image you should verify your config.json file





