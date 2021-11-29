#!/usr/bin/env python3
import os
import sys
import requests
import json
import mr_template_constants


def get_mr_template():

    """
    The function hits the merge request api and extracts the description from it

    :return: merge request api description
    :rtype: str
    """

    try:
        project_id = os.environ["CI_PROJECT_ID"]
        mr_iid = os.environ["CI_MERGE_REQUEST_IID"]
        # endpoint = 'https://gitlab.com/api/v4/projects/31630126/merge_requests/13'
        endpoint = f"{mr_template_constants.GITLAB_BASE_ENDPOINT}/projects/{project_id}/merge_requests/{mr_iid}"
        print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
        merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(mr_template_constants.CI_PRIVATE_TOKEN)})
        merge_requests_response.raise_for_status()
        mr_template = merge_requests_response.json()['description']
        if mr_template:
            return mr_template
        else:
            print('Skipping the creation of merge request template json as the template is empty')
    except requests.exceptions.HTTPError as err:
        print(err)
        print('An error occurred while fetching the merge request template')


def create_mr_template_json(mr_template, header_text):

    """
    The function looks for the merge request's header text and stores the information corresponding to its checkboxes in a json file
    
    """

    try:
        mr_template = mr_template.splitlines()
        if header_text in mr_template:
            for i, val in enumerate(mr_template):
                if val == header_text:
                    mr_template_dict = create_mr_template_dict(mr_template, header_text, i+1)
                    print('mr_template_dict', mr_template_dict)
                    if mr_template_dict:
                        with open("mr_template.json", "w") as fp:
                            json.dump(mr_template_dict, fp)
                        break
                    else:
                        print(f"No content found corresponding to the mr header text {header_text}")
        else:
            print(f"mr template does not contain the header text: {header_text}")
    except RuntimeError as re:
        print(re)
        print('An error occurred while creating the merge request template json')



def create_mr_template_dict(mr_template, header_text, header_text_index):

    """
    The function creates a dictionary of the merge request's checkboxes along with their enabled/disabled information.

    :return: dictionary of checkboxes along with their enabled/disabled information
    :rtype: dict
    """

    try:

        mr_template_dict = {header_text: []}
        for val in range(header_text_index, len(mr_template)):
            mr_template[val] = mr_template[val].strip()
            if mr_template[val].startswith(mr_template_constants.ENABLED_CHECKBOX_MARKDOWN):
                checkbox_text = mr_template[val].split(mr_template_constants.ENABLED_CHECKBOX_MARKDOWN)
                mr_template_dict[header_text].append({checkbox_text[1]: "enabled"})
            elif mr_template[val].startswith(mr_template_constants.DISABLED_CHECKBOX_MARKDOWN):
                checkbox_text = mr_template[val].split(mr_template_constants.DISABLED_CHECKBOX_MARKDOWN)
                mr_template_dict[header_text].append({checkbox_text[1]: "disabled"})
            elif mr_template[val] is None or mr_template[val] == '' or mr_template[val] == ' ':
                continue
            else:
                break
        return mr_template_dict
    except RuntimeError as re:
        print(re)
        print('An error occurred while creating the merge request template dictionary')




def main():

    """

    The functions pefroms the following steps:
     - Gets the content of the merge request template 
     - Looks for the Header Text corresponding to which the checkboxes should be retrieved
     - Grabs the content corresponding to the chekboxes along  with their enabled/disabled information and stores them in a json file

    """

    try:
        mr_template = get_mr_template()
        if mr_template:
            mr_template_json = create_mr_template_json(mr_template, os.environ.get(mr_template_constants.MERGE_REQUEST_HEADER_TEXT))
            return 0
            
    except RuntimeError as re:
        print('Oops!! An exception occurred!')
        print(re)

if __name__ == "__main__":
    sys.exit(main())
