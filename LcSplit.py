#!/usr/bin/env python3
"""
InterVar Column Converter
Splits the 'InterVar: InterVar and Evidence' column into ACMG classification and rules.
Usage: python convert.py input_file output_file
"""

import sys
import pandas as pd
import re
from typing import Tuple, List


def parse_intervar_column(intervar_text: str) -> Tuple[str, str]:
    """
    Parse InterVar column text to extract ACMG classification and active rules.
    
    Args:
        intervar_text (str): Raw InterVar text
        
    Returns:
        Tuple[str, str]: (ACMG classification, comma-separated active rules)
    """
    if pd.isna(intervar_text) or not intervar_text.strip():
        return "", ""
    
    # Clean the text
    text = str(intervar_text).strip()
    
    # Extract ACMG classification
    acmg_classification = ""
    classifications = [
        "Pathogenic", 
        "Likely pathogenic", 
        "Uncertain significance", 
        "Likely benign", 
        "Benign"
    ]
    
    for classification in classifications:
        if classification in text:
            acmg_classification = classification
            break
    
    # Extract active rules
    active_rules = []
    
    # Define rule patterns and their indices
    rule_patterns = {
        'PVS1': r'PVS1=(\d+)',
        'PS1': r'PS=\[(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PS2': r'PS=\[\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+\]',
        'PS3': r'PS=\[\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+\]',
        'PS4': r'PS=\[\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+\]',
        'PS5': r'PS=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\]',
        'PM1': r'PM=\[(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PM2': r'PM=\[\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PM3': r'PM=\[\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PM4': r'PM=\[\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+\]',
        'PM5': r'PM=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+\]',
        'PM6': r'PM=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+\]',
        'PM7': r'PM=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\]',
        'PP1': r'PP=\[(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PP2': r'PP=\[\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'PP3': r'PP=\[\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+\]',
        'PP4': r'PP=\[\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+\]',
        'PP5': r'PP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+\]',
        'PP6': r'PP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\]',
        'BA1': r'BA1=(\d+)',
        'BS1': r'BS=\[(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'BS2': r'BS=\[\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+\]',
        'BS3': r'BS=\[\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+\]',
        'BS4': r'BS=\[\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+\]',
        'BS5': r'BS=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\]',
        'BP1': r'BP=\[(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'BP2': r'BP=\[\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'BP3': r'BP=\[\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'BP4': r'BP=\[\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*\d+\]',
        'BP5': r'BP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+,\s*\d+\]',
        'BP6': r'BP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+,\s*\d+\]',
        'BP7': r'BP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*\d+\]',
        'BP8': r'BP=\[\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*\d+,\s*(\d+)\]'
    }
    
    # Check each rule pattern
    for rule_name, pattern in rule_patterns.items():
        match = re.search(pattern, text)
        if match and int(match.group(1)) > 0:
            active_rules.append(rule_name)
    
    # Join active rules with comma
    acmg_rules = ", ".join(active_rules)
    
    return acmg_classification, acmg_rules


def process_tsv_file(input_file: str, output_file: str) -> None:
    """
    Process the TSV file and split InterVar column.
    
    Args:
        input_file (str): Path to input TSV file
        output_file (str): Path to output TSV file
    """
    try:
        print(f"Reading file: {input_file}")
        
        # Read the TSV file
        df = pd.read_csv(input_file, sep='\t', low_memory=False)
        
        print(f"Original file shape: {df.shape}")
        print(f"Columns found: {list(df.columns)}")
        
        # Find the InterVar column
        intervar_col = None
        for col in df.columns:
            if 'InterVar' in col and 'Evidence' in col:
                intervar_col = col
                break
        
        if intervar_col is None:
            print("ERROR: Could not find 'InterVar: InterVar and Evidence' column!")
            print("Available columns containing 'InterVar':")
            for col in df.columns:
                if 'InterVar' in col:
                    print(f"  - {col}")
            return
        
        print(f"Processing InterVar column: {intervar_col}")
        
        # Process the InterVar column
        acmg_data = []
        acmg_rules_data = []
        
        total_rows = len(df)
        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                print(f"Processing row {idx + 1}/{total_rows}")
            
            intervar_text = row[intervar_col]
            acmg_class, acmg_rules = parse_intervar_column(intervar_text)
            acmg_data.append(acmg_class)
            acmg_rules_data.append(acmg_rules)
        
        # Find the position of Freq_gnomAD_genome_ALL column
        target_col = 'Freq_gnomAD_genome_ALL'
        if target_col not in df.columns:
            print(f"WARNING: '{target_col}' column not found! Available columns:")
            for col in df.columns:
                if 'Freq' in col or 'gnomAD' in col:
                    print(f"  - {col}")
            print("Inserting ACMG columns at the end instead.")
            # Fallback: add at the end
            df['ACMG'] = acmg_data
            df['ACMG_Rules'] = acmg_rules_data
        else:
            # Get the position of the target column
            target_pos = df.columns.get_loc(target_col)
            print(f"Inserting ACMG columns before '{target_col}' at position {target_pos}")
            
            # Create a new column order
            cols = df.columns.tolist()
            
            # Remove the original InterVar column from the list
            if intervar_col in cols:
                cols.remove(intervar_col)
                # Adjust target position if InterVar column was before target
                if df.columns.get_loc(intervar_col) < df.columns.get_loc(target_col):
                    target_pos -= 1
            
            # Insert the new columns at the target position
            cols.insert(target_pos, 'ACMG')
            cols.insert(target_pos + 1, 'ACMG_Rules')
            
            # Create new dataframe with the desired column order
            df_new = df.drop(columns=[intervar_col]).copy()
            df_new['ACMG'] = acmg_data
            df_new['ACMG_Rules'] = acmg_rules_data
            
            # Reorder columns
            df = df_new[cols]
        
        print(f"Writing output file: {output_file}")
        
        # Write the output file
        df.to_csv(output_file, sep='\t', index=False)
        
        print(f"Successfully processed file!")
        print(f"Output file shape: {df.shape}")
        
        # Show some statistics
        acmg_counts = pd.Series(acmg_data).value_counts()
        print("\nACMG Classification Distribution:")
        for classification, count in acmg_counts.items():
            if classification:  # Skip empty strings
                print(f"  {classification}: {count}")
        
        # Show examples
        print("\nFirst 5 examples:")
        for i in range(min(5, len(df))):
            print(f"  ACMG: '{df.iloc[i]['ACMG']}' | Rules: '{df.iloc[i]['ACMG_Rules']}'")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python convert.py input_file output_file")
        print("Example: python convert.py 322870_GATK_merged.tsv output_converted.tsv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print("InterVar Column Converter")
    print("=" * 50)
    
    process_tsv_file(input_file, output_file)


if __name__ == "__main__":
    main()
