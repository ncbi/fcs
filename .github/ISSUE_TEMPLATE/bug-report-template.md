---
name: Bug Report Template
about: Create a report to help us improve
title: "[BUG]: <title>"
labels: ''
assignees: ''

---

*Describe the bug*
A clear and concise description of what the bug is.

*To Reproduce*
Copy the full ``run_fcsadaptor.sh``/``fcs.py`` command used.

If you are having trouble with your genome, please ensure that you can run the pipeline with one of our test genomes first. If your installation works fine with the sample input, please tell us if you are willing and able to share your genome with us, if asked.

*Software versions (please complete the following information):*
 - OS [e.g. CentOS 7, macOS , etc.].
 - Cloud Platform VM [e.g. AWS , GCP], if applicable.  
 - Docker or Singularity version [``docker --version``]/[``singularity --version``].
 - Docker or Singularity FCS image version [``docker image ls``].
 - Python version if using FCS-GX [``python --version``].

*Log Files*
Please rerun with the ``--debug`` flag and attach an archive (e.g. zip or tarball) of the logs in the directory [``debug/tmp-outdir*.log``] for FCS-adaptor or the saved log file [``run_gx.py ... > GX.log 2>&1``] for FCS-GX.

*Additional context*
Add any other context about the problem here.
