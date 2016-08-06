import ectl
import ectl.launch

description = 'Continues (or restarts) a run.'

def setup_parser(subparser):
    subparser.add_argument('run', nargs='?', default='.',
        help='Directory of run to give execution command')
    subparser.add_argument('--restart', action='store_true', dest='restart', default=False,
        help="Restart the run, even if it's already started")
    subparser.add_argument('--end', '-e', action='store', dest='end',
        help='[iso8601] Time to stop the run')
#    subparser.add_argument('-o', action='store', dest='log_dir',
#        help="Name of file for output (relative to rundir); '-' means STDOUT")
    subparser.add_argument('-l', '--launcher', action='store', dest='launcher', default='mpi',
        help='How to run the program')

    # -------- Arguments for SOME launchers
    subparser.add_argument('-np', action='store', dest='np',
        help='Number of MPI jobs (launcher=fg,slurm)')

    subparser.add_argument('-t', action='store', dest='slurm_t',
        help='Slurm time allocation length')


def run(parser, args, unknown_args):
    if len(unknown_args) > 0:
        raise ValueError('Unkown arguments: %s' % unknown_args)

    ectl.launch.run(args, restart=args.restart)