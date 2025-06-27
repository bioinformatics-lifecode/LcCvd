#!/usr/bin/env python3
"""
MAGI-ACMG VUS Subclassification Implementation
Based on the paper: "We have developed MAGI-ACMG, a classification algorithm..."

This script implements the VUS subclassification system (Hot/Middle/Cold)
based on ACMG criteria combinations from Table 1 of the paper.

IMPORTANT: This script ONLY modifies variants with ACMG = "Uncertain significance"
All other data remains completely unchanged.
"""

import pandas as pd
import re
from collections import Counter
import sys

def parse_acmg_criteria(acmg_rules_str):
    """
    Parse ACMG criteria from the ACMG_Rules column
    Returns a Counter object with counts of each criterion type
    """
    if pd.isna(acmg_rules_str) or acmg_rules_str == '' or str(acmg_rules_str) == 'nan':
        return Counter()
    
    # Split by comma and strip whitespace
    criteria = [c.strip() for c in str(acmg_rules_str).split(',')]
    
    # Count different types of criteria
    counts = Counter()
    
    for criterion in criteria:
        if criterion.startswith('PVS'):
            counts['PVS'] += 1
        elif criterion.startswith('PS'):
            counts['PS'] += 1
        elif criterion.startswith('PM'):
            counts['PM'] += 1
        elif criterion.startswith('PP'):
            counts['PP'] += 1
        elif criterion.startswith('BS'):
            counts['BS'] += 1
        elif criterion.startswith('BP'):
            counts['BP'] += 1
    
    return counts

def classify_vus(criteria_counts):
    """
    Classify VUS based on ACMG criteria combinations
    Implementation of Table 1 from MAGI-ACMG paper
    
    Args:
        criteria_counts: Counter object with counts of each criterion type
        
    Returns:
        str: 'Vus H', 'Vus M', or 'Vus C'
    """
    pvs = criteria_counts.get('PVS', 0)
    ps = criteria_counts.get('PS', 0)
    pm = criteria_counts.get('PM', 0)
    pp = criteria_counts.get('PP', 0)
    bs = criteria_counts.get('BS', 0)
    bp = criteria_counts.get('BP', 0)
    
    # HOT VUS Classification Rules (from Table 1)
    # These are the exact combinations from the paper's Table 1
    
    # PVS combinations
    if pvs >= 1:
        # PVS alone OR PVS + BP OR PVS + PP
        if (bp == 0 and pp == 0) or (bp >= 1) or (pp >= 1):
            return 'Vus H'
    
    # PS combinations  
    if ps >= 1:
        # PS alone OR PS + PP OR PS + BP + PP OR PS + BS + PP OR PS + BP
        if (bp == 0 and pp == 0 and bs == 0) or \
           (pp >= 1) or \
           (bp >= 1 and pp >= 1) or \
           (bs >= 1 and pp >= 1) or \
           (bp >= 1 and pp == 0):
            return 'Vus H'
    
    # PM combinations for HOT
    if pm >= 2:
        # PM + PM + PP OR PM + PM + PP + BP OR PM + PM + PP + BS
        if pp >= 1:
            return 'Vus H'
    
    # PP combinations for HOT
    if pp >= 4:
        # PP + PP + PP + PP (without stronger evidence)
        if pm == 0 and ps == 0 and pvs == 0 and bp == 0:
            return 'Vus H'
        # PP + PP + PP + PP + BP
        elif pm == 0 and ps == 0 and pvs == 0 and bp >= 1:
            return 'Vus H'
    
    if pp >= 3 and pm >= 1:
        # PP + PP + PP + PM
        if ps == 0 and pvs == 0:
            if bp == 0 or bs == 0:
                return 'Vus H'
    
    # MIDDLE VUS Classification Rules (from Table 1)
    
    # BS + PVS OR BS + PS
    if bs >= 1 and (pvs >= 1 or ps >= 1):
        return 'Vus M'
    
    # PM + PM (without PP)
    if pm >= 2 and pp == 0:
        if bp <= 1:  # PM + PM OR BP + PM + PM
            return 'Vus M'
    
    # PM + PP combinations
    if pm >= 1 and pp >= 1:
        # PP + PM OR BP + PP + PM  
        if pm == 1 and pp == 1:
            return 'Vus M'
        # PP + PP + PM OR BP + PP + PP + PM
        elif pm == 1 and pp == 2:
            return 'Vus M'
    
    # PP + PP + PP (without stronger evidence)
    if pp >= 3 and pm == 0 and ps == 0 and pvs == 0:
        # PP + PP + PP OR BP + PP + PP + PP
        if bp <= 1:
            return 'Vus M'
    
    # COLD VUS Classification Rules (everything else from Table 1)
    
    # Single PM
    if pm == 1 and pp == 0 and ps == 0 and pvs == 0:
        # PM alone OR BP + PM  
        return 'Vus C'
    
    # PP combinations for COLD
    if pp == 2 and pm == 0 and ps == 0 and pvs == 0:
        # PP + PP OR BP + PP + PP OR BS + PP + PP
        return 'Vus C'
    
    # Single PP
    if pp == 1 and pm == 0 and ps == 0 and pvs == 0:
        # PP alone OR BP + PP OR BS + PP
        return 'Vus C'
    
    # Single benign evidence
    if bp >= 1 or bs >= 1:
        if pm == 0 and pp == 0 and ps == 0 and pvs == 0:
            # BP alone OR BS alone
            return 'Vus C'
    
    # Default to COLD for any remaining combinations
    return 'Vus C'

