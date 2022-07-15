import argparse
import os
from pathlib import Path
import subprocess
import sys

CONTAINER = "run_gx"
CONTAINER_DB = Path("/app/db/gxdb")
DEFAULT_DOCKER_IMAGE = "ncbi/cgr-fcs-genome:v1alpha1-latest"
GX_BIN_DIR = Path("/app/bin")


class RunGX:
    """main run stuff"""

    def __init__(self, args):
        self.args = args

    def run_retrieve_db(self):
        expanded_gxdb = Path(os.path.realpath(os.path.dirname(self.args.gx_db)))
        gxdb_name = os.path.basename(self.args.gx_db)

        expanded_gxdb_disk = None
        if self.args.disk_index_path is not None:
            expanded_gxdb_disk = Path(os.path.realpath(self.args.disk_index_path))

        docker_image = self.args.docker_image
        container_engine = self.args.container_engine
        subprocess.run(
            [container_engine, "pull", docker_image],
            shell=False,
            check=True,
        )

        extra_docker_args = []
        extra_db_args = []
        if expanded_gxdb_disk is not None:
            extra_docker_args = ["-v", str(expanded_gxdb_disk) + ":/db-disk-volume/"]
            extra_db_args = ["--gx-db-disk", "/db-disk-volume/"]

        retrieve_db_args = [
            container_engine,
            "run",
            "--name",
            "retrieve_db",
            "-v",
            str(expanded_gxdb) + ":" + str(CONTAINER_DB),
            *extra_docker_args,
            docker_image,
            "python3",
            str(GX_BIN_DIR / "retrieve_db"),
            "--gx-db",
            str(CONTAINER_DB / gxdb_name),
            *extra_db_args,
        ]
        subprocess.run(
            retrieve_db_args,
            shell=False,
            check=True,
        )
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

        subprocess.run([container_engine, "pull", docker_image], shell=False, check=True)
        docker_args = [
            container_engine,
            "run",
            "--name",
            CONTAINER,
            "-v",
            str(expanded_gxdb) + ":" + str(CONTAINER_DB),
            "-v",
            str(fasta_path) + ":" + str(Path("/sample-volume/")),
            "-v",
            str(expanded_output) + ":" + str(Path("/output-volume/")),
            docker_image,
            "python3",
            str(GX_BIN_DIR / "run_gx"),
            "--fasta",
            str(Path("/sample-volume/") / fasta_name),
            "--out-dir",
            str(Path("/output-volume/")),
            "--gx-db",
            str(CONTAINER_DB / gxdb_name),
            "--tax-id",
            str(self.args.tax_id),
            "--blast-div",
            self.args.blast_div,
            "--debug",
        ]
        if self.args.out_basename:
            docker_args.extend(["--out-basename", self.args.out_basename])
        if self.args.split_fasta:
            docker_args.extend(["--split-fasta"])
        print(docker_args)
        subprocess.run(docker_args, shell=False, check=True)

        subprocess.run([container_engine, "container", "rm", CONTAINER], shell=False, check=True)

    def run(self):
        self.run_retrieve_db()
        self.run_gx()


def main() -> int:
    parser = argparse.ArgumentParser(description="run fcsgenome docker image")
    parser.add_argument(
        "--fasta",
        required=True,
        help="input fasta file path",
    )
    parser.add_argument(
        "--out-dir",
        metavar="path",
        default=".",
        help="output directory default .",
    )
    parser.add_argument(
        "--gx-db",
        required=True,
        default=os.getenv("GX_DB_DIR"),
        help="required: path to the gx database. env GX_DB_DIR",
    )
    parser.add_argument(
        "--gx-db-disk",
        dest="disk_index_path",
        default=None,
        help="if storing the database in shared memory, keep a copy of the files in this path",
    )
    parser.add_argument(
        "--out-basename",
        help="output filename will be {out-basename}.{tax-id}.rpt",
    )
    parser.add_argument(
        "--split-fasta",
        action="store_true",
        help="use this to split fasta, default off",
    )
    parser.add_argument(
        "--tax-id",
        default="",
        type=int,
        help="taxid of input fasta",
    )
    parser.add_argument(
        "--blast-div",
        default="",
        help="input blast-div of the tax-id, from 'NCBI BLAST name' on taxon Info page.",
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
        "--debug",
        action="store_true",
        help="Debug mode",
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
