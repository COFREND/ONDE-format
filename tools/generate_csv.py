import os
import sys
import yaml
import glob
import csv


def parse_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_csv():
    input_dir = 'class_definitions'
    output_csv = 'build/ONDE_fields.csv'
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    files = glob.glob(os.path.join(input_dir, '*.yaml'))
    
    classes_data = []
    modalities_data = []
    
    for f in files:
        data = parse_yaml(f)
            
        if data is not None:
            if 'modality' in data:
                modalities_data.append(data)
            else:
                classes_data.append(data)
            
    # Inject TYPE fields dynamically based on inheritance for classes
    def get_inheritance_chain_dict(c_name, visited=None):
        if visited is None: visited = set()
        if c_name in visited or not c_name: return []
        visited.add(c_name)
        
        c_data = next((c for c in classes_data if c.get('onde_class') == c_name), None)
        if not c_data: return [c_name]
        
        inherits = c_data.get('inherits', [])
        chain = [c_name]
        for parent in inherits:
            chain.extend(get_inheritance_chain_dict(parent, visited))
        
        return chain

    for c_data in classes_data:
        cls_name = c_data.get('onde_class', '')
        
        chain = get_inheritance_chain_dict(cls_name)
        allowed_str = '["' + '", "'.join(chain) + '"]'
        dim_str = f'[{len(chain)}]' if len(chain) > 1 else '1'
        
        type_field = {
            'full_name': 'ONDE:TYPE',
            'required': True,
            'storage': 'attribute',
            'hdf5_type': 'H5T_STRING',
            'description': '',
            'dimensions': dim_str,
            'allowed_values': allowed_str
        }
        
        fields = c_data.get('fields', {})
        new_fields = {'TYPE': type_field}
        new_fields.update(fields)
        c_data['fields'] = new_fields
            
    # Sort to ensure consistent output based on modality allowed_classes
    ordered_classes = modalities_data[0].get('allowed_classes', []) if modalities_data else []
    
    def get_sort_key(x):
        c_name = x.get('onde_class', '')
        try:
            return ordered_classes.index(c_name)
        except ValueError:
            return 9999
            
    classes_data.sort(key=get_sort_key)
    
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        header = ['Class', 'Name', 'Comments', 'M or O', 'D or A', 'Class', 'Dims', 'Size or content', 'Min', 'Max', 'Accessory Class']
        f.write(';'.join(header) + '\n')
        
        # Write modalities first
        for mod_data in modalities_data:
            mod_name = mod_data.get('modality', '')
            fields = mod_data.get('fields', {})
            for fname, field in fields.items():
                row = [
                    mod_name,
                    field.get('full_name', ''),
                    field.get('description', ''),
                    'M' if field.get('required') else 'O',
                    'D' if field.get('storage') == 'dataset' else 'A',
                    field.get('hdf5_type', ''),
                    field.get('dimensions', ''),
                    field.get('allowed_values', ''),
                    field.get('min_value', ''),
                    field.get('max_value', ''),
                    ''
                ]
                row_str = ';'.join(str(x).replace('\n', ' ').replace(';', ',') for x in row) + '\n'
                f.write(row_str)
                
        # Write classes
        for cls_data in classes_data:
            cls_name = cls_data.get('onde_class', '')
                
            fields = cls_data.get('fields', [])
            
            # YAML format stores fields as a dict, Markdown as a list
            if isinstance(fields, dict):
                fields_list = []
                for k, v in fields.items():
                    v['short_name'] = k
                    fields_list.append(v)
                fields = fields_list
                
            for field in fields:
                m_o = 'M' if field.get('required') else 'O'
                
                storage = field.get('storage', '')
                d_a = 'D' if storage == 'dataset' else 'A'
                if not storage:
                    d_a = ''
                # Retain original "A or D" value if specified exactly like that
                if storage == 'A or D':
                    d_a = 'A or D'
                    
                hdf5_type = field.get('hdf5_type', '')
                ref_target = field.get('ref_target', '')
                if ref_target:
                    hdf5_type = f"{hdf5_type}<{ref_target}>"
                    
                row = [
                    cls_name,
                    field.get('full_name', ''),
                    field.get('description', ''),
                    m_o,
                    d_a,
                    hdf5_type,
                    field.get('dimensions', ''),
                    field.get('allowed_values', ''),
                    field.get('min_value', ''),
                    field.get('max_value', ''),
                    ''
                ]
                
                # Format without strict CSV quoting to preserve intended json-like arrays and pipe-separations
                row_str = ';'.join(str(x).replace('\n', ' ').replace(';', ',') for x in row) + '\n'
                f.write(row_str)

    print(f"Generated {output_csv} successfully from {len(classes_data)} classes.")

if __name__ == '__main__':
    generate_csv()
