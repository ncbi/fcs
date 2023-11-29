#!/bin/bash

SCRIPT_NAME=$0
DEFAULT_VERSION="0.5.0"
DOCKER_IMAGE=ncbi/fcs-adaptor:${DEFAULT_VERSION}
SINGULARITY_IMAGE=""
CONTAINER_ENGINE="docker"

usage()
{
cat <<EOF
Usage:
    $SCRIPT_NAME [options]

Options:

    --help
    --fasta-input <file>          input FASTA file (required)
    --output-dir <directory>      output path (required)
    --image <file>                dockerhub address or sif file (required for singularity only)
    --container-engine <string>   default docker

    Taxonomy (exactly one required):
    --prok                        prokaryotes
    --euk                         eukaryotes

EOF
    exit $1
}

DOCKER=docker

while [[ $# -gt 0 ]]
do
  case $1 in
    -h|--help)
      echo "usage: "
      usage 0
      ;;
    --fasta-input)
      FASTA_INPUT="$2"
      shift # past argument
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift
      ;;
    --image)
      DOCKER_IMAGE="$2"
      SINGULARITY_IMAGE="$2"
      shift
      ;;
    --euk)
      TAX=--euk
      ;;
    --prok)
      TAX=--prok
      ;;
    --container-engine)
        CONTAINER_ENGINE=$2
        shift
        ;;
    -*)
      echo "invalid option : '$1'"
      usage 10
      ;;
    *)
      echo "$SCRIPT_NAME does not accept any positional arguments"
      echo "$@"
      usage 10
      ;;
  esac
  shift
done

if [[ -z $TAX ]]
then
    printf -- "Error: Taxonomy must be specified using --euk or --prok\n"
    usage 10
fi

# get full path and expand symlinks
EXPANDED_FASTA=$(readlink -e $FASTA_INPUT)
if [[ $? != 0 ]] ; then
  echo "Error: File not found $FASTA_INPUT"; exit 1;
fi

EXPANDED_OUTPUT=$(readlink -e $OUTPUT_DIR)
if [[ $? != 0 ]] ; then
  echo "Error: File not found $OUTPUT_DIR"; exit 1;
fi


FASTA_DIRNAME=$(dirname "$EXPANDED_FASTA")
FASTA_FILENAME=$(basename "$EXPANDED_FASTA")

# this only needs set one time, but gives a misleading error message if not done
#gcloud auth configure-docker us-east4-docker.pkg.dev

if [[ ${CONTAINER_ENGINE} == "docker" ]]
then
  $DOCKER pull $DOCKER_IMAGE
  CONTAINER=run_av_screen_x

  function finish {
    $DOCKER stop $CONTAINER
    $DOCKER rm $CONTAINER
  }
  trap finish EXIT

  $DOCKER run --init --name $CONTAINER --user "$(id -u):$(id -g)" -v $FASTA_DIRNAME:/sample-volume/ \
      -v $EXPANDED_OUTPUT:/output-volume/ $DOCKER_IMAGE \
      /app/fcs/bin/av_screen_x -o /output-volume/ $TAX /sample-volume/$FASTA_FILENAME

elif [[ ${CONTAINER_ENGINE} == "singularity" ]]
then
  if [[ -n "$SINGULARITY_IMAGE" ]]
  then
    singularity run $CONTAINER --bind $FASTA_DIRNAME:/sample-volume/ \
        --bind $EXPANDED_OUTPUT:/output-volume/ $SINGULARITY_IMAGE \
        /app/fcs/bin/av_screen_x -o /output-volume/ $TAX /sample-volume/$FASTA_FILENAME
  else
    echo "--image is required when specifying --container-engine singularity"
  fi
else
    echo "No container engine ${CONTAINER_ENGINE}"
fi
