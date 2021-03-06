from __future__ import print_function
import os
from ectl import pathutil


class Config(object):
    """General configuration of where things are stored in this Ectl
    instance."""

    def __init__(self, ectl=None, run=None):
        self.ectl = None    # Root of ectl tree
        self.runs = None        # Where to create run directories, if needed
        self.builds = None      # Where to create build directories, if needed
        self.pkgs = None        # Where to create pkg directories, if needed


        # We are given an ectl root... EASY!
        if ectl is not None:
            print('Getting config from ectl')
            self.ectl = os.path.abspath(ectl)
            self.runs = os.path.join(self.ectl)
            self.builds = os.path.join(self.ectl, 'builds')
            self.pkgs = os.path.join(self.ectl, 'pkgs')
            return

        # Look at an existing run
        if os.path.exists(run):
            print('Getting config from run')

            # Determine directories from existing run
            self.runs = os.path.abspath(os.path.join(run, '..'))

            build = pathutil.follow_link(os.path.join(run, 'build'))
            pkg = pathutil.follow_link(os.path.join(run, 'pkg'))

            if build is not None and pkg is not None:
                self.builds = os.path.abspath(os.path.join(build, '..'))
                ectl_build = os.path.abspath(os.path.join(self.builds, '..'))

                self.pkgs = os.path.abspath(os.path.join(pkg, '..'))
                ectl_pkg = os.path.abspath(os.path.join(self.pkgs, '..'))

                if ectl_build == ectl_pkg:
                    self.ectl = ectl_build
                return

        # Last resort: search up from run directory
        print('Getting config from run directory location')

        # We're given a rundeck: search up for ectl.conf
        start_path = os.path.split(os.path.abspath(run))[0]

        # Find the root of the ectl tree
        ectl_conf = pathutil.search_up(start_path,
            lambda path: pathutil.has_file(path, 'ectl.conf'))

        if ectl_conf is None:
            raise ValueError('Could not find ectl.conf starting from %s' % start_path)

        self.ectl = os.path.split(ectl_conf)[0]
        self.runs = os.path.join(self.ectl)
        self.builds = os.path.join(self.ectl, 'builds')
        self.pkgs = os.path.join(self.ectl, 'pkgs')
