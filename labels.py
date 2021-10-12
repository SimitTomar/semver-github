#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess
import requests
import re

import constants


def main():

    project_id = os.environ["CI_PROJECT_ID"]
    print('project_id', project_id)
    merge_request_iid = os.environ["CI_MERGE_REQUEST_IID"]
    print('merge_request_iid', merge_request_iid)
    if merge_request_iid != '$CI_MERGE_REQUEST_IID':

        endpoint = f"{constants.BASE_ENDPOINT}/projects/{project_id}/merge_requests/{merge_request_iid}?labels=version::minor"
        print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
        mr_response = requests.put(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
        print('mr_response', mr_response.json())
    else:
        print('merge_request_iid is blank')


if __name__ == "__main__":
    sys.exit(main())
