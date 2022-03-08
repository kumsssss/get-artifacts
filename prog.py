import json

unique_products = []
unique_verticals = []
with open('deployment_manifest.json', 'r') as f:
    arr = json.load(f)
    for component in arr['artifacts']:
        if 'products' in component:
            curr_products = component['products']
            for prod in curr_products:
                if prod not in unique_products:
                    unique_products.append(prod)
        if 'verticals' in component:
            curr_verticals = component['verticals']
            for vert in curr_verticals:
                if vert not in unique_verticals:
                    unique_verticals.append(vert)

unique_products.sort()
unique_verticals.sort()

with open('products_master.out', "w") as f:
    f.writelines('\n'.join(unique_products))

with open('verticals_master.out', "w") as f:
    f.writelines('\n'.join(unique_verticals))