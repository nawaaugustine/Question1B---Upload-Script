import json
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
from datetime import date
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)

def load_config(config_file):
    """
    Load the JSON configuration file and return the configuration dictionary.
    
    Args:
        config_file (str): Path to the JSON configuration file.

    Returns:
        dict: Configuration dictionary.
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return None


def process_submission(row, matching_rows, project_uuid):
    """
    Create an XML tree structure for the given row, matching_rows, and project_uuid.
    Add various elements to the XML tree based on the input data and return the root
    of the XML tree structure.

    Args:
        row (pd.Series): A row from the parent dataframe.
        matching_rows (pd.DataFrame): Matching rows from the child dataframe.
        project_uuid (str): The project UUID.

    Returns:
        xml.etree.ElementTree.Element: Root of the XML tree structure.
    """

    today = date.today()
    today_str = today.strftime('%Y-%m-%d')  # Convert the date object to a string

    root = ET.Element('data')
    root.set('id', project_uuid)
    root.set('xmlns:orx', 'http://openrosa.org/xforms')
    root.set('xmlns:jr', 'http://openrosa.org/javarosa')

    # set root level elements
    ET.SubElement(root, 'start').text = today_str
    ET.SubElement(root, 'end').text = today_str
    ET.SubElement(root, 'today').text = today_str

    # creating the intro group element - This is a regular group in KoBo
    intro = ET.SubElement(root, 'intro')
    ET.SubElement(intro, 'acknowledgement').text = 'OK'
    
    # creating the Household head element - This is a regular group in KoBo
    household = ET.SubElement(root, 'household')
    ET.SubElement(household, 'FID').text = str(row['FID'])
    ET.SubElement(household, 'HName').text = str(row['HName'])
    ET.SubElement(household, 'HSex').text = str(row['HSex'])
    ET.SubElement(household, 'HAge').text = str(row['HAge'])
    ET.SubElement(household, 'HLocation').text = str(row['HLocation'])
    
    # Add the new household element to check if a child record exists
    has_child_record = 'Yes' if not matching_rows.empty else 'No'
    ET.SubElement(household, 'other_members').text = has_child_record
    
    # Add the total count of matching child records plus 1 to the household element
    child_count = len(matching_rows) + 1
    ET.SubElement(household, 'HHSize').text = str(child_count)

    # Creating the Individual elements which is a repeating group in kobo. Individual group is a repeat group in this use case
    for j, matching_row in matching_rows.iterrows():
        Individual = ET.SubElement(root, 'Individual')
        
        ET.SubElement(Individual, 'FID').text = str(matching_row['FID'])
        ET.SubElement(Individual, 'Individual_FullName').text = str(matching_row['Individual_FullName'])
        ET.SubElement(Individual, 'Individual_Sex').text = str(matching_row['Individual_Sex'])
        ET.SubElement(Individual, 'Individual_Age').text = str(matching_row['Individual_Age'])
        ET.SubElement(Individual, 'Relationship').text = str(matching_row['Relationship'])
    
    # Although kobo may accept the submission without this meta element it is highly recommended by openrosa
    meta = ET.SubElement(root, 'meta')
    meta_instanceID = ET.SubElement(meta, 'instanceID')
    meta_instanceID.text = project_uuid

    return root


def post_submission(root, endpoint, headers):
    """
    Post the XML submission data to the KoBoToolbox server.

    Args:
        root (xml.etree.ElementTree.Element): Root of the XML tree structure.
        endpoint (str): The API endpoint for posting the submission.
        headers (dict): The headers for the HTTP request.

    Returns:
        None
    """
    try:
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        payload = {'xml_submission_file': ('data.xml', xml_string, 'text/xml')}
        response = requests.post(endpoint, headers=headers, files=payload)
        logging.info(f'Submission status: {response.status_code} {response.text}')
    except Exception as e:
        logging.error(f"Failed to post submission: {e}")


def main():
    """
    Main function that reads Excel data into Pandas dataframes, iterates through
    the rows, creates XML entries, and posts them to the KoBoToolbox server.

    Steps:
    1. Load the configuration from the 'config.json' file.
    2. Read Excel data into Pandas dataframes for parent and child data.
    3. Construct the endpoint URL and headers for API requests to KoBoToolbox.
    4. Iterate through the rows in the parent dataframe, find the matching rows 
       in the child dataframe, and process the submissions by creating XML entries.
    5. Send the XML submission data to the KoBoToolbox server using HTTP POST requests.
    6. Print the submission status and response from the server.
    """
    config = load_config('config.json')
    if config is None:
        return

    df_parent  = pd.read_excel(config['parent_data_path'])
    df_children = config['child_data_paths']
    
    endpoint = 'https://kobocat.unhcr.org/api/v1/submissions'
    headers = {'Authorization': f"Token {config['api_token']}"}

    with ThreadPoolExecutor(max_workers=5) as executor:
        for i, row in df_parent.iterrows():
            parent_id = row[config['parent_id_column']]
            matching_rows_data = []
            if len(df_children) > 0:
                for child_data_path in df_children:
                    if os.path.isfile(child_data_path['path']):
                        df_child = pd.read_excel(child_data_path['path'])
                        matching_rows_data.extend(df_child[df_child[config['child_id_column']] == parent_id].to_dict('records'))
                    else:
                        logging.warning(f"{child_data_path['name']} does not exist!")
            matching_rows_df = pd.DataFrame(matching_rows_data)
            root = process_submission(row, matching_rows_df, config['project_uuid'])
            executor.submit(post_submission, root, endpoint, headers)


if __name__ == '__main__':
    main()