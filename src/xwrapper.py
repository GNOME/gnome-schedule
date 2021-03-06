# xwrapper.py - wrapper around X applications
# Copyright (C) 2004 - 2010  Gaute Hope <eg at gaute dot vetsj dot com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#python
import sys
import os
import pwd


# g-s modules
import config
import crontab


##
## I18N
##
import gettext
gettext.install(config.GETTEXT_PACKAGE(), config.GNOMELOCALEDIR(), unicode=1)

def check_X (display, xauth):
    # Checking if I can use X
    os.environ['DISPLAY'] = display
    os.environ['XAUTHORITY'] = xauth

    try:
        import pygtk
        pygtk.require("2.0")

    except:
        pass

    try:
        import gtk

    except:
        print _("You need to install pyGTK or GTKv2,\n"
                "or set your PYTHONPATH correctly.\n"
                "try: export PYTHONPATH= ")
        sys.exit(1)

    try:
        gtk.init_check ()

    except Exception as e:
        print _("Could not open a connection to X!")
        print e
        sys.exit (1)

poscorrect_isset = os.getenv ("POSIXLY_CORRECT", False)
manual_poscorrect = False
if poscorrect_isset == False:
    os.environ["POSIXLY_CORRECT"] = "enabled"
    manual_poscorrect = True

if (len (sys.argv) < 2):
    print _("Wrong number of arguments.")

    print _("Wrapper script for Gnome-schedule (http://gnome-schedule.sf.net) for applications to be run from crontab or at under X. Use through gnome-schedule.")
    sys.exit (1)

if sys.argv[1] == "c":
    job_type = 0
    if (len (sys.argv) != 3):
        print _("Wrong number of arguments.")

        print _("Wrapper script for Gnome-schedule (http://gnome-schedule.sf.net) for applications to be run from crontab or at under X. Use through gnome-schedule.")
        sys.exit (1)

elif sys.argv[1] == "a":
    job_type = 1
else:
    print _("Unknown type of job.")
    sys.exit (1)

uid = os.geteuid ()
gid = os.getegid ()
user = pwd.getpwuid (uid)[0]
home_dir = pwd.getpwuid (uid)[5]
user_shell = pwd.getpwuid (uid)[6]
if uid == 0:
    is_root = True
else:
    is_root = False

# CRONTAB
if job_type == 0:

    try:
        job_id = int (sys.argv[2])
    except:
        print _("Invalid job id.")
        sys.exit (1)

    if job_id < 0:
        print _("Invalid job id.")
        sys.exit (1)

    c = crontab.Crontab (is_root, user, uid, gid, home_dir)
    success, ver, title, desc, output, display, command = c.get_job_data (job_id)

    if success == False:
        print _("Could not get job data, the task might have been created with an old version - try recreating the task.")
        sys.exit (1)

    if ver < 5:
        print _("Data file too old. Recreate task.")
        sys.exit (1)


    print _("Launching %s.." % title)
    if (output < 2):
        print _("output<2: Why am I launched?")
        sys.exit (1)
    if (len (display) < 2):
        print _("len(display)<2: No proper DISPLAY variable")
        sys.exit (1)

    # TODO: Can/Does this change ?
    xauth = home_dir + "/.Xauthority"

    check_X (display, xauth)

    # Execute task
    sh = os.popen ("/bin/sh -s", 'w')
    sh.write ("export DISPLAY=" + display + "\n")
    sh.write ("export XAUTHORITY=" + xauth + "\n")
    sh.write (command + "\n")
    sh.close ()

    sys.exit ()

# AT
elif (job_type == 1):
    display = os.getenv ('DISPLAY')
    xauth = home_dir + "/.Xauthority"
    check_X (display, xauth)
    sys.exit (0) # All fine

else:
    print _("I will never be displayed.")
    sys.exit (1)

print _("xwrapper.py: completed")


