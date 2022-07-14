# FCS

The NCBI Foreign Contamination Screen (FCS) is a tool suite for identifying and removing contaminant sequences in genome assemblies. Contaminants are defined as sequences in a dataset that do not originate from the biological source organism and can arise from a variety of environmental and laboratory sources. FCS will help you remove contaminants from genomes before submission to GenBank.

## FCS-adaptor
FCS-adaptor detects adaptor and vector contamination in genome sequences. FCS-adaptor is a high-throughput implementation of NCBI VecScreen https://www.ncbi.nlm.nih.gov/tools/vecscreen/about/. The FCS-adaptor executable retrieves a Docker or Singularity container and runs a pipeline to screen input sequences against a non-redudant database of adaptors and vectors using stringent BLAST searches and remove contaminants from your genome.

FCS-adaptor removes terminal and internal matches to foreign sequences. Sequences identified as mostly adaptor/vector are removed entirely. FCS-adaptor produces a tabular output with details on the contaminant sequences identified as well as a cleaned FASTA.

Please read the [wiki](https://github.com/ncbi/fcs/wiki) for instructions on how to run FCS-adaptor.

## FCS-GX
FCS-GX detects contamination from foreign organisms in genome sequences using the GX (Genome Cross-species) aligner. The FCS-GX executable retrieves a Docker or Singularity container and runs a pipeline to align sequences to a large database of NCBI genomes through modified k-mer seeds and assign a most likely taxonomic division.

FCS-GX classifies sequences as contaminant when their taxonomic assignment is different from the user provided taxonomic identifier. A contamination summary provides an overview of observed contaminant divisions, counts, and total sizes, and an action report provides details and recommended actions for each problematic sequence. 

Please read the [wiki](https://github.com/ncbi/fcs/wiki) for instructions on how to run FCS-GX.