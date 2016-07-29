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
When you first install Apache on FreeBSD there are no sites-available or sites-enabled directories, so either
crete them by hand or run
```$ sudo a2ensite --create```
Before the symlinked configurations can be used an Include directrive needs to be added to the httpd.conf file,
which if not present will create a warning to that effect. This can be automatically added by 
```$ sudo a2ensite --add-include```
After creating a configuration file, e.g. blah.conf, you can enable it by
```$ sudo a2ensite blah```
When finished with the configuration file, e.g. blah.conf, simply run
```$ sudo a2dissite blah```

If you can't remember the filename simply run with no name and a list will be displayed. More than one
file can specified at once. Matches are done using fnmatch so standard wildcards are available.


