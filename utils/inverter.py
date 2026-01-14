import re
import csv
from datetime import datetime

def invert_sub_texts(match):
    text = match.group(1)
    sub_texts = [s.strip() for s in text.split(',')]
    if len(sub_texts) > 1:
        return '[' + ', '.join(reversed(sub_texts)) + ']'
    else:
        return match.group(0)

def process_line(line):
    return re.sub(r'\[([^\]]+)\]', invert_sub_texts, line)

def process_csv_file(filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{filename.rsplit('.', 1)[0]}_{timestamp}.csv"

    with open(filename, mode='r', newline='', encoding='utf-8') as input_file, \
         open(output_filename, mode='w', newline='', encoding='utf-8') as output_file:

        csv_reader = csv.reader(input_file, delimiter=';')
        csv_writer = csv.writer(output_file,delimiter=';')

        for row in csv_reader:
            processed_row = [process_line(cell) for cell in row]
            csv_writer.writerow(processed_row)

    return output_filename

# Example usage
input_filename = r"C:\\work\\ONDE-format\\ONDE-format\\ONDE_fields\\ONDE_fields_old.csv"
output_filename = process_csv_file(input_filename)
print(f"The processed file has been saved as: {output_filename}")
