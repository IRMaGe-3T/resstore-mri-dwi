from useful import execute_command, verify_file



def getFAstats (FA, ROI_mask):

    # Create a dictionnary
    d = {} 
    
    ROI_mask_grid = ROI_mask.replace(".nii.gz", "_grid.nii.gz")
    if not verify_file(ROI_mask_grid):
        cmd = ["mrgrid", ROI_mask, "regrid", "-template", FA, ROI_mask_grid, "-interp", "nearest"]
        result, stderrl, sdtoutl = execute_command(cmd)

    
    cmd = ["mrstats", "-mask", ROI_mask_grid, FA]
    result, stderrl, sdtoutl = execute_command(cmd)
    
    res = sdtoutl.split()    
       
    d['FA'] = FA
    d['ROI_mask'] = ROI_mask
    d[res[0]]=res[8]
    d[res[1]]=res[10]
    d[res[2]]=res[11]
    d[res[3]]=res[12]
    d[res[4]]=res[13]
    d[res[5]]=res[14]
    d[res[6]]=res[15]

    return d
