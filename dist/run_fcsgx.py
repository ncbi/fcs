import argparse
import os
from pathlib import Path
import subprocess
import sys
import ssl
import urllib.request

# import json
import hashlib


CONTAINER = "run_gx"
DEFAULT_CONTAINER_DB = "/app/db/gxdb"
DEFAULT_VERSION = "0.2.2"
DEFAULT_DOCKER_IMAGE = f"ncbi/fcs-gx:{DEFAULT_VERSION}"
DEFAULT_SINGULARITY_IMAGE = f"fcs-gx.{DEFAULT_VERSION}.sif"
# FILE_MANIFEST = "sing-image.manifest"
SINGULARITY_FTP_SITE = f"https://ftp.ncbi.nlm.nih.gov/genomes/TOOLS/FCS/releases/{DEFAULT_VERSION}"
GX_BIN_DIR = Path("/app/bin")


# from retrieve_db.py
def compute_md5hash_by_chunk(filename):
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
    return file_hash.hexdigest()


class RunGX:
    """main run stuff"""

    def __init__(self, args):
        self.args = args
        self.args.container_db = Path(args.container_db)

    def retrieve_singularity_image(self, local_filename):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ftp_loc = os.path.join(SINGULARITY_FTP_SITE, DEFAULT_SINGULARITY_IMAGE)
        with urllib.request.urlopen(ftp_loc, context=ctx) as mr:
            if mr.status != 200:
                raise RuntimeError("Error retrieving singularity image")
            content = mr.read()
            # md5hash = compute_md5hash_by_chunk(content)
            # Save to file
            with open(local_filename, "wb") as download:
                download.write(content)
        # ftp_loc = os.path.join(SINGULARITY_FTP_SITE, FILE_MANIFEST)
        # with urllib.request.urlopen(ftp_loc, context=ctx) as fm:
        #    if fm.status != 200:
        #        raise RuntimeError("Error retrieving file manifest")
        #    data = json.load(fm)
        #    for file_detail in data["fileDetails"]:
        #        if file_detail["fileName"] == DEFAULT_SINGULARITY_IMAGE:
        #            if file_detail["hashValue"] == md5hash:
        #                print("file checksums verified to be correct")
        #                return local_filename
        #            else:
        #                ValueError("checksum verification failed")
        # print(f"checksum for file {DEFAULT_SINGULARITY_IMAGE} not found in file manifest")
        return local_filename

    def run_retrieve_db(self):
        expanded_gxdb = Path(os.path.realpath(os.path.dirname(self.args.gx_db)))
        gxdb_name = os.path.basename(self.args.gx_db)

        expanded_gxdb_disk = None
        if self.args.disk_index_path:
            expanded_gxdb_disk = Path(os.path.realpath(self.args.disk_index_path))

        docker_image = self.args.docker_image
        container_engine = self.args.container_engine
        if container_engine == "docker":
            subprocess.run(
                [container_engine, "pull", docker_image],
                shell=False,
                check=True,
            )
        elif container_engine == "singularity":
            if docker_image == os.getenv("GX_DOCKER_IMAGE", default=DEFAULT_DOCKER_IMAGE):
                # image not specified -->> download from the ftp site
                docker_image = self.retrieve_singularity_image(DEFAULT_SINGULARITY_IMAGE)

        mount_arg = ""
        if container_engine == "docker":
            mount_arg = "-v"
        elif container_engine == "singularity":
            mount_arg = "--bind"

        extra_docker_args = []
        extra_db_args = []
        if expanded_gxdb_disk is not None:
            extra_docker_args = [mount_arg, str(expanded_gxdb_disk) + ":/db-disk-volume/"]
            extra_db_args = ["--gx-db-disk", "/db-disk-volume/"]

        name_args = []
        if container_engine == "docker":
            name_args = ["--name", "retrieve_db"]

        retrieve_db_args = [
            container_engine,
            "run",
            *name_args,
            mount_arg,
            str(expanded_gxdb) + ":" + str(self.args.container_db),
            *extra_docker_args,
            docker_image,
            "python3",
            str(GX_BIN_DIR / "retrieve_db"),
            "--gx-db",
            str(self.args.container_db / gxdb_name),
            *extra_db_args,
        ]
        subprocess.run(
            retrieve_db_args,
            shell=False,
            check=True,
        )
        if container_engine == "docker":
            subprocess.run([container_engine, "container", "rm", "retrieve_db"], shell=False, check=True)

    def run_gx(self):
        expanded_gxdb = Path(os.path.realpath(os.path.dirname(self.args.gx_db)))
        gxdb_name = os.path.basename(self.args.gx_db)

        expanded_fasta = Path(os.path.realpath(self.args.fasta))
        fasta_path = expanded_fasta.parent
        fasta_name = expanded_fasta.name

        expanded_output = Path(os.path.realpath(self.args.out_dir))
        container_engine = self.args.container_engine
        docker_image = self.args.docker_image

        if container_engine == "docker":
            subprocess.run([container_engine, "pull", docker_image], shell=False, check=True)

        name_args = []
        if container_engine == "docker":
            name_args = ["--name", CONTAINER]

        mount_arg = ""
        if container_engine == "docker":
            mount_arg = "-v"
        elif container_engine == "singularity":
            mount_arg = "--bind"

        docker_args = [
            container_engine,
            "run",
            *name_args,
            mount_arg,
            str(expanded_gxdb) + ":" + str(self.args.container_db),
            mount_arg,
            str(fasta_path) + ":" + str(Path("/sample-volume/")),
            mount_arg,
            str(expanded_output) + ":" + str(Path("/output-volume/")),
            docker_image,
            "python3",
            str(GX_BIN_DIR / "run_gx"),
            "--fasta",
            str(Path("/sample-volume/") / fasta_name),
            "--out-dir",
            str(Path("/output-volume/")),
            "--gx-db",
            str(self.args.container_db / gxdb_name),
            "--tax-id",
            str(self.args.tax_id),
            "--split-fasta=" + ("T" if self.args.split_fasta else "F"),
        ]
        if self.args.out_basename:
            docker_args.extend(["--out-basename", self.args.out_basename])
        if self.args.blast_div:
            docker_args.extend(["--div", self.args.blast_div])
        if self.args.allow_same_species:
            docker_args.extend(["--allow-same-species", self.args.allow_same_species])

        print(docker_args)
        subprocess.run(docker_args, shell=False, check=True)

        if container_engine == "docker":
            subprocess.run([container_engine, "container", "rm", CONTAINER], shell=False, check=True)

    def run_verify_checksums(self):
        expanded_gxdb = Path(os.path.realpath(os.path.dirname(self.args.gx_db)))
        gxdb_name = os.path.basename(self.args.gx_db)

        container_engine = self.args.container_engine
        docker_image = self.args.docker_image

        if container_engine == "docker":
            subprocess.run([container_engine, "pull", docker_image], shell=False, check=True)

        mount_arg = ""
        if container_engine == "docker":
            mount_arg = "-v"
        elif container_engine == "singularity":
            mount_arg = "--bind"

        name_args = []
        if container_engine == "docker":
            name_args = ["--name", "verify_checksums"]

        docker_args = [
            container_engine,
            "run",
            *name_args,
            mount_arg,
            str(expanded_gxdb) + ":" + str(self.args.container_db),
            docker_image,
            "python3",
            str(GX_BIN_DIR / "verify_checksums"),
            "--gx-db",
            str(self.args.container_db / gxdb_name),
            "--debug",
        ]
        print(docker_args)
        subprocess.run(docker_args, shell=False, check=True)

        if container_engine == "docker":
            subprocess.run([container_engine, "container", "rm", "verify_checksums"], shell=False, check=True)

    def run(self):
        self.run_retrieve_db()
        if self.args.fasta:
            self.run_gx()
        if self.args.verify_checksums:
            self.run_verify_checksums()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run fcsgenome Docker image",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--fasta",
        # required=True,
        help="input fasta file path",
    )
    parser.add_argument(
        "--out-dir",
        metavar="path",
        default=".",
        help="output directory",
    )
    parser.add_argument(
        "--gx-db",
        required=True,
        default=os.getenv("GX_DB_DIR"),
        help="path to the gx database. env GX_DB_DIR",
    )
    parser.add_argument(
        "--gx-db-disk",
        dest="disk_index_path",
        default=None,
        help="if storing the database in shared memory, keep a copy of the files in this path",
    )
    parser.add_argument(
        "--out-basename",
        default=None,
        help="output filename will be {out-basename}.{tax-id}.rpt",
    )
    parser.add_argument(
        "--split-fasta",
        action="store_true",
        help="use this to split fasta, default off",
    )
    parser.add_argument(
        "--tax-id",
        required=True,
        type=int,
        help="taxid of input fasta",
    )
    parser.add_argument(
        "--blast-div",
        default=None,
        help="input blast-div of the tax-id, from 'NCBI BLAST name' on taxon Info page.",
    )
    parser.add_argument(
        "--allow-same-species",
        default=None,
        help="Whether to use same-species hits as evidence",
    )
    parser.add_argument(
        "--container-engine",
        default=os.getenv("GX_CONTAINER_ENGINE", default="docker"),
        help="specify container engine default 'docker' env GX_CONTAINER_ENGINE",
    )
    parser.add_argument(
        "--image",
        dest="docker_image",
        default=os.getenv("GX_DOCKER_IMAGE", default=DEFAULT_DOCKER_IMAGE),
        help=f"the location of the image. default {DEFAULT_DOCKER_IMAGE} env GX_DOCKER_IMAGE",
    )
    parser.add_argument(
        "--container-db",
        default=Path(os.getenv("GX_CONTAINER_DB", default=DEFAULT_CONTAINER_DB)),
        help=f"internal location of shared mem db. default {DEFAULT_CONTAINER_DB} env GX_CONTAINER_DB",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="database file's checksum will be verified",
    )
    args = parser.parse_args()
    retcode = 0
    try:
        gx = RunGX(args)
        gx.run()
    except (RuntimeError, ValueError, KeyboardInterrupt) as exc:
        if args.debug:
            raise
        retcode = 1
        print(exc)
    return retcode


if __name__ == "__main__":
    sys.exit(main())
