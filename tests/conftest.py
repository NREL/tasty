import os

import tasty.templates as tt


def populate_pgt_from_file(file_path):
    # -- Setup
    templates = tt.load_template_file(file_path)
    assert len(templates) == 1

    template_data = templates[0]
    pgt = tt.PointGroupTemplate(template_data)
    pgt.populate_template_basics()
    pgt.resolve_telemetry_point_types()

    return template_data, pgt


def prep_for_write(output_dir, file, write_type, ext):
    file_name = os.path.splitext(os.path.basename(file))[0]
    out_file = os.path.join(output_dir, f"{write_type}-{file_name}.{ext}")
    if os.path.isfile(out_file):
        os.remove(out_file)
    return out_file


def reset_pgt_all_templates_to_empty_set():
    tt.PointGroupTemplate.all_templates = set()
    assert len(tt.PointGroupTemplate.all_templates) == 0
