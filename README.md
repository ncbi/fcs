# FCS

The NCBI Foreign Contamination Screen (FCS) is a tool suite for identifying and removing contaminant sequences in genome assemblies. Contaminants are defined as sequences in a dataset that do not originate from the biological source organism and can arise from a variety of environmental and laboratory sources. FCS will help you remove contaminants from genomes before submission to GenBank.

## FCS-adaptor
FCS-adaptor detects adaptor and vector contamination in genome sequences. FCS-adaptor is a high-throughput implementation of [NCBI VecScreen](https://www.ncbi.nlm.nih.gov/tools/vecscreen/about/). The FCS-adaptor executable retrieves a Docker or Singularity container and runs a pipeline to screen input sequences against a database of adaptors and vectors using stringent BLAST searches.

Please read the [wiki](https://github.com/ncbi/fcs/wiki/FCS-adaptor-quickstart) for instructions on how to run FCS-adaptor.

## FCS-GX
FCS-GX detects contamination from foreign organisms in genome sequences using the genome cross-species aligner (GX). The FCS-GX executable retrieves a Docker or Singularity container and runs a pipeline to align sequences to a large database of NCBI genomes through modified k-mer seeds and assign a most likely taxonomic division. FCS-GX classifies sequences as contaminant when their taxonomic assignment is different from the user-provided taxonomic identifier. 

Please read the [wiki](https://github.com/ncbi/fcs/wiki/FCS-GX-quickstart) for instructions on how to run FCS-GX.

## NEWS
:exclamation: FCS is live on on [Galaxy](https://usegalaxy.org/)! Tutorial [here](https://training.galaxyproject.org/training-material/topics/sequence-analysis/tutorials/ncbi-fcs/tutorial.html).

## REFERENCES

### FCS-GX
Astashyn A, Tvedte ES, Sweeney D, Sapojnikov V, Bouk N, Joukov V, Mozes E, Strope PK, Sylla PM, Wagner L, Bidwell SL, Brown LC, Clark K, Davis EW, Smith-White B, Hlavina W, Pruitt KD, Schneider VA, Murphy TD. Rapid and sensitive detection of genome contamination at scale with FCS-GX. Genome Biol. 2024 Feb 26;25(1):60. doi: 10.1186/s13059-024-03198-7. PMID: 38409096; PMCID: PMC10898089.

[Read the FCS-GX paper](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-024-03198-7)

## LICENSING
The NCBI FCS tool suite software authored by NCBI is a "United States
Government Work" under the terms of the United States Copyright
Act. It was written as part of the authors' official duties as United
States Government employees and thus cannot be copyrighted. This
software is freely available to the public for use. The National
Library of Medicine and the U.S. Government have not placed any
restriction on its use or reproduction.

Although all reasonable efforts have been taken to ensure the accuracy
and reliability of the software and data, the NLM and the
U.S. Government do not and cannot warrant the performance or results
that may be obtained by using this software or data. The NLM and the
U.S. Government disclaim all warranties, express or implied, including
warranties of performance, merchantability or fitness for any
particular purpose.

Please cite NCBI in any work or product based on this material.

## FUNDING
This work was supported by the National Center for Biotechnology Information of the National Library of Medicine (NLM), National Institutes of Health.

FCS is part of the [NIH Comparative Genomics Resource (CGR)](https://www.ncbi.nlm.nih.gov/comparative-genomics-resource/), an NLM project to establish an ecosystem to facilitate reliable comparative genomics analyses for all eukaryotic organisms.

