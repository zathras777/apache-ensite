import os
import sys
import glob
import errno
import argparse
import fnmatch


class A2ConfigFile(object):
    def __init__(self, fn):
        self.fn = fn
        self.enabled = None

    @property
    def name(self):
        return os.path.basename(self.fn)

    @property
    def enabled_fn(self):
        return self.fn.replace('sites-available', 'sites-enabled')

    def check_enabled(self):
        if not os.path.exists(self.enabled_fn):
            return False
        if not os.path.islink(self.enabled_fn):
            print("{} exists and isn't a link?".format(self.enabled_fn))
            return False
        src = os.path.abspath(os.path.join(os.path.dirname(self.enabled_fn), os.readlink(self.enabled_fn)))
        if not os.path.samefile(src, self.fn):
            print("{} exists but does not link to {}?".format(self.enabled_fn, self.fn))
            return False
        return True

    def _toggle(self, enable=True):
        if self.enabled is None:
            self.enabled = self.check_enabled()
        if self.enabled == enable:
            return True
        try:
            if enable:
                os.symlink(self.fn, self.enabled_fn)
            else:
                os.unlink(self.enabled_fn)
        except OSError as e:
            print(e)
        self.enabled = self.check_enabled()
    
    def enable(self):
        self._toggle(True)
        return self.enabled

    def disable(self):
        self._toggle(False)
        return self.enabled
        

class A2Install(object):
    def __init__(self, directory):
        self.directory = os.path.realpath(directory)
        self.avail_path = os.path.join(self.directory, 'sites-available')
        self.enabled_path = os.path.join(self.directory, 'sites-enabled')
        self.configs = []
        self.find_configs()

    @property
    def version(self):
        return os.path.basename(self.directory)

    def check_directories(self, create=False):
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
        # Only those config files available in sites-available are
        # included.
        if not os.path.exists(self.avail_path):
            print("The Apache2 install at {} does not have a sites-available directory.".format(self.directory))
            return
        for fn in glob.glob("{}/*.conf".format(self.avail_path)):
            self.configs.append(A2ConfigFile(fn))

    def list(self):
        rv = "\n{} installation in {}\n\n".format(self.version, self.directory)
        rv += '  {:40s} {}\n  {} {}\n'.format("Configuration File", 
                                              "Enabled?", "=" * 40, "=" * 10)
        for cfg in sorted(self.configs, key=lambda x: x.name):
            rv += "  {:40s} {}\n".format(cfg.name, cfg.check_enabled())
        return rv

    def change_status(self, sitename, enabled=True):
        if not sitename.endswith('.conf'):
            sitename += '.conf'
        found = []
        for c in self.configs:
            if fnmatch.fnmatch(c.name, sitename):
                cfg = {'config': c.name, 'before': c.check_enabled()}
                cfg['after'] = c.enable() if enabled else c.disable()
                found.append(cfg)
        return found
                

def do_command_line():
    if os.geteuid() != 0:
        print("\n*** You are not running with root privileges, so changes may not be possible.\n")

    parser = argparse.ArgumentParser(description='Apache 2 configuration management tool')
    parser.add_argument('sites', nargs='*', help='Configuration filename to enable')
    parser.add_argument('--version', action='store_true', help='Show version and exit')
    parser.add_argument('--list', action='store_true', help='List available configuration files')
    parser.add_argument('--create', action='store_true', 
                        help='Create site-available and site-enabled directories')
    parser.add_argument('--add-include', action='store_true',
                        help='Modify the httpd.conf file to include the configuration files')

    args = parser.parse_args()
    if (args.version):
        print("{} version {}".format(sys.argv[0], __version__))
        print("https://github.com/zathras777/apache2-ensite")
        sys.exit(0)

    installs = [A2Install(poss) for poss in glob.glob('/usr/local/etc/apache2*')]
    if len(installs) == 0:
        print("No Apache 2.x installations found in searched paths?")
        sys.exit(0)
    elif len(installs) > 1:
        install = sorted(installs, key=lambda x: x.version)[-1]
        print("Found more than one Apache 2.x install, will use {}".format(install.directory))
    else:
        install = installs[0]

    if args.create:
        install.check_directories(True)

    if install.check_directories(False) == False:
        print("Required directories are not available for {}".format(install.directory))
        if args.create is False:
            print("You can use the --create flag to create them automatically.")
        sys.exit(0)

    if args.add_include:
        install.check_include_entry(True)

    if install.check_include_entry(False) == False:
        print("\033[93mThe required include entry does not appear to be present. Changes made will not be available.\033[0m")

    if args.list:
        print(install.list())
        sys.exit(0)

    if args.sites is None:
        print(install.list())
        print("Please enter the filename(s) of the configuation files to enable")
        try:
            input = raw_input
        except NameError:
            pass
        site = input(": ").strip()
        if site == '':
            print("Exiting...")
            sys.exit(0)
        return install, site

    return install, args.sites 


def reload_notice(install):
    print("""
The configuration for {} has been updated. To reload the server run

$ sudo service {} reload

""".format(install.version, install.version))  


def action_changes(enable=True):
    install, sites = do_command_line()
    changed = 0
    for s in sites:
        rv = install.change_status(s, enable)
        if len(rv) == 0:
            print("No matching configuration file(s) found for {}".format(s))
        else:
            print("Tried to change configuration files matching {}".format(s))
            print("  {:40s} {:6s} {:6s}\n  {} {} {}".format("Configuration File", 
                                                            "Before", "After",
                                                            "=" * 40, "=" * 6, "=" * 6))
            for found in rv:
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
    action_changes(True)
 

def a2dissite():
    action_changes(False)

