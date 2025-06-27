#!/bin/bash

FASTQ_DIR="."

THREADS=28

# Function to process a single sample
process_sample() {
    local sample=$1
    local fastq1=$2
    local fastq2=$3
    local trimmed1="trimmed/${sample}_trimmed_1.fq.gz"
    local trimmed2="trimmed/${sample}_trimmed_2.fq.gz"

    TARGETS="/home/administrator/Lc/LcDatabase_hg38/bed_files/CVD_HG38/CVD_3433051_Covered.adj50bp.bed"

    echo "Processing sample: $sample"

    # 1. Count raw reads (from both R1 and R2 files)
    raw_reads_r1=$(zcat $fastq1 | wc -l | awk '{print $1/4}')
    raw_reads_r2=$(zcat $fastq2 | wc -l | awk '{print $1/4}')
    raw_reads=$((raw_reads_r1 + raw_reads_r2))
    
    # 2. Count trimmed reads (from both trimmed files)
    trimmed_reads_r1=$(zcat $trimmed1 | wc -l | awk '{print $1/4}')
    trimmed_reads_r2=$(zcat $trimmed2 | wc -l | awk '{print $1/4}')
    trimmed_reads=$((trimmed_reads_r1 + trimmed_reads_r2))
    
    # 3. Calculate mean read length (from raw reads, sampling first 10000 reads for efficiency)
    mean_length_r1=$(zcat $fastq1 | awk 'NR%4==2 {sum+=length($0); count++} count==10000 {print sum/count; exit}')
    mean_length_r2=$(zcat $fastq2 | awk 'NR%4==2 {sum+=length($0); count++} count==10000 {print sum/count; exit}')
    mean_read_length=$(echo "($mean_length_r1 + $mean_length_r2) / 2" | bc -l)
    
    # 4. Count aligned, uniquely mapped, and duplicate reads
    # Total aligned (exclude unmapped reads with -F 4)
    total_aligned=$(samtools view -@ $THREADS -c -F 4 ${sample}_aligned_marked_bqsr.bam)
    
    # Uniquely mapped reads - count unique read names with primary alignments
    # -F 0x900 excludes secondary (0x100) and supplementary (0x800) alignments
    uniquely_mapped=$(samtools view -@ $THREADS -f 0x2 -F 0x904 ${sample}_aligned_marked_bqsr.bam | cut -f 1 | sort | uniq -c | awk '$1==2{c++} END{print c}')
    
    # Count duplicate reads (flag 0x400 = 1024)
    # -f 1024 includes only reads marked as duplicates
    # -F 4 excludes unmapped reads (we only want mapped duplicates)
    duplicate_reads=$(samtools view -@ $THREADS -c -f 1024 -F 4 ${sample}_aligned_marked_bqsr.bam)
    
    # 5. Generate coverage information using samtools depth
    samtools depth -b $TARGETS ${sample}_aligned_marked_bqsr.bam > ${sample}_coverage.txt

    # 6. Calculate all coverage metrics and save to output file
    awk -v sample="$sample" \
        -v raw="$raw_reads" \
        -v trimmed="$trimmed_reads" \
        -v mean_len="$mean_read_length" \
        -v aligned="$total_aligned" \
        -v unique="$uniquely_mapped" \
        -v dup="$duplicate_reads" '
    BEGIN {
        total_bases = 0;
        total_coverage = 0;
        bases_10x = 0;
        bases_30x = 0;
        bases_50x = 0;
        bases_100x = 0;
        bases_200x = 0;
        bases_300x = 0;
    }
    {
        total_bases++;
        total_coverage += $3;
        
        if ($3 >= 10) bases_10x++;
        if ($3 >= 30) bases_30x++;
        if ($3 >= 50) bases_50x++;
        if ($3 >= 100) bases_100x++;
        if ($3 >= 200) bases_200x++;
        if ($3 >= 300) bases_300x++;
    }
    END {
        avg_coverage = total_coverage / total_bases;
        pct_10x = (bases_10x / total_bases) * 100;
        pct_30x = (bases_30x / total_bases) * 100;
        pct_50x = (bases_50x / total_bases) * 100;
        pct_100x = (bases_100x / total_bases) * 100;
        pct_200x = (bases_200x / total_bases) * 100;
        pct_300x = (bases_300x / total_bases) * 100;
        
        printf "Sample metrics for WES clinical analysis: %s\n", sample;
        printf "----------------------------------------\n";
        printf "# Read statistics:\n";
        printf "Raw reads: %d (total from R1 and R2)\n", raw;
        printf "Trimmed reads: %d (total from R1 and R2)\n", trimmed;
        printf "Mean read length: %.2f bp\n", mean_len;
        printf "Total aligned reads: %d\n", aligned;
        printf "Uniquely mapped reads: %d (%.2f%%)\n", unique, (unique*2/raw)*100;
        printf "Duplicate reads: %d (%.2f%%)\n", dup, (dup/aligned)*100;
        printf "\n# Coverage statistics:\n";
        printf "Average coverage: %.2fX\n", avg_coverage;
        printf "Percentage of bases with ≥10X coverage: %.2f%%\n", pct_10x;
        printf "Percentage of bases with ≥30X coverage: %.2f%%\n", pct_30x;
        printf "Percentage of bases with ≥50X coverage: %.2f%%\n", pct_50x;
        printf "Percentage of bases with ≥100X coverage: %.2f%%\n", pct_100x;
        printf "Percentage of bases with ≥200X coverage: %.2f%%\n", pct_200x;
        printf "Percentage of bases with ≥300X coverage: %.2f%%\n", pct_300x;
    }' ${sample}_coverage.txt > ${sample}_coverage_metrics.txt

    # 7. View the results
    cat ${sample}_coverage_metrics.txt
}

# Main script
for fastq1 in $FASTQ_DIR/*_1.fq.gz; do
    # Skip trimmed files
    if [[ $fastq1 == *"_t1.fq.gz" ]]; then
        continue
    fi
    
    fastq2="${fastq1/_1.fq.gz/_2.fq.gz}"
    if [ -f "$fastq2" ]; then
        sample=$(basename "$fastq1" | sed 's/_1.fq.gz//')
        process_sample "$sample" "$fastq1" "$fastq2"
    else
        echo "Warning: No matching read 2 file found for $fastq1"
    fi
done
