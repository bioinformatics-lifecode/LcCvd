#!/usr/bin/env python3
"""
Genomics WES Data Processing Pipeline
Adds three new columns: Variant Type, Inheritance, Allelic Balance

Usage: python script.py input.tsv output.tsv

Author: Clinical Bioinformatics Pipeline
Version: 2.0
Date: 2025
"""

import sys
import pandas as pd
import re
from typing import Set, List


def parse_inheritance_pattern(inheritance_text: str) -> Set[str]:
    """
    Parse inheritance patterns from Orpha data and return standardized abbreviations.
    
    Args:
        inheritance_text: Raw inheritance text from Orpha column
        
    Returns:
        Set of standardized inheritance abbreviations
    """
    if not inheritance_text or inheritance_text.strip() in ['-', '', 'Unknown']:
        return {'Unknown'}
    
    patterns = set()
    
    # Clean HTML tags and normalize text
    text = re.sub(r'<[^>]*>', ' ', inheritance_text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = text.lower().strip()
    
    # Handle common separators and split into parts
    separators = ['or', 'and', '/', '&']
    parts = [text]
    
    for sep in separators:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts
    
    # Map each part to standard abbreviation
    for part in parts:
        part = part.strip()
        
        if 'autosomal dominant' in part:
            patterns.add('AD')
        elif 'autosomal recessive' in part:
            patterns.add('AR')
        elif 'x-linked dominant' in part:
            patterns.add('XD')
        elif 'x-linked recessive' in part or 'x-linked' in part:
            patterns.add('XR')
        elif 'mitochondrial' in part:
            patterns.add('MT')
        elif 'multigenic' in part or 'multifactorial' in part:
            patterns.add('MF')
        elif 'oligogenic' in part:
            patterns.add('OG')
        elif any(keyword in part for keyword in ['not applicable', 'unknown', '-']):
            patterns.add('Unknown')
    
    return patterns if patterns else {'Unknown'}


def extract_inheritance_from_orpha(orpha_data: str) -> str:
    """
    Extract and parse inheritance patterns from Orpha column with clinical prioritization.
    
    Args:
        orpha_data: Raw Orpha column data
        
    Returns:
        Standardized inheritance pattern string (e.g., 'AD/AR', 'XR')
    """
    if not orpha_data or pd.isna(orpha_data):
        return ''
    
    # Parse conditions with their metadata
    conditions = []
    condition_parts = str(orpha_data).split('~')
    
    for condition in condition_parts:
        fields = condition.split('|')
        if len(fields) >= 4:
            condition_id = fields[0] if fields[0] else ''
            condition_name = fields[1] if len(fields) > 1 else ''
            frequency = fields[2] if len(fields) > 2 else ''
            inheritance = fields[3] if len(fields) > 3 else ''
            
            # Clean HTML tags and normalize spacing
            inheritance = re.sub(r'<[^>]*>', ' ', inheritance)
            inheritance = re.sub(r'&nbsp;', ' ', inheritance)
            inheritance = inheritance.strip()
            
            # Skip conditions with empty, dash, or unknown inheritance
            if inheritance and inheritance not in ['-', '', 'Unknown']:
                patterns = parse_inheritance_pattern(inheritance)
                # Only keep conditions that have valid inheritance patterns (exclude Unknown)
                valid_patterns = {p for p in patterns if p != 'Unknown'}
                if valid_patterns:
                    conditions.append({
                        'id': condition_id,
                        'name': condition_name,
                        'frequency': frequency,
                        'inheritance': inheritance,
                        'patterns': valid_patterns
                    })
    
    if not conditions:
        return ''
    
    # Clinical prioritization scoring
    def priority_score(condition):
        freq = condition['frequency'].lower()
        score = 0
        
        # Frequency-based scoring (higher frequency = more clinically relevant)
        if '1-5 / 10 000' in freq or '1-9 / 10 000' in freq:
            score += 100
        elif '1-9 / 100 000' in freq:
            score += 90
        elif '1-5 / 100 000' in freq:
            score += 80
        elif '1-9 / 1 000 000' in freq:
            score += 70
        elif '<1 / 1 000 000' in freq:
            score += 60
        elif 'unknown' in freq:
            score += 30
        
        # Prefer simpler inheritance patterns
        if len(condition['patterns']) == 1:
            score += 20
        
        # Boost common autosomal patterns
        if 'AR' in condition['patterns'] or 'AD' in condition['patterns']:
            score += 10
            
        return score
    
    # Sort conditions by clinical priority (highest score first)
    conditions.sort(key=priority_score, reverse=True)
    
    # Strategy: Use a more selective approach for combining patterns
    final_patterns = set()
    
    if conditions:
        # Start with the highest priority condition
        top_condition = conditions[0]
        top_score = priority_score(top_condition)
        
        # Add patterns from the top condition
        final_patterns.update(top_condition['patterns'])
        
        # Only add patterns from other conditions if they are very close in score
        # and contribute clinically relevant patterns
        for condition in conditions[1:]:
            current_score = priority_score(condition)
            
            # Only consider conditions with scores within 25 points of the top
            if current_score >= top_score - 25:
                # Add patterns, but apply clinical filtering during addition
                for pattern in condition['patterns']:
                    # Skip X-linked if we already have autosomal patterns
                    if pattern == 'XR' and ('AD' in final_patterns or 'AR' in final_patterns):
                        continue
                    # Skip less common patterns if we already have AD/AR
                    if pattern in ['MF', 'OG', 'MT'] and ('AD' in final_patterns or 'AR' in final_patterns):
                        continue
                    final_patterns.add(pattern)
    
    # Final clinical filtering
    if final_patterns:
        # Rule 1: If we have both autosomal (AD/AR) and X-linked (XR), remove X-linked
        if ('AD' in final_patterns or 'AR' in final_patterns) and 'XR' in final_patterns:
            final_patterns.discard('XR')
        
        # Rule 2: If we have too many patterns, keep only the most standard ones
        if len(final_patterns) > 2:
            # Prioritize AD and AR over other patterns
            standard_patterns = final_patterns.intersection({'AD', 'AR'})
            if standard_patterns:
                final_patterns = standard_patterns
    
    # Return sorted patterns joined with /
    return '/'.join(sorted(final_patterns)) if final_patterns else ''


def determine_variant_type(ref: str, alt: str) -> str:
    """
    Determine variant type based on Ref and Alt columns.
    
    Args:
        ref: Reference allele
        alt: Alternative allele
        
    Returns:
        Variant type string
    """
    if pd.isna(ref) or pd.isna(alt):
        return 'Unknown'
    
    ref, alt = str(ref), str(alt)
    
    # Single nucleotide variant
    if len(ref) == 1 and len(alt) == 1 and ref != '-' and alt != '-':
        return 'SNV'
    
    # Pure insertion (ref is -)
    elif ref == '-' and alt != '-':
        return f'Insertion ({len(alt)})'
    
    # Pure deletion (alt is -)
    elif ref != '-' and alt == '-':
        return f'Deletion ({len(ref)})'
    
    # Complex indel (different lengths)
    elif len(ref) > len(alt):
        deleted_bases = len(ref) - len(alt)
        return f'Deletion ({deleted_bases})'
    
    elif len(alt) > len(ref):
        inserted_bases = len(alt) - len(ref)
        return f'Insertion ({inserted_bases})'
    
    # Same length but different sequences
    else:
        return 'Complex'


def calculate_allelic_balance(gen_ad: str, dp: str) -> str:
    """
    Calculate allelic balance from GEN[0].AD and DP columns.
    
    Args:
        gen_ad: GEN[0].AD column value (format: "ref_count,alt_count")
        dp: DP column value (total depth)
        
    Returns:
        Allelic balance as decimal ratio (format: "0.41")
    """
    if pd.isna(gen_ad) or pd.isna(dp) or not gen_ad or not dp:
        return ''
    
    try:
        # Parse AD field (format: ref_count,alt_count)
        ad_values = str(gen_ad).split(',')
        if len(ad_values) == 2:
            alt_count = int(ad_values[1])
            total_depth = int(dp)
            
            if total_depth > 0:
                ratio = alt_count / total_depth
                return f'{ratio:.2f}'
    except (ValueError, IndexError):
        pass
    
    return ''


def process_genomics_data(input_file: str, output_file: str):
    """
    Process genomics TSV file and add new columns.
    
    Args:
        input_file: Path to input TSV file
        output_file: Path to output TSV file
    """
    try:
        # Read TSV file
        print(f"Reading data from {input_file}...")
        df = pd.read_csv(input_file, sep='\t', dtype=str, low_memory=False)
        
        print(f"Original data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Add new columns
        print("Processing Variant Type...")
        df['Variant Type'] = df.apply(
            lambda row: determine_variant_type(row.get('Ref'), row.get('Alt')), 
            axis=1
        )
        
        print("Processing Inheritance...")
        df['Inheritance'] = df.apply(
            lambda row: extract_inheritance_from_orpha(row.get('Orpha')), 
            axis=1
        )
        
        print("Processing Allelic Balance...")
        df['Allelic Balance'] = df.apply(
            lambda row: calculate_allelic_balance(
                row.get('GEN[0].AD'), 
                row.get('DP')
            ), 
            axis=1
        )
        
        # Display statistics
        print("\n=== PROCESSING RESULTS ===")
        print(f"New columns added: Variant Type, Inheritance, Allelic Balance")
        print(f"Final data shape: {df.shape}")
        
        # Variant type statistics
        print("\n=== VARIANT TYPE DISTRIBUTION ===")
        variant_counts = df['Variant Type'].value_counts()
        for variant, count in variant_counts.items():
            print(f"  {variant}: {count}")
        
        # Inheritance pattern statistics
        print("\n=== INHERITANCE PATTERN DISTRIBUTION ===")
        inheritance_counts = df[df['Inheritance'] != '']['Inheritance'].value_counts()
        for pattern, count in inheritance_counts.head(10).items():
            print(f"  {pattern}: {count}")
        
        # Sample results
        print("\n=== SAMPLE RESULTS (First 5 rows) ===")
        sample_cols = ['Ref.Gene', 'Ref', 'Alt', 'Variant Type', 'Inheritance', 'Allelic Balance']
        available_cols = [col for col in sample_cols if col in df.columns]
        
        for idx, row in df.head(5).iterrows():
            print(f"\nRow {idx + 1}:")
            for col in available_cols:
                print(f"  {col}: {row[col]}")
        
        # Write output file
        print(f"\nWriting results to {output_file}...")
        df.to_csv(output_file, sep='\t', index=False)
        print("Processing completed successfully!")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python script.py input.tsv output.tsv")
        print("\nDescription:")
        print("  Processes genomics WES data and adds three new columns:")
        print("  1. Variant Type: SNV, Insertion (x), Deletion (x), Complex")
        print("  2. Inheritance: AD, AR, XR, XD, MT, MF, OG, Unknown (combinations with /)")
        print("  3. Allelic Balance: alt_count/total_depth as decimal ratio (e.g., 0.41)")
        print("\nFeatures:")
        print("  - Clinical prioritization of inheritance patterns")
        print("  - Frequency-based condition scoring")
        print("  - Professional-grade filtering aligned with clinical tools")
        print("  - Comprehensive variant type classification")
        print("  - Robust error handling and progress reporting")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print("=== Genomics WES Data Processing Pipeline v2.0 ===")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    process_genomics_data(input_file, output_file)


if __name__ == "__main__":
    main()
