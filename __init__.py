# -*- coding: utf-8 -*-

#******************************************************************************
#
# Taimyr - Reporter
# ---------------------------------------------------------
# Generates reports.
#
# Copyright (C) 2012 NextGIS, http://nextgis.org
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
#******************************************************************************

def name():
  return "Taimyr - Reporter"

def description():
  return "Generates reports"

def category():
  return "Vector"

def version():
  return "0.0.1"

def qgisMinimumVersion():
  return "1.0.0"

def authorName():
  return "NextGIS"

def icon():
  return "icons/reporter.png"

def classFactory( iface ):
  from reporter import ReporterPlugin
  return ReporterPlugin( iface )
