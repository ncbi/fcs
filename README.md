## FCS-adaptor
Foreign contamination screening (FCS)-adaptor is a VecScreen-based program to detect adaptor contamination in genomic sequences. This tool is one module within a larger NCBI FCS program suite. Please read the [wiki](https://github.com/ncbi/fcs/wiki) for instructions on how to run FCS-adaptor.  
` `
## FCS-GX
Foreign contamination screening (FCS)-GX is a genome-level contamination detecting tool based on a cross-species alignment component called the GX aligner. FCS-GX is one module within a larger NCBI foreign contamination screening program suite.

To assign contaminants, FCS-GX requires an input assembly in FASTA format and a numeric NCBI taxonomic identifier (tax-id) corresponding to the source genome. The FCS-GX then aligns sequences to a large database of NCBI genomes through modified k-mer seeds, and resolves matches to alignments.

The GX aligner operates in two passes. In the first pass, GX retains identifiers from taxonomic groups with the highest scoring alignments and filters out lower scoring alignments. During this phase, GX also performs masking for both low-complexity and high-copy repeats. In the second pass, sequence alignments are refined and extended to produce final coverage and scoring metrics.

FCS-GX detects contaminant sequences when their taxonomic assignment is different from the user provided tax-id. A contamination summary report provides the counts and total sizes of contaminant regions. Results are also provided at the sequence-level for the inspection of FCS-GX assignments.

Please read the [wiki](https://github.com/ncbi/fcs/wiki) for instructions on how to run FCS-GX.
