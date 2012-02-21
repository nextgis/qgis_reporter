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

class ODFReportWriter( QObject ):
  def __init__( self ):
    QObject.__init__( self )
    self.doc = QTextDocument()
    self.cursor = QTextCursor( self.doc )

  def writeTitle( self, layerName ):
    self.cursor.insertText( self.tr( "Report for layer %1\n" ).arg( layerName ) )

  def writeAreaTable( self, fieldName, tableData ):
    tableFormat = QTextTableFormat()
    tableFormat.setCellPadding( 5 )
    tableFormat.setHeaderRowCount( 1 )
    tableFormat.setBorderStyle( QTextFrameFormat.BorderStyle_Solid )
    tableFormat.setWidth( QTextLength( QTextLength.PercentageLength, 100 ) )

    # table header
    self.cursor.insertTable( 1, 3, tableFormat )
    self.cursor.insertText( fieldName )
    self.cursor.movePosition( QTextCursor.NextCell )
    self.cursor.insertText( self.tr( "Area" ) )
    self.cursor.movePosition( QTextCursor.NextCell)
    self.cursor.insertText( self.tr( "Total area percent" ) )

    table = self.cursor.currentTable()

    # process data
    coef = 100.0 / tableData[ "totalArea" ]
    del tableData[ "totalArea" ]
    for k, v in tableData.iteritems():
      table.appendRows( 1 )
      self.cursor.movePosition( QTextCursor.PreviousRow )
      self.cursor.movePosition( QTextCursor.NextCell )
      self.cursor.insertText( k )
      self.cursor.movePosition( QTextCursor.NextCell )
      self.cursor.insertText( QString.number( v ) )
      self.cursor.movePosition( QTextCursor.NextCell )
      self.cursor.insertText( QString( "%1%" ).arg( v * coef ) )

  def writeToFile( self, fileName ):
    writer = QTextDocumentWriter( fileName )
    writer.write( self.doc )
