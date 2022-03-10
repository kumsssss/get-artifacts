import json
import functools

def comparator(a, b):
    return comparator_by_key(a, b, 'deploymentTarget')

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

    if attr == 'deploymentTarget':
        return comparator_by_key(a, b, 'artifactType')
    elif attr == 'artifactType':
        return comparator_by_key(a, b, 'applicationType')
    else:
        return 0


with open('output.json', 'r') as f:
    arr = json.load(f)
    components = arr['artifacts']
    components.sort(key=functools.cmp_to_key(comparator))

dictionary = {
    "artifacts" : components
}
json_object = json.dumps(dictionary, indent=4)

with open('output.json', "w") as output_file:
    output_file.write(json_object)
