import os
import git
import shutil
import tempfile
import json
import sys, getopt
import functools
from prettytable import PrettyTable

DEPLOYMENT_TARGET = 'deploymentTarget'
ARTIFACT_ID = 'artifactId'
ARTIFACT_TYPE = 'artifactType'
APP_NAME = 'appName'
APP_TYPE = 'applicationType'
PRODUCTS = 'products'
VERTICALS = 'verticals'


def read_arguments(argv):
    '''
    Contains the flags with the argument paired together. Assigns arguments to the respective global variable.
    Ensures either branch or version is provided.
    Ensures product or vertical is provided but not both.
    '''
    try:
        short_options = "b:v:f:p:"
        long_options = ["branch=", "version=", "filename=", "filepath=", "products=", "verticals="]
        opts, args = getopt.getopt(argv,short_options,long_options)
    except getopt.GetoptError:
        print('Error in getopt')
        sys.exit(2)

    global verticals, branch, version, filename, filepath, products
    for opt, arg in opts:
        # print(opt, arg)
        if opt in ("-b", "--branch"):
            branch = arg
        elif opt in ("-v", "--version"):
            version = arg
        elif opt in ("-f", "--filename"):
            filename = arg
        elif opt == "--filepath":
            if (not os.path.exists(arg)):
                print("Incorrect file path given")
                sys.exit(4)
            filepath = arg
        elif opt in ("-p", "--products"):
            if verticals:
                print("provide either verticals or products. Do not give both")
                sys.exit(3)
            products.append(arg)
        elif opt == "--verticals":
            if products:
                print("provide either verticals or products. Do not give both")
                sys.exit(3)
            verticals.append(arg)
        else: 
            print("failed for ", opt, arg)

    if not branch and not filename and not filepath:
        print("Branch must be provided if no filename or filepath given")
        sys.exit(1)
    elif not products and not verticals:
        print("Either products or verticals must be provided")
        sys.exit(1)


def get_deployment_manifest_file(branch):
    '''
    Pulls the deployment_manifest.json file from the specified branch
    Clones the whole repo into a temporary folder and deletes it after moving out
    the json file.
    '''
    # repo_url = 'https://stash.trusted.visa.com:7990/scm/cl/dmpdtopology.git'
    repo_url = 'ssh://git@stash.trusted.visa.com:7999/cl/dmpdtopology.git'
    file_to_bring = 'service/src/main/resources/deployment_manifest.json'

    t = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, t, branch=branch, depth=1)
    shutil.move(os.path.join(t, file_to_bring), '.')
    shutil.rmtree(t)


def get_matching_artifacts(filename, **kwargs):
    output = []
    to_compare_with = []
    using_products = PRODUCTS in kwargs.keys() and kwargs[PRODUCTS]
    using_verticals = VERTICALS in kwargs.keys() and kwargs[VERTICALS]
    is_branch_provided = branch != ''
    is_version_provided = version != ''

    if using_products:
        to_compare_with = kwargs[PRODUCTS]
    else:
        to_compare_with = kwargs[VERTICALS]


    with open(filename, "r") as file_to_read:
        data = json.load(file_to_read)          
        for component in data['artifacts']:
            used_for_product, used_for_vertical = False, False
            matching_branch, matching_version = True, True
            if using_verticals:
                used_for_vertical = component[VERTICALS] and all(x in component[VERTICALS] for x in verticals)
            elif PRODUCTS in component:
                used_for_product = component[PRODUCTS] and all(x in component[PRODUCTS] for x in products)

            if is_branch_provided:
                matching_branch = component['branch'] and component['branch'] == branch
            if is_version_provided:
                matching_version = component['version'] and component['version'] == version

            if matching_version and matching_branch and (used_for_product or used_for_vertical):
                match = {}
                if DEPLOYMENT_TARGET in component:
                    match[DEPLOYMENT_TARGET] = component[DEPLOYMENT_TARGET]

                if ARTIFACT_ID in component and ARTIFACT_TYPE in component:
                    match[ARTIFACT_ID] = component[ARTIFACT_ID]
                    match[ARTIFACT_TYPE] = component[ARTIFACT_TYPE]
                elif APP_NAME in component and APP_TYPE in component:
                    match[APP_NAME] = component[APP_NAME]
                    match[APP_TYPE] = component[APP_TYPE]
                output.append(match)

    output.sort(key=functools.cmp_to_key(comparator))
    print_output_table(output)

    dictionary = {
        "artifacts" : output
    }
    json_object = json.dumps(dictionary, indent=4)
    with open('output.json', "w") as output_file:
        output_file.write(json_object)


def comparator(a, b):

    def comparator_by_key(a,b, attr):
        if attr in a and attr not in b:
            return -1
        elif attr in b and attr not in a:
            return 1
        elif attr in a and attr in b:
            if a[attr] < b[attr]:
                return -1
            elif a[attr] > b[attr]:
                return 1

        if attr == DEPLOYMENT_TARGET:
            return comparator_by_key(a, b, ARTIFACT_TYPE)
        elif attr == ARTIFACT_TYPE:
            return comparator_by_key(a, b, APP_TYPE)
        else:
            return 0

    return comparator_by_key(a, b, DEPLOYMENT_TARGET)


def print_output_table(output):
    headers = [DEPLOYMENT_TARGET, ARTIFACT_ID, ARTIFACT_TYPE, APP_NAME, APP_TYPE]
    t = PrettyTable(headers)
    current_deployment_target = ''


    for x in output:
        if DEPLOYMENT_TARGET in x and current_deployment_target == '':
            current_deployment_target = x[DEPLOYMENT_TARGET]
        elif DEPLOYMENT_TARGET in x and current_deployment_target != x[DEPLOYMENT_TARGET]:
            print(current_deployment_target)
            print(t)
            t = PrettyTable(headers)
            current_deployment_target = x[DEPLOYMENT_TARGET]
        elif DEPLOYMENT_TARGET not in x and current_deployment_target != '':
            print(current_deployment_target)
            print(t)
            t = PrettyTable(headers)
            current_deployment_target = ''

        if DEPLOYMENT_TARGET in x and ARTIFACT_TYPE in x:
            t.add_row([x[DEPLOYMENT_TARGET], x[ARTIFACT_ID], x[ARTIFACT_TYPE], '', ''])
        elif DEPLOYMENT_TARGET in x and APP_TYPE in x:
            t.add_row([x[DEPLOYMENT_TARGET], '', '', x[APP_NAME], x[APP_TYPE]])
        elif ARTIFACT_TYPE in x:
            t.add_row(['', x[ARTIFACT_ID], x[ARTIFACT_TYPE], '', ''])
        else:
            t.add_row(['', '', '', x[APP_NAME], x[APP_TYPE]])
    print(t)


def main(argv):
    read_arguments(argv)
    global filename
    if not filename and not filepath and branch:
        get_deployment_manifest_file(branch)
        filename = "deployment_manifest.json"
    if filename:
        get_matching_artifacts(filename, products=products, verticals=verticals)
    else:
        get_matching_artifacts(filepath, products=products, verticals=verticals)


if __name__ == "__main__":
    branch, version, filename, filepath = '', '', '', ''
    products, verticals = [], []
    main(sys.argv[1:])