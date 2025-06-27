#!/bin/bash

# LcCvd version 1.2.0

# Set the directory where the FASTQ files are located
FASTQ_DIR="."

# Set paths to required tools and reference files
# Alignment-Variant Calling
REF_GENOME="/home/administrator/Lc/LcDatabase_hg38/bwa_index/gatk_hg38/hg38"
REF_GENOME_FA="/home/administrator/Lc/LcDatabase_hg38/bwa_index/gatk_hg38/hg38.fa"
TARGETS="/home/administrator/Lc/LcDatabase_hg38/bed_files/CVD_HG38/CVD_3433051_Covered.adj50bp.bed"
# Annotation
SNPEFF_JAR="/home/administrator/snpeff/snpEff/snpEff.jar"
CLINVAR_VCF="/home/administrator/Lc/LcDatabase_hg38/GATK_resources/clinvar.chr.vcf.gz"
Mills_1000G="/home/administrator/Lc/LcDatabase_hg38/GATK_resources/resources_broad_hg38_v0_Mills_and_1000G_gold_standard.indels.hg38.vcf.gz"
Phase1_1000G="/home/administrator/Lc/LcDatabase_hg38/GATK_resources/resources_broad_hg38_v0_1000G_phase1.snps.high_confidence.hg38.vcf.gz"
Known_Indels="/home/administrator/Lc/LcDatabase_hg38/GATK_resources/resources_broad_hg38_v0_Homo_sapiens_assembly38.known_indels.vcf.gz"
DBSNP_138="/home/administrator/Lc/LcDatabase_hg38/GATK_resources/resources_broad_hg38_v0_Homo_sapiens_assembly38.dbsnp138.vcf"
GNOMAD_VCF="emtpy"
# Downstream analysis
INTERVARDB="/home/administrator/Lc/LcDatabase_hg38/intervar"
HUMANDB="/home/administrator/Lc/LcDatabase_hg38/humandb_hg38"
FREEBAYES_REGIONS="emtpy"
# Computation
THREADS=28

