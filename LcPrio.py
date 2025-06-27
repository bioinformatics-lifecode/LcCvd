#!/usr/bin/env python3
"""
Variant Prioritization Script for Germline WES/Panel Analysis
Strict hierarchical prioritization: ACMG -> ClinVar -> CLNSIGCONF -> In Silico
"""

import pandas as pd
import sys
import re
from typing import Dict, Tuple

# ACMG Priority - STRICTLY ORDERED
ACMG_PRIORITY = {
    'Pathogenic': 1,
    'Likely pathogenic': 2,
    'Vus H': 3,
    'VUS H': 3,
    'VUS h': 3,
    'VUS_H': 3,
    'Vus M': 4,
    'VUS M': 4, 
    'VUS m': 4,
    'VUS_M': 4,
    'Vus C': 5,
    'VUS C': 5,
    'VUS c': 5,
    'VUS_C': 5,
    'VUS': 6,
    'Vus': 6,
    'Uncertain significance': 6,
    'Likely benign': 7,
    'Benign': 8,
    'UNK': 9,
    '': 9,
    '.': 9
}

# ClinVar categories for secondary prioritization
CLINVAR_PRIORITY = {
    # Pathogenic variants
    'Pathogenic': 1,
    'Pathogenic/Likely_pathogenic': 1,
    'Pathogenic/Likely_pathogenic/Likely_risk_allele': 1,
    'Pathogenic/Likely_pathogenic/Pathogenic\\x2c_low_penetrance': 1,
    'Pathogenic/Likely_risk_allele': 1,
    'Pathogenic/Pathogenic\\x2c_low_penetrance': 1,
    
    # Likely pathogenic
    'Likely_pathogenic': 2,
    'Likely_pathogenic/Likely_risk_allele': 2,
    'Likely_pathogenic\\x2c_low_penetrance': 2,
    'Likely_risk_allele': 2,
    
    # Conflicting
    'Conflicting_classifications_of_pathogenicity': 3,
    
    # Uncertain
    'Uncertain_significance': 4,
    'Uncertain_significance/Uncertain_risk_allele': 4,
    'Uncertain_risk_allele': 4,
    
    # Functional annotations
    'Affects': 5,
    'association': 5,
    'drug_response': 5,
    'confers_sensitivity': 5,
    'risk_factor': 5,
    'protective': 5,
    
    # Unknown/missing
    'not_provided': 6,
    'no_classification_for_the_single_variant': 6,
    'no_classifications_from_unflagged_records': 6,
    'other': 6,
    'UNK': 6,
    '': 6,
    '.': 6,
    
    # Likely benign
    'Likely_benign': 7,
    'Benign/Likely_benign': 7,
    
    # Benign
    'Benign': 8
}

def get_acmg_priority(acmg_value):
    """Get ACMG priority with case-insensitive matching."""
    if pd.isna(acmg_value):
        return 9
    
    acmg_str = str(acmg_value).strip()
    
    # Direct lookup first
    if acmg_str in ACMG_PRIORITY:
        return ACMG_PRIORITY[acmg_str]
    
    # Case-insensitive lookup
    acmg_lower = acmg_str.lower()
    for key, priority in ACMG_PRIORITY.items():
        if key.lower() == acmg_lower:
            return priority
    
    # Check for VUS with subcategories
    if 'vus' in acmg_lower:
        if 'h' in acmg_lower or 'high' in acmg_lower:
            return 3
        elif 'm' in acmg_lower or 'medium' in acmg_lower:
            return 4
        elif 'c' in acmg_lower or 'cold' in acmg_lower:
            return 5
        else:
            return 6
    
    return 9  # Unknown

def get_clinvar_priority(clinvar_value):
    """Parse ClinVar value and return priority."""
    if pd.isna(clinvar_value):
        return 6
    
    # Clean the value
    clinvar_str = str(clinvar_value).replace('clinvar: ', '').strip()
    
    # Handle pipe-separated values
    if '|' in clinvar_str:
        parts = clinvar_str.split('|')
        priorities = []
        for part in parts:
            part = part.strip()
            if part in CLINVAR_PRIORITY:
                priorities.append(CLINVAR_PRIORITY[part])
        return min(priorities) if priorities else 6
    
    # Direct lookup
    return CLINVAR_PRIORITY.get(clinvar_str, 6)

