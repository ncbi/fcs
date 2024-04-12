# Privacy 

## Privacy Statement
We collect limited usage data for each run of FCS. The information collected helps us determine how FCS is being used in the scientific community. The reports help us to support FCS development, so we encourage users to report usage when possible. Additional privacy and security policy information can be found on the [NLM Web Policies](https://www.nlm.nih.gov/web_policies.html). page. 
The following is the usage data that is currently collected:

| Reported parameter | Description |
| ----------- | ----------- |
| IP      | The apparent IP address of the machine running FCS |
| ncbi_architecture   | Host operating system      |
| ncbi_container_engine | FCS container used (docker, singularity) | 
| ncbi_duration | Duration of the application running time | 
| ncbi_exit_status | Exit Status | 
| ncbi_gxdb | FCS-GX database version |
| ncbi_mem_gib | Host memory (GiB) | 
| ncbi_mode   | FCS run mode (db, screen, clean)      |
| ncbi_op   | FCS run operation (genome, get, check, all)        |
| ncbi_python_version   | Host Python version    |
| sgversion   | FCS software version    |

## Opt out of usage reporting
You can disable usage reporting by setting the `--no-report-analytics` parameter for the FCS-GX `fcs.py` runner script.
