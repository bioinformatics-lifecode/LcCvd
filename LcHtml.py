#!/usr/bin/env python3
import sys
import os
import json
import csv
from datetime import datetime

def read_tsv_file(file_path):
    """Read TSV file and return headers and data rows"""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        headers = next(reader)  # Get the first row as headers
        rows = []
        for i, row in enumerate(reader):
            if row and len(row) >= len(headers):  # Skip empty or invalid rows
                # Create a dictionary for each row
                variant = {headers[j]: row[j] if j < len(row) else '' for j in range(len(headers))}
                # Add rank based on position
                variant['rank'] = i + 1
                rows.append(variant)
    return headers, rows

def read_coverage_metrics(file_path):
    """Read coverage metrics file and extract key values"""
    metrics = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract sample ID from the first line
            first_line = content.split('\n')[0]
            sample_id = first_line.split(':')[-1].strip() if ':' in first_line else "Unknown"
            metrics['sample_id'] = sample_id
            
            # Extract metrics using simple parsing
            raw_reads = extract_metric(content, 'Raw reads: ')
            trimmed_reads = extract_metric(content, 'Trimmed reads: ')
            
            # Remove "(total from R1 and R2)" from raw and trimmed reads
            metrics['raw_reads'] = raw_reads.replace("(total from R1 and R2)", "").strip()
            metrics['trimmed_reads'] = trimmed_reads.replace("(total from R1 and R2)", "").strip()
            
            metrics['mean_read_length'] = extract_metric(content, 'Mean read length: ')
            metrics['uniquely_mapped_reads'] = extract_metric(content, 'Uniquely mapped reads: ').split(' ')[0]
            metrics['duplicate_reads'] = extract_metric(content, 'Duplicate reads: ').split(' ')[0]
            metrics['average_coverage'] = extract_metric(content, 'Average coverage: ')
            metrics['bases_10x'] = extract_metric(content, 'Percentage of bases with ≥10X coverage: ')
            metrics['bases_30x'] = extract_metric(content, 'Percentage of bases with ≥30X coverage: ')
            metrics['bases_50x'] = extract_metric(content, 'Percentage of bases with ≥50X coverage: ')
            metrics['bases_100x'] = extract_metric(content, 'Percentage of bases with ≥100X coverage: ')
            metrics['bases_200x'] = extract_metric(content, 'Percentage of bases with ≥200X coverage: ')
            metrics['bases_300x'] = extract_metric(content, 'Percentage of bases with ≥300X coverage: ')
    except Exception as e:
        print(f"Warning: Could not read coverage metrics file: {e}")
        # Set default values
        metrics = {
            'sample_id': "Unknown",
            'raw_reads': "N/A",
            'trimmed_reads': "N/A",
            'mean_read_length': "N/A",
            'uniquely_mapped_reads': "N/A",
            'duplicate_reads': "N/A",
            'average_coverage': "N/A",
            'bases_10x': "N/A",
            'bases_30x': "N/A",
            'bases_50x': "N/A",
            'bases_100x': "N/A",
            'bases_200x': "N/A",
            'bases_300x': "N/A"
        }
    return metrics

def extract_metric(content, prefix):
    """Helper function to extract a metric value from the content"""
    try:
        for line in content.split('\n'):
            if prefix in line:
                return line.split(prefix)[1].strip()
    except:
        pass
    return "N/A"

