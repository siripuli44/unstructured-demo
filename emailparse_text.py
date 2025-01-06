import os
from unstructured.partition.email import partition_email

 # Define your source and output directories
source_dir = "/Projects/AI/unstructured_demo/input"
output_dir = "/Projects/AI/unstructured_demo/output"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Open the output file
with open(os.path.join(output_dir, "output.txt"), "w") as output_file:
    # Iterate over all files in the source directory
    for filename in os.listdir(source_dir):
        # Check if the file is an .eml file
        if filename.endswith(".eml"):
            # Parse the email
            elements = partition_email(filename=os.path.join(source_dir, filename))
            # Write the text of each element to the output file
            for element in elements:
                output_file.write(element.text + "\n")