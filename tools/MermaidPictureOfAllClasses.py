"""
Generate the Mermaid graph with all classes dependencies
"""
import os
import sys
import yaml
import glob
import shutil
import subprocess

try:
    from pydantic import BaseModel, ValidationError
    from jinja2 import Template
except ImportError:
    print(
        "Missing required packages. Please install them using your system's package manager or within a virtual environment.")
    print("Example: pip install pydantic jinja2 mkdocs mkdocs-material")
    sys.exit(1)

from typing import Dict, List, Optional, Any

# ==========================================
# PYDANTIC SCHEMA DEFINITIONS
# ==========================================

from schema_classes import OndeClass, OndeModality, OndeField
import re

def get_ref_targets(hdf5_type):
    if not hdf5_type: return []
    return re.findall(r'H5T_STD_REF_OBJ<([^>]+)>', hdf5_type)


def main():
    input_dir = 'class_definitions'

    files = glob.glob(os.path.join(".\..", input_dir, '*.yaml'))
    parsed_classes = {}
    parsed_modalities = {}
    children_map = {}

    print("Parsing and validating YAML files with Pydantic...")
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        try:
            if 'modality' in data:
                validated_data = OndeModality(**data)
                parsed_modalities[validated_data.modality] = validated_data
            else:
                validated_data = OndeClass(**data)
                cls_name = validated_data.onde_class
                parsed_classes[cls_name] = validated_data

                for parent in validated_data.inherits:
                    children_map.setdefault(parent, []).append(cls_name)
        except ValidationError as e:
            print(f"Validation error in {filepath}:\n{e}")
            sys.exit(1)

    # Inject TYPE fields dynamically
    def get_inheritance_chain(c_name, visited=None):
        if visited is None: visited = set()
        if c_name in visited or c_name not in parsed_classes: return [c_name]
        visited.add(c_name)
        chain = []
        parents = parsed_classes[c_name].inherits
        if parents:
            chain.extend(get_inheritance_chain(parents[0], visited))
        chain.append(c_name)
        return chain
    def get_relative_html_link(from_cls, to_cls):
        from_chain = get_inheritance_chain(from_cls) if from_cls else []
        to_chain = get_inheritance_chain(to_cls) if to_cls else []
        ups = "../" * len(from_chain)
        down = "/".join(c.lower() for c in to_chain) + "/index.html" if to_chain else "index.html"
        return ups + down

    for cls_name, cls_obj in parsed_classes.items():
        if cls_name == 'ONDE_ET': continue
        chain = get_inheritance_chain(cls_name)
        allowed_str = '["' + '", "'.join(chain) + '"]'
        dim_str = f'[{len(chain)}]' if len(chain) > 1 else '1'

        type_field = OndeField(
            full_name="ONDE:TYPE",
            required=True,
            storage="attribute",
            hdf5_type="H5T_STRING",
            description="",
            dimensions=dim_str,
            allowed_values=allowed_str
        )
        # Prepend TYPE field
        new_fields = {'TYPE': type_field}
        new_fields.update(cls_obj.fields)
        cls_obj.fields = new_fields

    print("Building relationships and generating Markdown...")
    class_names = list(parsed_classes.keys())
    class_names.sort()

    for cls_name, cls_obj in parsed_classes.items():
        parents = cls_obj.inherits
        children = children_map.get(cls_name, [])

        # Build local mermaid graph
        mermaid_lines = []
        unique_classes = set([cls_name])

        for parent in parents:
            mermaid_lines.append(f"  {parent} <|-- {cls_name}")
            unique_classes.add(parent)

        for child in children:
            mermaid_lines.append(f"  {cls_name} <|-- {child}")
            unique_classes.add(child)

        for fname, field in cls_obj.fields.items():
            refs = get_ref_targets(field.hdf5_type)
            for ref in refs:
                if ref in parsed_classes:
                    mermaid_lines.append(f"  {cls_name} o-- {ref} : {fname}")
                    unique_classes.add(ref)

        # Add outgoing accessories
        for acc in cls_obj.accessories:
            mermaid_lines.append(f"  {cls_name} ..|> {acc} : accessory")
            unique_classes.add(acc)

        # Find incoming references
        for other_name, other_obj in parsed_classes.items():
            if other_name == cls_name: continue
            for fname, field in other_obj.fields.items():
                if cls_name in get_ref_targets(field.hdf5_type):
                    mermaid_lines.append(f"  {other_name} o-- {cls_name} : {fname}")
                    unique_classes.add(other_name)

            # Find incoming accessories
            if cls_name in other_obj.accessories:
                mermaid_lines.append(f"  {other_name} ..|> {cls_name} : accessory")
                unique_classes.add(other_name)

        if not mermaid_lines:
            mermaid_lines.append(f"  {cls_name}")

        for c in unique_classes:
            mermaid_lines.append(f'  click {c} href "{get_relative_html_link(cls_name, c)}"')

        mermaid_lines.append(f'  style {cls_name} stroke:#3f51b5,stroke-width:3px')

        mermaid_graph = "\n".join(mermaid_lines)

    # Copy overview.md to docs/index.md
    # Generate master diagram
    master_lines = []
    unique_classes = set()
    ii=0
    for cls_name, cls_obj in parsed_classes.items():
        print(ii)
        unique_classes.add(cls_name)
        for parent in cls_obj.inherits:
            master_lines.append(f"  {parent} <|-- {cls_name}")
            unique_classes.add(parent)
        for fname, field in cls_obj.fields.items():
            refs = get_ref_targets(field.hdf5_type)
            for ref in refs:
                if ref in parsed_classes:
                    master_lines.append(f"  {cls_name} o-- {ref} : {fname}")
                    unique_classes.add(ref)

    for c in unique_classes:
        master_lines.append(f'  click {c} href "{get_relative_html_link(None, c)}"')

    master_mermaid = "classDiagram\n" + "\n".join(master_lines)
    print(master_mermaid)



if __name__ == '__main__':
    main()
