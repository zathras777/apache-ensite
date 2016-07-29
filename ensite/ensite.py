""" Module to provide Apache 2.x configuration file management. """
from __future__ import print_function

import os
import sys
import glob
import argparse
import fnmatch

from . import __version__


class A2ConfigFile(object):
    """ A configuration file within an installation. """
    def __init__(self, fnn):
        self.fnn = fnn
        self.enabled = None

    @property
    def name(self):
        """ The name of the configuration file. """
        return os.path.basename(self.fnn)

    @property
    def enabled_fn(self):
        """ The filename of this file when enabled. """
        return self.fnn.replace('sites-available', 'sites-enabled')

    def check_enabled(self):
        """ Check if this configuration file is presently enabled. """
        if not os.path.exists(self.enabled_fn):
            return False
        if not os.path.islink(self.enabled_fn):
            print("{} exists and isn't a link?".format(self.enabled_fn))
            return False
        src = os.path.abspath(os.path.join(os.path.dirname(self.enabled_fn),
                                           os.readlink(self.enabled_fn)))
        if not os.path.samefile(src, self.fnn):
            print("{} exists but does not link to {}?".format(self.enabled_fn, self.fnn))
            return False
        return True

    def _toggle(self, enable=True):
        """ Internal function to make changes to symlinks. """
        if self.enabled is None:
            self.enabled = self.check_enabled()
        if self.enabled == enable:
            return True
        try:
            if enable:
                os.symlink(self.fnn, self.enabled_fn)
            else:
                os.unlink(self.enabled_fn)
        except OSError as err:
            print(err)
        self.enabled = self.check_enabled()

    def enable(self):
        """ Enable this configuration (add symlink to sites-enabled) """
        self._toggle(True)
        return self.enabled

    def disable(self):
        """ Disable this configuration (remove from sites-enabled) """
        self._toggle(False)
        return self.enabled


class A2Install(object):
    """ Class that represents an installation directory. """
    def __init__(self, directory):
        self.directory = os.path.realpath(directory)
        self.avail_path = os.path.join(self.directory, 'sites-available')
        self.enabled_path = os.path.join(self.directory, 'sites-enabled')
        self.configs = []
        self.find_configs()

    @property
    def version(self):
        """ The Apache version for this directory. """
        return os.path.basename(self.directory)

    def check_directories(self, create=False):
        """ Check for required directories, optionally creating them. """
        for rqd in [self.avail_path, self.enabled_path]:
            if not os.path.exists(rqd):
                if create is False:
                    return False
                os.mkdir(rqd, 0755)
            if not os.path.isdir(rqd):
                print("The required directory {} is not a directory???".format(rqd))
                return False
        return True

    def check_include_entry(self, update=False):
        """ Check if the required Include has been set, optionaly adding it """
        for poss in ['httpd.conf', 'apache.conf']:
            poss_fn = os.path.join(self.directory, poss)
            if not os.path.exists(poss_fn):
                continue

            if not os.path.isfile(poss_fn):
                print("The configuration file {} isn't a regular file?".format(poss_fn))
                continue
            with open(poss_fn, 'r') as conf:
                inc_cmd = "Include etc/{}/sites-enabled/*.conf".format(self.version)
                for line in conf.readlines():
                    if inc_cmd in line and not line.strip().startswith('#'):
                        return True
            if update:
                with open(poss_fn, 'a') as conf:
                    conf.write("\n# Added by a2ensite script\n")
                    conf.write("Include etc/{}/sites-enabled/*.conf\n".format(self.version))
                print("Configuration has been updated. Reload will be required.")
                return True
        return False

    def find_configs(self):
        """ Find configuration files in the sites-available directory """
        # Only those config files available in sites-available are
        # included.
        if not os.path.exists(self.avail_path):
            print("The install at {} does not have a sites-available directory.".
                  format(self.directory))
            return
        for fnn in glob.glob("{}/*.conf".format(self.avail_path)):
            self.configs.append(A2ConfigFile(fnn))

    def list(self):
        """ Return a formatted string of the configuration files available. """
        rvs = "\n{} installation in {}\n\n".format(self.version, self.directory)
        rvs += '  {:40s} {}\n  {} {}\n'.format("Configuration File",
                                               "Enabled?", "=" * 40, "=" * 10)
        for cfg in sorted(self.configs, key=lambda x: x.name):
            rvs += "  {:40s} {}\n".format(cfg.name, cfg.check_enabled())
        return rvs

    def change_status(self, sitename, enabled=True):
        """ Link/unlink a configuration file. """
        if not sitename.endswith('.conf'):
            sitename += '.conf'
        found = []
        for conf in self.configs:
            if fnmatch.fnmatch(conf.name, sitename):
                cfg = {'config': conf.name, 'before': conf.check_enabled()}
                cfg['after'] = conf.enable() if enabled else conf.disable()
                found.append(cfg)
        return found


