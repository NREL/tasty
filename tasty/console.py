import argparse
import os
import sys

from tasty.generate_shapes import load_sources, set_version_and_load, generate_shapes_given_source_template
from tasty.generate_input_file import generate_input_file
from tasty.validate import validate_from_csv

current_dir = os.path.dirname(__file__)
source_shapes_dir = os.path.join(current_dir, 'source_shapes')
generated_dir = os.path.join(current_dir, 'generated_shapes')
tasty_root = os.path.join(current_dir, '..')


def generate_shapes(args):
    data = load_sources()
    for file_path, shape_template in data.items():
        name = os.path.splitext(os.path.basename(file_path))[0]
        print("#" * 20)
        print(f"Shapes from file: {name}")
        g, ontology = set_version_and_load(file_path)
        generate_shapes_given_source_template(shape_template, g, ontology, name)


def generate_input(args):
    potential_shapes = [x for x in os.listdir(source_shapes_dir) if x.endswith('.json')]
    shape_to_load = False
    for potential in potential_shapes:
        if args.schema.lower() in potential and args.version.lower() in potential:
            shape_to_load = os.path.join(source_shapes_dir, potential)
            break
    if shape_to_load:
        print(f"Generating input from {os.path.splitext(potential)[0]}")
        generate_input_file(shape_to_load, args.data_graph, args.output, args.composite_only)
    else:
        print(f"No shapes file found to load")
        sys.exit(1)


def validate(args):
    print(args)
    validate_from_csv(args.data_graph, args.input_file)


def main():
    # Construct Parsers
    parser = argparse.ArgumentParser(
        description='Tool for generating SHACL files and validating RDF data against SHACL shapes')
    subparsers = parser.add_subparsers()

    # Generate shapes command
    parser_generate_shapes = subparsers.add_parser('generate-shapes',
                                                   description='Command for generating SHACL shape files')

    parser_generate_shapes.set_defaults(func=generate_shapes)

    # Generate input file command
    parser_generate_input = subparsers.add_parser('generate-input',
                                                  description='Command for generating a simple csv input file')
    parser_generate_input.add_argument(
        '-s',
        '--schema',
        type=str,
        choices=['haystack', 'brick'],
        help='Schema that shapes are defined in',
        default='haystack',
        nargs='?'
    )
    parser_generate_input.add_argument(
        '-v',
        '--version',
        type=str,
        default='v2',
        choices=['v1', 'v2', 'nrel'],
        help='Version of the implementation to use',
        nargs='?'
    )
    parser_generate_input.add_argument(
        '-dg',
        '--data-graph',
        type=str,
        default=None,
        help='Data graph to load ids into the input file',
    )
    parser_generate_input.add_argument(
        '-o',
        '--output',
        type=str,
        default='input-file.csv',
        help='Name of the csv file to write',
        nargs='?'
    )
    parser_generate_input.add_argument(
        '-c',
        '--composite-only',
        type=bool,
        default=False,
        const=True,
        help='Whether to only add "shapes of shapes" into output header file',
        nargs='?'
    )
    parser_generate_input.set_defaults(func=generate_input)

    # Generate input file command
    parser_validate = subparsers.add_parser('validate',
                                            description='Command for validating a data graph against shapes marked in the csv')
    parser_validate.add_argument(
        '-dg',
        '--data-graph',
        type=str,
        help='RDF data graph to validate',
        required=True
    )
    parser_validate.add_argument(
        '-i',
        '--input-file',
        type=str,
        help='Name of the csv file to read from',
        default='input-file.csv',
        nargs='?'
    )
    parser_validate.set_defaults(func=validate)

    # command with no sub-commands should just print help
    parser.set_defaults(func=lambda _: parser.print_help())

    args = parser.parse_args()
    args.func(args)
