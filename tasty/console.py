import argparse
import os
import sys

from tasty.generate_shapes import load_sources, set_version_and_load, generate_shapes_given_source_template, \
    write_to_output
from tasty.generate_input_file import generate_input_file
from tasty.validate import validate_from_csv

current_dir = os.path.dirname(__file__)
source_shapes_dir = os.path.join(current_dir, 'source_shapes')
generated_dir = os.path.join(current_dir, 'generated_shapes')
tasty_root = os.path.join(current_dir, '..')


def generate_shapes(args):
    data = load_sources(args.schema)
    if len(data) == 0:
        print(f"No source shapes found for {args.schema}")
    else:
        for file_path, shape_template in data.items():
            name = os.path.splitext(os.path.basename(file_path))[0]
            print("#" * 20)
            print(f"Shapes from file: {name}")
            g, ontology = set_version_and_load(file_path)
            output_graph = generate_shapes_given_source_template(shape_template, g, ontology, name)
            write_to_output(output_graph, f"{args.schema}_{name}.ttl")


def generate_input(args):
    """
    Generate a CSV input file with shape names as headers.
    Doesn't use the generated shapes files, instead uses the:
        - source_shapes/*.json
    :param args:
    :return:
    """
    load_dir = os.path.join(source_shapes_dir, args.schema)
    potential_shapes = [os.path.join(load_dir, x) for x in os.listdir(load_dir) if x.endswith('.json')]
    input_files = None
    if args.library == 'all':
        input_files = [os.path.basename(shape) for shape in potential_shapes]
        generate_input_file(potential_shapes, args.data_graph, args.output, args.composite_only)
    else:
        for potential in potential_shapes:
            if args.library.lower() == os.path.splitext(os.path.basename(potential))[0]:
                input_files = [potential]
                break
        if input_files:
            generate_input_file(input_files, args.data_graph, args.output, args.composite_only)
        else:
            print(f"No shapes file found to load")
            sys.exit(1)
    print(f"Generated input from {[os.path.basename(f) for f in input_files]}")


def validate(args):
    validate_from_csv(args.data_graph, args.input_file)


def main():
    """Main launch point for the CLI. Mainly points to other functions."""
    # Construct Parsers
    parser = argparse.ArgumentParser(
        description='Tool for generating SHACL files and validating RDF data against SHACL shapes')
    subparsers = parser.add_subparsers()

    # Generate shapes command
    parser_generate_shapes = subparsers.add_parser('generate-shapes',
                                                   description='Command for generating SHACL shape files. Attempt to generate a shapes file for each file in tasty/source_shapes. The resulting shape files are placed in tasty/generated_shapes.')

    parser_generate_shapes.add_argument(
        '-s',
        '--schema',
        type=str,
        choices=['haystack', 'brick'],
        help='Schema that shapes are defined in',
        default='haystack',
        nargs='?'
    )

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
        '-l',
        '--library',
        type=str,
        default='core',
        choices=['core', 'nrel', 'all'],
        help='Name of the library to use for populating shape headers.',
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
