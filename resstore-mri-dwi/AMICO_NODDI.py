import amico
import os
from useful import convert_mif_to_nifti, delete_directory, verify_file


def NODDI(dwi, mask):

    # Paths
    base_dir = os.path.dirname(os.path.dirname(dwi))
    AMICO_dir = os.path.join(base_dir, "AMICO")
    bval_file = dwi.replace(".nii.gz", ".bval")
    bvec_file = dwi.replace(".nii.gz", ".bvec")
    if not verify_file(AMICO_dir):
        # Setup AMICO
        os.chdir(base_dir)
        print("Setting up AMICO...")
        amico.setup()
        print("AMICO setup complete.\n")
        dir_name = os.path.dirname(dwi)
        scheme_file = os.path.join(dir_name, "scheme")

        # Convert FSL scheme
        print(
            f"Converting FSL scheme: {bval_file} {bvec_file} -> {scheme_file}")
        amico.util.fsl2scheme(bval_file, bvec_file, scheme_file)
        print(f"Scheme file saved to: {scheme_file}\n")

        # Load data
        print("Loading data...")
        ae = amico.Evaluation()
        ae.load_data(dwi, scheme_file, mask_filename=mask, b0_thr=0)
        print("Data loaded.\n")

        # Set model and generate kernels
        print("Setting model: NODDI")
        ae.set_model("NODDI")
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

        analysis_dir = os.path.dirname(dir_name)
        kernels = os.path.join(analysis_dir, "kernels")
        delete_directory(kernels)

    preproc_dir = os.path.dirname(dwi)
    analysis_dir = os.path.dirname(preproc_dir)
    NODDI_dir = os.path.join(analysis_dir, "AMICO", "NODDI")
    os.remove(scheme_file)

    print("AMICO processing completed.")
    return NODDI_dir
