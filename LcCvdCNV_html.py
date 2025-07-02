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
                cnv_variant = {headers[j]: row[j] if j < len(row) else '' for j in range(len(headers))}
                # Add rank based on position
                cnv_variant['rank'] = i + 1
                rows.append(cnv_variant)
    return headers, rows

def generate_html(file_path, output_path=None):
    """Generate HTML report from CNV TSV file"""
    # Determine output filename if not specified
    if not output_path:
        output_path = os.path.splitext(file_path)[0] + "_cnv_report.html"
    
    # Get the sample name from the file path
    full_filename = os.path.basename(os.path.splitext(file_path)[0])
    # Extract sample name (assuming format like "319754_CNV_prioritized")
    sample_name = full_filename.split('_CNV')[0] if '_CNV' in full_filename else full_filename.split('_')[0]
    
    # Read the TSV file
    try:
        headers, cnv_variants = read_tsv_file(file_path)
    except Exception as e:
        print(f"Error reading TSV file: {e}")
        return False
    
    # Convert data to JSON for embedding in HTML
    cnv_variants_json = json.dumps(cnv_variants)
    
    # Current date for the report
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Generate HTML content with embedded data
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNV Analysis Report</title>
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
            
            /* Classification colors */
            --pathogenic-red: #E74C3C;
            --likely-pathogenic-red: #F07470;
            --uncertain-orange: #FF8C00;
            --likely-benign-green: #10B981;
            --benign-green: #4CAF50;
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
        
        /* Header Styles */
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
        
        /* Pagination controls */
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
        
        /* CNV Table Container */
        .cnv-container {{
            background-color: var(--white-bg);
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            position: relative;
            overflow-x: auto;
            overflow-y: visible;
        }}
        
        /* Enhanced Table Layout */
        .cnv-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            table-layout: fixed;
            min-width: 100%;
        }}
        
        .cnv-table th,
        .cnv-table td {{
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
        
        .cnv-table th:last-child,
        .cnv-table td:last-child {{
            border-right: none;
        }}
        
        .cnv-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Enhanced Table Headers */
        .cnv-table th {{
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
        
        .cnv-table th:hover {{
            background: linear-gradient(180deg, #2C5282 0%, #1A365D 100%);
        }}

        .cnv-table th.sortable {{
            cursor: pointer;
        }}

        .cnv-table th.sorted-asc::after {{
            content: " ▲";
            color: var(--lime);
        }}

        .cnv-table th.sorted-desc::after {{
            content: " ▼";
            color: var(--lime);
        }}
        
        /* Enhanced Table Body Styling */
        .cnv-table tbody tr:nth-child(even) {{
            background-color: var(--soft-gray);
        }}
        
        .cnv-table tbody tr:hover {{
            background-color: rgba(44, 166, 164, 0.05);
            transition: background-color 0.15s ease;
        }}
        
        /* Default Column Widths */
        .col-rank {{ width: 60px; min-width: 50px; max-width: 100px; }}
        .col-cnv {{ width: 200px; min-width: 150px; max-width: 300px; }}
        .col-length {{ width: 100px; min-width: 80px; max-width: 150px; }}
        .col-type {{ width: 80px; min-width: 60px; max-width: 120px; }}
        .col-classification {{ width: 150px; min-width: 120px; max-width: 200px; }}
        .col-dosage-genes {{ width: 150px; min-width: 120px; max-width: 200px; }}
        .col-all-genes {{ width: 150px; min-width: 120px; max-width: 200px; }}
        
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
        
        /* CNV code styling */
        .cnv-code {{
            font-family: 'Courier New', monospace;
            background-color: rgba(30, 58, 95, 0.1);
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 12px;
        }}
        
        /* Type Styling */
        .type-del {{
            background-color: rgba(231, 76, 60, 0.1);
            color: var(--red);
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
        }}
        
        .type-dup {{
            background-color: rgba(76, 175, 80, 0.1);
            color: var(--green);
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
        }}
        
        /* Badge Styling for Classification */
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
            background: linear-gradient(90deg, var(--likely-pathogenic-red) 0%, #C53030 100%);
        }}
        
        .badge-uncertain {{
            background: linear-gradient(90deg, var(--uncertain-orange) 0%, #D97706 100%);
        }}
        
        .badge-likely-benign {{
            background: linear-gradient(90deg, var(--likely-benign-green) 0%, #059669 100%);
        }}
        
        .badge-benign {{
            background: linear-gradient(90deg, var(--benign-green) 0%, #047857 100%);
        }}
        
        .badge-other {{
            background: linear-gradient(90deg, var(--medium-gray) 0%, #4B5563 100%);
        }}
        
        /* Gene count styling */
        .gene-count {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .gene-number {{
            background-color: var(--deep-blue);
            color: var(--white-bg);
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .download-btn {{
            background-color: var(--lime);
            color: var(--white-bg);
            border: none;
            padding: 4px 8px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
        }}
        
        .download-btn:hover {{
            background-color: #8bc34a;
            transform: scale(1.1);
        }}
        
        /* Not available text */
        .not-available {{
            color: var(--medium-gray);
            font-style: italic;
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
        }}
        
        @media (max-width: 768px) {{
            .report-header {{
                width: 41%;
                max-width: none;
            }}
            
            .pagination-controls {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
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
                    <div class="info-icon"><i class="fas fa-chart-line"></i></div>
                    <div class="info-text"><strong>CNV Results</strong> • Sample ID: {sample_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-calendar-alt"></i></div>
                    <div class="info-text"><strong>Analysis Date:</strong> {current_date}</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-clipboard-list"></i></div>
                    <div class="info-text">This report contains prioritized copy number variants classified according to ACMG/ClinGen guidelines.</div>
                </div>
                <div class="info-item">
                    <div class="info-icon"><i class="fas fa-sort-amount-down"></i></div>
                    <div class="info-text">CNVs are sorted by clinical significance, with pathogenic variants appearing first.</div>
                </div>
            </div>
        </div>
        
        <!-- Search and Reset View Button -->
        <div class="controls">
            <div class="search-controls">
                <button id="refreshButton" class="refresh-button"><i class="fas fa-sync-alt"></i> Reset View</button>
                <input type="text" id="searchInput" class="search-box" placeholder="Search for genes, chromosomes, or classifications...">
            </div>
        </div>
        
        <!-- Pagination Controls -->
        <div class="pagination-controls">
            <div class="results-per-page">
                <label for="rowsPerPage">Show:</label>
                <select id="rowsPerPage">
                    <option value="10" selected>10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
                <span>CNVs per page</span>
            </div>
            
            <div class="page-info" id="pageInfo">
                Showing 1-10 of 0 CNVs
            </div>
            
            <div class="page-navigation" id="pageNavigation">
                <!-- Page navigation will be generated dynamically -->
            </div>
        </div>
        
        <!-- CNV Table -->
        <div class="cnv-container">
            <table class="cnv-table" id="cnvTable">
                <thead>
                    <tr>
                        <th class="col-rank" data-sort="rank">RANK</th>
                        <th class="col-cnv" data-sort="cnv">CNV</th>
                        <th class="col-length sortable" data-sort="length">LENGTH</th>
                        <th class="col-type" data-sort="type">TYPE</th>
                        <th class="col-classification sortable" data-sort="classification">CLASSIFICATION</th>
                        <th class="col-dosage-genes" data-sort="dosageGenes">DOSAGE GENES</th>
                        <th class="col-all-genes" data-sort="allGenes">ALL GENES</th>
                    </tr>
                </thead>
                <tbody id="cnvTableBody">
                    <!-- CNVs will be added here dynamically -->
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
        
        // Embedded CNV data from TSV file
        const allCnvs = {cnv_variants_json};
        
        document.addEventListener('DOMContentLoaded', function() {{
            // Initialize variables
            let filteredCnvs = [...allCnvs];
            let currentPage = 1;
            let rowsPerPage = 10;
            let originalCnvs = [...allCnvs];
            
            // Sorting state
            let currentSortColumn = null;
            let currentSortDirection = 'asc';
            
            // Priority mappings for sorting
            const classificationPriority = {{
                'Pathogenic': 1,
                'Likely pathogenic': 2,
                'Uncertain significance': 3,
                'Likely benign': 4,
                'Benign': 5
            }};
            
            // Function to format CNV location
            function formatCnvLocation(chromosome, start, end) {{
                if (!chromosome || !start || !end) return 'N/A';
                const cleanChr = chromosome.toString().replace(/^chr/i, '');
                return `chr${{cleanChr}}:${{start}}...${{end}}`;
            }}
            
            // Function to calculate CNV length
            function calculateLength(start, end) {{
                if (!start || !end) return 'N/A';
                const length = parseInt(end) - parseInt(start);
                if (length >= 1000000) {{
                    return (length / 1000000).toFixed(2) + ' Mb';
                }} else if (length >= 1000) {{
                    return (length / 1000).toFixed(1) + ' kb';
                }} else {{
                    return length + ' bp';
                }}
            }}
            
            // Function to get classification badge class
            function getClassificationBadgeClass(classification) {{
                if (!classification) return 'badge-other';
                
                const cls = classification.toLowerCase();
                if (cls.includes('pathogenic') && !cls.includes('likely')) {{
                    return 'badge-pathogenic';
                }} else if (cls.includes('likely pathogenic')) {{
                    return 'badge-likely-pathogenic';
                }} else if (cls.includes('uncertain')) {{
                    return 'badge-uncertain';
                }} else if (cls.includes('likely benign')) {{
                    return 'badge-likely-benign';
                }} else if (cls.includes('benign')) {{
                    return 'badge-benign';
                }}
                
                return 'badge-other';
            }}
            
            // Function to get CNV value safely
            function getCnvValue(cnv, key, defaultValue = 'N/A') {{
                const value = cnv[key];
                if (!value || value === '.' || value === '') {{
                    return defaultValue;
                }}
                return value;
            }}
            
            // Function to count genes
            function countGenes(geneString) {{
                if (!geneString || geneString === 'N/A' || geneString === '.' || geneString === '') {{
                    return 0;
                }}
                return geneString.split(',').map(g => g.trim()).filter(g => g.length > 0).length;
            }}
            
            // Function to download gene list
            function downloadGeneList(geneString, filename) {{
                if (!geneString || geneString === 'N/A' || geneString === '.' || geneString === '') {{
                    alert('No genes available for download');
                    return;
                }}
                
                const genes = geneString.split(',').map(g => g.trim()).filter(g => g.length > 0);
                const content = genes.join('\\n');
                
                const blob = new Blob([content], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }}
            
            // Enhanced search function
            function applySearch() {{
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                
                filteredCnvs = allCnvs.filter(cnv => {{
                    if (searchTerm === '') {{
                        return true;
                    }}
                    
                    return (
                        (getCnvValue(cnv, 'Chromosome', '').toLowerCase().includes(searchTerm)) ||
                        (getCnvValue(cnv, 'Type', '').toLowerCase().includes(searchTerm)) ||
                        (getCnvValue(cnv, 'Classification', '').toLowerCase().includes(searchTerm)) ||
                        (getCnvValue(cnv, 'Known or predicted dosage-sensitive genes', '').toLowerCase().includes(searchTerm)) ||
                        (getCnvValue(cnv, 'All protein coding genes', '').toLowerCase().includes(searchTerm))
                    );
                }});
                
                currentPage = 1;
                renderTable(currentPage);
                renderPaginationControls();
            }}
            
            // Reset button functionality
            document.getElementById('refreshButton').addEventListener('click', function() {{
                filteredCnvs = [...originalCnvs];
                document.getElementById('searchInput').value = '';
                currentPage = 1;
                rowsPerPage = 10;
                document.getElementById('rowsPerPage').value = '10';
                
                // Reset sorting
                currentSortColumn = null;
                currentSortDirection = 'asc';
                document.querySelectorAll('.cnv-table th').forEach(th => {{
                    th.classList.remove('sorted-asc', 'sorted-desc');
                }});
                
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
                applySearch();
            }});
            
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
                    document.querySelectorAll('.cnv-table th').forEach(th => {{
                        th.classList.remove('sorted-asc', 'sorted-desc');
                    }});
                    
                    // Add sort indicator to current column
                    const currentHeader = document.querySelector(`[data-sort="${{sortKey}}"]`);
                    if (currentHeader) {{
                        currentHeader.classList.add(currentSortDirection === 'asc' ? 'sorted-asc' : 'sorted-desc');
                    }}
                    
                    // Sort the filtered CNVs
                    filteredCnvs.sort((a, b) => {{
                        let aVal, bVal;
                        
                        switch (sortKey) {{
                            case 'classification':
                                aVal = classificationPriority[getCnvValue(a, 'Classification')] || 999;
                                bVal = classificationPriority[getCnvValue(b, 'Classification')] || 999;
                                break;
                            case 'length':
                                const aStart = parseInt(getCnvValue(a, 'Start', '0')) || 0;
                                const aEnd = parseInt(getCnvValue(a, 'End', '0')) || 0;
                                const bStart = parseInt(getCnvValue(b, 'Start', '0')) || 0;
                                const bEnd = parseInt(getCnvValue(b, 'End', '0')) || 0;
                                aVal = aEnd - aStart;
                                bVal = bEnd - bStart;
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
            
            // Initialize sorting system
            const sortingSystem = new SortingSystem();
            
            // Render table with pagination
            function renderTable(page) {{
                const startIndex = (page - 1) * rowsPerPage;
                const endIndex = startIndex + rowsPerPage;
                const displayedCnvs = filteredCnvs.slice(startIndex, endIndex);
                
                const tbody = document.getElementById('cnvTableBody');
                tbody.innerHTML = '';
                
                if (displayedCnvs.length === 0) {{
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="7" style="text-align: center; padding: 20px;">
                                No CNVs match your search criteria.
                            </td>
                        </tr>
                    `;
                    return;
                }}
                
                displayedCnvs.forEach((cnv, index) => {{
                    const row = document.createElement('tr');
                    
                    // RANK
                    const rankCell = document.createElement('td');
                    rankCell.className = 'col-rank';
                    const rankBubble = document.createElement('div');
                    rankBubble.className = 'rank-bubble';
                    rankBubble.textContent = startIndex + index + 1;
                    rankCell.appendChild(rankBubble);
                    row.appendChild(rankCell);
                    
                    // CNV
                    const cnvCell = document.createElement('td');
                    cnvCell.className = 'col-cnv';
                    const cnvSpan = document.createElement('span');
                    cnvSpan.className = 'cnv-code';
                    cnvSpan.textContent = formatCnvLocation(
                        getCnvValue(cnv, 'Chromosome'),
                        getCnvValue(cnv, 'Start'),
                        getCnvValue(cnv, 'End')
                    );
                    cnvCell.appendChild(cnvSpan);
                    row.appendChild(cnvCell);
                    
                    // LENGTH
                    const lengthCell = document.createElement('td');
                    lengthCell.className = 'col-length';
                    lengthCell.textContent = calculateLength(
                        getCnvValue(cnv, 'Start'),
                        getCnvValue(cnv, 'End')
                    );
                    row.appendChild(lengthCell);
                    
                    // TYPE
                    const typeCell = document.createElement('td');
                    typeCell.className = 'col-type';
                    const typeValue = getCnvValue(cnv, 'Type');
                    if (typeValue !== 'N/A') {{
                        const typeSpan = document.createElement('span');
                        typeSpan.className = typeValue.toLowerCase() === 'del' ? 'type-del' : 'type-dup';
                        typeSpan.textContent = typeValue;
                        typeCell.appendChild(typeSpan);
                    }} else {{
                        typeCell.textContent = 'N/A';
                        typeCell.className += ' not-available';
                    }}
                    row.appendChild(typeCell);
                    
                    // CLASSIFICATION
                    const classificationCell = document.createElement('td');
                    classificationCell.className = 'col-classification';
                    const classificationValue = getCnvValue(cnv, 'Classification');
                    if (classificationValue !== 'N/A') {{
                        const badge = document.createElement('span');
                        badge.className = `badge ${{getClassificationBadgeClass(classificationValue)}}`;
                        badge.textContent = classificationValue;
                        classificationCell.appendChild(badge);
                    }} else {{
                        classificationCell.textContent = 'N/A';
                        classificationCell.className += ' not-available';
                    }}
                    row.appendChild(classificationCell);
                    
                    // DOSAGE GENES
                    const dosageGenesCell = document.createElement('td');
                    dosageGenesCell.className = 'col-dosage-genes';
                    const dosageGenesValue = getCnvValue(cnv, 'Known or predicted dosage-sensitive genes');
                    const dosageGeneCount = countGenes(dosageGenesValue);
                    
                    if (dosageGeneCount > 0) {{
                        const geneCountDiv = document.createElement('div');
                        geneCountDiv.className = 'gene-count';
                        
                        const numberSpan = document.createElement('span');
                        numberSpan.className = 'gene-number';
                        numberSpan.textContent = dosageGeneCount;
                        
                        const downloadBtn = document.createElement('button');
                        downloadBtn.className = 'download-btn';
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                        downloadBtn.title = 'Download gene list';
                        downloadBtn.onclick = () => downloadGeneList(dosageGenesValue, `${{sampleName}}_dosage_genes_rank_${{startIndex + index + 1}}.txt`);
                        
                        geneCountDiv.appendChild(numberSpan);
                        geneCountDiv.appendChild(downloadBtn);
                        dosageGenesCell.appendChild(geneCountDiv);
                    }} else {{
                        dosageGenesCell.textContent = '0';
                        dosageGenesCell.className += ' not-available';
                    }}
                    row.appendChild(dosageGenesCell);
                    
                    // ALL GENES
                    const allGenesCell = document.createElement('td');
                    allGenesCell.className = 'col-all-genes';
                    const allGenesValue = getCnvValue(cnv, 'All protein coding genes');
                    const allGeneCount = countGenes(allGenesValue);
                    
                    if (allGeneCount > 0) {{
                        const geneCountDiv = document.createElement('div');
                        geneCountDiv.className = 'gene-count';
                        
                        const numberSpan = document.createElement('span');
                        numberSpan.className = 'gene-number';
                        numberSpan.textContent = allGeneCount;
                        
                        const downloadBtn = document.createElement('button');
                        downloadBtn.className = 'download-btn';
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                        downloadBtn.title = 'Download gene list';
                        downloadBtn.onclick = () => downloadGeneList(allGenesValue, `${{sampleName}}_all_genes_rank_${{startIndex + index + 1}}.txt`);
                        
                        geneCountDiv.appendChild(numberSpan);
                        geneCountDiv.appendChild(downloadBtn);
                        allGenesCell.appendChild(geneCountDiv);
                    }} else {{
                        allGenesCell.textContent = '0';
                        allGenesCell.className += ' not-available';
                    }}
                    row.appendChild(allGenesCell);
                    
                    tbody.appendChild(row);
                }});
            }}
            
            // Render pagination controls
            function renderPaginationControls() {{
                const totalCnvs = filteredCnvs.length;
                const totalPages = Math.ceil(totalCnvs / rowsPerPage);
                const startIndex = (currentPage - 1) * rowsPerPage + 1;
                const endIndex = Math.min(currentPage * rowsPerPage, totalCnvs);
                
                // Update page info
                document.getElementById('pageInfo').textContent = 
                    `Showing ${{startIndex}}-${{endIndex}} of ${{totalCnvs}} CNVs`;
                
                // Generate page navigation
                const pageNavigation = document.getElementById('pageNavigation');
                pageNavigation.innerHTML = '';
                
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
    
    print(f"Generated CNV report: {output_path}")
    return True

def main():
    """Main function to run from the command line"""
    if len(sys.argv) < 2:
        print("Usage: python LcCnvHtml.py <input_tsv_file> [output_html_file]")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return
    
    result = generate_html(input_file, output_file)
    if result:
        print("CNV report generation completed successfully!")
    else:
        print("CNV report generation failed.")

if __name__ == "__main__":
    main()
