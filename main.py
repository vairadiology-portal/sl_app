import streamlit as st
from pathlib import Path
from tqdm import tqdm
from pydicom import dcmread
import SimpleITK as sitk
from pathlib import Path
import numpy as np
import os, glob

# Define a function to parse the DICOMDIR file
def parse_dicomdir(path_to_jacket, root_dir):
    # Load the DICOMDIR file
    ds = dcmread(path_to_jacket)
    root_dir = Path(ds.filename).resolve().parent
    series_list = []

    # Iterate through the PATIENT records
    for patient in ds.patient_records:
        # Find all the STUDY records for the patient
        studies = [ii for ii in patient.children if ii.DirectoryRecordType == "STUDY"]
        for study in studies:
            descr = study.StudyDescription or "(no value available)"
            # Find all the SERIES records in the study
            all_series = [ii for ii in study.children if ii.DirectoryRecordType == "SERIES"]
            for series in tqdm(all_series):
                images = [ii for ii in series.children if ii.DirectoryRecordType == "IMAGE"]
                plural = ('', 's')[len(images) > 1]
                descr = getattr(series, "SeriesDescription", "(no value available)")
                elems = [ii["ReferencedFileID"] for ii in images]
                paths = [[ee.value] if ee.VM == 1 else ee.value for ee in elems]
                paths = [Path(*p) for p in paths]
                paths_clean = clean_paths(paths, root_dir)
                if (len(paths_clean) > 3):
                    series_list.append(f"SERIES: SeriesNumber={series.SeriesNumber}, "
                                       f"Modality={series.Modality}, SeriesDescription={descr} - "
                                       f"{len(paths_clean)} SOP Instance{plural}")
    return series_list

def load_im(st, path, root_dir):
    ds = dcmread(path)

    for patient in ds.patient_records:
        studies = [ii for ii in patient.children if ii.DirectoryRecordType == "STUDY"]

        for study in studies:
            all_series = [ii for ii in study.children if ii.DirectoryRecordType == "SERIES"]

            for series in all_series:
                images = [ii for ii in series.children if ii.DirectoryRecordType == "IMAGE"]
                plural = ('', 's')[len(images) > 1]
                descr = getattr(series, "SeriesDescription", "(no value available)")
                elems = [ii["ReferencedFileID"] for ii in images]
                paths = [[ee.value] if ee.VM == 1 else ee.value for ee in elems]
                paths = [Path(*p) for p in paths]
                paths_clean = clean_paths(paths, root_dir)

                if (len(paths_clean) > 3) & (st == (f"SERIES: SeriesNumber={series.SeriesNumber}, "
                    f"Modality={series.Modality}, SeriesDescription={descr} - "
                    f"{len(paths_clean)} SOP Instance{plural}")):
                    loc = []

                    for p in paths_clean:
                        instance = dcmread(Path(root_dir) / p)
                        loc.append(float(instance.get('SliceLocation', '(missing)')))
                    paths_clean = [x for _,x in sorted(zip(loc, paths_clean))]
                    instance = sitk.ReadImage(paths_clean, imageIO='GDCMImageIO')
                    direction = instance.GetDirection()
                    origin = instance.GetOrigin()
                    spacing = instance.GetSpacing()
                    vol = sitk.Image([instance.GetWidth(), instance.GetHeight(), len(paths_clean)],
                                     instance.GetPixelIDValue())
                    vol.SetOrigin(origin)
                    vol.SetSpacing(spacing)
                    vol.SetDirection(direction)

                    for i, path in enumerate(paths_clean):
                        instance = sitk.ReadImage(str(root_dir / path))
                        instance.SetDirection(direction)
                        vol[:, :, i] = instance[:, :]

                    return vol

# Define a function to clean up file paths
def clean_paths(paths, root_dir):
    cleaned_paths = []
    for path in paths:
        print('path', path)
        print('exists')
        print('list',os.listdir(root_dir))
        cleaned_paths.append(root_dir.joinpath(path))
    return cleaned_paths

#Function used to remove paths in the .DICOMDIR file that are not present in the folder
def filter_files_in_root(files, root):
    root_files = []
    for file in files:
        print(os.path.join(root, file))
        if os.path.isfile(os.path.join(root, file)):
            root_files.append(file)
    return root_files
# Define the Streamlit app
st.title("DICOMDIR parser and viewer")

root_dir = Path(st.text_input("Enter the root directory path:"))

# Select the DICOMDIR file using the file_uploader widget
dicomdir = st.file_uploader("Select a DICOMDIR file")

# If a DICOMDIR file is selected, parse it and display the series list
if dicomdir is not None:
    # Save the DICOMDIR file to a temporary file
    with open("temp.dcm", "wb") as f:
        f.write(dicomdir.getvalue())

    # Parse the DICOMDIR file
    series_list = parse_dicomdir("temp.dcm", root_dir)
    st.write("You selected the following series len:", len(series_list))
    # Display the series list using the selectbox widget
    if len(series_list) > 0:
        selected_series = st.selectbox("Select a series", series_list)
        st.write("You selected the following series:", selected_series)
        # Load the selected series as a 3D volume
        volume = load_im(selected_series, "temp.dcm", root_dir)
        # Display a slicer widget to allow the
        if volume is not None:
            slice_index = st.slider("Select a slice index", 0, volume.GetSize()[2]-1)
            slice_image = sitk.GetArrayViewFromImage(volume)[slice_index, :, :]
            normalized_image = (slice_image - slice_image.min()) * (255 / (slice_image.max() - slice_image.min()))
            st.image(normalized_image.astype(np.uint8))