"""
                          PUBLIC DOMAIN NOTICE
             National Center for Biotechnology Information

This software is a "United States Government Work" under the
terms of the United States Copyright Act.  It was written as part of
the authors' official duties as United States Government employees and
thus cannot be copyrighted.  This software is freely available
to the public for use.  The National Library of Medicine and the U.S.
Government have not placed any restriction on its use or reproduction.

Although all reasonable efforts have been taken to ensure the accuracy
and reliability of the software and data, the NLM and the U.S.
Government do not and cannot warrant the performance or results that
may be obtained by using this software or data.  The NLM and the U.S.
Government disclaim all warranties, express or implied, including
warranties of performance, merchantability or fitness for any particular
purpose.

Please cite NCBI in any work or product based on this material.

"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import urllib.parse
import atexit
import time
import platform
import shutil
import json

CONTAINER = "run_gx"
DEFAULT_CONTAINER_DB = "/app/db/gxdb/"
DEFAULT_VERSION = "0.5.0"
DEFAULT_DOCKER_IMAGE = f"ncbi/fcs-gx:{DEFAULT_VERSION}"
GX_BIN_DIR = Path("/app/bin")

start_time = time.time()

# data that will be reported back to NCBI at the end of execution.


class GlobalStat:
    opt_in = False
    mode = ""
    exit_status = 1
    ncbi_op = ""
    container_engine = ""
    gxdb = ""
    gx_db_path = ""


@atexit.register
def report_to_ncbi_stat():
    if not GlobalStat.opt_in:
        return
    url = "https://www.ncbi.nlm.nih.gov/stat?"
    elapsed_time = round(time.time() - start_time)
    # required
    url_args = {"ncbi_app": "fcs"}
    url_args["ncbi_op"] = GlobalStat.ncbi_op
    # not required
    python_version = sys.version.split()[0]
    architecture = platform.platform()
    mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")  # e.g. 4015976448
    mem_gib = mem_bytes / (1024.0**3)  # e.g. 3.74
    url_args["ncbi_mem_gib"] = mem_gib
    url_args["ncbi_python_version"] = python_version
    url_args["ncbi_exit_status"] = GlobalStat.exit_status
    url_args["sgversion"] = DEFAULT_VERSION
    url_args["ncbi_architecture"] = architecture
    url_args["ncbi_duration"] = elapsed_time
    url_args["ncbi_mode"] = GlobalStat.mode
    url_args["ncbi_container_engine"] = GlobalStat.container_engine
    url_args["ncbi_gxdb"] = GlobalStat.gxdb
    url += urllib.parse.urlencode(url_args)

    try:
        with urllib.request.urlopen(url) as _:
            pass
    except Exception:  # pylint: disable=W0703, W0612
        pass


def find_argument(command, argument):
    """
    this method looks into the command input for the value of an
    argument and its position

    example:
    find_argument("cmd -a A -b -c", "-a")  would produce ('A', 6)

    However, this method has its limitations. It assumes uniqueness of args
    it assumes that args-values are not named such that an argument's name
    is a part of another argument's name
    example:
     find_argument("cmd not-a -a A", "-a")  would produce ('-a', 9)
        which not desired

    Returns:  value (str)
              position (int)

    """
    arg_pos = command.find(argument + " ")
    # check that we have found it
    if arg_pos == -1:
        arg_pos = command.find(argument + "=")
        if arg_pos == -1:
            return None, None
    val = command[(arg_pos + len(argument)) :]
    string_size = len(val)
    a = 0
    while string_size > a and (val[a] == " " or val[a] == "="):
        a += 1
    if a == string_size:
        return None, None
    b = a
    while string_size > b and val[b] != " ":
        b += 1
    return val[a:b], arg_pos + len(argument)


class RunFCS:
    def __init__(self, parser):
        self.parser = parser
        self.args, self.extra_args = parser.parse_known_args()
        self.joined_extra_args = " ".join(self.extra_args)

        using_singularity = (
            self.args.docker_image.endswith(".sif")
            or self.args.docker_image.startswith("docker://")
            and shutil.which("singularity")
        )
        GlobalStat.container_engine = "singularity" if using_singularity else "docker"
        self.mount_arg = (
            "-v"
            if GlobalStat.container_engine == "docker"
            else "--bind"
            if GlobalStat.container_engine == "singularity"
            else ""
        )
        self.directory_volume_map = {}

    def substitute_file_argument(self, cmd, argument, pos, volume, create_dir=False):
        self.directory_volume_map[volume] = Path(os.path.abspath(os.path.dirname(argument)))
        file_name = os.path.basename(argument)
        replacement = str(Path(volume) / file_name)
        if create_dir:
            os.makedirs(self.directory_volume_map[volume], exist_ok=True)
        return cmd[:pos] + cmd[pos:].replace(argument, replacement, 1)

    def substitute_directory_argument(self, cmd, argument, pos, volume, create_dir=False):
        self.directory_volume_map[volume] = Path(os.path.realpath(argument))
        if create_dir:
            os.makedirs(self.directory_volume_map[volume], exist_ok=True)
        return cmd[:pos] + cmd[pos:].replace(argument, volume, 1)

    def safe_exec(self, args):
        if self.args.debug:
            print("safe_exec: ", " ".join(args))
        if not self.args.dry_run:
            subprocess.run(args, shell=False, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)

    def make_dirs(self, path, exist_ok):
        if self.args.debug:
            print("make_dirs: ", path, exist_ok)
        if not self.args.dry_run:
            os.makedirs(path, exist_ok=exist_ok)

    def get_db_build_date(self):
        try:
            file_list = [f for f in os.listdir(GlobalStat.gx_db_path) if f.endswith(".meta.jsonl")]
            if file_list:
                with open(os.path.join(GlobalStat.gx_db_path, file_list[0])) as f:  # pylint: disable=W1514
                    file_content = json.load(f)
                    GlobalStat.gxdb = file_content["build-date"]
        except Exception as e:  # pylint: disable=W0703
            if self.args.debug:
                print(f"Failed to extract the database's build-date: {e}")

    def run_sync_files(self):
        extra_docker_arg = []

        if GlobalStat.container_engine == "docker":
            # GP-34570: -i to propagate keyboard-interrupt signals; -t to connect stdout.
            extra_docker_arg = ["-it", "--rm"]

        sync_files_args = [
            GlobalStat.container_engine,
            "run" if GlobalStat.container_engine == "docker" else "exec",
            *extra_docker_arg,
        ]

        for volume, path in self.directory_volume_map.items():
            sync_files_args += [self.mount_arg, str(path) + ":" + volume]

        sync_files_args += [
            self.args.docker_image,
            "python3",
            str(GX_BIN_DIR / "sync_files"),
            self.args.cmd,
        ] + self.joined_extra_args.split()

        self.safe_exec(sync_files_args)

        if GlobalStat.opt_in:
            self.get_db_build_date()

    def run_gx(self):
        docker_args = [
            GlobalStat.container_engine,
            "run" if GlobalStat.container_engine == "docker" else "exec",
        ]

        if self.args.env_file is not None:
            docker_args += ["--env-file", self.args.env_file]

        if GlobalStat.container_engine == "docker":
            docker_args += ["-i", "--rm"]

        for volume, path in self.directory_volume_map.items():
            docker_args += [self.mount_arg, str(path) + ":" + volume]

        if GlobalStat.mode == "screen":
            docker_args += [
                self.args.docker_image,
                "python3",
                str(GX_BIN_DIR / "run_gx"),
            ] + self.joined_extra_args.split()
        else:
            docker_args += [
                self.args.docker_image,
                str(GX_BIN_DIR / "gx"),
                "clean-genome",
            ] + self.joined_extra_args.split()

        self.safe_exec(docker_args)

        if GlobalStat.opt_in:
            self.get_db_build_date()

    def modify_screen_arguments(self):
        cmd = self.joined_extra_args
        argument, pos = find_argument(cmd, "--gx-db")
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, DEFAULT_CONTAINER_DB)
            GlobalStat.gx_db_path = Path(os.path.abspath(os.path.dirname(argument))) / os.path.basename(argument)

        argument, pos = find_argument(cmd, "--fasta")
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, "/sample-volume/")

        argument, pos = find_argument(cmd, "--out-dir")
        if argument is not None:
            cmd = self.substitute_directory_argument(cmd, argument, pos, "/output-volume/", True)
        elif "--help" not in cmd:
            self.directory_volume_map["/output-volume/"] = Path(os.path.realpath("."))
            cmd += " --out-dir=/output-volume/"

        self.joined_extra_args = cmd

    def modify_db_arguments(self):
        cmd = self.joined_extra_args
        argument, pos = find_argument(cmd, "--dir")
        if argument is not None:
            cmd = self.substitute_directory_argument(cmd, argument, pos, DEFAULT_CONTAINER_DB, True)
            GlobalStat.gx_db_path = Path(os.path.realpath(argument))
        elif "--help" not in cmd:
            print("Error: database path not specified")
            print('Please specify "--dir=path/to/db"')
            self.parser.print_usage()
            sys.exit()

        argument, pos = find_argument(cmd, "--mft")
        if argument is None and "--help" not in cmd:
            print("Error: database source is required")
            print('Please specify "--mft=url/or/path/to/db"')
            print("Please see https://github.com/ncbi/fcs/wiki/")
            self.parser.print_usage()
            sys.exit()
        elif argument is not None and Path(argument).exists():
            cmd = self.substitute_file_argument(cmd, argument, pos, "/mft-volume/")

        self.joined_extra_args = cmd

    def modify_clean_arguments(self):
        cmd = self.joined_extra_args
        argument, pos = find_argument(cmd, "--input")
        if argument is None:
            argument, pos = find_argument(cmd, "-i")
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, "/sample-volume/")

        argument, pos = find_argument(cmd, "--action-report")
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, "/report-volume/")
        elif "--help" not in cmd:
            print("Error: action report file is required")
            print('Please specify "--action-report=path/to/action-report-file"')
            sys.exit()

        argument, pos = find_argument(cmd, "--output")
        if argument is None:
            argument, pos = find_argument(cmd, "-o")
        # add arguments section
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, "/output-volume/", True)

        argument, pos = find_argument(cmd, "--contam-fasta-out")
        if argument is not None:
            cmd = self.substitute_file_argument(cmd, argument, pos, "/contam-out-volume/", True)

        self.joined_extra_args = cmd

    def run_screen_mode(self):
        GlobalStat.mode = "screen"
        self.modify_screen_arguments()
        if self.args.cmd == "genome":
            self.run_gx()
        elif self.args.cmd in ["adaptor", "all"]:
            print(f'"{self.args.cmd}" command not yet supported')
            self.parser.print_help()
        else:
            print("Error: Wrong command for screen mode")
            self.parser.print_help()

    def run_db_mode(self):
        GlobalStat.mode = "db"
        self.modify_db_arguments()
        if self.args.cmd in ["get", "check"]:
            self.run_sync_files()

    def run_clean_mode(self):
        GlobalStat.mode = "clean"
        self.modify_clean_arguments()
        if self.args.cmd in ["genome"]:
            self.run_gx()

    def run(self):
        if hasattr(self.args, "func"):
            self.args.func(self)
        else:
            self.parser.print_help()


def configure_parser(parser):
    parser.add_argument(
        "--image",
        dest="docker_image",
        default=os.getenv("FCS_DEFAULT_IMAGE", "ncbi/fcs-gx:latest"),
        help="Dockerhub registry path, or a filepath to Singularity .sif image. default=$FCS_DEFAULT_IMAGE",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode",
    )
    parser.add_argument(
        "--no-report-analytics",
        action="store_true",
        help="Do not send usage stats to NCBI. NCBI does not collect any personal information",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="file with environment variables",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="do not actually do anything",
    )
    return parser


def main() -> int:
    parser = argparse.ArgumentParser(
        description="test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,
    )
    parser = configure_parser(parser)
    _, args = parser.parse_known_args()
    num_of_unknown_args = len(args)

    parser = argparse.ArgumentParser(
        description="Run FCS Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=(len(sys.argv) <= 2),
    )
    parser = configure_parser(parser)

    subparsers = parser.add_subparsers(dest="mode")
    # screen
    parser_screen = subparsers.add_parser("screen", add_help=(num_of_unknown_args <= 2))
    parser_screen.add_argument(
        "cmd",
        choices=["genome", "adaptor", "all"],
    )
    parser_screen.set_defaults(func=RunFCS.run_screen_mode)
    # db
    parser_db = subparsers.add_parser("db", add_help=(num_of_unknown_args <= 2))
    parser_db.add_argument(
        "cmd",
        choices=["get", "check"],
    )
    parser_db.set_defaults(func=RunFCS.run_db_mode)
    # clean
    parser_clean = subparsers.add_parser("clean", add_help=(num_of_unknown_args <= 2))
    parser_clean.add_argument(
        "cmd",
        choices=["genome"],
    )
    parser_clean.set_defaults(func=RunFCS.run_clean_mode)

    args, extra_args = parser.parse_known_args()

    if len(sys.argv) <= 1:
        parser.print_usage()
        sys.exit()

    GlobalStat.opt_in = (not args.no_report_analytics) and ("--help" not in extra_args) and (not args.dry_run)
    if hasattr(args, "cmd"):
        GlobalStat.ncbi_op = args.cmd
    retcode = 0
    try:
        gx = RunFCS(parser)
        gx.run()
        GlobalStat.exit_status = 0
    except (RuntimeError, ValueError, KeyboardInterrupt) as exc:
        if args.debug:
            raise
        retcode = 1
        print(exc)
    return retcode


if __name__ == "__main__":
    sys.exit(main())
