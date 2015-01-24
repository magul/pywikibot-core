# -*- coding: utf-8 -*-
"""
Module to define and load pywikibot configuration.

Provides two family class methods which can be used in
the user-config:
 - register_family_file
 - register_families_folder

Sets module global base_dir and provides utility methods to
build paths relative to base_dir:
 - makepath
 - datafilepath
 - shortpath
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import types
import sys
import pywikibot.configuration


def get_base_dir(test_directory=None):
    r"""Return the directory in which user-specific information is stored.

    This is determined in the following order:
     1.  If the script was called with a -dir: argument, use the directory
         provided in this argument.
     2.  If the user has a PYWIKIBOT2_DIR environment variable, use the value
         of it.
     3.  If user-config is present in current directory, use the current
         directory.
     4.  If user-config is present in pwb.py directory, use that directory
     5.  Use (and if necessary create) a 'pywikibot' folder under
         'Application Data' or 'AppData\Roaming' (Windows) or
         '.pywikibot' directory (Unix and similar) under the user's home
         directory.

    Set PYWIKIBOT2_NO_USER_CONFIG=1 to disable loading user-config.py

    @param test_directory: Assume that a user config file exists in this
        directory. Used to test whether placing a user config file in this
        directory will cause it to be selected as the base directory.
    @type test_directory: str or None
    @rtype: unicode
    """
    args, arg_path = pywikibot.configuration._parse_arg(sys.argv[1:])
    sys.argv[:] = [sys.argv[0]] + args
    return pywikibot.configuration.get_base_dir(arg_path, test_directory)


class _ConfigDeprecationWrapper(types.ModuleType):

    """A wrapper for a module to deprecate classes or variables of it."""

    def __init__(self):
        """
        Initialise the wrapper.

        It will automatically overwrite the module with this instance in
        C{sys.modules}.

        @param module: The module name or instance
        @type module: str or module
        """
        module = sys.modules['pywikibot.config2']
        super(_ConfigDeprecationWrapper, self).__setattr__('_configuration', pywikibot.configuration)
        super(_ConfigDeprecationWrapper, self).__setattr__('__doc__', module.__doc__)

        if __debug__:
            sys.modules[module.__name__] = self

        if __name__ == '__main__':
            self._configuration(*sys.argv)

    def __setattr__(self, name, value):
        setattr(self._configuration.configuration, name, value)

    def __getattr__(self, name):
        return getattr(self._configuration.configuration, name)

_ConfigDeprecationWrapper()
