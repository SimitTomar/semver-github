#!/usr/bin/env python3
import os
import sys
import requests
import json
import subprocess
import traceback
import release_notes_constants


class MrTemplate():


    def get_mr_template_dict(self, mr_for_target_branch, header_text):

        """

        The function returns the template dictionary containing the info of the components impacted/not impacted by a merge reequest
        :param: mr_for_target_branch: merge request corresponding to the target branch 
        :param: header_text: text following which the component checkboxes need to be captured
        :return: components impacted/not impacted by a merge request
        :rtype: dict

        """

        try:
            mr_template_dict = {}
            mr_template = mr_for_target_branch['description']
            if mr_template:
                mr_template = mr_template.splitlines()
                if header_text in mr_template:
                    for i, val in enumerate(mr_template):
                        if val == header_text:
                            mr_template_dict = self.create_mr_template_dict(mr_template, i+1)
                            if mr_template_dict:
                                if mr_template_dict['impacted_components']:
                                    return mr_template_dict
                                else:
                                    print(f"No impacted components found for the merge request header text: {header_text} in mr_template: {mr_template}")
                                    return {}
                            else:
                                print(f"mr_template_dict is empty: {mr_template_dict}")
                                return mr_template_dict
                    return mr_template_dict
                else:
                    print(f"merge request template does not contain the header text: {header_text}")
                    return mr_template_dict
            else:
                print('merge request does not have any description')
                return mr_template_dict
        except KeyError:
            print(f"Oops !! A key error occurred while creating the merge request template json")
            traceback.print_exc()
            return {}
        except:
            print("Oops !! An unhandled error occurred while creating the merge request template json")
            traceback.print_exc()
            
    def create_mr_template_dict(self, mr_template, header_text_index):

        """

        The function creates a dictionary containing the info of the components impacted/not impacted by a merge reequest
        :param: mr_template: description of a merge request
        :param: header_text_index: i+1, where i is the index of header_text, corresponding to which the checkboxes are to be captured
        :return: dictionary of components impacted/not impacted based on their corresponding checkboxes (enabled=impacted, disabled=not impacted)
        :rtype: dict

        """

        try:

            mr_template_dict = {"impacted_components": [], "non_impacted_components": []}

            for text in range(header_text_index, len(mr_template)):
                mr_template[text] = mr_template[text].strip()
                if mr_template[text].startswith(release_notes_constants.ENABLED_CHECKBOX_MARKDOWN):
                    checkbox_text = mr_template[text].split(release_notes_constants.ENABLED_CHECKBOX_MARKDOWN)
                    mr_template_dict["impacted_components"].append(checkbox_text[1].strip())
                elif mr_template[text].startswith(release_notes_constants.DISABLED_CHECKBOX_MARKDOWN):
                    checkbox_text = mr_template[text].split(release_notes_constants.DISABLED_CHECKBOX_MARKDOWN)
                    mr_template_dict["non_impacted_components"].append(checkbox_text[1].strip())
                elif mr_template[text] is None or mr_template[text] == '' or mr_template[text] == ' ':
                    continue
                else:
                    break
            return mr_template_dict
        except IndexError:
            print(f"Oops !! An index error occurred while creating the merge request template dictionary")
            traceback.print_exc()
        except AttributeError:
            print(f"Oops !! An attribute error occurred while creating the merge request template dictionary")
            traceback.print_exc()
        except KeyError:
            print(f"Oops !! A key error occurred while creating the merge request template dictionary")
            traceback.print_exc()
        except:
            print("Oops !! An unhandled error occurred while creating the merge request template dictionary")
            traceback.print_exc()
