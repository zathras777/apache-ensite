# apache-ensite
Apache 2 configuration file management a la debian

## Why?
Having recently started movign away from Ubuntu I found that their way of managing apache configuration
files still made sense, so I wrote this small bit of python to allow me to have a2ensite and a2dissite
available on a FreeBSD system.

## Huh?
The basic theory is to have a sites-available directory where you create the configuration files. When you
want to actually use the configurations you enable them by creating a symlink from the sites-available
directory to the sites-enabled directory. When you have finished using the configuration file, you simply
remove the symlink. It makes things a lot easier and using these 2 small scripts make things even simpler.

## How?
When you first install Apache on FreeBSD there are no sites-available or sites-enabled directories and the default configuration lacks the required directive, so either create the directories manually and then edit the httpd.conf file, or run
```
$ sudo a2ensite --setup
```

After creating a configuration file, e.g. blah.conf, you can enable it by
```
$ sudo a2ensite blah
```
When finished with the configuration file, e.g. blah.conf, simply run
```
$ sudo a2dissite blah
```

If you can't remember the filename simply run with no name (or use the --list command) and a list will be displayed.
```
$ a2ensite --list

*** You are not running with root privileges, so changes may not be possible.


apache24 installation in /usr/local/etc/apache24

  Configuration File                       Enabled?
  ======================================== ==========
  000-default.conf                         True
  svn.conf                                 False
```

## Notes
- More than one file can specified at once.
- Matches are done using fnmatch so standard wildcards are available.

