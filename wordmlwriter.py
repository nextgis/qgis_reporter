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
    self.report = QString( "" )

  def addTitle( self, layerName ):
    self.report += '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
    self.report += self.tr( '<w:r><w:t>Cool report for layer: </w:t></w:r>' )
    self.report += QString( '<w:r><w:rPr><w:b/></w:rPr><w:t>%1</w:t></w:r>' ).arg( layerName )
    self.report += '</w:p>\n'

  def addAreaTable( self, fieldName, tableData ):
    # table
    self.report += '<w:tbl><w:tblPr><w:tblStyle w:val="MyTable"/><w:tblW w:w="0" w:type="auto"/><w:tblLook w:val="01E0"/></w:tblPr>\n'
    self.report += '<w:tblGrid><w:gridCol w:w="3190"/><w:gridCol w:w="3190"/><w:gridCol w:w="3190"/></w:tblGrid>\n'

    # header
    self.report += '<w:tr><w:trPr><w:cnfStyle w:val="100000000000"/></w:trPr>\n'
    self.addAreaTableCell( fieldName )
    self.addAreaTableCell( self.tr( "Area" ) )
    self.addAreaTableCell( self.tr( "Percents" ) )
    self.report += '</w:tr>\n'

    # table data
    coef = 100.0 / tableData[ "totalArea" ]
    del tableData[ "totalArea" ]
    for k, v in tableData.iteritems():
      self.report += '<w:tr>'
      self.addAreaTableCell( k )
      self.addAreaTableCell( v )
      self.addAreaTableCell( v * coef )
      self.report += '</w:tr>\n'

    # close table
    self.report += '</w:tbl>\n<w:p/>\n'

  def addAreaTableCell( self, cellValue ):
    self.report += '<w:tc><w:tcPr><w:tcW w:w="3190" w:type="dxa"/></w:tcPr>'
    self.report += QString( '<w:p><w:r><w:t>%1</w:t></w:r></w:p></w:tc>\n' ).arg( cellValue )

  def addThematicImage( self, layerName, image ):
    self.report += '<w:p><w:r><w:pict>'
    self.report += QString( '<w:binData w:name="wordml://%1">' ).arg( layerName )
    self.report += image
    self.report += '</w:binData><v:shape id="_x0000_i1025" type="#_x0000_t75" style="width:467pt;height:330.1pt">'
    self.report += QString( '<v:imagedata src="wordml://%1" o:title="map"/>' ).arg( layerName )
    self.report += '</v:shape></w:pict></w:r></w:p>'

  def closeReport( self ):
    self.report += "</wx:sect></w:body></w:wordDocument>"

  def write( self, fileName ):
    f = QFile( ":/myReportTemplate.xml" )
    f.open( QIODevice.ReadOnly | QIODevice.Text )
    reportFooter = QString.fromUtf8( f.readAll( ) )
    f.close()

    f = QFile( fileName )
    if not f.open( QIODevice.WriteOnly | QIODevice.Text ):
      return ( False, f.errorString() )

    out = QTextStream( f )
    out << reportFooter
    out << self.report
    f.close()
