# Question 1B

This script extracts data from specified Excel files, transforms the data into XML format, and uploads it to the KoBo API endpoint.

## Prerequisites

Before you run the script, ensure that you have:

1. **Python 3**: This script is written in Python 3. If you don't have Python installed, you can download it from the [official Python website](https://www.python.org/downloads/).

2. **Required Python Packages**: The script relies on several Python packages, including `pandas`, `requests`, and `openpyxl`. These can be installed via pip, Python's package installer. Open your terminal or command prompt and run the following command:

    ```sh
    pip install pandas requests openpyxl
    ```

## Configuration

To customize the script for your use, you will need to update the `config.json` file. This file controls various parameters and paths that the script uses to read the data and communicate with the API. The key elements you will need to update include:

- `parent_data_path`: This is the path to the Excel file containing the parent data.
- `child_data_paths`: This is a list of dictionaries, each containing a name and path for an Excel file with child data.
- `parent_id_column` and `child_id_column`: These fields define the column names used to match records between parent and child data.
- `project_uuid`: This is the unique identifier of the project on KoBoToolbox where you intend to upload the data to.
- `api_token`: This is your personal API token for KoBoToolbox.

Please ensure all paths are correct, and all files are not currently open to prevent read/write conflicts.

## Running the Script

Once you have configured your settings, you can run the script using Python. Open your terminal or command prompt, navigate to the directory containing the `main.py` file, and enter the following command:

```sh
python main.py
```

If the script encounters a `Permission denied` error, make sure the Excel files are closed and not in use by another program, then try running the script again.

The script will process each row of data, transform it into XML, and submit it to the KoBoToolbox API. It will log the response status codes and messages for each submission in the terminal. If you encounter any issues, refer to these messages for troubleshooting or contact your technical support.

## Understanding the Output

After running the script, the console will output status codes and messages for each data submission. A 201 or 200 status code generally indicates a successful submission, while other codes may indicate an error occurred. If you see any error messages, note down the associated status codes and refer to the HTTP status codes documentation for more information.
