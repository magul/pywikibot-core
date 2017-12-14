"""Check that the latest commit diff follows the guidelines.

Currently the script only checks line lengths. Lines longer than 79 characters
should be avoided.
See [[Manual:Pywikibot/Development/Guidelines]] for more info.

Todo: The following rules could be added (requires parsing the modules):         a
    - For any changes or new lines use single quotes for strings, or double
        quotes  if the string contains a single quote. But keep older code
        unchanged.
    - Do not use a u'' prefix on strings, as it is meaningless due to
        __future__.unicode_literals. But keep older code unchanged.

"""

from unidiff import PatchSet
from subprocess import check_output
from re import compile as re_compile

# regex from https://github.com/PyCQA/pylint/blob/master/pylintrc
ignorable_long_line = re_compile(r'^\s*(# )?<?https?://\S+>?$').search

output = check_output(['git', 'diff', '-U0', 'head^'], universal_newlines=True)
patchset = PatchSet.from_string(output)

error = False
for patched_file in patchset:
    target_file = patched_file.target_file
    if not (target_file.endswith('.py') or patched_file.is_removed_file):
        continue
    for hunk in patched_file:
        for line in hunk:
            if not line.is_added:
                continue
            if len(line.value) > 80 and not ignorable_long_line(line.value):
                print(
                    target_file + ':' + line.target_line_no + ':'
                    + str(len(line.value))
                    + ': line is too long (more than 79 characters)'
                )
                error = True

if error:
    raise SystemExit('one or more lines where longer than 79 characters')
