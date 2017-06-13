#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to create user-config.py."""
#
# (C) Pywikibot team, 2010-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals
__version__ = '$Id$'

import codecs
import os
import re
import sys

from textwrap import wrap
from warnings import warn

# Disable user-config usage as we are creating it here
_orig_no_user_config = os.environ.get('PYWIKIBOT2_NO_USER_CONFIG')
os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '2'

import pywikibot

from pywikibot import config

# Reset this flag in case another script is run by pwb after this script
if not _orig_no_user_config:
    del os.environ['PYWIKIBOT2_NO_USER_CONFIG']
else:
    os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = _orig_no_user_config

base_dir = pywikibot.config2.base_dir
console_encoding = sys.stdout.encoding
# the directory in which generate_user_files.py is located
pywikibot_dir = sys.path[0]

if console_encoding is None or sys.platform == 'cygwin':
    console_encoding = "iso-8859-1"


def change_base_dir():
    """Create a new user directory."""
    while True:
        new_base = pywikibot.input("New user directory? ")
        new_base = os.path.abspath(new_base)
        if os.path.exists(new_base):
            if os.path.isfile(new_base):
                pywikibot.error("there is an existing file with that name.")
                continue
            # make sure user can read and write this directory
            if not os.access(new_base, os.R_OK | os.W_OK):
                pywikibot.error("directory access restricted")
                continue
            pywikibot.output("Using existing directory")
            break
        else:
            try:
                os.mkdir(new_base, pywikibot.config2.private_files_permission)
            except Exception as e:
                pywikibot.error('directory creation failed: {0}'.format(e))
                continue
            pywikibot.output("Created new directory.")
            break

    if new_base == pywikibot.config2.get_base_dir(new_base):
        # config would find that file
        return new_base

    msg = wrap(u"""WARNING: Your user files will be created in the directory
'%(new_base)s' you have chosen. To access these files, you will either have
to use the argument "-dir:%(new_base)s" every time you run the bot, or set
the environment variable "PYWIKIBOT2_DIR" equal to this directory name in
your operating system. See your operating system documentation for how to
set environment variables.""" % {'new_base': new_base}, width=76)
    for line in msg:
        pywikibot.output(line)
    if pywikibot.input_yn('Is this OK?', default=False, automatic_quit=False):
        return new_base
    pywikibot.output("Aborting changes.")
    return False


def file_exists(filename):
    """Return whether the file exists and print a message if it exists."""
    if os.path.exists(filename):
        pywikibot.output(u"'%s' already exists." % filename)
        return True
    return False


def get_site_and_lang(default_family='wikipedia', default_lang='en',
                      default_username=None, force=False):
    """
    Ask the user for the family, language and username.

    @param default_family: The default family which should be chosen.
    @type default_family: None or str
    @param default_lang: The default language which should be chosen, if the
        family supports this language.
    @type default_lang: None or str
    @param default_username: The default username which should be chosen.
    @type default_username: None or str
    @return: The family, language and username
    @rtype: tuple of three str
    """
    known_families = sorted(pywikibot.config2.family_files.keys())
    if default_family not in known_families:
        default_family = None
    fam = pywikibot.bot.input_list_choice(
        u"Select family of sites we are working on, "
        u"just enter the number or name",
        known_families,
        force=force,
        default=default_family)
    fam = pywikibot.family.Family.load(fam)
    if hasattr(fam, "langs"):
        if hasattr(fam, "languages_by_size"):
            by_size = [code for code in fam.languages_by_size
                       if code in fam.langs.keys()]
        else:
            by_size = []
        known_langs = by_size + sorted(
            set(fam.langs.keys()).difference(by_size))
    else:
        known_langs = []

    if len(known_langs) == 0:
        pywikibot.output('There were no known languages found in {0}.'.format(fam.name))
        default_lang = None
    elif len(known_langs) == 1:
        pywikibot.output('The only known language: {0}'.format(known_langs[0]))
        default_lang = known_langs[0]
    else:
        pywikibot.output("This is the list of known languages:")
        pywikibot.output(u", ".join(known_langs))
        if default_lang not in known_langs:
            if default_lang != 'en' and 'en' in known_langs:
                default_lang = 'en'
            else:
                default_lang = None
    message = "The language code of the site we're working on"

    mycode = None
    while not mycode:
        mycode = pywikibot.input(message, default=default_lang, force=force)
        if known_langs and mycode and mycode not in known_langs:
            if not pywikibot.input_yn("The language code {0} is not in the "
                                      "list of known languages. Do you want "
                                      "to continue?".format(mycode),
                                      default=False, automatic_quit=False):
                mycode = None

    message = 'Username on {0}:{1}'.format(mycode, fam.name)
    username = pywikibot.input(message, default=default_username, force=force)
    # Escape ''s
    if username:
        username = username.replace("'", "\\'")
    return fam.name, mycode, username


