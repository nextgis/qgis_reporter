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

import layersettingsdialog
import wordmlwriter
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

    QObject.connect( self.lstLayers, SIGNAL( "itemChanged( QTreeWidgetItem*, int )" ), self.toggleLayer )
    QObject.connect( self.lstLayers, SIGNAL( "itemDoubleClicked( QTreeWidgetItem*, int )" ), self.openConfigDialog )

    QObject.connect( self.btnNewConfig, SIGNAL( "clicked ()" ), self.newConfiguration )
    QObject.connect( self.btnLoadConfig, SIGNAL( "clicked ()" ), self.loadConfiguration )
    QObject.connect( self.btnSaveConfig, SIGNAL( "clicked ()" ), self.saveConfiguration )

    QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.setOutput )

    self.manageGui()

  def manageGui( self ):
    # hide some UI elements
    self.chkUseSelection.hide()

    # load settings
    settings = QSettings( "NextGIS", "reporter" )
    self.chkUseSelection.setChecked( settings.value( "useSelection", False ).toBool() )

    # setup controls
    self.btnSaveConfig.setEnabled( False )
    self.lstLayers.setEnabled( False )

    # populate GUI
    self.cmbAnalysisRegion.addItems( utils.getVectorLayersNames( [ QGis.Polygon ] ) )
    layers = utils.getVectorLayersNames( [ QGis.Polygon ] )
    self.lstLayers.blockSignals( True )
    for lay in layers:
      ti = QTreeWidgetItem( self.lstLayers )
      ti.setText( 0, lay )
      ti.setCheckState( 0, Qt.Unchecked )
    self.lstLayers.blockSignals( False )

  def setOutput( self ):
    #outDir = utils.getExistingDirectory( self, self.tr( "Select output directory" ) )
    outDir = utils.saveReportFile( self,
                                   self.tr( "Select output directory" ),
                                   self.tr( "Micosoft Word 2003 (*.doc *.DOC)" ) )
    if outDir:
      self.leOutput.setText( outDir )

  def newConfiguration( self ):
    self.config = QDomDocument( "reporter_config" )
    self.cfgRoot = self.config.createElement( "reporter_config" )
    self.cfgRoot.setAttribute( "version", "1.0" )
    self.config.appendChild( self.cfgRoot )

    # enable controls
    self.btnSaveConfig.setEnabled( True )
    self.lstLayers.setEnabled( True )

  def loadConfiguration( self ):
    fileName = utils.openConfigFile( self,
                                     self.tr( "Load configuration" ),
                                     self.tr( "XML files (*.xml *.XML)" ) )
    if not fileName:
      return

    fl = QFile( fileName )
    if not fl.open( QIODevice.ReadOnly | QIODevice.Text ):
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

    # parse configuration and update UI
    self.cfgRoot = self.config.documentElement()

    self.lstLayers.blockSignals( True )

    missedLayers = []
    child = self.cfgRoot.firstChildElement()
    while not child.isNull():
      items = self.lstLayers.findItems( child.attribute( "name" ), Qt.MatchExactly, 0 )
      if len( items ) > 0:
        items[ 0 ].setCheckState( 0, Qt.Checked )
      else:
        missedLayers.append( child.attribute( "name" ) )
      child = child.nextSiblingElement()

    self.lstLayers.blockSignals( False )

    # config cleanup
    if len( missedLayers ) > 0:
      for lay in missedLayers:
        utils.removeLayerFromConfig( self.cfgRoot, lay )

    # enable controls
    self.btnSaveConfig.setEnabled( True )
    self.lstLayers.setEnabled( True )

  def saveConfiguration( self ):
    fileName = utils.saveConfigFile( self,
                                     self.tr( "Save configuration" ),
                                     self.tr( "XML files (*.xml *.XML)" ) )
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

    # cleanup config and update UI
    self.cleanupConfigAndGui()

    out = QTextStream( fl )
    self.config.save( out, 4 )
    fl.close()

  def openConfigDialog( self, item, column ):
    layerElement = utils.findLayerInConfig( self.cfgRoot, item.text( 0 ) )
    if layerElement == None:
      return

    d = layersettingsdialog.LayerSettingsDialog( self )

    # update dialog
    d.setAreasReport( utils.hasReport( layerElement, "area" ) )
    d.setObjectsReport( utils.hasReport( layerElement, "objects" ) )
    d.setOtherReport( utils.hasReport( layerElement, "other" ) )

    if not d.exec_() == QDialog.Accepted:
      return

    # update layer config if necessary
    if d.areasReport():
      utils.addLayerReport( self.config, layerElement, "area" )
    else:
      utils.removeLayerReport( layerElement, "area" )

    if d.objectsReport():
      utils.addLayerReport( self.config, layerElement, "objects" )
    else:
      utils.removeLayerReport( layerElement, "objects" )

    if d.otherReport():
      utils.addLayerReport( self.config, layerElement, "other" )
    else:
      utils.removeLayerReport( layerElement, "other" )

  def toggleLayer( self, item, column ):
    if self.config:
      if item.checkState( 0 ) == Qt.Checked:
        utils.addLayerToConfig( self.config, self.cfgRoot, item.text( 0 ) )
      else:
        utils.removeLayerFromConfig( self.cfgRoot, item.text( 0 ) )

  def cleanupConfigAndGui( self ):
    missedLayers = utils.layersWithoutReports( self.cfgRoot )
    if len( missedLayers ) > 0:
      self.lstLayers.blockSignals( True )
      for lay in missedLayers:
        utils.removeLayerFromConfig( self.cfgRoot, lay )
        items = self.lstLayers.findItems( lay, Qt.MatchExactly, 0 )
        items[ 0 ].setCheckState( 0, Qt.Unchecked )
      self.lstLayers.blockSignals( False )

  def accept( self ):
    if not self.config:
      return

    self.cleanupConfigAndGui()

    # save settings
    settings = QSettings( "NextGIS", "reporter" )
    settings.setValue( "useSelection", self.chkUseSelection.isChecked() )

    # process layers
    for i in xrange( self.lstLayers.topLevelItemCount() ):
      item = self.lstLayers.topLevelItem( i )
      if item.checkState( 0 ) == Qt.Checked:
        print "PROCESSING", item.text( 0 )
        cLayer = utils.findLayerInConfig( self.cfgRoot, item.text( 0 ) )

        if utils.hasReport( cLayer, "area" ):
          print "RUNNIG AREA REPORT"
          self.areaReport( item.text( 0 ) )

  def areaReport( self, layerName ):
    layerA = utils.getVectorLayerByName( self.cmbAnalysisRegion.currentText() )
    providerA = layerA.dataProvider()

    layerB = utils.getVectorLayerByName( layerName )
    providerB = layerB.dataProvider()

    # determine classification field
    renderer = None
    if layerB.isUsingRendererV2():
      renderer = layerB.rendererV2()

    if renderer.type() != "categorizedSymbol":
      print "INVALID RENDERER TYPE"
      return

    fieldName = renderer.classAttribute()
    fieldIndex = utils.fieldIndexByName( providerB, fieldName )
    print "CLASS ATTR", fieldName, fieldIndex

    #~ mLayer = QgsVectorLayer( "Polygon", "tempPoly", "memory" )
    #~ mProvider = mLayer.dataProvider()
    #~ mProvider.addAttributes( [ QgsField( "class", QVariant.String ) ] )
    #~ mLayer.updateFieldMap()

    index = utils.createSpatialIndex( providerB )

    featA = QgsFeature()
    featB = QgsFeature()
    outFeat = QgsFeature()

    if self.chkUseSelection.isChecked():
      print "Use selection option currently not supported"
    else:
      nFeat = providerA.featureCount()

      while providerA.nextFeature( featA ):
        rptData = dict()
        geom = QgsGeometry( featA.geometry() )
        intersects = index.intersects( geom.boundingBox() )
        for i in intersects:
          providerB.featureAtId( int( i ), featB , True, [ fieldIndex ] )
          tmpGeom = QgsGeometry( featB.geometry() )

          if geom.intersects( tmpGeom ):
            attrMap = featB.attributeMap()
            intGeom = QgsGeometry( geom.intersection( tmpGeom ) )
            if intGeom.wkbType() == 7:
              intCom = geom.combine( tmpGeom )
              intSym = geom.symDifference( tmpGeom )
              intGeom = QgsGeometry( intCom.difference( intSym ) )

            if attrMap[0].toString() not in rptData:
              rptData[ attrMap[0].toString() ] = intGeom.area()
            else:
              rptData[ attrMap[0].toString() ] += intGeom.area()

            #~ outFeat.setGeometry( intGeom )
            #~ outFeat.setAttributeMap( attrMap )
            #~ mProvider.addFeatures( [ outFeat ] )

    #~ mLayer.updateExtents()
    #~ QgsMapLayerRegistry.instance().addMapLayer( mLayer )
        rptData[ "totalArea" ] = geom.area()
        print "DATA", rptData
