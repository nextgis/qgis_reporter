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
from PyQt4.QtXml import *

from qgis.core import *
from qgis.gui import *

from ui_reporterdialogbase import Ui_ReporterDialog
import reporter_utils as utils

class ReporterDialog( QDialog, Ui_ReporterDialog ):
  def __init__( self, iface ):
    QDialog.__init__( self )
    self.setupUi( self )
    self.iface = iface

    self.config = None
    self.cfgRoot = None

    self.btnOk = self.buttonBox.button( QDialogButtonBox.Ok )
    self.btnClose = self.buttonBox.button( QDialogButtonBox.Close )

    QObject.connect( self.lstLayers, SIGNAL( "itemChanged( QTreeWidgetItem*, int )" ), self.updateConfig )
    QObject.connect( self.lstLayers, SIGNAL( "itemDoubleClicked( QTreeWidgetItem*, int )" ), self.openConfigDialog )

    QObject.connect( self.btnNewConfig, SIGNAL( "clicked ()" ), self.newConfiguration )
    QObject.connect( self.btnLoadConfig, SIGNAL( "clicked ()" ), self.loadConfiguration )
    QObject.connect( self.btnSaveConfig, SIGNAL( "clicked ()" ), self.saveConfiguration )

    QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.setOutDirectory )

    self.manageGui()

  def manageGui( self ):
    # load settings
    settings = QSettings( "NextGIS", "reporter" )
    self.chkUseSelection.setChecked( settings.value( "useSelection", False ).toBool() )

    # setup controls
    self.btnSaveConfig.setEnabled( False )

    # populate GUI
    self.cmbAnalysisRegion.addItems( utils.getVectorLayersNames( [ QGis.Polygon ] ) )
    layers = utils.getVectorLayersNames( [ QGis.Polygon ] )
    for lay in layers:
      ti = QTreeWidgetItem( self.lstLayers )
      ti.setText( 0, lay )
      ti.setCheckState( 0, Qt.Unchecked )

  def setOutDirectory( self ):
    outDir = utils.getExistingDirectory( self, self.tr( "Select output directory" ) )
    if outDir:
      self.leOutputDirectory.setText( outDir )

  def newConfiguration( self ):
    self.config = QDomDocument( "reporter_config" )
    self.cfgRoot = self.config.createElement( "reporter_config" )
    self.config.appendChild( self.cfgRoot )

    # enable save button
    self.btnSaveConfig.setEnabled( True )

  def loadConfiguration( self ):
    fileName = utils.openConfigFile( self, self.tr( "Load configuration" ), self.tr( "XML files (*.xml *.XML)" ) )
    if not fileName:
      return

    fl = QFile( fileName )
    if not fl.open( QIODevice.WriteOnly | QIODevice.Text ):
      QMessageBox.warning( self,
                           self.tr( "Load error" ),
                           self.tr( "Cannot read file %1:\n%2." )
                           .arg( fileName )
                           .arg( fl.errorString() ) )
      return

    self.config = QDomDocument()
    setOk, errorString, errorLine, errorColumn = self.config.setContent( fl, True )
    if not setOk:
      QMessageBox.warning( self,
                           self.tr( "Load error" ),
                           self.tr( "Parse error at line %1, column %2:\n%3" )
                           .arg( errorLine )
                           .arg( errorColumn )
                           .arg( errorString ) )
      self.config = None
      fl.close()
      return

    fl.close()

    # enable save button
    self.btnSaveConfig.setEnabled( True )

    self.cfgRoot = doc.documentElement()

    # parse configuration and update UI

  def saveConfiguration( self ):
    fileName = utils.saveConfigFile( self, self.tr( "Save configuration" ), self.tr( "XML files (*.xml *.XML)" ) )
    if not fileName:
      return

    fl = QFile( fileName )
    if not fl.open( QIODevice.WriteOnly | QIODevice.Text ):
      QMessageBox.warning( self,
                           self.tr( "Save error" ),
                           self.tr( "Cannot write file %1:\n%2." )
                           .arg( fileName )
                           .arg( fl.errorString() ) )
      return

    out = QTextStream( fl )
    self.config.save( out, 4 )
    fl.close()

  def openConfigDialog( self, item, column ):
    print "DOUBLECLICKED", column, item.text( 0 )

  def updateConfig( self, item, column ):
    if item.checkState( 0 ) == Qt.Checked:
      print "CHECKED", item.text( 0 )
    else:
      print "UNCHECKED", item.text( 0 )

  def accept( self ):
    # save settings
    settings = QSettings( "NextGIS", "reporter" )
    settings.setValue( "useSelection", self.chkUseSelection.isChecked() )

    # process layers
    for i in xrange( self.lstLayers.topLevelItemCount() ):
      item = self.lstLayers.topLevelItem( i )
      if item.checkState( 0 ) == Qt.Checked:
        print "ITEM", item.text( 0 )
