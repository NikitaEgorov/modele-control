import copy
import os
import subprocess
import re
from ectl import pathutil,rundeck,rundir,xhash
import sys
import ectl
import ectl.util
import shutil


# --------------------------------------------------------------------
def run(args, restart=False, verify_restart=False):
    """restart:
        True if being called from the `ectl start` command, or if args.restart.
    verify_restart:
        If True, then ask user if we're starting a run over."""

    # ------ Parse Arguments
    paths = rundir.FollowLinks(args.run)
    status = rundir.Status(paths.run)
    if (status.status == rundir.NONE):
        sys.stderr.write('Run does not exist, cannot run: {}\n'.format(args.run))
        sys.exit(-1)
    if (status.status == rundir.RUNNING):
        sys.stderr.write('Run is already running: {}\n'.format(args.run))
        sys.exit(-1)

    cold_restart = restart or (status.status == rundir.INITIAL)

    if cold_restart:    # Start a new run
        if status.status >= rundir.STOPPED:
            if not ectl.util.query_yes_no('Run is STOPPED; do you wish to overwrite and restart?', default='no'):
                sys.exit(-1)

    else:    # Continue a previous run
        if status.status == rundir.FINISHED:
            sys.stderr.write('Run is finished, cannot continue: {}\n'.format(args.run))
            sys.exit(-1)

    modelexe = os.path.join(paths.run, 'pkg', 'bin', 'modelexe')
    launcher = rundir.new_launcher(paths.run, args.launcher)
    log_dir = os.path.join(paths.run, 'log')

    # ------- Load the rundeck and rewrite the I file
    try:
        rd = rundeck.load(os.path.join(paths.run, 'rundeck', 'rundeck.R'), modele_root=paths.src)
        rd.resolve(file_path=ectl.rundeck.default_file_path, download=True,
            download_dir=ectl.rundeck.default_file_path[0])

        # Set end date
        if args.end is not None:
            end = datetime.datetime(*iso8601.parse_date(args.end))
            rd.set(('INPUTZ_cold' if cold_restart else 'INPUTZ', 'END_TIME'), end)

        sections = rundeck.ParamSections(rd)
        rundir.make_rundir(rd, paths.run)

    except IOError:
        print 'Warning: Cannot load rundeck.R.  NOT rewriting I file'

    # -------- Construct the main command line
    mpi_cmd = ['mpirun', '-timestamp-output']

    # -------- Determine log file(s)
    if log_dir != '-':
        try:
            shutil.rmtree(log_dir)
        except:
            pass
        os.mkdir(log_dir)

        log_main = os.path.join(paths.run,'log0')
        try:
            os.remove(log_main)
        except:
            pass
        os.symlink(os.path.join(log_dir, 'l.1.0'), log_main)
        mpi_cmd.append('-output-filename')
        mpi_cmd.append(os.path.join(log_dir, 'q'))

    # ------ Add modele to the command
    modele_cmd = [modelexe]
    if cold_restart:
        modele_cmd.append('-cold-restart')
    modele_cmd.append('-i')
    modele_cmd.append('I')

    # ------- Run it!
    launcher(mpi_cmd, modele_cmd, np=args.np, time=args.time)
    launcher.wait()
    print_status(paths.run)
# --------------------------------------------------------------------
def print_status(run,status=None):
    """run:
        Run directory
    status:
        rundir.Status(run)"""
    if status is None:
        status = rundir.Status(run)

    if (status.status == ectl.rundir.NONE):
        sys.stderr.write('Error: No valid run in directory %s\n' % run)
        sys.exit(-1)

    # Top-line status
    print('============================ {}'.format(os.path.split(run)[1]))
    print('status:  {}'.format(status.sstatus))

    # Run configuration
    paths = rundir.FollowLinks(run)
    paths.dump()

    # Launch.txt
    if status.launch_list is not None:
        for key,val in status.launch_list:
            print('{} = {}'.format(key, val))

    # Do launcher-specific stuff to look at the actual processes running.
    launcher = status.new_launcher()
    if launcher is not None:
        launcher.ps(sys.stdout)