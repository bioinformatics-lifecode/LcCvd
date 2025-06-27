import sys

def merge_files(intervar_file, snpsift_file, output_matched_file, output_unmatched_file):
    # Read SnpSift file and create a lookup table
    snpsift_variants = {}
    snpsift_cols = ['ANN[0].GENE', 'ANN[0].FEATUREID', 'ANN[0].HGVS_P', 'ANN[0].HGVS_C',
                    'ANN[0].EFFECT', 'ANN[0].IMPACT', 'ANN[0].RANK', 'DP', 'AF',
                    'GEN[0].AD', 'CLNHGVS', 'CLNSIGCONF', 'ALLELEID', 'FILTER', 'RS']
    
    with open(snpsift_file, 'r') as snpsift:
        # Read header
        header = snpsift.readline().strip().split('\t')
        
        # Find indices for key columns and columns to extract
        try:
            chr_idx = header.index('CHROM')
            start_idx = header.index('AVINPUTSTART')
            end_idx = header.index('AVINPUTEND')
            ref_idx = header.index('AVINPUTREF')
            alt_idx = header.index('AVINPUTALT')
            
            extract_indices = []
            for col in snpsift_cols:
                try:
                    extract_indices.append(header.index(col))
                except ValueError:
                    extract_indices.append(-1)  # Column not found
        except ValueError as e:
            print(f"Error: Could not find required column in SnpSift file: {e}")
            sys.exit(1)
        
        # Process variants
        for line in snpsift:
            fields = line.strip().split('\t')
            if len(fields) <= max(chr_idx, start_idx, end_idx, ref_idx, alt_idx):
                continue  # Skip lines that don't have enough fields
            
            # Create key
            key = (fields[chr_idx], fields[start_idx], fields[end_idx], fields[ref_idx], fields[alt_idx])
            
            # Extract values
            values = []
            for idx in extract_indices:
                if idx >= 0 and idx < len(fields):
                    values.append(fields[idx])
                else:
                    values.append('')
            
            snpsift_variants[key] = values
    
    # Process InterVar file and create merged output
    matched_count = 0
    unmatched_count = 0
    
    with open(intervar_file, 'r') as intervar, \
         open(output_matched_file, 'w') as matched_out, \
         open(output_unmatched_file, 'w') as unmatched_out:
        
        # Read header line
        intervar_header = intervar.readline().strip()
        
        # Write headers to both output files
        matched_out.write(intervar_header + '\t' + '\t'.join(snpsift_cols) + '\n')
        unmatched_out.write(intervar_header + '\n')
        
        # Process variants
        for line in intervar:
            fields = line.strip().split('\t')
            if len(fields) < 5:
                # Not enough fields, consider as unmatched
                unmatched_out.write(line.strip() + '\n')
                unmatched_count += 1
                continue
            
            # Create key
            key = (fields[0], fields[1], fields[2], fields[3], fields[4])
            
            # Look up in SnpSift data
            if key in snpsift_variants:
                matched_out.write(line.strip() + '\t' + '\t'.join(snpsift_variants[key]) + '\n')
                matched_count += 1
            else:
                unmatched_out.write(line.strip() + '\n')
                unmatched_count += 1
    
    # Print statistics
    print(f"Total variants processed: {matched_count + unmatched_count}")
    print(f"Matched variants: {matched_count} ({matched_count/(matched_count + unmatched_count)*100:.2f}%)")
    print(f"Unmatched variants: {unmatched_count} ({unmatched_count/(matched_count + unmatched_count)*100:.2f}%)")
    print(f"Matched variants written to: {output_matched_file}")
    print(f"Unmatched variants written to: {output_unmatched_file}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py intervar_file snpsift_file output_matched_file output_unmatched_file")
        sys.exit(1)
    
    intervar_file = sys.argv[1]
    snpsift_file = sys.argv[2]
    output_matched_file = sys.argv[3]
    output_unmatched_file = sys.argv[4]
    
    merge_files(intervar_file, snpsift_file, output_matched_file, output_unmatched_file)
