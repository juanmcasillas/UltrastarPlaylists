#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# helper.py
# 09/27/2023 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# implements a class with method helpers
#
# ############################################################################

import os
import shutil
import datetime


class Helper:

    @staticmethod
    def seconds_to_str(seconds, trim=False):
        """convert seconds to hh:mm:ss.uu repr

        Args:
            seconds (float): seconds
            trim (bool): if found, remove the microseconds

        Returns:
            str: string with hh:mm:ss.uu representation
        """
        s = str(datetime.timedelta(seconds=seconds))
        if trim:
            s = s.split(".")[0]
        return s

    @staticmethod
    def do_backup(filename, ext="bak"):
        """copy filename to filename.bak if backup doesn't exists

        Args:
            filename (str): the source file
            ext (str, optional): _description_. Defaults to "bak".
        """
        bckfile = "%s.%s" % (filename, ext)
        if os.path.exists(filename) and not os.path.exists(bckfile):
            shutil.copy2(filename, bckfile)