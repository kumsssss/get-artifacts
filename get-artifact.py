import os
import git
import shutil
import tempfile
import json
import sys, getopt


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
    repo_url = 'https://stash.trusted.visa.com:7990/scm/cl/dmpdtopology.git'
    file_to_bring = 'service/src/main/resources/deployment_manifest.json'

    t = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, t, branch=branch, depth=1)
    shutil.move(os.path.join(t, file_to_bring), '.')
    shutil.rmtree(t)


def get_matching_artifacts(filename, **kwargs):
    output = []
    to_compare_with = []
    using_products = 'products' in kwargs.keys() and kwargs['products']
    using_verticals = 'verticals' in kwargs.keys() and kwargs['verticals']
    is_branch_provided = branch != ''
    is_version_provided = version != ''

    if using_products:
        to_compare_with = kwargs['products']
    else:
        to_compare_with = kwargs['verticals']


    with open(filename, "r") as file_to_read:
        data = json.load(file_to_read)          
        for component in data['artifacts']:
            used_for_product, used_for_vertical = False, False
            matching_branch, matching_version = True, True
            if using_verticals:
                used_for_vertical = component['verticals'] and all(x in component['verticals'] for x in verticals)
            elif 'products' in component:
                used_for_product = component['products'] and all(x in component['products'] for x in products)

            if is_branch_provided:
                matching_branch = component['branch'] and component['branch'] == branch
            if is_version_provided:
                matching_version = component['version'] and component['version'] == version

            if matching_version and matching_branch and (used_for_product or used_for_vertical):
                match = {}
                if 'artifactId' in component and 'artifactType' in component:
                    match['artifactId'] = component['artifactId']
                    match['artifactType'] = component['artifactType']
                elif 'appName' in component and 'applicationType' in component:
                    match['appName'] = component['appName']
                    match['applicationType'] = component['applicationType']
                output.append(match)

    dictionary = {
        "artifacts" : output
    }
    json_object = json.dumps(dictionary, indent=4)
    with open('output.json', "w") as output_file:
        output_file.write(json_object)


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