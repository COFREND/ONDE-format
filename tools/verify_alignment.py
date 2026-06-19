#!/usr/bin/env python3
import os
import sys
import csv
import re
import glob
import yaml
import subprocess

def normalize_text(text):
    if not text:
        return ""
    # Strip all whitespace and convert to lowercase for robust description comparison
    return re.sub(r'\s+', '', text).lower()

def parse_allowed_values(val_str):
    if not val_str:
        return set()
    cleaned = val_str.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
    parts = []
    for p in cleaned.split('|'):
        for sub_p in p.split(','):
            sub_p = sub_p.strip()
            if sub_p:
                parts.append(sub_p)
    return set(parts)

def parse_type_string(t_str):
    if not t_str:
        return set()
    # Normalize some common typos or variations
    t_str = t_str.replace('HT5_INTEGER', 'H5T_INTEGER')
    parts = []
    for p in t_str.split(' or '):
        for sub_p in p.split('|'):
            sub_p = sub_p.strip()
            if sub_p:
                parts.append(sub_p)
    return set(parts)

def main():
    csv_path = 'build/ONDE_fields_ground_truth.csv'
    schema_dir = 'schema'
    
    if not os.path.exists(csv_path):
        print(f"Error: Ground truth CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
        
    # 1. Parse CSV ground truth
    csv_data = {}
    csv_classes = set()
    
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        # Columns: Class;Name;Comments;M or O;D or A;Class;Dims;Size or content;Min;Max;Accessory Class
        for i, row in enumerate(reader):
            if not row or len(row) < 2:
                continue
            cls_name = row[0].strip()
            if not cls_name:
                cls_name = "ROOT"
            
            field_name = row[1].strip()
            if not field_name:
                continue
                
            csv_classes.add(cls_name)
            
            # Short name is the part after colon
            if ':' in field_name:
                short_name = field_name.split(':', 1)[1].strip()
            else:
                short_name = field_name
                
            csv_data.setdefault(cls_name, {})[short_name] = {
                'line_num': i + 2,
                'full_name': field_name,
                'comments': row[2].strip(),
                'required': row[3].strip(), # 'M' or 'O'
                'storage': row[4].strip(),  # 'A', 'D', 'A or D', etc.
                'type': row[5].strip(),     # e.g. H5T_STRING, H5T_STD_REF_OBJ<ONDE_SETUP>
                'dims': row[6].strip(),     # dimensions
                'allowed': row[7].strip(),  # allowed values
            }

    # 2. Parse YAML files
    yaml_files = glob.glob(os.path.join(schema_dir, '*.yaml'))
    yaml_classes = {}
    
    for y_path in yaml_files:
        with open(y_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except Exception as e:
                print(f"Error parsing YAML file {y_path}: {e}", file=sys.stderr)
                sys.exit(1)
                
            if not data or 'onde_class' not in data:
                continue
            cls_name = data['onde_class']
            yaml_classes[cls_name] = {
                'path': y_path,
                'data': data
            }

    failures = []

    # Check: All classes in CSV have a corresponding YAML file
    for cls in csv_classes:
        if cls not in yaml_classes:
            failures.append(f"Class '{cls}' specified in CSV does not have a corresponding YAML file.")

    # Check: All fields in CSV have corresponding fields in YAML, and compare properties
    for cls_name, csv_fields in csv_data.items():
        if cls_name not in yaml_classes:
            continue
        
        yaml_cls = yaml_classes[cls_name]['data']
        yaml_fields = yaml_cls.get('fields', {})
        
        for short_name, csv_f in csv_fields.items():
            if short_name not in yaml_fields:
                failures.append(f"Class '{cls_name}': Field '{csv_f['full_name']}' (short: '{short_name}') from CSV is missing in YAML.")
                continue
                
            yaml_f = yaml_fields[short_name]
            
            # 1. Compare required
            csv_req = csv_f['required']
            yaml_req = yaml_f.get('required', False)
            expected_req = True if csv_req == 'M' else False
            if yaml_req != expected_req:
                failures.append(f"Class '{cls_name}', Field '{short_name}': required mismatch. CSV has '{csv_req}', YAML has '{yaml_req}' (expected: {expected_req}).")
                
            # 2. Compare storage
            csv_storage = csv_f['storage']
            yaml_storage = yaml_f.get('storage', '')
            # Normalization of storage
            # CSV 'A' -> YAML 'attribute', CSV 'D' -> YAML 'dataset', CSV 'A or D' -> YAML 'A or D'
            # (Wait, let's allow either exact matching or converted matching)
            expected_storage = []
            if csv_storage == 'A':
                expected_storage = ['attribute']
            elif csv_storage == 'D':
                expected_storage = ['dataset']
            elif csv_storage == 'A or D':
                expected_storage = ['A or D']
            elif csv_storage == '':
                expected_storage = ['', None]
            else:
                expected_storage = [csv_storage]
                
            if yaml_storage not in expected_storage:
                failures.append(f"Class '{cls_name}', Field '{short_name}': storage mismatch. CSV has '{csv_storage}', YAML has '{yaml_storage}' (expected: {expected_storage}).")

            # 3. Compare hdf5_type and ref_target
            csv_type_raw = csv_f['type']
            yaml_type_raw = yaml_f.get('hdf5_type', '')
            yaml_ref = yaml_f.get('ref_target', None)
            
            reconstructed_yaml_type = yaml_type_raw
            if yaml_ref:
                reconstructed_yaml_type = f"{yaml_type_raw}<{yaml_ref}>"
                
            csv_type_options = parse_type_string(csv_type_raw)
            yaml_type_options = parse_type_string(reconstructed_yaml_type)
            
            # Check if yaml_type_options is a subset of csv_type_options
            if not yaml_type_options.issubset(csv_type_options):
                failures.append(f"Class '{cls_name}', Field '{short_name}': type mismatch. CSV has '{csv_type_raw}', YAML has '{reconstructed_yaml_type}'.")

            # 4. Compare dimensions
            csv_dims = csv_f['dims'].replace(' ', '')
            yaml_dims = str(yaml_f.get('dimensions', '') or '').replace(' ', '')
            # If both are empty, it's a match
            if csv_dims != yaml_dims:
                failures.append(f"Class '{cls_name}', Field '{short_name}': dimensions mismatch. CSV has '{csv_f['dims']}', YAML has '{yaml_f.get('dimensions')}'.")

            # 5. Compare allowed_values
            csv_allowed = parse_allowed_values(csv_f['allowed'])
            yaml_allowed = parse_allowed_values(yaml_f.get('allowed_values', ''))
            if csv_allowed != yaml_allowed:
                failures.append(f"Class '{cls_name}', Field '{short_name}': allowed_values mismatch. CSV has '{csv_f['allowed']}', YAML has '{yaml_f.get('allowed_values')}'.")

            # 6. Compare description/comments
            csv_comments = csv_f['comments']
            yaml_description = yaml_f.get('description', '')
            if normalize_text(csv_comments) != normalize_text(yaml_description):
                failures.append(f"Class '{cls_name}', Field '{short_name}': description mismatch.\nCSV: {repr(csv_comments)}\nYAML: {repr(yaml_description)}")

    # 3. Verify that there are no broken references of the form `CLASS_NAME:FIELD_NAME` in YAML descriptions
    # Build list of all valid field paths: {class_name}:{field_name}
    valid_paths = set()
    for cls_name, cls_info in yaml_classes.items():
        fields = cls_info['data'].get('fields', {})
        for fname in fields:
            # E.g. ONDE_DATASET:DATA or ONDE:TYPE
            # Wait, let's see what forms references can take.
            # In descriptions, a reference might be ONDE_DATASET:DATA.
            # Also, ONDE:TYPE is valid (as ROOT class fields have ONDE: scoping, or ONDE namespace).
            # Let's add all forms of full_name of the fields to valid_paths.
            full_name = fields[fname].get('full_name', '')
            if full_name:
                valid_paths.add(full_name)
            
            # Also add standard scoping
            valid_paths.add(f"{cls_name}:{fname}")
            if cls_name == "ROOT":
                valid_paths.add(f"ONDE:{fname}")

    # Let's inspect descriptions for potential CLASS_NAME:FIELD_NAME references.
    # Ref pattern: matches uppercase letters with colons starting with ONDE or ROOT, e.g. ONDE_DATASET:DATA or ONDE:TYPE
    ref_pattern = re.compile(r'\b((?:ONDE|ROOT)[A-Z0-9_]*:[A-Z0-9_]+)\b')
    
    # We check description of each class and field in each YAML file
    for cls_name, cls_info in yaml_classes.items():
        cls_data = cls_info['data']
        # Class description
        cls_desc = cls_data.get('description', '')
        for match in ref_pattern.findall(cls_desc):
            if match not in valid_paths:
                failures.append(f"Class '{cls_name}' class description contains broken reference '{match}'.")
                
        # Field descriptions
        fields = cls_data.get('fields', {})
        for fname, f_info in fields.items():
            f_desc = f_info.get('description', '')
            for match in ref_pattern.findall(f_desc):
                if match not in valid_paths:
                    failures.append(f"Class '{cls_name}', Field '{fname}' description contains broken reference '{match}'.")

    # 4. Verify tools/generate_docs.py compiles successfully
    print("Running tools/generate_docs.py verification...")
    try:
        res = subprocess.run([sys.executable, 'tools/generate_docs.py'], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        failures.append(f"tools/generate_docs.py failed with return code {e.returncode}.\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
    except Exception as e:
        failures.append(f"Failed to run tools/generate_docs.py: {e}")

    # Report results
    if failures:
        print(f"\n--- Alignment Verification Failed with {len(failures)} errors ---", file=sys.stderr)
        for fail in failures:
            print(f"FAIL: {fail}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n--- Alignment Verification Passed! ---")
        sys.exit(0)

if __name__ == '__main__':
    main()
