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
    self.readSettings()

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

    if self.chkLoadLastProfile.isChecked() and not self.lblProfilePath.text().isEmpty():
      self.readConfigurationFile( self.lblProfilePath.text() )

  def setOutput( self ):
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

    self.readConfigurationFile( fileName )

  def readConfigurationFile( self, fileName ):
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

    self.lblProfilePath.setText( fileName )

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

    self.lblProfilePath.setText( fileName )

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

  def readSettings( self ):
    settings = QSettings( "NextGIS", "reporter" )
    self.chkUseSelection.setChecked( settings.value( "useSelection", False ).toBool() )
    self.chkLoadLastProfile.setChecked( settings.value( "loadLastProfile", False ).toBool() )
    self.chkCreateMaps.setChecked( settings.value( "createMaps", True ).toBool() )
    self.chkAddMapsToReport.setChecked( settings.value( "mapsInReport", True ).toBool() )
    self.lblProfilePath.setText( settings.value( "lastProfile", "" ).toString() )

    # dimensioning buttons
    if settings.value( "dimensioning", "none" ).toString() == "none":
      self.rbSimpleUnits.setChecked( True )
    elif settings.value( "dimensioning", "none" ).toString() == "kilo":
      self.rbKiloUnits.setChecked( True )
    else:
      self.rbMegaUnits.setChecked( True )

  def saveSettings( self ):
    settings = QSettings( "NextGIS", "reporter" )
    settings.setValue( "useSelection", self.chkUseSelection.isChecked() )
    settings.setValue( "loadLastProfile", self.chkLoadLastProfile.isChecked() )
    settings.setValue( "createMaps", self.chkCreateMaps.isChecked() )
    settings.setValue( "mapsInReport", self.chkAddMapsToReport.isChecked() )
    settings.setValue( "lastProfile", self.lblProfilePath.text() )

    # dimensioning buttons
    if self.rbSimpleUnits.isChecked():
      settings.setValue( "dimensioning", "none" )
    elif self.rbKiloUnits.isChecked():
      settings.setValue( "dimensioning", "kilo" )
    else:
      settings.setValue( "dimensioning", "mega" )

  def accept( self ):
    if not self.config:
      return

    if self.leOutput.text().isEmpty():
      QMessageBox.warning( self,
                           self.tr( "Reporter" ),
                           self.tr( "Please specify output report file" ) )
      return

    self.cleanupConfigAndGui()

    self.btnOk.setEnabled( False )

    # save settings
    self.saveSettings()

    # get layer count
    layerCount = 0
    for i in xrange( self.lstLayers.topLevelItemCount() ):
      item = self.lstLayers.topLevelItem( i )
      if item.checkState( 0 ) == Qt.Checked:
        layerCount += 1

    self.progressBar.setRange( 0, layerCount )

    # get extent of the overlay geometry (for reports)
    vl = utils.getVectorLayerByName( self.cmbAnalysisRegion.currentText() )
    ft = QgsFeature()
    vl.featureAtId( 0, ft, True, False )
    rect = ft.geometry().boundingBox()
    t = rect.width() * 0.05
    rect.setXMinimum( rect.xMinimum() - t )
    rect.setXMaximum( rect.xMaximum() + t )
    rect.setYMinimum( rect.yMinimum() - t )
    rect.setYMaximum( rect.yMaximum() + t )

    crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
    otf = self.iface.mapCanvas().hasCrsTransformEnabled()

    # output dir
    dirName = QFileInfo( self.leOutput.text() ).absolutePath()

    # init report writer
    writer = wordmlwriter.WordMLWriter()

    # process layers
    for i in xrange( self.lstLayers.topLevelItemCount() ):
      item = self.lstLayers.topLevelItem( i )

      # maybe can be safely removed, because we run check before this
      if item.checkState( 0 ) == Qt.Unchecked:
        continue

      currentLayerName = item.text( 0 )
      #print "processing", unicode( currentLayerName )
      cLayer = utils.findLayerInConfig( self.cfgRoot, currentLayerName )

      self.progressBar.setFormat( "%p% " + currentLayerName )
      self.progressBar.setValue( self.progressBar.value() + 1 )
      QCoreApplication.processEvents()

      # create map
      if self.chkCreateMaps.isChecked():
        vlThematic = utils.getVectorLayerByName( currentLayerName )
        #~ utils.createMapImage( vl, vlThematic, rect, self.iface.mapCanvas().scale(), dirName + "/" + currentLayerName, crs, otf )

      # print title
      writer.addTitle( currentLayerName )

      if utils.hasReport( cLayer, "area" ):
        #print "running area report"
        self.areaReport( writer, currentLayerName, rect, crs, otf )
        writer.addPageBreak()

    # write report to file
    writer.closeReport()
    writer.write( self.leOutput.text() )

    self.progressBar.setFormat( "%p%" )
    self.progressBar.setValue( 0 )
    QMessageBox.information( self,
                             self.tr( "Reporter" ),
                             self.tr( "Completed!" ) )

    self.btnOk.setEnabled( True )

  def areaReport( self, writer, layerName, rect, crs, otf ):
    layerA = utils.getVectorLayerByName( self.cmbAnalysisRegion.currentText() )
    providerA = layerA.dataProvider()

    layerB = utils.getVectorLayerByName( layerName )
    providerB = layerB.dataProvider()

    providerA.rewind()
    providerA.select( providerA.attributeIndexes() )
    providerB.rewind()
    providerB.select( providerB.attributeIndexes() )

    crsTransform = QgsCoordinateTransform( layerA.crs(), self.iface.mapCanvas().mapRenderer().destinationCrs() )

    # get dimensioning coefficient
    coef = 1.0
    if self.rbSimpleUnits.isChecked():
      coef = 1.0
    elif self.rbKiloUnits.isChecked():
      coef = 0.0001
    else:
      coef = 0.0000001

    # determine classification field
    rendererType = None
    fieldName = None
    fieldIndex = None

    if layerB.isUsingRendererV2():
      renderer = layerB.rendererV2()
      rendererType = renderer.type()

      fieldName = renderer.classAttribute()
      fieldIndex = utils.fieldIndexByName( providerB, fieldName )
    else:
      renderer = layerB.renderer()
      rendererType = renderer.name()

      fieldIndex = renderer.classificationField()
      fieldName = utils.fieldNameByIndex( providerB, fieldIndex )

    if rendererType not in [ "categorizedSymbol", "Unique Value" ]:
      #print "Invalid renderer type!"
      return

    index = utils.createSpatialIndex( providerB )

    featA = QgsFeature()
    featB = QgsFeature()
    outFeat = QgsFeature()

    if self.chkUseSelection.isChecked():
      #print "Use selection option currently not supported!"
      pass
    else:
      nFeat = providerA.featureCount()
      className = None

      rptData = dict()

      while providerA.nextFeature( featA ):
        rptData.clear()
        geom = QgsGeometry( featA.geometry() )
        if geom.transform( crsTransform ) != 0:
          continue
        rptData[ "totalArea" ] = float( geom.area() * coef )
        intersects = index.intersects( geom.boundingBox() )
        for i in intersects:
          providerB.featureAtId( int( i ), featB , True, [ fieldIndex ] )
          tmpGeom = QgsGeometry( featB.geometry() )

          if geom.intersects( tmpGeom ):
            attrMap = featB.attributeMap()
            className = attrMap.values()[ 0 ].toString()
            intGeom = QgsGeometry( geom.intersection( tmpGeom ) )
            if intGeom.wkbType() == 7:
              intCom = geom.combine( tmpGeom )
              intSym = geom.symDifference( tmpGeom )
              intGeom = QgsGeometry( intCom.difference( intSym ) )

            if className not in rptData:
              rptData[ className ] = float( intGeom.area() * coef )
            else:
              rptData[ className ] += float( intGeom.area() * coef )

        # process only first feature
        break

    writer.addAreaTable( fieldName, rptData )

    # add image if requested
    #~ if self.chkAddMapsToReport.isChecked():
      #~ img = utils.mapForReport( layerA, layerB, rect, self.iface.mapCanvas().scale(), crs, otf )
      #~ writer.addThematicImage( layerName, img )
