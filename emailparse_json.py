import os
import json
from unstructured.partition.email import partition_email

 # Define your source and output directories
source_dir = "/Projects/AI/unstructured_demo/input"
output_dir = "/Projects/AI/unstructured_demo/output"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Parse an email from a file
for filename in os.listdir(source_dir):
     if filename.endswith(".eml"):
        elements = partition_email(filename=os.path.join(source_dir, filename))

        # Convert the elements to dictionaries
        elements_dict = [element.to_dict() for element in elements]

        # Convert the dictionaries to JSON
        elements_json = json.dumps(elements_dict, indent=4)
        outputfile = filename.split(".")

        # Write the output to a file in the specified directory
        with open(os.path.join(output_dir, outputfile[0]+ ".json"), "w") as f:
            f.write(elements_json)