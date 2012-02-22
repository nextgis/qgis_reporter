# -*- coding: utf-8 -*-

#******************************************************************************
#
# Reporter
# ---------------------------------------------------------
# Generates reports.
#
# Copyright (C) 2012 Alexander Bruy (alexander.bruy@gmail.com), NextGIS
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import resources_rc

class WordMLWriter( QObject ):
  def __init__( self ):
    QObject.__init__( self )

    f = QFile( ":/report_template.xml" )
    f.open( QIODevice.ReadOnly | QIODevice.Text )
    self.report = QString.fromUtf8( f.readAll( ) )
    f.close()

  def addTitle( self ):
    pass

  def addAreaTable( self, fieldName, tableData ):
    pass

  def write( self, fileName ):
    f = QFile( fileName )
    if not f.open( QIODevice.WriteOnly | QIODevice.Text ):
      return ( False, f.errorString() )

    out = QTextStream( f )
    out << self.report
    f.close()