EXTENDED_CONFIG = """# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

# This is an automatically generated file. You can find more configuration
# parameters in 'config.py' file.

# The family of sites to work on by default.
#
# ‘site.py’ imports ‘families/xxx_family.py’, so if you want to change
# this variable, you need to use the name of one of the existing family files
# in that folder or write your own, custom family file.
#
# For ‘site.py’ to be able to read your custom family file, you must
# save it to ‘families/xxx_family.py’, where ‘xxx‘ is the codename of the
# family that your custom ‘xxx_family.py’ family file defines.
#
# You can also save your custom family files to a different folder. As long
# as you follow the ‘xxx_family.py’ naming convention, you can register your
# custom folder in this configuration file with the following global function:
#
#   register_families_folder(folder_path)
#
# Alternatively, you can register particular family files that do not need
# to follow the ‘xxx_family.py’ naming convention using the following
# global function:
#
#   register_family_file(family_name, file_path)
#
# Where ‘family_name’ is the family code (the ‘xxx’ in standard family file
# names) and ‘file_path’ is the absolute path to the target family file.
#
# If you use either of these functions to define the family to work on by
# default (the ‘family’ variable below), you must place the function call
# before the definition of the ‘family’ variable.
family = '{main_family}'

# The language code of the site we're working on.
mylang = '{main_code}'

# The dictionary usernames should contain a username for each site where you
# have a bot account. If you have a unique username for all languages of a
# family , you can use '*'
{usernames}

# The list of BotPasswords is saved in another file. Import it if needed.
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords to know how
# use them.
{botpasswords}

{config_text}"""

SMALL_CONFIG = ('# -*- coding: utf-8 -*-\n'
                "from __future__ import absolute_import, unicode_literals\n"
                "family = '{main_family}'\n"
                "mylang = '{main_code}'\n"
                "{usernames}\n"
                "{botpasswords}\n")

PASSFILE_CONFIG = """# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

# This is an automatically generated file used to store BotPasswords. See
# user-config.py for general informations about user- files.
#
# As a simpler (but less secure) alternative to OAuth, MediaWiki allows bot
# users to uses BotPasswords to limit the permissions given to a bot.
# When using BotPasswords, each instance gets keys. This combination can only
# access the API, not the normal web interface.
#
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords for more
# information.
{botpasswords}"""


