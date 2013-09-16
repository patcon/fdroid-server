#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# publish.py - part of the FDroid server tools
# Copyright (C) 2010-13, Ciaran Gultnieks, ciaran@ciarang.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import shutil
import subprocess
import glob
from optparse import OptionParser

from common import BuildException

def main():

    #Read configuration...
    execfile('config.py', globals())

    # Parse command line...
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      help="Spew out even more information than normal")
    parser.add_option("-p", "--package", default=None,
                      help="Verify only the specified package")
    (options, args) = parser.parse_args()

    tmp_dir = 'tmp'
    if not os.path.isdir(tmp_dir):
        print "Creating temporary directory"
        os.makedirs(tmp_dir)

    unsigned_dir = 'unsigned'
    if not os.path.isdir(unsigned_dir):
        print "No unsigned directory - nothing to do"
        sys.exit(0)

    verified = 0
    notverified = 0

    for apkfile in sorted(glob.glob(os.path.join(unsigned_dir, '*.apk'))):

        apkfilename = os.path.basename(apkfile)
        i = apkfilename.rfind('_')
        if i == -1:
            raise BuildException("Invalid apk name")
        appid = apkfilename[:i]

        if not options.package or options.package == appid:

            try:

                print "Processing " + apkfilename

                remoteapk = os.path.join(tmp_dir, apkfilename)
                if os.path.exists(remoteapk):
                    os.remove(remoteapk)
                url = 'https://f-droid.org/repo/' + apkfilename
                print "...retrieving " + url
                p = subprocess.Popen(['wget', url],
                    cwd=tmp_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out = p.communicate()[0]
                if p.returncode != 0:
                    raise Exception("Failed to get " + apkfilename)

                thisdir = os.path.join(tmp_dir, 'this_apk')
                thatdir = os.path.join(tmp_dir, 'that_apk')
                for d in [thisdir, thatdir]:
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    os.mkdir(d)

                if subprocess.call(['jar', 'xf',
                    os.path.join("..", "..", unsigned_dir, apkfilename)],
                    cwd=thisdir) != 0:
                    raise Exception("Failed to unpack local build of " + apkfilename)
                if subprocess.call(['jar', 'xf', os.path.join("..", "..", remoteapk)],
                    cwd=thatdir) != 0:
                    raise Exception("Failed to unpack remote build of " + apkfilename)

                p = subprocess.Popen(['diff', '-r', 'this_apk', 'that_apk'],
                    cwd=tmp_dir, stdout=subprocess.PIPE)
                out = p.communicate()[0]
                lines = out.splitlines()
                if len(lines) != 1 or lines[0].find('META-INF') == -1:
                    raise Exception("Unexpected diff output - " + out)

                print "...successfully verified"
                verified += 1

            except Exception, e:
                print "...NOT verified - {0}".format(e)
                notverified += 1

    print "\nFinished"
    print "{0} successfully verified".format(verified)
    print "{0} NOT verified".format(notverified)

if __name__ == "__main__":
    main()

