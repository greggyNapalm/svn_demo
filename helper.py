#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Usage:
  svn_helper [--cfg=S] [--path=S] ACTION
  svn_helper --version

Arguments:
  ACTION                co - to checkuot.

Options:
  --version             Show version and exit.
  -v --verbose          Give more verbose output.
  -h --help             Show this help message and exit.

  -c --cfg=S            Path to config file.
  -p --path=S           Path to working copy folder
"""

"""
    helper.main
    ~~~~~~~~~~~

    Command line tool to help with SVN routine.
"""
import os
import sys
import csv
import shutil
import contextlib
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

import sh
from sh import svn
from docopt import docopt

VERSION = '0.0.1'
DEFAULTS = {
    'cfg_path': './helper.cfg',
}


@contextlib.contextmanager
def preserve_cwd():
    cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(cwd)


class VcsWrapper(object):
    supported_actions = {
        'co': 'checkout',
        'clean': 'clean',
    }

    @classmethod
    def act(cls, action, cfg):
        """
        Cretae dict with app cfg by combining cmd opts with config file.
        Args:
            action: str, action to perform.
            cfg: dict, main app cfg struct.

        Throws:
            IOError, ValueError
        """
        if action not in cls.supported_actions.keys():
            raise ValueError('called action not supported: {0}, use one from {1}'.format(
                action, cls.supported_actions))

        dst_path = cfg['PATH'] or cfg['SVN_URL'].split('/')[-1]
        print 'Working copy path: {0}'.format(dst_path)
        getattr(cls, cls.supported_actions[action])(cfg, dst_path)

    @classmethod
    def checkout(cls, cfg, dst_path):
        if os.path.exists(dst_path):
            is_under_ctl, meta = cls._get_vcs_info(dst_path)
            if not is_under_ctl:
                print 'Woring copy path allready exists, but not under VCS control.'
                return
            cls._switch(dst_path, cfg['SVN_URL'])
            cls._up_to_rev(dst_path, cfg['SVN_REV'])
        else:
            svn('co', cfg['SVN_URL'], '-r', cfg['SVN_REV'], dst_path)

    @classmethod
    def _get_vcs_info(cls, path):
        """
        Retrive working copy metadata.
        Args:
            path: str, path to folder to update.

        Returns:
            tuple of two elements
            bool - is path under VSC control or  not.
            str - VCS metadata.
        """
        rv = (False, None)
        try:
            meta = svn('info', path)
            return (True, meta)
        except sh.ErrorReturnCode_1:
            return rv

    @classmethod
    def _up_to_rev(cls, path, rev):
        """
        Update working copy to passed rev.
        Args:
            path: str, path to folder to update.
            rev: str, target revision, HEAD and etc supported as well.

        Throws:
            sh.ErrorReturnCode_1
        """
        svn('up', path, '-r{0}'.format(rev))

    @classmethod
    def _switch(cls, path, repo_addr):
        """
        Update working copy to passed rev.
        Args:
            path: str, path to folder to update.
            rev: str, target revision, HEAD and etc supported as well.

        Throws:
            sh.ErrorReturnCode_1
        """
        svn('switch', repo_addr, path)

    @classmethod
    def _collect_derty(cls):
        """
        Collect changed and unwanted files in cwd.

        Returns:
            tuple of lists
            to_remove - files and folders names, which would be removed.
            to_rollback - files and folders names, which would be rolled back.
        """
        to_rollback = []
        to_remove = []
        clr_f_name = lambda row: row.rstrip().split(' ')[-1]

        for row in sh.svn('status', '--no-ignore'):
            if row.startswith('?'):
                to_remove.append(clr_f_name(row))
            elif row.startswith('M'):
                to_rollback.append(clr_f_name(row))

        return to_remove, to_rollback

    @classmethod
    def _rm(cls, path):
        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno == 20:  # Not a directory.
                os.unlink(path)
            else:
                raise

    @classmethod
    def clean(cls, cfg, path):
        names2txt = lambda names: '\n'.join(['\t* ' + os.path.join(path, n) for n in names])
        with preserve_cwd():
            os.chdir(path)
            to_remove, to_rollback = cls._collect_derty()

            to_remove_txt = names2txt(to_remove)
            to_rollback_txt = names2txt(to_rollback)
            msg_rm = "The following untracked working tree files would be removed:"
            msg_rallback = "The following untracked working tree files would be rolled back:"

            def ask():
                msg = []
                if to_remove:
                    msg.extend([msg_rm, to_remove_txt])
                if to_rollback:
                    msg.extend([msg_rallback, to_rollback_txt])

                msg.append('\nContinue (y/n)')
                return raw_input('\n'.join(msg))


            while True:
                if to_remove or to_rollback:
                    is_agreed = ask()
                else:
                    print 'Nothing to clean'
                    return
                if is_agreed.lower() == 'n':
                    print 'Doing nothing'
                    return
                elif is_agreed.lower() == 'y':
                    break
                else:
                    is_agreed = ask()

            [cls._rm(f) for f in to_remove]
            [svn('revert', f) for f in to_rollback]
        cls.checkout(cfg, path)
        print 'Working copy cleared'


def compose_cfg(defaults, args):
    """
    Cretae dict with app cfg by combining cmd opts with config file.
    Args:
        defaults: dict.
        args: dict, docopt returned.

    Returns:
        dict

    Throws:
        IOError, ValueError
    """
    cfg = {}
    c_path = args.get('--cfg') or defaults['cfg_path']

    with open(c_path, "rb") as fh:
        reader = csv.reader(fh, delimiter='=', escapechar='\\', quoting=csv.QUOTE_NONE)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) != 2:
                raise ValueError("Config file malformed: {0}".format(row))
            cfg[row[0]] = row[1]

    cfg['PATH'] = args.get('--path') or cfg.get('PATH') or None
    # TODO: validate cfg struct
    return cfg


def main():
    cmd_args = docopt(__doc__, version=VERSION)
    app_cfg = compose_cfg(DEFAULTS, cmd_args)

    VcsWrapper.act(cmd_args['ACTION'], app_cfg)
    sys.exit(0)

if __name__ == '__main__':
    main()
