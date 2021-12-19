import csv
import json


test_report_json = open('test_report.json')
test_report_dict = json.load(test_report_json)


def flatten_test_report(test_report_dict):

    test_suites = test_report_dict['test_suites']
    flatened_test_report_list = []
    for test_suite in test_suites:
        for test_case in test_suite['test_cases']:
            test_case['suite_name'] = test_suite['name']
            flatened_test_report_list.append(test_case)
    return flatened_test_report_list

flatened_test_report = flatten_test_report(test_report_dict)

print(flatened_test_report[0].keys())

with open("test_report.csv", 'w') as f: 
    wr = csv.DictWriter(f, fieldnames = flatened_test_report[0].keys())
    wr.writeheader() 
    wr.writerows(flatened_test_report)

