#!/usr/bin/env python3

import sys
import os

def convert_chr_format(input_file, output_file):
    """
    Convert chromosome names from numeric (1,2,3...) to chr format (chr1,chr2,chr3...)
    in InterVar output files.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith('#Chr'):
                # Header line
                outfile.write(line)
                continue
                
            fields = line.split('\t')
            # Check if the chromosome field is numeric and doesn't already have 'chr' prefix
            if fields[0].isdigit() or fields[0] in ['X', 'Y', 'M', 'MT']:
                fields[0] = f"chr{fields[0]}"
            
            # Write the modified line
            outfile.write('\t'.join(fields))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {os.path.basename(sys.argv[0])} input_file output_file")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    convert_chr_format(input_file, output_file)
    print(f"Conversion complete: {input_file} → {output_file}")