def process_vus_classification(input_file, output_file=None):
    """
    Process the prioritized TSV file and add VUS subclassification
    
    IMPORTANT: Only modifies variants with ACMG = "Uncertain significance"
    All other data remains completely unchanged.
    
    Args:
        input_file: Path to input TSV file
        output_file: Path to output TSV file (optional)
    """
    print(f"Reading file: {input_file}")
    
    # Read the TSV file - preserve all original data
    try:
        df = pd.read_csv(input_file, sep='\t', low_memory=False)
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    print(f"Total variants: {len(df)}")
    
    # Filter for VUS variants ONLY
    # Only these will be modified - everything else stays exactly the same
    vus_mask = df['ACMG'].str.contains('Uncertain significance', na=False, case=False)
    vus_indices = df[vus_mask].index
    
    print(f"VUS variants found: {len(vus_indices)}")
    
    if len(vus_indices) == 0:
        print("No VUS variants found. Check the ACMG column values.")
        print("Available ACMG values:", df['ACMG'].value_counts())
        return
    
    # Add new column for criteria parsing (optional - for analysis)
    df['ACMG_Criteria_Parsed'] = ''
    
    # Process ONLY the VUS variants - leave everything else untouched
    classifications = {'Vus H': 0, 'Vus M': 0, 'Vus C': 0}
    
    for idx in vus_indices:
        # Parse ACMG criteria for this VUS variant
        criteria_counts = parse_acmg_criteria(df.at[idx, 'ACMG_Rules'])
        
        # Classify the VUS according to MAGI-ACMG rules
        vus_class = classify_vus(criteria_counts)
        
        # Update ONLY the ACMG column for this VUS variant
        # Replace "Uncertain significance" with specific classification
        df.at[idx, 'ACMG'] = vus_class
        
        # Optional: Add criteria parsing for analysis
        if len(criteria_counts) > 0:
            df.at[idx, 'ACMG_Criteria_Parsed'] = ', '.join([f"{k}:{v}" for k, v in criteria_counts.items()])
        
        classifications[vus_class] += 1
    
    # Print classification summary
    print("\nVUS Classification Summary:")
    print(f"Vus H (should be reported): {classifications['Vus H']}")
    print(f"Vus M (consider for reporting): {classifications['Vus M']}")
    print(f"Vus C (not reported): {classifications['Vus C']}")
    
    # Show some examples
    print("\nExamples of each classification:")
    for vus_type in ['Vus H', 'Vus M', 'Vus C']:
        examples = df[df['ACMG'] == vus_type].head(3)
        if len(examples) > 0:
            print(f"\n{vus_type} examples:")
            for _, example in examples.iterrows():
                print(f"  Gene: {example['Ref.Gene']}, "
                      f"ACMG_Rules: {example['ACMG_Rules']}, "
                      f"Variant: {example.get('ANN[0].HGVS_C', 'N/A')}")
    
    # Save the results - all original data preserved, only VUS classifications changed
    if output_file is None:
        output_file = input_file.replace('.tsv', '_with_VUS_classification.tsv')
    
    print(f"\nSaving results to: {output_file}")
    df.to_csv(output_file, sep='\t', index=False)
    
    # Create a summary report of just the VUS variants
    vus_summary_file = output_file.replace('.tsv', '_VUS_summary.tsv')
    
    # Handle column name variations for clinvar
    clinvar_col = None
    for col in df.columns:
        if 'clinvar' in col.lower():
            clinvar_col = col
            break
    
    # Select columns for summary
    summary_cols = ['Ref.Gene', 'ANN[0].HGVS_C', 'ANN[0].HGVS_P', 
                    'ACMG', 'ACMG_Rules', 'ACMG_Criteria_Parsed']
    if clinvar_col:
        summary_cols.append(clinvar_col)
    
    # Filter for existing columns only
    available_cols = [col for col in summary_cols if col in df.columns]
    
    # Get all VUS variants (now classified as Vus H/M/C)
    vus_results = df[df['ACMG'].isin(['Vus H', 'Vus M', 'Vus C'])][available_cols].copy()
    vus_results.to_csv(vus_summary_file, sep='\t', index=False)
    print(f"VUS summary saved to: {vus_summary_file}")
    
    return df

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python vus_classifier.py <input_file.tsv> [output_file.tsv]")
        print("Example: python vus_classifier.py prioritized.tsv")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Process the file
    result_df = process_vus_classification(input_file, output_file)
    
    if result_df is not None:
        print("\nVUS classification completed successfully!")
        print("\nIMPORTANT: Only variants with 'Uncertain significance' were modified.")
        print("All other data remains exactly as in the original file.")
        print("\nRecommendations based on MAGI-ACMG paper:")
        print("- Vus H: Should be reported in diagnostic setting")
        print("- Vus M: Consider for reporting based on clinical context")
        print("- Vus C: Generally not reported")

if __name__ == "__main__":
    main()
