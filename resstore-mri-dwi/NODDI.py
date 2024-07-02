import amico
import os
from useful import convert_mif_to_nifti, delete_directory

def NODDI(dwi_mif,bval_file,bvec_file,mask_nii):
    # dwi and mask are given . mif and should be .nii.gz
    # Setup AMICO
    print("Setting up AMICO...")
    amico.setup()
    print("AMICO setup complete.\n")

    # Paths
    dir = os.path.dirname(dwi_mif)
    convert_mif_to_nifti(dwi_mif, dir, diff=True)
    dwi_file = dwi_mif.replace("mif", "nii.gz")
    scheme_file = os.path.join(dir, "scheme")

    # Convert FSL scheme
    print(f"Converting FSL scheme: {bval_file} {bvec_file} -> {scheme_file}")
    amico.util.fsl2scheme(bval_file, bvec_file, scheme_file)
    print(f"Scheme file saved to: {scheme_file}\n")

    # Load data
    print("Loading data...")
    ae = amico.Evaluation()
    ae.load_data(dwi_file, scheme_file, mask_filename=mask_nii, b0_thr=0)
    print("Data loaded.\n")

    # Set model and generate kernels
    print("Setting model: NODDI")
    ae.set_model('NODDI')
    print("Generating kernels...")
    ae.generate_kernels(regenerate=True)
    print("Kernels generated.\n")

    # Load kernels
    print("Loading kernels...")
    ae.load_kernels()
    print("Kernels loaded.\n")

    # Fit model
    print("Fitting model...")
    ae.fit()
    print("Model fitted.\n")

    # Save results
    print("Saving results...")
    ae.save_results()
    print("Results saved.\n")

    sup_dir = os.path.dirname(dir)
    kernels = os.path.join(sup_dir, "kernels")
    delete_directory(kernels)


    print("AMICO processing complete.")