# Function to process a single sample
process_sample() {
	local sample=$1
	local fastq1=$2
	local fastq2=$3

#-------------------------- Filtering & Alignment ---------------------------#

# Trimming first 5bp (MAX protocol)
conda run -n FASTP fastp -i ${sample}_1.fq.gz -I ${sample}_2.fq.gz \
	-o ${sample}_trimmed_1.fq.gz -O ${sample}_trimmed_2.fq.gz \
	-f 5 -F 5 \
	-w $THREADS -V \
	-h ${sample}_trim_report.html

# Trimming automated
conda run -n FASTP fastp -i ${sample}_1.fq.gz -I ${sample}_2.fq.gz \
	-o ${sample}_trimmed_1.fq.gz -O ${sample}_trimmed_2.fq.gz \
	-w $THREADS -V \
	-h ${sample}_trim_report.html

mkdir trimmed
mv ${sample}_trimmed* trimmed

# Alignment
bwa-mem2 mem -R "@RG\tID:${sample}\tLB:exome_lib\tPL:MGISEQ\tPU:unit1\tSM:${sample}" -t $THREADS \
	$REF_GENOME \
	trimmed/${sample}_trimmed_1.fq.gz \
	trimmed/${sample}_trimmed_2.fq.gz | samtools view -@ $THREADS -bS | samtools sort -@ $THREADS -o ${sample}_aligned_rg.bam

# Mark Duplicates
gatk MarkDuplicates \
	-I ${sample}_aligned_rg.bam \
	-O ${sample}_aligned_marked.bam \
	-M ${sample}_output.metrics.txt \
	--ASSUME_SORT_ORDER coordinate \
	--CREATE_INDEX true \
	--OPTICAL_DUPLICATE_PIXEL_DISTANCE 2500

rm ${sample}_aligned_rg.bam*

# Base Quality Score Recalibration
gatk BaseRecalibrator \
	--java-options "-Xmx48G -XX:+UseParallelGC -XX:ParallelGCThreads=$THREADS" \
	-R $REF_GENOME_FA \
	-I ${sample}_aligned_marked.bam \
	--known-sites $DBSNP_138 \
	--known-sites $Mills_1000G \
	--known-sites $Phase1_1000G \
	--known-sites $Known_Indels \
	-L $TARGETS \
	-O ${sample}_recal_data.table

# Apply BQSR
gatk ApplyBQSR \
	--java-options "-Xmx48G -XX:+UseParallelGC -XX:ParallelGCThreads=$THREADS" \
	-R $REF_GENOME_FA \
	-I ${sample}_aligned_marked.bam \
	--bqsr-recal-file ${sample}_recal_data.table \
	-O ${sample}_aligned_marked_bqsr.bam

rm ${sample}_aligned_marked.bam*

#-------------------------- GATK Variant Calling ---------------------------#

# Variant calling GATK
gatk HaplotypeCaller \
	-R $REF_GENOME_FA \
	-I ${sample}_aligned_marked_bqsr.bam \
	-O ${sample}_variants.vcf.gz \
	-L $TARGETS \
	--native-pair-hmm-threads $THREADS

gatk VariantFiltration \
	-V ${sample}_variants.vcf.gz \
	-O ${sample}_variants.filtered.vcf.gz \
	--filter-name "FAIL" --filter-expression "QUAL < 100.0 || vc.getGenotype(0).getDP() < 8" \
	--filter-name "LowQual" --filter-expression "QUAL < 30.0"

mkdir tmp
mv ${sample}_variants.vcf.gz* tmp/

# Spilit mulitallelic sites / Normalize
bcftools norm --threads $THREADS -f $REF_GENOME_FA -m "-any" ${sample}_variants.filtered.vcf.gz | \
vt normalize - -n -r $REF_GENOME_FA | \
bgzip -@ $THREADS -c > ${sample}_GATK.filtered.norm.vcf.gz  && \
tabix ${sample}_GATK.filtered.norm.vcf.gz

mv ${sample}_variants.filtered.vcf.gz* tmp/

# Filter only pass
bcftools view -f PASS ${sample}_GATK.filtered.norm.vcf.gz -o ${sample}_GATK.filtered.norm.pass.vcf

mv ${sample}_GATK.filtered.norm.vcf.gz* tmp/

#-------------------------- GATK Variant Annoation ---------------------------#

# Annotate with SnpEff
java -jar $SNPEFF_JAR ann -v hg38 -lof -hgvs -canon ${sample}_GATK.filtered.norm.pass.vcf | \
bcftools view --threads $THREADS -Oz -o ${sample}_GATK.filtered.norm.snpeff.vcf

bgzip ${sample}_GATK.filtered.norm.snpeff.vcf
bcftools index ${sample}_GATK.filtered.norm.snpeff.vcf.gz

mv ${sample}_GATK.filtered.norm.pass.vcf tmp/

# Annotate with Clinvar
bcftools annotate --threads $THREADS -a $CLINVAR_VCF \
	-c CLNHGVS,CLNSIGCONF,ALLELEID,RS \
	-o ${sample}_GATK.vcf ${sample}_GATK.filtered.norm.snpeff.vcf.gz

mv ${sample}_GATK.filtered.norm.snpeff.vcf.gz* tmp/

# Link to Annovar scripts
ln -s /home/administrator/Lc/Annovar/annovar/*.pl .

# Convert to avinput
perl convert2annovar.pl --format vcf4 \
	--includeinfo \
	--allsample \
	--withfreq \
	${sample}_GATK.vcf > ${sample}_GATK.avinput

mv ${sample}_GATK.vcf tmp/

# Intervar/Annovar annotation
Intervar.py -b hg38 \
	-i ${sample}_GATK.avinput --input_type=AVinput \
	-o ${sample}_GATK.intervar \
	-t $INTERVARDB \
	-d $HUMANDB

#-------------------------- GATK Variants Processing ---------------------------#

# Convert 1->chr1 in intervar output file
python LcConv.py ${sample}_GATK.intervar.hg38_multianno.txt.intervar ${sample}_GATK.intervar.hg38_multianno.txt.chr.intervar

mv ${sample}_GATK.intervar.hg38_multianno.txt.intervar tmp/
mv ${sample}_GATK.intervar.hg38_multianno.txt.grl_p tmp/
mv ${sample}_GATK.avinput tmp/
mv ${sample}_GATK.intervar.hg38_multianno.txt tmp/

# Extract vcf headers
bcftools view -h tmp/${sample}_GATK.vcf > ${sample}_header.tmp

# Add INFO fields to vcf headers
awk '
/^##INFO/ && !added_info {
	print;
	print "##INFO=<ID=AVINPUTCHR,Number=1,Type=String,Description=\"Original ANNOVAR input chromosome\">";
	print "##INFO=<ID=AVINPUTSTART,Number=1,Type=Integer,Description=\"Original ANNOVAR input start position\">";
	print "##INFO=<ID=AVINPUTEND,Number=1,Type=Integer,Description=\"Original ANNOVAR input end position\">";
	print "##INFO=<ID=AVINPUTREF,Number=1,Type=String,Description=\"Original ANNOVAR input reference allele\">";
	print "##INFO=<ID=AVINPUTALT,Number=1,Type=String,Description=\"Original ANNOVAR input alternate allele\">";
	added_info=1;
	next;
}
{ print }
' ${sample}_header.tmp > ${sample}_header.txt
rm ${sample}_header.tmp

# Convert avinput to vcf
awk '{print $9 "\t" $10 "\t" $11 "\t" $12 "\t" $13 "\t" $7 "\t" $15 "\t" $16 ";" "AVINPUTCHR=" $1 ";" "AVINPUTSTART=" $2 ";" "AVINPUTEND=" $3 ";" "AVINPUTREF=" $4 ";" "AVINPUTALT=" $5 ";" "\t" $17 "\t" $18}' tmp/${sample}_GATK.avinput > ${sample}_GATK.avinput.tmp

# Merge vcf headers to avinput (converted2vcf)
cat ${sample}_header.txt ${sample}_GATK.avinput.tmp > ${sample}_GATK.avinput.vcf
mv ${sample}_GATK.avinput.tmp tmp/
mv ${sample}_header.txt tmp/

# Snisift Info Extraction
conda run -n SNPSIFT SnpSift extractFields ${sample}_GATK.avinput.vcf CHROM POS REF ALT "ANN[0].GENE" "ANN[0].FEATUREID" "ANN[0].HGVS_P" "ANN[0].HGVS_C" "ANN[0].EFFECT" "ANN[0].IMPACT" "ANN[0].RANK" DP AF "GEN[0].AD" CLNHGVS CLNSIGCONF ALLELEID FILTER RS AVINPUTSTART AVINPUTEND AVINPUTREF AVINPUTALT >  ${sample}_GATK.snpsift.tmp

# Re-order with avinput coordinates
awk -F'\t' '{print $1 "\t" $20 "\t" $21 "\t" $22 "\t" $23 "\t" $5 "\t" $6 "\t" $7 "\t" $8 "\t" $9 "\t" $10 "\t" $11 "\t" $12 "\t" $13 "\t" $14 "\t" $15 "\t" $16 "\t" $17 "\t" $18 "\t" $19}' ${sample}_GATK.snpsift.tmp > ${sample}_GATK.snpsift.tsv

mv ${sample}_GATK.snpsift.tmp tmp/
mv ${sample}_GATK.avinput.vcf tmp/

# Merge Snpsift & Intervar
python LcMrg.py ${sample}_GATK.intervar.hg38_multianno.txt.chr.intervar ${sample}_GATK.snpsift.tsv ${sample}_GATK_merged.tsv ${sample}_GATK.unmatched.tsv

# Split Intervar Column to ACMG & ACMG Rules
python LcSplit.py ${sample}_GATK_merged.tsv ${sample}_GATK_merged_split.tsv

mv ${sample}_GATK.unmatched.tsv tmp/
mv ${sample}_GATK.intervar.hg38_multianno.txt.chr.intervar tmp/
mv ${sample}_GATK_merged.tsv tmp/
mv ${sample}_GATK.snpsift.tsv tmp/
mv ${sample}_GATK.filtered.norm.snpeff.vcf.gz tmp/

#-------------------------- MAGI ACMG Implementation & Prioritization ---------------------------#

# Implement MAGI Vus sub classification
python LcMagi.py ${sample}_GATK_merged_split.tsv ${sample}_GATK_magi.tsv


# Prioritize Variants
python LcPrio.py ${sample}_GATK_magi.tsv ${sample}_GATK_prioritized.tsv

#-------------------------- Process File for HTML ---------------------------#

# Create new info columns
python LcPrehtml.py ${sample}_GATK_prioritized.tsv ${sample}_GATK_prehtml.tsv

mv ${sample}_GATK_merged_split.tsv tmp/
mv ${sample}_GATK_magi.tsv tmp/
mv ${sample}_GATK_prioritized.tsv tmp/
mv ${sample}_variants.prioritized.magi_VUS_summary.tsv tmp/

#-------------------------- Extract QC ---------------------------#

bash LcQc.py

#-------------------------- IGV report ---------------------------#

# Create bed file (top 500)
cut -f 1,2,3,10 ${sample}_GATK_prehtml.tsv | head -n 500 > ${sample}_GATK_prehtml.bed

create_report ${sample}_GATK_prehtml.bed \
	--fasta $REF_GENOME_FA \
	--flanking 1000 \
	--tracks ${sample}_aligned_marked_bqsr.bam \
	--output ${sample}.IGV.html

#-------------------------- HTML Report ---------------------------#

python LcHtml.py ${sample}_GATK_prehtml.tsv ${sample}.html ${sample}_coverage_metrics.txt

}

# Main script
for fastq1 in $FASTQ_DIR/*_1.fq.gz; do
	fastq2="${fastq1/_1.fq.gz/_2.fq.gz}"
	if [ -f "$fastq2" ]; then
		sample=$(basename "$fastq1" | sed 's/_1.fq.gz//')
		process_sample "$sample" "$fastq1" "$fastq2"
	else
		echo "Warning: No matching read 2 file found for $fastq1"
	fi
done