def generate_html(file_path, output_path=None, coverage_metrics_path=None):
    """Generate HTML report from TSV file"""
    # Determine output filename if not specified
    if not output_path:
        output_path = os.path.splitext(file_path)[0] + "_report.html"
    
    # Get the sample name from the file path
    full_filename = os.path.basename(os.path.splitext(file_path)[0])
    # Remove _GATK_prehtml suffix if present
    if full_filename.endswith('_GATK_prehtml'):
        sample_name = full_filename.replace('_GATK_prehtml', '')
    else:
        sample_name = full_filename.split('_variants')[0]
    
    # Read the TSV file
    try:
        headers, variants = read_tsv_file(file_path)
    except Exception as e:
        print(f"Error reading TSV file: {e}")
        return False
    
    # Read coverage metrics if available
    coverage_metrics = {}
    if coverage_metrics_path and os.path.exists(coverage_metrics_path):
        coverage_metrics = read_coverage_metrics(coverage_metrics_path)
    else:
        # Try to find a coverage metrics file with standard naming
        potential_metrics_file = f"{sample_name}_coverage_metrics.txt"
        if os.path.exists(potential_metrics_file):
            coverage_metrics = read_coverage_metrics(potential_metrics_file)
        else:
            print(f"Warning: Coverage metrics file not found. Using default values.")
            coverage_metrics = {
                'sample_id': sample_name,
                'raw_reads': "N/A",
                'trimmed_reads': "N/A",
                'mean_read_length': "N/A",
                'uniquely_mapped_reads': "N/A",
                'duplicate_reads': "N/A",
                'average_coverage': "N/A",
                'bases_10x': "N/A",
                'bases_30x': "N/A",
                'bases_50x': "N/A",
                'bases_100x': "N/A",
                'bases_200x': "N/A",
                'bases_300x': "N/A"
            }
    
    # Convert data to JSON for embedding in HTML
    variants_json = json.dumps(variants)
    
    # Current date for the report
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Generate HTML content with embedded data
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genetic Variant Analysis Report</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <style>
        /* Color Palette */
        :root {{
            /* Primary Colors */
            --deep-blue: #06274b;
            --teal: #2CA6A4;
            --soft-gray: #F4F4F4;
            
            /* Accent Colors */
            --orange: #F39237;
            --green: #4CAF50;
            --red: #E74C3C;
            --purple: #9C27B0;
            --lime: #a6ce4d;
            
            /* Typography & Background */
            --dark-text: #212121;
            --white-bg: #FFFFFF;
            
            /* Additional UI Colors */
            --light-border: #E0E0E0;
            --medium-gray: #757575;
            --light-teal: rgba(44, 166, 164, 0.1);
            
            /* ACMG colors including enhanced VUS variants */
            --pathogenic-red: #E74C3C;
            --likely-pathogenic-red: #F07470;
            --likely-pathogenic-end: #C53030; /* Rich darker red for gradient */
            --vus-orange: #FF8C00; /* Dark orange for VUS H, M, C */
            --vus-m-end: #5F9EA0; /* Ice blue end for VUS M (similar to old VUS C) */
            --vus-h-end: #D2691E; /* Orange-red end for VUS H */
            --vus-c-end: #87CEEB; /* Light sky blue end for VUS C (more distinguishable) */
            --benign-color: #4CAF50;
            
            /* ClinVar colors - similar to ACMG but distinguishable */
            --clinvar-pathogenic: #DC2626;
            --clinvar-likely-pathogenic: #EF4444;
            --clinvar-benign: #059669;
            --clinvar-likely-benign: #10B981;
            --clinvar-uncertain: #F59E0B;
            --clinvar-conflicting: #c4b030; /* Changed to yellow */
            --clinvar-risk-factor: #EC4899;
            --clinvar-drug-response: #06B6D4;
            --clinvar-other: #6B7280;
            --clinvar-not-available: #9CA3AF;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        body {{
            background-color: var(--soft-gray);
            color: var(--dark-text);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header Styles - REDUCED BY 15% */
        .report-header {{
            background-color: var(--deep-blue);
            color: var(--white-bg);
            padding: 8.5px 12px;
            border-radius: 10px 10px 0 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: center;
            align-items: center;
            width: 23%;
            max-width: 231px;
            margin-left: 0;
            margin-right: auto;
            height: 45px;
        }}
        
        .logo img {{
            height: 29px;
            width: auto;
        }}
        
        /* Info Card */
        .info-card {{
            background-color: var(--light-teal);
            border-left: 4px solid var(--teal);
            padding: 10px 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        
        .info-card h3 {{
            color: var(--deep-blue);
            margin-bottom: 8px;
            font-size: 16px;
        }}
        
        .info-details {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .info-item {{
            display: flex;
            align-items: flex-start;
            gap: 6px;
        }}
        
        .info-icon {{
            color: var(--teal);
            width: 16px;
            text-align: center;
            font-size: 12px;
            margin-top: 3px;
        }}
        
        .info-text {{
            font-size: 13px;
            color: var(--dark-text);
            line-height: 1.4;
        }}
        
        /* Coverage Metrics Section - REDUCED BY 50% */
        .coverage-section {{
            background-color: var(--white-bg);
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }}
        
        .coverage-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            border-bottom: 1px solid var(--light-border);
            padding-bottom: 5px;
        }}
        
        .coverage-header h3 {{
            color: var(--deep-blue);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .coverage-metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 8px;
        }}
        
        .metrics-card {{
            background-color: var(--soft-gray);
            border-radius: 8px;
            padding: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
            height: 55px;
        }}
        
        .metrics-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        }}
        
        .metrics-title {{
            font-size: 11px;
            color: var(--medium-gray);
            margin-bottom: 3px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .metrics-title i {{
            color: var(--lime);
        }}
        
        .metrics-value {{
            font-size: 15px;
            font-weight: 600;
            color: var(--deep-blue);
        }}
        
        .coverage-distribution {{
            margin-top: 10px;
        }}
        
        .coverage-distribution h4 {{
            color: var(--deep-blue);
            font-size: 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .coverage-bars {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 8px;
        }}
        
        .coverage-item {{
            margin-bottom: 3px;
        }}
        
        .coverage-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 2px;
            font-size: 11px;
        }}
        
        .coverage-label-text {{
            color: var(--deep-blue);
            font-weight: 500;
        }}
        
        .coverage-percent {{
            color: var(--lime);
            font-weight: 700;
        }}
        
        .coverage-bar-bg {{
            width: 100%;
            height: 5px;
            background-color: var(--soft-gray);
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .coverage-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--lime) 0%, #8bc34a 100%);
            border-radius: 3px;
        }}
        
        /* Controls */
        .controls {{
            background-color: var(--white-bg);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }}
        
        .search-controls {{
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .search-box {{
            flex-grow: 1;
            padding: 10px 15px;
            border: 1px solid var(--light-border);
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .refresh-button {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background-color: var(--teal);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
            white-space: nowrap;
        }}
        
        .refresh-button:hover {{
            background-color: #249391;
        }}
        
        /* VarSome-style pagination controls */
        .pagination-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: var(--white-bg);
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .results-per-page {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .results-per-page label {{
            font-size: 14px;
            color: var(--dark-text);
            font-weight: 500;
        }}
        
        .results-per-page select {{
            padding: 8px 12px;
            border: 1px solid var(--light-border);
            border-radius: 4px;
            font-size: 14px;
            background-color: var(--white-bg);
            cursor: pointer;
        }}
        
        .page-info {{
            font-size: 14px;
            color: var(--medium-gray);
        }}
        
        .page-navigation {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .page-nav-btn {{
            background-color: var(--white-bg);
            border: 1px solid var(--light-border);
            color: var(--deep-blue);
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.2s;
            font-size: 14px;
        }}
        
        .page-nav-btn:hover:not(:disabled) {{
            background-color: var(--light-teal);
        }}
        
        .page-nav-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .page-nav-btn.active {{
            background-color: var(--teal);
            color: var(--white-bg);
            border-color: var(--teal);
        }}

        /* Enhanced Filters Section */
        .filters-button {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: var(--deep-blue);
            color: var(--white-bg);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            margin-left: 15px;
        }}
        
        .filters-button:hover {{
            background-color: #1a365d;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .filters-button.active {{
            background-color: var(--orange);
        }}

        /* IGV Button Styles */
        .igv-button {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: var(--lime);
            color: var(--white-bg);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            margin-left: 10px;
            text-decoration: none;
        }}
        
        .igv-button:hover {{
            background-color: #8bc34a;
            color: var(--white-bg);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .igv-button:focus {{
            outline: none;
            box-shadow: 0 0 0 2px rgba(166, 206, 77, 0.3);
        }}
        
        .filters-panel {{
            position: absolute;
            top: 100%;
            right: 0;
            background-color: var(--white-bg);
            border: 1px solid var(--light-border);
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            padding: 20px;
            width: 320px;
            z-index: 1000;
            display: none;
            margin-top: 5px;
        }}
        
        .filters-panel.active {{
            display: block;
        }}
        
        .filters-panel h4 {{
            color: var(--deep-blue);
            margin-bottom: 15px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .filter-group {{
            margin-bottom: 20px;
        }}
        
        .filter-label {{
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: var(--dark-text);
            margin-bottom: 8px;
        }}
        
        .filter-input-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-range {{
            flex: 1;
            -webkit-appearance: none;
            appearance: none;
            height: 6px;
            background: var(--soft-gray);
            border-radius: 3px;
            outline: none;
        }}
        
        .filter-range::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            background: var(--teal);
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .filter-range::-webkit-slider-thumb:hover {{
            transform: scale(1.1);
            background: #249391;
        }}
        
        .filter-range::-moz-range-thumb {{
            width: 18px;
            height: 18px;
            background: var(--teal);
            border-radius: 50%;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
        }}
        
        .filter-value {{
            min-width: 60px;
            padding: 6px 10px;
            border: 1px solid var(--light-border);
            border-radius: 4px;
            font-size: 13px;
            text-align: center;
            background-color: var(--soft-gray);
            font-weight: 600;
            color: var(--deep-blue);
        }}
        
        .filter-actions {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid var(--light-border);
        }}
        
        .filter-btn {{
            flex: 1;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .filter-apply {{
            background-color: var(--teal);
            color: var(--white-bg);
        }}
        
        .filter-apply:hover {{
            background-color: #249391;
        }}
        
        .filter-reset {{
            background-color: var(--medium-gray);
            color: var(--white-bg);
        }}
        
        .filter-reset:hover {{
            background-color: #616161;
        }}
        
        .filters-container {{
            position: relative;
        }}
        
        /* Enhanced Variants Table Container */
        .variants-container {{
            background-color: var(--white-bg);
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            position: relative;
            overflow-x: auto;
            overflow-y: visible;
        }}
        
        /* Enhanced Table Layout for Excel-like Column Resizing */
        .variants-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            table-layout: fixed;
            min-width: 100%;
        }}
        
        .variants-table th,
        .variants-table td {{
            padding: 12px 8px;
            text-align: left;
            position: relative;
            border-right: 1px solid var(--light-border);
            border-bottom: 1px solid var(--light-border);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            box-sizing: border-box;
        }}
        
        .variants-table th:last-child,
        .variants-table td:last-child {{
            border-right: none;
        }}
        
        .variants-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Enhanced Table Headers */
        .variants-table th {{
            background: linear-gradient(180deg, var(--deep-blue) 0%, #2C5282 100%);
            color: var(--white-bg);
            font-weight: 600;
            cursor: pointer;
            position: sticky;
            top: 0;
            z-index: 10;
            transition: background 0.2s ease;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            user-select: none;
            border-bottom: 2px solid var(--deep-blue);
        }}
        
        .variants-table th:hover {{
            background: linear-gradient(180deg, #2C5282 0%, #1A365D 100%);
        }}

        .variants-table th.sortable {{
            cursor: pointer;
        }}

        .variants-table th.sorted-asc::after {{
            content: " ▲";
            color: var(--lime);
        }}

        .variants-table th.sorted-desc::after {{
            content: " ▼";
            color: var(--lime);
        }}
        
        /* Enhanced Column Resizer */
        .column-resizer {{
            position: absolute;
            top: 0;
            right: -3px;
            width: 6px;
            height: 100%;
            cursor: col-resize;
            z-index: 30;
            background: transparent;
            border-radius: 3px;
            transition: background-color 0.2s ease;
        }}
        
        .column-resizer:hover {{
            background: rgba(44, 166, 164, 0.3);
        }}
        
        .column-resizer:active {{
            background: rgba(44, 166, 164, 0.6);
        }}
        
        /* Enhanced Resizing States */
        .resizing {{
            cursor: col-resize !important;
            user-select: none !important;
        }}
        
        .resizing * {{
            cursor: col-resize !important;
            user-select: none !important;
        }}
        
        /* Enhanced Resize Line */
        .resize-line {{
            position: fixed;
            width: 2px;
            background: var(--teal);
            z-index: 1000;
            pointer-events: none;
            display: none;
            box-shadow: 0 0 4px rgba(44, 166, 164, 0.5);
        }}
        
        .resize-line.active {{
            background: #FF6B35;
            box-shadow: 0 0 6px rgba(255, 107, 53, 0.6);
        }}
        
        /* Enhanced Table Body Styling */
        .variants-table tbody tr:nth-child(even) {{
            background-color: var(--soft-gray);
        }}
        
        .variants-table tbody tr:hover {{
            background-color: rgba(44, 166, 164, 0.05);
            transition: background-color 0.15s ease;
        }}
        
        /* Default Column Widths */
        .col-rank {{ width: 60px; min-width: 50px; max-width: 100px; }}
        .col-variant {{ width: 140px; min-width: 100px; max-width: 300px; }}
        .col-variant-type {{ width: 120px; min-width: 80px; max-width: 200px; }}
        .col-gene {{ width: 80px; min-width: 60px; max-width: 150px; }}
        .col-rs {{ width: 100px; min-width: 80px; max-width: 200px; }}
        .col-clinvar {{ width: 150px; min-width: 100px; max-width: 200px; }}
        .col-acmg {{ width: 120px; min-width: 100px; max-width: 200px; }}
        .col-acmg-rules {{ width: 160px; min-width: 120px; max-width: 300px; }}
        .col-hgvs {{ width: 200px; min-width: 150px; max-width: 400px; }}
        .col-hgvs-protein {{ width: 150px; min-width: 120px; max-width: 300px; }}
        .col-hgvs-coding {{ width: 150px; min-width: 120px; max-width: 300px; }}
        .col-inheritance {{ width: 100px; min-width: 80px; max-width: 150px; }}
        .col-effect {{ width: 140px; min-width: 100px; max-width: 250px; }}
        .col-exon {{ width: 60px; min-width: 60px; max-width: 120px; }}
        .col-zygosity {{ width: 100px; min-width: 80px; max-width: 150px; }}
        .col-gnomad {{ width: 100px; min-width: 80px; max-width: 150px; }}
        .col-allelic-balance {{ width: 120px; min-width: 100px; max-width: 180px; }}
        .col-depth {{ width: 80px; min-width: 60px; max-width: 120px; }}
        .col-filter {{ width: 80px; min-width: 60px; max-width: 120px; }}
        
        /* Rank Styling */
        .rank-bubble {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background-color: var(--deep-blue);
            color: var(--white-bg);
            border-radius: 50%;
            font-weight: bold;
            font-size: 12px;
        }}
        
        /* Variant code styling */
        .variant-code {{
            font-family: 'Courier New', monospace;
            background-color: rgba(30, 58, 95, 0.1);
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 12px;
        }}
        
        /* Gene Styling */
        .gene-link {{
            color: var(--teal);
            text-decoration: none;
            font-weight: 600;
        }}
        
        .gene-link:hover {{
            text-decoration: underline;
        }}
        
        /* Badge Styling for ACMG */
        .badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 11px;
            font-weight: 600;
            color: var(--white-bg);
            text-align: center;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            white-space: nowrap;
        }}
        
        .badge:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .badge-pathogenic {{
            background: linear-gradient(90deg, var(--pathogenic-red) 0%, #8b2635 100%);
        }}
        
        .badge-likely-pathogenic {{
            background: linear-gradient(90deg, var(--likely-pathogenic-red) 0%, var(--likely-pathogenic-end) 100%);
        }}
        
        .badge-vus {{
            background: linear-gradient(90deg, var(--vus-orange) 0%, var(--vus-m-end) 100%);
        }}
        
        .badge-vus-h {{
            background: linear-gradient(90deg, var(--vus-orange) 0%, var(--vus-h-end) 100%);
        }}
        
        .badge-vus-c {{
            background: linear-gradient(90deg, var(--vus-orange) 0%, var(--vus-c-end) 100%);
        }}
        
        .badge-benign, .badge-likely-benign {{
            background: linear-gradient(90deg, var(--benign-color) 0%, #059669 100%);
        }}
        
        .badge-other {{
            background: linear-gradient(90deg, var(--purple) 0%, #7C3AED 100%);
        }}
        
        /* ClinVar Badge Styling */
        .badge-clinvar-pathogenic {{
            background: linear-gradient(90deg, var(--clinvar-pathogenic) 0%, #991B1B 100%);
        }}
        
        .badge-clinvar-likely-pathogenic {{
            background: linear-gradient(90deg, var(--clinvar-likely-pathogenic) 0%, #DC2626 100%);
        }}
        
        .badge-clinvar-benign {{
            background: linear-gradient(90deg, var(--clinvar-benign) 0%, #047857 100%);
        }}
        
        .badge-clinvar-likely-benign {{
            background: linear-gradient(90deg, var(--clinvar-likely-benign) 0%, #059669 100%);
        }}
        
        .badge-clinvar-uncertain {{
            background: linear-gradient(90deg, var(--clinvar-uncertain) 0%, #D97706 100%);
        }}
        
        .badge-clinvar-conflicting {{
            background: linear-gradient(90deg, var(--clinvar-conflicting) 0%, #b08c39 100%);
            color: var(--white-bg); /* Changed to dark text for better readability on yellow */
        }}
        
        .badge-clinvar-risk-factor {{
            background: linear-gradient(90deg, var(--clinvar-risk-factor) 0%, #BE185D 100%);
        }}
        
        .badge-clinvar-drug-response {{
            background: linear-gradient(90deg, var(--clinvar-drug-response) 0%, #0891B2 100%);
        }}
        
        .badge-clinvar-other {{
            background: linear-gradient(90deg, var(--clinvar-other) 0%, #4B5563 100%);
        }}
        
        .badge-clinvar-not-available {{
            background: linear-gradient(90deg, var(--clinvar-not-available) 0%, #6B7280 100%);
        }}
        
        /* Professional ACMG Rules Styling */
        .acmg-rules {{
            font-family: 'Courier New', monospace;
            background-color: rgba(44, 166, 164, 0.08);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            color: var(--deep-blue);
            letter-spacing: 0.5px;
            border: 1px solid rgba(44, 166, 164, 0.2);
        }}
        
        /* Professional Effect Styling */
        .effect-text {{
            font-weight: 500;
            color: var(--dark-text);
            background-color: rgba(76, 175, 80, 0.08);
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 13px;
            border: 1px solid rgba(76, 175, 80, 0.2);
        }}
        
        /* Not available text */
        .not-available {{
            color: var(--medium-gray);
            font-style: italic;
        }}
        
        /* Filter icons */
        .filter-pass {{
            color: var(--green);
            font-size: 16px;
        }}
        
        .filter-fail {{
            color: var(--red);
            font-size: 16px;
        }}
        
        /* Footer */
        .footer {{
            background-color: var(--white-bg);
            padding: 20px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
            text-align: center;
            color: var(--medium-gray);
            font-size: 0.9rem;
        }}
        
        /* Responsive Design */
        @media (max-width: 1200px) {{
            .container {{
                padding: 10px;
            }}
            
            .coverage-metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .coverage-bars {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 768px) {{
            .report-header {{
                width: 41%;
                max-width: none;
            }}
            
            .coverage-metrics-grid {{
                grid-template-columns: 1fr;
            }}
            
            .coverage-bars {{
                grid-template-columns: 1fr;
            }}
            
            .pagination-controls {{
                flex-direction: column;
                gap: 15px;
            }}

            .filters-panel {{
                width: 280px;
                right: -20px;
            }}

            .igv-button {{
                margin-left: 5px;
                padding: 6px 12px;
                font-size: 13px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Enhanced resize line for column resizing -->
        <div class="resize-line" id="resizeLine"></div>
        
        <!-- Report Header -->
        <div class="report-header">
            <div class="logo">
                <img src="logo.png" alt="Company Logo" style="height: 29px; width: auto;">
            </div>
        </div>
        
        <!-- Info Card -->
        <div class="info-card">
            <h3>Sample Information</h3>
            <div class="info-details">
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-dna"></i></div>
                    <div class="info-text"><strong>CVD Results</strong> • Sample ID: {sample_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-calendar-alt"></i></div>
                    <div class="info-text"><strong>Analysis Date:</strong> {current_date}</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-clipboard-list"></i></div>
                    <div class="info-text">This report contains prioritized genetic variants classified according to ACMG guidelines.</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-sort-amount-down"></i></div>
                    <div class="info-text">Variants are sorted by clinical significance, with potentially pathogenic variants appearing first.</div>
                </div>
            </div>
        </div>
        
        <!-- Coverage Metrics Section -->
        <div class="coverage-section">
            <div class="coverage-header">
                <h3><i class="fas fa-chart-line"></i> Sequencing Quality Metrics</h3>
            </div>
            
            <div class="coverage-metrics-grid">
                <!-- Read Statistics -->
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-file-alt"></i> Raw Reads</div>
                    <div class="metrics-value">{coverage_metrics.get('raw_reads', 'N/A')}</div>
                </div>
                
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-cut"></i> Trimmed Reads</div>
                    <div class="metrics-value">{coverage_metrics.get('trimmed_reads', 'N/A')}</div>
                </div>
                
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-ruler"></i> Mean Read Length</div>
                    <div class="metrics-value">{coverage_metrics.get('mean_read_length', 'N/A')}</div>
                </div>
                
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-map-marker-alt"></i> Uniquely Mapped Reads</div>
                    <div class="metrics-value">{coverage_metrics.get('uniquely_mapped_reads', 'N/A')}</div>
                </div>
                
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-copy"></i> Duplicate Reads</div>
                    <div class="metrics-value">{coverage_metrics.get('duplicate_reads', 'N/A')}</div>
                </div>
                
                <div class="metrics-card">
                    <div class="metrics-title"><i class="fas fa-layer-group"></i> Average Coverage</div>
                    <div class="metrics-value">{coverage_metrics.get('average_coverage', 'N/A')}</div>
                </div>
            </div>
            
            <!-- Coverage Distribution Section -->
            <div class="coverage-distribution">
                <h4><i class="fas fa-chart-bar"></i> Coverage Distribution</h4>
                
                <div class="coverage-bars">
                    <!-- 10X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥10X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_10x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_10x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                    
                    <!-- 30X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥30X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_30x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_30x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                    
                    <!-- 50X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥50X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_50x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_50x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                    
                    <!-- 100X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥100X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_100x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_100x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                    
                    <!-- 200X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥200X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_200x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_200x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                    
                    <!-- 300X Coverage -->
                    <div class="coverage-item">
                        <div class="coverage-label">
                            <span class="coverage-label-text">≥300X Coverage</span>
                            <span class="coverage-percent">{coverage_metrics.get('bases_300x', 'N/A')}</span>
                        </div>
                        <div class="coverage-bar-bg">
                            <div class="coverage-bar-fill" style="width: {coverage_metrics.get('bases_300x', '0%').replace('%', '')}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Search and Reset View Button -->
        <div class="controls">
            <div class="search-controls">
                <button id="refreshButton" class="refresh-button"><i class="fas fa-sync-alt"></i> Reset View</button>
                <input type="text" id="searchInput" class="search-box" placeholder="Search for genes, variants, or phenotypes...">
            </div>
        </div>
        
        <!-- VarSome-style Pagination Controls with Filters and IGV -->
        <div class="pagination-controls">
            <div class="results-per-page">
                <label for="rowsPerPage">Show:</label>
                <select id="rowsPerPage">
                    <option value="10" selected>10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
                <span>variants per page</span>
            </div>
            
            <div class="page-info" id="pageInfo">
                Showing 1-10 of 0 variants
            </div>
            
            <div class="page-navigation" id="pageNavigation">
                <!-- Enhanced Filters Container -->
                <div class="filters-container">
                    <button id="filtersButton" class="filters-button">
                        <i class="fas fa-filter"></i>
                        Filters
                    </button>
                    
                    <!-- IGV Button -->
                    <a href="{sample_name}.IGV.html" target="_blank" class="igv-button" title="Open IGV Viewer">
                        <i class="fas fa-chart-area"></i>
                        IGV
                    </a>
                    
                    <div id="filtersPanel" class="filters-panel">
                        <h4><i class="fas fa-sliders-h"></i> Filter Variants</h4>
                        
                        <div class="filter-group">
                            <label class="filter-label">Minimum Depth (DP)</label>
                            <div class="filter-input-group">
                                <input type="range" id="depthRange" class="filter-range" min="0" max="1000" value="0" step="1">
                                <input type="number" id="depthValue" class="filter-value" min="0" max="1000" value="0">
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">Minimum Allelic Balance</label>
                            <div class="filter-input-group">
                                <input type="range" id="allelicRange" class="filter-range" min="0" max="1" value="0" step="0.01">
                                <input type="number" id="allelicValue" class="filter-value" min="0" max="1" value="0" step="0.01">
                            </div>
                        </div>
                        
                        <div class="filter-actions">
                            <button id="applyFilters" class="filter-btn filter-apply">Apply Filters</button>
                            <button id="resetFilters" class="filter-btn filter-reset">Reset</button>
                        </div>
                    </div>
                </div>
                <!-- Page navigation will be generated dynamically -->
            </div>
        </div>
        
        <!-- Enhanced Variants Table -->
        <div class="variants-container">
            <table class="variants-table" id="variantsTable">
                <thead>
                    <tr>
                        <th class="col-rank" data-sort="rank">RANK<div class="column-resizer"></div></th>
                        <th class="col-variant" data-sort="variant">VARIANT<div class="column-resizer"></div></th>
                        <th class="col-variant-type" data-sort="variantType">VARIANT TYPE<div class="column-resizer"></div></th>
                        <th class="col-gene" data-sort="gene">GENE<div class="column-resizer"></div></th>
                        <th class="col-rs" data-sort="rs">RS<div class="column-resizer"></div></th>
                        <th class="col-clinvar sortable" data-sort="clinvar">CLINVAR<div class="column-resizer"></div></th>
                        <th class="col-acmg sortable" data-sort="acmg">ACMG<div class="column-resizer"></div></th>
                        <th class="col-acmg-rules" data-sort="acmgRules">ACMG RULES<div class="column-resizer"></div></th>
                        <th class="col-hgvs" data-sort="hgvs">HGVS<div class="column-resizer"></div></th>
                        <th class="col-hgvs-protein" data-sort="hgvsProtein">HGVS PROTEIN<div class="column-resizer"></div></th>
                        <th class="col-hgvs-coding" data-sort="hgvsCoding">HGVS CODING<div class="column-resizer"></div></th>
                        <th class="col-inheritance" data-sort="inheritance">INHERITANCE<div class="column-resizer"></div></th>
                        <th class="col-effect" data-sort="effect">EFFECT<div class="column-resizer"></div></th>
                        <th class="col-exon" data-sort="exon">EXON<div class="column-resizer"></div></th>
                        <th class="col-zygosity" data-sort="zygosity">ZYGOSITY<div class="column-resizer"></div></th>
                        <th class="col-gnomad" data-sort="gnomad">GNOMAD<div class="column-resizer"></div></th>
                        <th class="col-allelic-balance sortable" data-sort="allelicBalance">ALLELIC BALANCE<div class="column-resizer"></div></th>
                        <th class="col-depth sortable" data-sort="depth">DEPTH<div class="column-resizer"></div></th>
                        <th class="col-filter" data-sort="filter">FILTER</th>
                    </tr>
                </thead>
                <tbody id="variantsTableBody">
                    <!-- Variants will be added here dynamically -->
                </tbody>
            </table>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated with Lc Analysis Pipeline</p>
            <p><small>For research and clinical use. Sort columns by clicking headers. Use horizontal scroll to view all columns.</small></p>
        </div>
    </div>

    <script>
        // Store the sample name
        const sampleName = "{sample_name}";
        
        // Embedded variant data from TSV file
        const allVariants = {variants_json};
        
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize variables
            let filteredVariants = [...allVariants];
            let currentPage = 1;
            let rowsPerPage = 10; // Default to 10 as per VarSome style
            let originalVariants = [...allVariants];
            
            // Sorting state
            let currentSortColumn = null;
            let currentSortDirection = 'asc';
            
            // Filter state
            let minDepth = 0;
            let minAllelicBalance = 0;
            
            // Priority mappings for sorting
            const acmgPriority = {{
                'Pathogenic': 1,
                'Likely pathogenic': 2,
                'VUS H': 3,
                'VUS M': 4,
                'VUS C': 5,
                'Uncertain significance': 6,
                'Likely benign': 7,
                'Benign': 8
            }};
            
            const clinvarPriority = {{
                'Pathogenic': 1,
                'Likely pathogenic': 2,
                'Uncertain significance': 3,
                'Conflicting': 4,
                'Risk factor': 5,
                'Drug response': 6,
                'Other': 7,
                'Likely benign': 8,
                'Benign': 9,
                'Not available': 10
            }};
            
            // UPDATED ClinVar classification function - with UNK and not_provided handling
            function classifyClinVar(clinvarValue) {{
                if (!clinvarValue || clinvarValue === '.' || clinvarValue === '' || clinvarValue === 'N/A') {{
                    return 'Not available';
                }}
                
                const value = clinvarValue.toLowerCase();
                
                // CHECK FOR UNK AND NOT_PROVIDED FIRST - new additions
                if (value.includes('unk') || value.includes('not_provided')) {{
                    return 'Not available';
                }}
                
                // CHECK CONFLICTING FIRST (before any pathogenic/benign matching)
                if (value.includes('conflicting_classifications') || value.includes('conflicting classifications')) {{
                    return 'Conflicting';
                }}
                
                // Pathogenic variants (now safe from conflicting matches)
                else if (value.includes('pathogenic/likely_pathogenic') || value.includes('pathogenic/likely pathogenic')) {{
                    return 'Pathogenic';
                }} else if (value.includes('likely_pathogenic') || value.includes('likely pathogenic')) {{
                    return 'Likely pathogenic';
                }} else if (value.includes('pathogenic') && !value.includes('likely')) {{
                    return 'Pathogenic';
                }}
                
                // Benign variants
                else if (value.includes('benign/likely_benign') || value.includes('benign/likely benign')) {{
                    return 'Benign';
                }} else if (value.includes('likely_benign') || value.includes('likely benign')) {{
                    return 'Likely benign';
                }} else if (value.includes('benign') && !value.includes('likely')) {{
                    return 'Benign';
                }}
                
                // Uncertain significance
                else if (value.includes('uncertain_significance') || value.includes('uncertain significance') || value.includes('uncertain_risk_allele')) {{
                    return 'Uncertain significance';
                }}
                
                // Risk factor
                else if (value.includes('risk_factor') || value.includes('risk factor') || value.includes('likely_risk_allele')) {{
                    return 'Risk factor';
                }}
                
                // Drug response
                else if (value.includes('drug_response') || value.includes('drug response')) {{
                    return 'Drug response';
                }}
                
                // Other categories
                else {{
                    return 'Other';
                }}
            }}
            
            // ClinVar badge class function
            function getClinVarBadgeClass(classification) {{
                switch(classification) {{
                    case 'Pathogenic':
                        return 'badge-clinvar-pathogenic';
                    case 'Likely pathogenic':
                        return 'badge-clinvar-likely-pathogenic';
                    case 'Benign':
                        return 'badge-clinvar-benign';
                    case 'Likely benign':
                        return 'badge-clinvar-likely-benign';
                    case 'Uncertain significance':
                        return 'badge-clinvar-uncertain';
                    case 'Conflicting':
                        return 'badge-clinvar-conflicting';
                    case 'Risk factor':
                        return 'badge-clinvar-risk-factor';
                    case 'Drug response':
                        return 'badge-clinvar-drug-response';
                    case 'Other':
                        return 'badge-clinvar-other';
                    case 'Not available':
                    default:
                        return 'badge-clinvar-not-available';
                }}
            }}
            
            // Enhanced Filters System
            class FilterSystem {{
                constructor() {{
                    this.filtersButton = document.getElementById('filtersButton');
                    this.filtersPanel = document.getElementById('filtersPanel');
                    this.depthRange = document.getElementById('depthRange');
                    this.depthValue = document.getElementById('depthValue');
                    this.allelicRange = document.getElementById('allelicRange');
                    this.allelicValue = document.getElementById('allelicValue');
                    this.applyButton = document.getElementById('applyFilters');
                    this.resetButton = document.getElementById('resetFilters');
                    
                    this.initializeFilters();
                    this.setupEventListeners();
                }}
                
                initializeFilters() {{
                    // Set up range limits based on data
                    const depths = allVariants.map(v => parseFloat(getVariantValue(v, 'DP', '0'))).filter(d => !isNaN(d));
                    const allelicBalances = allVariants.map(v => parseFloat(getVariantValue(v, 'Allelic Balance', '0'))).filter(ab => !isNaN(ab));
                    
                    const maxDepth = Math.max(...depths, 1000);
                    const maxAllelic = Math.max(...allelicBalances, 1);
                    
                    this.depthRange.max = maxDepth;
                    this.depthValue.max = maxDepth;
                    this.allelicRange.max = maxAllelic;
                    this.allelicValue.max = maxAllelic;
                }}
                
                setupEventListeners() {{
                    // Toggle filters panel
                    this.filtersButton.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        this.toggleFiltersPanel();
                    }});
                    
                    // Close panel when clicking outside
                    document.addEventListener('click', (e) => {{
                        if (!this.filtersPanel.contains(e.target) && !this.filtersButton.contains(e.target)) {{
                            this.closeFiltersPanel();
                        }}
                    }});
                    
                    // Sync range and number inputs
                    this.depthRange.addEventListener('input', () => {{
                        this.depthValue.value = this.depthRange.value;
                    }});
                    
                    this.depthValue.addEventListener('input', () => {{
                        this.depthRange.value = this.depthValue.value;
                    }});
                    
                    this.allelicRange.addEventListener('input', () => {{
                        this.allelicValue.value = parseFloat(this.allelicRange.value).toFixed(2);
                    }});
                    
                    this.allelicValue.addEventListener('input', () => {{
                        this.allelicRange.value = this.allelicValue.value;
                    }});
                    
                    // Apply and reset buttons
                    this.applyButton.addEventListener('click', () => {{
                        this.applyFilters();
                    }});
                    
                    this.resetButton.addEventListener('click', () => {{
                        this.resetFilters();
                    }});
                }}
                
                toggleFiltersPanel() {{
                    const isActive = this.filtersPanel.classList.contains('active');
                    if (isActive) {{
                        this.closeFiltersPanel();
                    }} else {{
                        this.openFiltersPanel();
                    }}
                }}
                
                openFiltersPanel() {{
                    this.filtersPanel.classList.add('active');
                    this.filtersButton.classList.add('active');
                }}
                
                closeFiltersPanel() {{
                    this.filtersPanel.classList.remove('active');
                    this.filtersButton.classList.remove('active');
                }}
                
                applyFilters() {{
                    minDepth = parseFloat(this.depthValue.value) || 0;
                    minAllelicBalance = parseFloat(this.allelicValue.value) || 0;
                    
                    applyFiltersAndSearch();
                    this.closeFiltersPanel();
                }}
                
                resetFilters() {{
                    this.depthRange.value = 0;
                    this.depthValue.value = 0;
                    this.allelicRange.value = 0;
                    this.allelicValue.value = 0;
                    
                    minDepth = 0;
                    minAllelicBalance = 0;
                    
                    applyFiltersAndSearch();
                    this.closeFiltersPanel();
                }}
            }}
            
            // Excel-like Column Resizing System
            class ExcelColumnResizer {{
                constructor() {{
                    this.isResizing = false;
                    this.currentColumn = null;
                    this.currentColumnIndex = -1;
                    this.startX = 0;
                    this.startWidth = 0;
                    this.minWidth = 50;
                    this.maxWidth = 500;
                    this.resizeLine = document.getElementById('resizeLine');
                    this.table = document.querySelector('.variants-table');
                    this.columnWidths = new Map();
                    
                    this.initializeResizing();
                    this.setInitialColumnWidths();
                }}
                
                initializeResizing() {{
                    // Add event listeners to all column resizers
                    const resizers = document.querySelectorAll('.column-resizer');
                    resizers.forEach((resizer, index) => {{
                        resizer.addEventListener('mousedown', (e) => this.startResize(e, resizer));
                    }});
                    
                    // Global mouse event listeners
                    document.addEventListener('mousemove', (e) => this.onMouseMove(e));
                    document.addEventListener('mouseup', (e) => this.endResize(e));
                    
                    // Prevent text selection during resize
                    document.addEventListener('selectstart', (e) => {{
                        if (this.isResizing) e.preventDefault();
                    }});
                }}
                
                startResize(event, resizer) {{
                    event.preventDefault();
                    event.stopPropagation();
                    
                    this.isResizing = true;
                    this.currentColumn = resizer.parentElement;
                    this.currentColumnIndex = Array.from(this.currentColumn.parentElement.children).indexOf(this.currentColumn);
                    this.startX = event.clientX;
                    this.startWidth = this.currentColumn.offsetWidth;
                    
                    // Store current width
                    this.columnWidths.set(this.currentColumnIndex, this.startWidth);
                    
                    // Show resize line
                    this.showResizeLine(event.clientX);
                    
                    // Add resizing class to body
                    document.body.classList.add('resizing');
                    
                    // Prevent text selection
                    document.body.style.userSelect = 'none';
                    document.body.style.webkitUserSelect = 'none';
                    document.body.style.msUserSelect = 'none';
                }}
                
                onMouseMove(event) {{
                    if (!this.isResizing) return;
                    
                    const deltaX = event.clientX - this.startX;
                    const newWidth = Math.max(this.minWidth, Math.min(this.maxWidth, this.startWidth + deltaX));
                    
                    // Update resize line position
                    this.updateResizeLine(event.clientX);
                    
                    // Live preview - update column width
                    this.updateColumnWidth(this.currentColumnIndex, newWidth);
                }}
                
                endResize(event) {{
                    if (!this.isResizing) return;
                    
                    const deltaX = event.clientX - this.startX;
                    const newWidth = Math.max(this.minWidth, Math.min(this.maxWidth, this.startWidth + deltaX));
                    
                    // Final update
                    this.updateColumnWidth(this.currentColumnIndex, newWidth);
                    this.columnWidths.set(this.currentColumnIndex, newWidth);
                    
                    // Hide resize line
                    this.hideResizeLine();
                    
                    // Remove resizing class
                    document.body.classList.remove('resizing');
                    
                    // Restore text selection
                    document.body.style.userSelect = '';
                    document.body.style.webkitUserSelect = '';
                    document.body.style.msUserSelect = '';
                    
                    // Reset state
                    this.isResizing = false;
                    this.currentColumn = null;
                    this.currentColumnIndex = -1;
                }}
                
                showResizeLine(clientX) {{
                    const containerRect = this.table.getBoundingClientRect();
                    this.resizeLine.style.left = clientX + 'px';
                    this.resizeLine.style.top = containerRect.top + window.scrollY + 'px';
                    this.resizeLine.style.height = containerRect.height + 'px';
                    this.resizeLine.style.display = 'block';
                    this.resizeLine.classList.add('active');
                }}
                
                updateResizeLine(clientX) {{
                    this.resizeLine.style.left = clientX + 'px';
                }}
                
                hideResizeLine() {{
                    this.resizeLine.style.display = 'none';
                    this.resizeLine.classList.remove('active');
                }}
                
                updateColumnWidth(columnIndex, width) {{
                    // Update header cell
                    const headerCell = this.table.querySelector(`thead tr th:nth-child(${{columnIndex + 1}})`);
                    if (headerCell) {{
                        headerCell.style.width = width + 'px';
                        headerCell.style.minWidth = width + 'px';
                        headerCell.style.maxWidth = width + 'px';
                    }}
                    
                    // Update all body cells in this column
                    const bodyCells = this.table.querySelectorAll(`tbody tr td:nth-child(${{columnIndex + 1}})`);
                    bodyCells.forEach(cell => {{
                        cell.style.width = width + 'px';
                        cell.style.minWidth = width + 'px';
                        cell.style.maxWidth = width + 'px';
                    }});
                }}
                
                setInitialColumnWidths() {{
                    // Define precise initial widths for each column (updated for new columns)
                    const initialWidths = [
                        60,   // RANK
                        180,  // VARIANT
                        120,  // VARIANT TYPE
                        80,   // GENE
                        100,  // RS
                        155,  // CLINVAR (new)
                        135,  // ACMG
                        160,  // ACMG RULES
                        200,  // HGVS
                        150,  // HGVS PROTEIN
                        150,  // HGVS CODING
                        115,  // INHERITANCE
                        140,  // EFFECT
                        55,   // EXON (new)
                        100,  // ZYGOSITY
                        100,  // GNOMAD
                        145,  // ALLELIC BALANCE
                        80,   // DEPTH
                        80    // FILTER
                    ];
                    
                    // Apply initial widths
                    initialWidths.forEach((width, index) => {{
                        this.updateColumnWidth(index, width);
                        this.columnWidths.set(index, width);
                    }});
                }}
                
                // Method to refresh column widths after table re-render
                refreshColumnWidths() {{
                    this.columnWidths.forEach((width, index) => {{
                        this.updateColumnWidth(index, width);
                    }});
                }}
            }}
            
            // Enhanced Sorting System
            class SortingSystem {{
                constructor() {{
                    this.setupSortingListeners();
                }}
                
                setupSortingListeners() {{
                    // Add click listeners to sortable headers
                    const sortableHeaders = document.querySelectorAll('.sortable');
                    sortableHeaders.forEach(header => {{
                        header.addEventListener('click', (e) => {{
                            e.preventDefault();
                            e.stopPropagation();
                            
                            const sortKey = header.getAttribute('data-sort');
                            this.sortTable(sortKey);
                        }});
                    }});
                }}
                
                sortTable(sortKey) {{
                    // Toggle sort direction if same column
                    if (currentSortColumn === sortKey) {{
                        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                    }} else {{
                        currentSortDirection = 'asc';
                        currentSortColumn = sortKey;
                    }}
                    
                    // Clear previous sort indicators
                    document.querySelectorAll('.variants-table th').forEach(th => {{
                        th.classList.remove('sorted-asc', 'sorted-desc');
                    }});
                    
                    // Add sort indicator to current column
                    const currentHeader = document.querySelector(`[data-sort="${{sortKey}}"]`);
                    if (currentHeader) {{
                        currentHeader.classList.add(currentSortDirection === 'asc' ? 'sorted-asc' : 'sorted-desc');
                    }}
                    
                    // Sort the filtered variants
                    filteredVariants.sort((a, b) => {{
                        let aVal, bVal;
                        
                        switch (sortKey) {{
                            case 'acmg':
                                aVal = acmgPriority[getVariantValue(a, 'ACMG')] || 999;
                                bVal = acmgPriority[getVariantValue(b, 'ACMG')] || 999;
                                break;
                            case 'clinvar':
                                const aClinVar = classifyClinVar(getVariantValue(a, 'clinvar: Clinvar '));
                                const bClinVar = classifyClinVar(getVariantValue(b, 'clinvar: Clinvar '));
                                aVal = clinvarPriority[aClinVar] || 999;
                                bVal = clinvarPriority[bClinVar] || 999;
                                break;
                            case 'depth':
                                aVal = parseFloat(getVariantValue(a, 'DP', '0')) || 0;
                                bVal = parseFloat(getVariantValue(b, 'DP', '0')) || 0;
                                break;
                            case 'allelicBalance':
                                aVal = parseFloat(getVariantValue(a, 'Allelic Balance', '0')) || 0;
                                bVal = parseFloat(getVariantValue(b, 'Allelic Balance', '0')) || 0;
                                break;
                            default:
                                return 0;
                        }}
                        
                        if (currentSortDirection === 'asc') {{
                            return aVal - bVal;
                        }} else {{
                            return bVal - aVal;
                        }}
                    }});
                    
                    // Refresh the table
                    currentPage = 1;
                    renderTable(currentPage);
                    renderPaginationControls();
                }}
            }}
            
            // Initialize systems
            const columnResizer = new ExcelColumnResizer();
            const filterSystem = new FilterSystem();
            const sortingSystem = new SortingSystem();
            
            // Function to format variant based on type - Enhanced Professional Version
            function formatVariant(chr, start, ref, alt) {{
                // Handle cases where chr might be undefined, null, or 'N/A'
                if (!chr || chr === 'N/A' || chr === '.' || !start || !ref || !alt) return 'N/A';
                
                // Clean up chromosome notation - ensure it has 'chr' prefix
                let cleanChr = chr.toString().replace(/^chr/i, '');
                if (cleanChr === '' || cleanChr === 'N/A' || cleanChr === '.') return 'N/A';
                
                // Format position
                const position = start.toString();
                
                // Handle deletions
                if (alt === '.' || alt === '-' || (ref && alt && ref.length > alt.length && alt.length === 1)) {{
                    const deletedSeq = ref.length > 6 ? ref.substring(0, 6) + '...' : ref;
                    return `chr${{cleanChr}}:${{position}} del${{deletedSeq}}`;
                }}
                
                // Handle insertions
                if (ref === '.' || ref === '-' || (ref && alt && alt.length > ref.length && ref.length === 1)) {{
                    const insertedSeq = alt.length > 6 ? alt.substring(0, 6) + '...' : alt;
                    return `chr${{cleanChr}}:${{position}} ins${{insertedSeq}}`;
                }}
                
                // Handle SNVs and small variants - Professional formatting
                return `chr${{cleanChr}}:${{position}} ${{ref}} → ${{alt}}`;
            }}
            
            // Function to get chromosome value with enhanced column name detection
            function getChromosomeValue(variant) {{
                // Try different possible chromosome column names including the user's format
                const possibleKeys = ['#Chr', 'Chr', 'chr', 'CHROM', '#CHROM', 'chromosome'];
                
                for (const key of possibleKeys) {{
                    const value = variant[key];
                    if (value && value !== '.' && value !== '' && value !== 'N/A') {{
                        return value;
                    }}
                }}
                
                return null; // Return null instead of 'N/A' to handle in formatVariant
            }}
            
            // Enhanced function to clean up effect text - Professional Version
            function cleanEffect(effectText) {{
                if (!effectText || effectText === 'N/A' || effectText === '.') return 'N/A';
                
                // Remove underscores, replace & with |, remove the word "variant"
                let cleaned = effectText
                    .replace(/_/g, ' ')
                    .replace(/&/g, ' | ')
                    .replace(/\\bvariant\\b/gi, '')
                    .trim();
                
                // Clean up multiple spaces and trim
                cleaned = cleaned.replace(/\\s+/g, ' ').trim();
                
                // Capitalize first letter of each word for professional look
                cleaned = cleaned.split(' ').map(word => {{
                    if (word === '|') return word;
                    return word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : word;
                }}).join(' ');
                
                return cleaned || 'N/A';
            }}
            
            // Professional ACMG Rules formatting function
            function formatAcmgRules(rulesText) {{
                if (!rulesText || rulesText === 'N/A' || rulesText === '.') return 'N/A';
                
                // Remove commas and clean up spacing
                return rulesText.replace(/,/g, ' ').replace(/\\s+/g, ' ').trim();
            }}
            
            // Function to get ACMG badge class with new VUS variants
            function getAcmgBadgeClass(classification) {{
                if (!classification) return 'badge-other';
                
                classification = classification.toLowerCase();
                if (classification.includes('pathogenic') && !classification.includes('likely')) {{
                    return 'badge-pathogenic';
                }} else if (classification.includes('likely pathogenic')) {{
                    return 'badge-likely-pathogenic';
                }} else if (classification.includes('vus h')) {{
                    return 'badge-vus-h';
                }} else if (classification.includes('vus m')) {{
                    return 'badge-vus';
                }} else if (classification.includes('vus c')) {{
                    return 'badge-vus-c';
                }} else if (classification.includes('vus') || classification.includes('uncertain')) {{
                    return 'badge-vus';
                }} else if (classification.includes('likely benign')) {{
                    return 'badge-likely-benign';
                }} else if (classification.includes('benign')) {{
                    return 'badge-benign';
                }}
                
                return 'badge-other';
            }}
            
            // Function to combine HGVS information
            function formatHGVS(featureId, hgvsP, hgvsC) {{
                if (!featureId && !hgvsP && !hgvsC) return 'N/A';
                
                let result = '';
                if (featureId && featureId !== '.' && featureId !== 'N/A') {{
                    result = featureId;
                }}
                
                if (hgvsC && hgvsC !== '.' && hgvsC !== 'N/A') {{
                    result += (result ? ':' : '') + hgvsC;
                }}
                
                if (hgvsP && hgvsP !== '.' && hgvsP !== 'N/A') {{
                    result += ' ' + hgvsP;
                }}
                
                return result || 'N/A';
            }}
            
            // Function to safely get value from variant
            function getVariantValue(variant, key, defaultValue = 'N/A') {{
                const value = variant[key];
                if (!value || value === '.' || value === '') {{
                    return defaultValue;
                }}
                return value;
            }}
            
            // Enhanced filter and search function
            function applyFiltersAndSearch() {{
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                
                filteredVariants = allVariants.filter(variant => {{
                    // Apply filters
                    const depth = parseFloat(getVariantValue(variant, 'DP', '0')) || 0;
                    const allelicBalance = parseFloat(getVariantValue(variant, 'Allelic Balance', '0')) || 0;
                    
                    if (depth < minDepth || allelicBalance < minAllelicBalance) {{
                        return false;
                    }}
                    
                    // Apply search
                    if (searchTerm === '') {{
                        return true;
                    }}
                    
                    return (
                        (getVariantValue(variant, 'Ref.Gene', '').toLowerCase().includes(searchTerm)) ||
                        (getChromosomeValue(variant) && getChromosomeValue(variant).toString().toLowerCase().includes(searchTerm)) ||
                        (getVariantValue(variant, 'avsnp151', '').toLowerCase().includes(searchTerm)) ||
                        (getVariantValue(variant, 'ACMG', '').toLowerCase().includes(searchTerm)) ||
                        (cleanEffect(getVariantValue(variant, 'ANN[0].EFFECT', '')).toLowerCase().includes(searchTerm))
                    );
                }});
                
                currentPage = 1;
                renderTable(currentPage);
                renderPaginationControls();
            }}
            
            // Reset button functionality
            document.getElementById('refreshButton').addEventListener('click', function() {{
                filteredVariants = [...originalVariants];
                document.getElementById('searchInput').value = '';
                currentPage = 1;
                rowsPerPage = 10;
                document.getElementById('rowsPerPage').value = '10';
                
                // Reset sorting
                currentSortColumn = null;
                currentSortDirection = 'asc';
                document.querySelectorAll('.variants-table th').forEach(th => {{
                    th.classList.remove('sorted-asc', 'sorted-desc');
                }});
                
                // Reset filters
                minDepth = 0;
                minAllelicBalance = 0;
                filterSystem.resetFilters();
                
                renderTable(currentPage);
                renderPaginationControls();
            }});
            
            // Rows per page change handler
            document.getElementById('rowsPerPage').addEventListener('change', function(e) {{
                rowsPerPage = parseInt(e.target.value);
                currentPage = 1;
                renderTable(currentPage);
                renderPaginationControls();
            }});
            
            // Search functionality
            document.getElementById('searchInput').addEventListener('input', function(e) {{
                applyFiltersAndSearch();
            }});
            
            // Render table with pagination
            function renderTable(page) {{
                const startIndex = (page - 1) * rowsPerPage;
                const endIndex = startIndex + rowsPerPage;
                const displayedVariants = filteredVariants.slice(startIndex, endIndex);
                
                const tbody = document.getElementById('variantsTableBody');
                tbody.innerHTML = '';
                
                if (displayedVariants.length === 0) {{
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="19" style="text-align: center; padding: 20px;">
                                No variants match your search criteria.
                            </td>
                        </tr>
                    `;
                    // Refresh column widths after table re-render
                    setTimeout(() => columnResizer.refreshColumnWidths(), 10);
                    return;
                }}
                
                displayedVariants.forEach((variant, index) => {{
                    const row = document.createElement('tr');
                    
                    // RANK
                    const rankCell = document.createElement('td');
                    rankCell.className = 'col-rank';
                    const rankBubble = document.createElement('div');
                    rankBubble.className = 'rank-bubble';
                    rankBubble.textContent = startIndex + index + 1;
                    rankCell.appendChild(rankBubble);
                    row.appendChild(rankCell);
                    
                    // VARIANT - Enhanced Professional Formatting
                    const variantCell = document.createElement('td');
                    variantCell.className = 'col-variant';
                    const variantSpan = document.createElement('span');
                    variantSpan.className = 'variant-code';
                    variantSpan.textContent = formatVariant(
                        getChromosomeValue(variant),
                        getVariantValue(variant, 'Start'),
                        getVariantValue(variant, 'Ref'),
                        getVariantValue(variant, 'Alt')
                    );
                    variantCell.appendChild(variantSpan);
                    row.appendChild(variantCell);
                    
                    // VARIANT TYPE
                    const variantTypeCell = document.createElement('td');
                    variantTypeCell.className = 'col-variant-type';
                    variantTypeCell.textContent = getVariantValue(variant, 'Variant Type');
                    row.appendChild(variantTypeCell);
                    
                    // GENE
                    const geneCell = document.createElement('td');
                    geneCell.className = 'col-gene';
                    const geneLink = document.createElement('a');
                    geneLink.href = `https://www.genecards.org/cgi-bin/carddisp.pl?gene=${{getVariantValue(variant, 'Ref.Gene')}}`;
                    geneLink.target = '_blank';
                    geneLink.className = 'gene-link';
                    geneLink.textContent = getVariantValue(variant, 'Ref.Gene');
                    geneCell.appendChild(geneLink);
                    row.appendChild(geneCell);
                    
                    // RS
                    const rsCell = document.createElement('td');
                    rsCell.className = 'col-rs';
                    rsCell.textContent = getVariantValue(variant, 'avsnp151');
                    row.appendChild(rsCell);
                    
                    // CLINVAR (NEW COLUMN)
                    const clinvarCell = document.createElement('td');
                    clinvarCell.className = 'col-clinvar';
                    const clinvarValue = getVariantValue(variant, 'clinvar: Clinvar ');
                    const clinvarClassification = classifyClinVar(clinvarValue);
                    
                    if (clinvarClassification !== 'Not available') {{
                        const badge = document.createElement('span');
                        badge.className = `badge ${{getClinVarBadgeClass(clinvarClassification)}}`;
                        badge.textContent = clinvarClassification;
                        clinvarCell.appendChild(badge);
                    }} else {{
                        clinvarCell.textContent = 'N/A';
                        clinvarCell.className += ' not-available';
                    }}
                    row.appendChild(clinvarCell);
                    
                    // ACMG
                    const acmgCell = document.createElement('td');
                    acmgCell.className = 'col-acmg';
                    const acmgValue = getVariantValue(variant, 'ACMG');
                    if (acmgValue !== 'N/A') {{
                        const badge = document.createElement('span');
                        badge.className = `badge ${{getAcmgBadgeClass(acmgValue)}}`;
                        badge.textContent = acmgValue;
                        acmgCell.appendChild(badge);
                    }} else {{
                        acmgCell.textContent = 'N/A';
                        acmgCell.className += ' not-available';
                    }}
                    row.appendChild(acmgCell);
                    
                    // ACMG RULES - Enhanced Professional Formatting
                    const acmgRulesCell = document.createElement('td');
                    acmgRulesCell.className = 'col-acmg-rules';
                    const acmgRulesValue = getVariantValue(variant, 'ACMG_Rules');
                    if (acmgRulesValue !== 'N/A') {{
                        const rulesSpan = document.createElement('span');
                        rulesSpan.className = 'acmg-rules';
                        rulesSpan.textContent = formatAcmgRules(acmgRulesValue);
                        acmgRulesCell.appendChild(rulesSpan);
                    }} else {{
                        acmgRulesCell.textContent = 'N/A';
                        acmgRulesCell.className += ' not-available';
                    }}
                    row.appendChild(acmgRulesCell);
                    
                    // HGVS (combined)
                    const hgvsCell = document.createElement('td');
                    hgvsCell.className = 'col-hgvs';
                    hgvsCell.textContent = formatHGVS(
                        getVariantValue(variant, 'ANN[0].FEATUREID'),
                        getVariantValue(variant, 'ANN[0].HGVS_P'),
                        getVariantValue(variant, 'ANN[0].HGVS_C')
                    );
                    row.appendChild(hgvsCell);
                    
                    // HGVS PROTEIN
                    const hgvsProteinCell = document.createElement('td');
                    hgvsProteinCell.className = 'col-hgvs-protein';
                    hgvsProteinCell.textContent = getVariantValue(variant, 'ANN[0].HGVS_P');
                    row.appendChild(hgvsProteinCell);
                    
                    // HGVS CODING
                    const hgvsCodingCell = document.createElement('td');
                    hgvsCodingCell.className = 'col-hgvs-coding';
                    hgvsCodingCell.textContent = getVariantValue(variant, 'ANN[0].HGVS_C');
                    row.appendChild(hgvsCodingCell);
                    
                    // INHERITANCE
                    const inheritanceCell = document.createElement('td');
                    inheritanceCell.className = 'col-inheritance';
                    inheritanceCell.textContent = getVariantValue(variant, 'Inheritance');
                    row.appendChild(inheritanceCell);
                    
                    // EFFECT - Enhanced Professional Formatting
                    const effectCell = document.createElement('td');
                    effectCell.className = 'col-effect';
                    const effectValue = cleanEffect(getVariantValue(variant, 'ANN[0].EFFECT'));
                    if (effectValue !== 'N/A') {{
                        const effectSpan = document.createElement('span');
                        effectSpan.className = 'effect-text';
                        effectSpan.textContent = effectValue;
                        effectCell.appendChild(effectSpan);
                    }} else {{
                        effectCell.textContent = 'N/A';
                        effectCell.className += ' not-available';
                    }}
                    row.appendChild(effectCell);
                    
                    // EXON (NEW COLUMN)
                    const exonCell = document.createElement('td');
                    exonCell.className = 'col-exon';
                    exonCell.textContent = getVariantValue(variant, 'ANN[0].RANK');
                    row.appendChild(exonCell);
                    
                    // ZYGOSITY
                    const zygosityCell = document.createElement('td');
                    zygosityCell.className = 'col-zygosity';
                    zygosityCell.textContent = getVariantValue(variant, 'Otherinfo');
                    row.appendChild(zygosityCell);
                    
                    // GNOMAD
                    const gnomadCell = document.createElement('td');
                    gnomadCell.className = 'col-gnomad';
                    gnomadCell.textContent = getVariantValue(variant, 'Freq_gnomAD_genome_ALL');
                    row.appendChild(gnomadCell);
                    
                    // ALLELIC BALANCE
                    const allelicBalanceCell = document.createElement('td');
                    allelicBalanceCell.className = 'col-allelic-balance';
                    allelicBalanceCell.textContent = getVariantValue(variant, 'Allelic Balance');
                    row.appendChild(allelicBalanceCell);
                    
                    // DEPTH
                    const depthCell = document.createElement('td');
                    depthCell.className = 'col-depth';
                    depthCell.textContent = getVariantValue(variant, 'DP');
                    row.appendChild(depthCell);
                    
                    // FILTER
                    const filterCell = document.createElement('td');
                    filterCell.className = 'col-filter';
                    const filterValue = getVariantValue(variant, 'FILTER');
                    
                    if (filterValue === 'PASS') {{
                        const icon = document.createElement('i');
                        icon.className = 'fas fa-check-circle filter-pass';
                        filterCell.appendChild(icon);
                    }} else if (filterValue !== 'N/A') {{
                        const icon = document.createElement('i');
                        icon.className = 'fas fa-times-circle filter-fail';
                        filterCell.appendChild(icon);
                    }} else {{
                        filterCell.textContent = 'N/A';
                        filterCell.className += ' not-available';
                    }}
                    row.appendChild(filterCell);
                    
                    tbody.appendChild(row);
                }});
                
                // Refresh column widths after table re-render
                setTimeout(() => columnResizer.refreshColumnWidths(), 10);
            }}
            
            // Render pagination controls
            function renderPaginationControls() {{
                const totalVariants = filteredVariants.length;
                const totalPages = Math.ceil(totalVariants / rowsPerPage);
                const startIndex = (currentPage - 1) * rowsPerPage + 1;
                const endIndex = Math.min(currentPage * rowsPerPage, totalVariants);
                
                // Update page info
                document.getElementById('pageInfo').textContent = 
                    `Showing ${{startIndex}}-${{endIndex}} of ${{totalVariants}} variants`;
                
                // Generate page navigation (clear existing buttons first, keeping filters container)
                const pageNavigation = document.getElementById('pageNavigation');
                const filtersContainer = pageNavigation.querySelector('.filters-container');
                pageNavigation.innerHTML = '';
                pageNavigation.appendChild(filtersContainer);
                
                // Previous button
                const prevBtn = document.createElement('button');
                prevBtn.className = 'page-nav-btn';
                prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
                prevBtn.disabled = currentPage === 1;
                prevBtn.addEventListener('click', () => {{
                    if (currentPage > 1) {{
                        currentPage--;
                        renderTable(currentPage);
                        renderPaginationControls();
                    }}
                }});
                pageNavigation.appendChild(prevBtn);
                
                // Page number buttons
                const maxButtons = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
                let endPage = Math.min(totalPages, startPage + maxButtons - 1);
                
                if (endPage - startPage + 1 < maxButtons && startPage > 1) {{
                    startPage = Math.max(1, endPage - maxButtons + 1);
                }}
                
                for (let i = startPage; i <= endPage; i++) {{
                    const pageBtn = document.createElement('button');
                    pageBtn.className = `page-nav-btn ${{i === currentPage ? 'active' : ''}}`;
                    pageBtn.textContent = i;
                    pageBtn.addEventListener('click', () => {{
                        currentPage = i;
                        renderTable(currentPage);
                        renderPaginationControls();
                    }});
                    pageNavigation.appendChild(pageBtn);
                }}
                
                // Next button
                const nextBtn = document.createElement('button');
                nextBtn.className = 'page-nav-btn';
                nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
                nextBtn.disabled = currentPage === totalPages;
                nextBtn.addEventListener('click', () => {{
                    if (currentPage < totalPages) {{
                        currentPage++;
                        renderTable(currentPage);
                        renderPaginationControls();
                    }}
                }});
                pageNavigation.appendChild(nextBtn);
            }}
            
            // Initialize
            renderTable(currentPage);
            renderPaginationControls();
        }});
    </script>
</body>
</html>"""
    
    # Write the HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated enhanced report: {output_path}")
    return True

def main():
    """Main function to run from the command line"""
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <input_tsv_file> [output_html_file] [coverage_metrics_file]")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    coverage_metrics_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return
    
    result = generate_html(input_file, output_file, coverage_metrics_file)
    if result:
        print("Enhanced report generation completed successfully!")
    else:
        print("Report generation failed.")

if __name__ == "__main__":
    main()
