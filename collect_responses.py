import pandas as pd
from os import makedirs
from shutil import copy
import os.path as osp
from glob import glob
import pandoc
import numpy as np
from pandas.api.types import is_any_real_numeric_dtype


df = pd.read_excel('responses.xlsx')

# For each response, collect everything in a folder for Conny
for i, row in df.iterrows():
    first_group = row['Research Group'].split(';')[0].split('(')[0].strip()
    full_name = row['Full Name'].strip().split()
    dest_dir = f'responses-conny/{first_group}/{full_name[-1]}, {" ".join(full_name[:(-1)])}'
    makedirs(dest_dir, exist_ok=True)

    # Copy the image files
    file_src = glob(f'response_data/portraits_renamed/portrait {row["ID"]} {row["Full Name"]}.*')
    if len(file_src) > 0:
        file_src = file_src[0]
    else:
        continue  # Skip these students for now
    file_dest = osp.join(dest_dir, osp.basename(file_src))
    copy(file_src, file_dest)

    file_src = glob(f'response_data/figures_renamed/figure {row["ID"]} {row["Full Name"]}.*')
    if len(file_src) > 0:  # It's allowed for responses to have no figures
        file_src = file_src[0]
        file_dest = osp.join(dest_dir, osp.basename(file_src))
        copy(file_src, file_dest)

    # Create the word file with project description and other info
    md_string = f"""\
| **{row['Project Title']}**

| **{row['Full Name']}** ({row['Project Type']}), {row['E-mail']}

| **Sponsor:** {row['Sponsor(s)']}
| **Supervisor(s):** {row['Supervisor(s)']}

| **Keyword(s):** {row['Keywords']}

"""
    file_src = glob(f'response_data/project_descriptions_renamed/project_description {row["ID"]} {row["Full Name"]}.*')
    if len(file_src) > 0:
        file_src = file_src[0]
    else:
        continue  # Skip these students for now
    if osp.splitext(file_src)[1] != '.docx':
        continue  # Skip these students for now
    project_description = pandoc.read(file=file_src)
    md_string += pandoc.write(project_description)
    fig_caption = row['Figure Caption (optional)']
    if not (is_any_real_numeric_dtype(type(fig_caption)) and np.isnan(fig_caption)):
        fig_caption = fig_caption.removeprefix('Figure 1').removeprefix('figure 1').removeprefix(':').removeprefix('.')
        md_string += f"""

Figure 1: {fig_caption.strip()}

"""

    # Here we have to add the references (bibliography) to the md_string
    file_src = glob(f'response_data/references_renamed/references {row["ID"]} {row["Full Name"]}.*')
    if len(file_src) > 0:  # References are optional
        if osp.splitext(file_src[0])[1] == '.docx':  # Skip students with bib files for now
            continue
        try:
            md_string += '\n'  # Add an empty line to separate from previous part
            ref_df = pd.read_excel(file_src[0]).sort_values(by='Number')
            for i, ref_row in ref_df.iterrows():
                if is_any_real_numeric_dtype(type(ref_row["Issue"])) and np.isnan(ref_row["Issue"]):
                    md_string += f'[{ref_row["Number"]}] {ref_row["First author"]} *et al.*, *{ref_row["Journal"]}* ({ref_row["year"]})  \n'
                else:
                    md_string += f'[{ref_row["Number"]}] {ref_row["First author"]} *et al.*, *{ref_row["Journal"]}* **{ref_row["Issue"]}**: {ref_row["page range"]} ({ref_row["year"]})  \n'
        except Exception:
            continue  # Skip these students for now
    else:
        # Add check here whether there are citations in the md_string so far, which would mean that there should be a ref file
        pass


        
    # Write the md_string to a Word file
    doc = pandoc.read(md_string)
    file_dest = osp.join(dest_dir, f'project_description {row["ID"]} {row["Full Name"]}.docx')
    pandoc.write(doc, file=file_dest, format='docx', options=['--reference-doc=custom-reference.docx'])