def create_user_config(args=None, force=False):
    """
    Create a user-config.py in base_dir.

    Create a user-password.py if necessary.
    """
    _fnc = os.path.join(base_dir, "user-config.py")
    _fncpass = os.path.join(base_dir, 'user-password.py')
    if file_exists(_fnc) or file_exists(_fncpass):
        return

    if args and force and not config.verbose_output:
        # main_username may be None, which is used in the next block
        main_family, main_code, main_username = args
        usernames = [args]
    else:
        main_family, main_code, main_username = get_site_and_lang(*args,
                                                                  force=force)
        usernames = [(main_family, main_code, main_username)]

        while pywikibot.input_yn("Do you want to add any other projects?",
                                 force=force,
                                 default=False, automatic_quit=False):
            usernames += [get_site_and_lang(main_family, main_code,
                                            main_username)]

    botpasswords = []
    if not main_username:
        usernames = "# usernames['{0}']['{1}'] = u'MyUsername'".format(
            main_family, main_code)
    else:
        # For each different username entered, ask if user wants to save a
        # BotPassword (username, BotPassword name, BotPassword pass)
        seen = set()
        for username in usernames:
            if username[2] in seen:
                continue
            seen.add(username[2])
            if pywikibot.input_yn('Do you want to add a BotPassword for {0}?'
                                  .format(username[2]),
                                  force=force, default=False):
                if not botpasswords:
                    pywikibot.output(
                        'See https://www.mediawiki.org/wiki/'
                        'Manual:Pywikibot/BotPasswords to know '
                        'how to get codes.')
                message = 'BotPassword\'s "bot name" for {0}'.format(
                    username[2])
                botpasswordname = pywikibot.input(message, force=force)
                message = 'BotPassword\'s "password" for BotPassword "{0}"' \
                          ' (no characters will be shown)' \
                    .format(botpasswordname)
                botpasswordpass = pywikibot.input(message, force=force,
                                                  password=True)
                if botpasswordname and botpasswordpass:
                    botpasswords.append((username[2], botpasswordname,
                                         botpasswordpass))

        usernames = '\n'.join(
            u"usernames['{0}']['{1}'] = u'{2}'".format(*username)
            for username in usernames)
        botpasswords = '\n'.join(
            "('{0}', BotPassword('{1}', '{2}'))".format(*botpassword)
            for botpassword in botpasswords)

    config_text = ''
    config_content = SMALL_CONFIG

    try:
        # config2.py will be in the pywikibot/ directory relative to this
        # script (generate_user_files)
        install = os.path.dirname(os.path.abspath(__file__))
        with codecs.open(os.path.join(install, "pywikibot", "config2.py"),
                         "r", "utf-8") as config_f:
            config_file = config_f.read()

        res = re.findall("^(# ############# (?:"
                         "LOGFILE|"
                         'EXTERNAL SCRIPT PATH|'
                         "INTERWIKI|"
                         "SOLVE_DISAMBIGUATION|"
                         "IMAGE RELATED|"
                         "TABLE CONVERSION BOT|"
                         "WEBLINK CHECKER|"
                         "DATABASE|"
                         "SEARCH ENGINE|"
                         "COPYRIGHT|"
                         "FURTHER"
                         ") SETTINGS .*)^(?=#####|# =====)",
                         config_file, re.MULTILINE | re.DOTALL)

        if not res:
            warn('Extended config extraction failed', UserWarning)

        config_text = '\n'.join(res)
        if len(config_text.splitlines()) < 350:
            warn('Extended config extraction too short: %d'
                 % len(config_text.splitlines()),
                 UserWarning)

        config_content = EXTENDED_CONFIG
    except Exception as e:
        # If the warning was explicitly enabled, raise
        if isinstance(e, UserWarning):
            raise
        pywikibot.output('Exception while creating extended user-config; '
                         'falling back to simple user-config.')
        pywikibot.exception()

    try:
        # Finally save user-config.py
        with codecs.open(_fnc, "w", "utf-8") as f:
            f.write(config_content.format(main_family=main_family,
                                          main_code=main_code,
                                          usernames=usernames,
                                          config_text=config_text,
                                          botpasswords='password_file = '
                                          '"user-password.py"'
                                          if botpasswords else ''))
        pywikibot.output(u"'%s' written." % _fnc)
    except:
        try:
            os.remove(_fnc)
        except:
            pass
        raise

    # Save if necessary user-password.py
    if botpasswords:
        try:
            with codecs.open(_fncpass, 'w', 'utf-8') as f:
                f.write(PASSFILE_CONFIG.format(botpasswords=botpasswords))
                pywikibot.output("'%s' written." % _fncpass)
        except:
            os.remove(_fncpass)
            raise


def main(*args):
    """
    Process command line arguments and generate user-config.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    global base_dir

    # set the config family and mylang values to an invalid state so that
    # the script can detect that the command line arguments -family & -lang
    # were used and and handle_args has updated these config values,
    # and 'force' mode can be activated below.
    (config.family, config.mylang) = ('wikipedia', None)

    pywikibot.output('You can abort at any time by pressing ctrl-c')

    local_args = pywikibot.handle_args(args)
    if local_args:
        pywikibot.output('Unknown arguments: %s' % ' '.join(local_args))
        return False

    if config.mylang is not None:
        force = True
        pywikibot.output(u'Automatically generating user-config.py')
    else:
        force = False
        # Force default site of en.wikipedia
        (config.family, config.mylang) = ('wikipedia', 'en')

    username = config.usernames[config.family].get(config.mylang)
    args = (config.family, config.mylang, username)

    # Only give option for directory change if user-config.py already exists
    # in the directory. This will repeat if user-config.py also exists in
    # the requested directory.
    # TODO: T167573: check for user-password.py too
    if not force or config.verbose_output:
        pywikibot.output(u'\nYour default user directory is "%s"' % base_dir)
        while os.path.isfile(os.path.join(base_dir, "user-config.py")):
            pywikibot.output('user-config.py already exists'
                             ' in the target directory.')
            if pywikibot.input_yn('Would you like to change the directory?',
                                  default=True,
                                  automatic_quit=False, force=force):
                new_base = change_base_dir()
                if new_base:
                    base_dir = new_base
            else:
                break

    # user-fixes.py also used to be created here, but has
    # been replaced by an example file.
    if not os.path.isfile(os.path.join(base_dir, "user-config.py")):
        create_user_config(args, force=force)
    else:
        pywikibot.output('user-config.py already exists in the target '
                         'directory "{0}".'.format(base_dir))


if __name__ == '__main__':
    main()
