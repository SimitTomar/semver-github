#!/usr/bin/env python3
import requests
import re
import traceback
import release_notes_constants


class MrJiraIds():

    def __init__(self, gitlab_env_vars):
        self.gitlab_env_vars = gitlab_env_vars

    def get_jira_ids_list(self, mr_for_target_branch):

        """

        The function gets all the unique jira ids from the commit messages of a merge request
        :param: mr_for_target_branch: merge request corresponding to the target branch 
        :return: list of all the unique jira ids
        :rtype: list

        """

        try:
            jira_ids_list = []
            mr_iid = mr_for_target_branch['iid']
            mr_commits = self.get_mr_commits(mr_iid)
            if mr_commits:
                for mr_commit in mr_commits:
                    jira_id = self.extract_jira_id(mr_commit['message'])
                    if jira_id:
                        if jira_id not in jira_ids_list:
                            jira_ids_list.append(jira_id)
                return jira_ids_list
            else:
                print('Unable to retrieve any commits for the merge request')
                return jira_ids_list
        except KeyError:
            print('Oops !! An key error occurred while creating the merge request jira ids json')
            traceback.print_exc()
        except:
            print('Oops !! An unhandled error occurred while creating the merge request jira ids json')
            traceback.print_exc()
      
    def get_mr_commits(self, mr_iid):

        """

        The function gets all the commits corresponding to a merge request through the gitlab's merge request api
        :param: mr_iid: merge request iid
        :return: all the commits corresponding to a merge request
        :rtype: dict

        """

        try:
            mr_commits = {}
            endpoint = f"{release_notes_constants.GITLAB_BASE_ENDPOINT}/projects/{self.gitlab_env_vars['CI_PROJECT_ID']}/merge_requests/{mr_iid}/commits"
            print(f"Getting all the commits of a merge request, endpoint is: {endpoint}")
            mr_commits = requests.get(endpoint, headers = {"PRIVATE-TOKEN": self.gitlab_env_vars['GITLAB_TOKEN']})
            mr_commits.raise_for_status()
            mr_commits = mr_commits.json()
            return mr_commits
        except requests.exceptions.HTTPError:
            print('Oops !! HTTP Error error occurred while getting all the commits of a merge request')
            traceback.print_exc()
        except:
            print('Oops !! An unhandled error occurred while getting all the commits of a merge request')
            traceback.print_exc()
         
    def extract_jira_id(self, message):

        """

        The function extracts the  jira id (like AQUA-1234) fro the commit message
        :param: message: commit message
        :return: jira id
        :rtype: string

        """

        try:
            jira_id_regex = re.search("[A-z]+-[0-9]+", message)
            if jira_id_regex:
                jira_id = jira_id_regex.group(0)
                return jira_id
        except IndexError:
            print('Oops !! An index error occurred while extracting the jira id from a commit message')
            traceback.print_exc()
        except:
            print('Oops !! An unhandled exception occured while extracting the jira id from a commit message')
            traceback.print_exc()


            
      