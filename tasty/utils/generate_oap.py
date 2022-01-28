from curses import ncurses_version
import os
import json


import tasty.graphs as tg
import tasty.templates as tt

temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
points_file = os.path.join(temp_dir, 'oap_points_1_1.json')
functions_file = os.path.join(temp_dir, 'oap_functions_1_1.json')
source_shapes_dir = os.path.join(os.path.dirname(__file__), '../source_shapes', 'haystack')


def stub_output():
    prefix = 'oap'
    ns = "https://oap.buildingsiot.com#"

    output = {
        'prefix': prefix,
        'namespace': ns,
    }
    return output


def write_output(output):
    with open(os.path.join(source_shapes_dir, 'oap.json'), 'w+') as f:
        f.write(json.dumps(output, indent=2))


def construct_point_shapes(haystack_ont):
    shapes = []
    with open(points_file, 'r') as f:
        data = json.loads(f.read())
    points = data['data']['points']
    for pt in points:
        print(f"Processing: {pt['code']}")
        shape = {
            'name': pt['code']
        }
        if pt.get('name') != '':
            shape['description'] = pt['name']
        tags = []
        tags_custom = []
        try:
            types = pt['haystack']['types']
        except KeyError:
            continue
        for tag in types:
            t = tag.get('tag')
            if t:
                if t['type'] == 'MARKER':
                    if t['source'] == 'HAY':
                        tags.append(t['name'])
                    else:
                        tags_custom.append(t['name'])

        ns_terms = tt.get_namespaced_terms(haystack_ont, '-'.join(tags))
        print(ns_terms)
        structured = tt.hget_entity_classes(haystack_ont, ns_terms)
        types = []
        markers = []
        for each_class in structured['classes']:
            types.append(each_class[1])
        for each_marker in structured['markers']:
            markers.append(each_marker[1])

        shape['types'] = types
        if markers:
            shape['tags'] = markers
        if tags_custom:
            shape['tags-custom'] = tags_custom
        shapes.append(shape)
    return shapes


def construct_composite_shapes(shapes):
    with open(functions_file, 'r') as f:
        data = json.loads(f.read())
    functions = data['data']['functions']
    for function in functions:
        print(f"Processing: {function['code']}")
        shape = {
            'name': function['code']
        }
        internal_shapes = []
        predicates = {
            'optional': [{
                'path': 'equipRef',
                'path-type': 'inverse',
            }]
        }
        if function.get('name') != '':
            shape['description'] = function['name']
        for point in function.get('points', []):
            matching_shape = next((shape for shape in shapes if shape['name'] == point.get('code')), None)
            if matching_shape:
                internal_shapes.append(matching_shape['name'])
        if internal_shapes:
            predicates['optional'][0]['shapes'] = internal_shapes
            shape['predicates'] = predicates
            shapes.append(shape)
        else:
            print(f"No matching shapes found for function: {function['code']}")

    return shapes


def main():
    haystack_ont = tg.load_ontology('Haystack', '3.9.10')
    output = stub_output()
    shapes = construct_point_shapes(haystack_ont)
    shapes = construct_composite_shapes(shapes)
    output['shapes'] = shapes
    write_output(output)


if __name__ == '__main__':
    main()
