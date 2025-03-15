### modified `fcs.py` script with `--container_platform` option

Orginal `fcs.py` requires the singularity/apptainer container image to have the `.sif` file extension as 
it uses this particular file extension as the identifier for non-docker images. This modified version allows 
you to define the container platform of choice as an argument than rely on a particular file extension 

Also implementation allows for explicit control while maintaining backward compatibility with the existing detection method. 
The code also includes a basic check to ensure the specified container platform is actually available on the system.

### Summary : 
1. Added a new command-line argument --container_platform with choices "docker", "singularity", and "apptainer"
2. Modified the container engine detection logic to prioritize the explicitly specified platform
3. There is a  validation to check if the specified container engine is available in PATH
4. Updated the mount argument handling to support `apptainer` (treated like singularity)
5. Updated the help text for the `--image` parameter to be more generic