def do_command_line():
    """ Process the command line. Common functionality between enable/disable. """
    if os.geteuid() != 0:
        print("\n*** You are not running with root privileges, so changes may not be possible.\n")

    parser = argparse.ArgumentParser(description='Apache 2 configuration management tool')
    parser.add_argument('sites', nargs='*', help='Configuration filename to enable')
    parser.add_argument('--version', action='store_true', help='Show version and exit')
    parser.add_argument('--list', action='store_true', help='List available configuration files')
    parser.add_argument('--setup', action='store_true',
                        help='Setup directory and config for use with a2ensite')

    args = parser.parse_args()
    if args.version:
        print("{} - version {}".format(os.path.dirname(sys.argv[0]), __version__))
        print("https://github.com/zathras777/apache-ensite")
        sys.exit(0)

    installs = [A2Install(poss) for poss in glob.glob('/usr/local/etc/apache2*')]
    if len(installs) == 0:
        print("No Apache 2.x installations found in searched paths?")
        sys.exit(0)

    if len(installs) > 1:
        install = sorted(installs, key=lambda x: x.version)[-1]
        print("Found more than one Apache 2.x install, will use {}".format(install.directory))
    else:
        install = installs[0]

    if args.setup:
        install.check_directories(True)
        install.check_include_entry(True)

    if not install.check_directories(False):
        print("Required directories are not available for {}".format(install.directory))
        if not args.setup:
            print("Try again with the --setup flag to set things up automatically.")
        sys.exit(0)

    if not install.check_include_entry(False):
        print("""
The required include entry does not appear to be present.
Changes made may not be visible.""")
        if not args.setup:
            print("Use the --setup flag to try and change the configuration automatically.")

    if args.list:
        print(install.list())
        sys.exit(0)

    if args.sites is None:
        print(install.list())
        print("Please enter the filename(s) of the configuation files to enable")
        try:
            input_fn = raw_input
        except NameError:
            input_fn = input
        site = input_fn(": ").strip()
        if site == '':
            print("Exiting...")
            sys.exit(0)
        return install, site

    return install, args.sites


def reload_notice(install):
    """ Print statement informing of need to reload configuration. """
    print("""
The configuration for {} has been updated. To reload the server run

 sudo service {} reload

""".format(install.version, install.version))


def action_changes(enable=True):
    """ Common function to actually make changes via an install object. """
    install, names = do_command_line()
    changed = 0
    for name in names:
        rvv = install.change_status(name, enable)
        if len(rvv) == 0:
            print("No matching configuration file(s) found for {}".format(name))
        else:
            print("Tried to change configuration files matching {}".format(name))
            print("  {:40s} {:6s} {:6s}\n  {} {} {}".format("Configuration File",
                                                            "Before", "After",
                                                            "=" * 40, "=" * 6, "=" * 6))
            for found in rvv:
                print("  {:40s} {:6s} {:6s}".format(found['config'],
                                                    str(found['before']),
                                                    str(found['after'])))
                if found['before'] != found['after']:
                    changed += 1

    if changed > 0:
        reload_notice(install)
    else:
        print("No configuration changes made.")


def a2ensite():
    """ Activate one or more configuration files. """
    action_changes(True)


def a2dissite():
    """ Deactivate one or more configuration files. """
    action_changes(False)