def parse_clnsigconf(clnsigconf_str):
    """Parse CLNSIGCONF and return a priority score."""
    if pd.isna(clnsigconf_str) or clnsigconf_str == '':
        return 0
    
    # Parse format: "Pathogenic(1)|Benign(10)|Likely_benign(2)"
    pattern = r'([^(]+)\((\d+)\)'
    matches = re.findall(pattern, str(clnsigconf_str))
    
    if not matches:
        return 0
    
    counts = {}
    for classification, count in matches:
        counts[classification] = int(count)
    
    total = sum(counts.values())
    if total == 0:
        return 0
    
    # Calculate weighted score
    weights = {
        'Pathogenic': -10,
        'Likely_pathogenic': -8,
        'Pathogenic\\x2c_low_penetrance': -7,
        'Likely_risk_allele': -6,
        'Uncertain_significance': 0,
        'Uncertain_risk_allele': 0,
        'Likely_benign': 5,
        'Benign': 8
    }
    
    score = 0
    for classification, count in counts.items():
        weight = weights.get(classification, 0)
        score += weight * count
    
    return score / total

def calculate_in_silico_score(row):
    """Calculate in silico score based on predictions."""
    score = 0
    count = 0
    
    # CADD phred
    try:
        cadd = float(row.get('CADD_phred', '.'))
        if cadd >= 25:
            score -= 2
        elif cadd >= 20:
            score -= 1
        count += 1
    except:
        pass
    
    # SIFT
    try:
        sift = float(row.get('SIFT_score', '.'))
        if sift < 0.05:
            score -= 1
        count += 1
    except:
        pass
    
    # GERP++
    try:
        gerp = float(row.get('GERP++_RS', '.'))
        if gerp > 4.4:
            score -= 1
        count += 1
    except:
        pass
    
    # phyloP
    try:
        phylop = float(row.get('phyloP46way_placental', '.'))
        if phylop > 2.0:
            score -= 1
        count += 1
    except:
        pass
    
    # MetaSVM
    metasvm = str(row.get('MetaSVM_score', '')).strip()
    if metasvm and metasvm not in ['.', '']:
        if 'D' in metasvm:
            score -= 1
        elif 'T' in metasvm:
            score += 1
        count += 1
    
    return score / count if count > 0 else 0

def prioritize_variants(input_file, output_file):
    """Main prioritization function."""
    
    print(f"Reading variants from {input_file}...")
    df = pd.read_csv(input_file, sep='\t', low_memory=False)
    original_columns = df.columns.tolist()
    
    print(f"Loaded {len(df)} variants")
    
    # Calculate priorities
    df['_acmg_priority'] = df['ACMG'].apply(get_acmg_priority)
    df['_clinvar_priority'] = df['clinvar: Clinvar '].apply(get_clinvar_priority)
    df['_clnsigconf_score'] = df['CLNSIGCONF'].apply(parse_clnsigconf)
    df['_in_silico_score'] = df.apply(calculate_in_silico_score, axis=1)
    
    # For Pathogenic/Likely pathogenic ACMG, ignore ClinVar
    is_pathogenic = df['_acmg_priority'] <= 2
    df.loc[is_pathogenic, '_clinvar_priority'] = 0
    
    # Calculate final priority
    df['_final_priority'] = (
        df['_acmg_priority'] * 1000000 +  # ACMG dominates
        df['_clinvar_priority'] * 10000 +  # ClinVar secondary
        df['_clnsigconf_score'] * 100 +    # CLNSIGCONF tertiary
        df['_in_silico_score']             # In silico fine-tuning
    )
    
    # Sort by priority (lower = higher priority)
    df_sorted = df.sort_values('_final_priority')
    
    # Keep only original columns
    df_sorted = df_sorted[original_columns]
    
    # Save results
    print(f"Saving prioritized variants to {output_file}...")
    df_sorted.to_csv(output_file, sep='\t', index=False)
    
    # Print summary
    print("\nPrioritization Summary:")
    print("-" * 50)
    print("ACMG Classification Distribution:")
    print(df_sorted['ACMG'].value_counts())
    
    print("\nTop 10 prioritized variants:")
    top10 = df_sorted.head(10)
    display_cols = ['#Chr', 'Start', 'Ref', 'Alt', 'Ref.Gene', 'ACMG', 'clinvar: Clinvar ']
    available_cols = [col for col in display_cols if col in top10.columns]
    print(top10[available_cols].to_string())

def main():
    if len(sys.argv) != 3:
        print("Usage: python prioritize_variants.py <input.tsv> <output.tsv>")
        sys.exit(1)
    
    try:
        prioritize_variants(sys.argv[1], sys.argv[2])
        print("\nSuccessfully prioritized variants")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
