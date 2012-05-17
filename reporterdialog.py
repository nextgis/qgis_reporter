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
    self.readSettings()

    self.btnSaveConfig.setEnabled( False )
    self.lstLayers.setEnabled( False )

    self.cmbAnalysisRegion.addItems( utils.getVectorLayersNames( [ QGis.Polygon ] ) )
    layers = utils.getVectorLayersNames( [ QGis.Polygon ] )
    self.lstLayers.blockSignals( True )
    for lay in layers:
      ti = QTreeWidgetItem( self.lstLayers )
      ti.setText( 0, lay )
      ti.setCheckState( 0, Qt.Unchecked )
    self.lstLayers.blockSignals( False )

    if self.chkLoadLastProfile.isChecked() and not self.lblProfilePath.text().isEmpty():
      self.readConfigurationFile( self.lblProfilePath.text().split( ": " )[ 1 ] )

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

    self.btnSaveConfig.setEnabled( True )
    self.lstLayers.setEnabled( True )

    self.lblProfilePath.setText( self.tr( "Config file: %1" ).arg( fileName ) )

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

    self.lblProfilePath.setText( self.tr( "Config file: %1" ).arg( fileName ) )

  def openConfigDialog( self, item, column ):
    layerElement = utils.findLayerInConfig( self.cfgRoot, item.text( 0 ) )
    if layerElement == None:
      return

    vLayer = utils.getVectorLayerByName( item.text( 0 ) )
    vProvider = vLayer.dataProvider()

    # check layer renderer and determine classification field
    fieldName = None
    fieldIndex = None

    if vLayer.isUsingRendererV2():
      renderer = vLayer.rendererV2()
      rendererType = renderer.type()
      fieldName = renderer.classAttribute()
      fieldIndex = utils.fieldIndexByName( vProvider, fieldName )
    else:
      renderer = vLayer.renderer()
      rendererType = renderer.name()
      fieldIndex = renderer.classificationField()
      fieldName = utils.fieldNameByIndex( vProvider, fieldIndex )

    d = layersettingsdialog.LayerSettingsDialog( self, vLayer )

    d.setAreasReport( utils.hasReport( layerElement, "area" ) )
    d.setObjectsReport( utils.hasReport( layerElement, "objects" ) )
    myLabelFieldName = utils.labelFieldName( layerElement )
    if myLabelFieldName.isEmpty():
      d.setLabelField( fieldName )
    else:
      d.setLabelField( myLabelFieldName )

    d.setComment( utils.layerComment( layerElement ) )

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

    utils.setLabelFieldName( self.config, layerElement, d.getLabelField() )
    utils.setLayerComment( self.config, layerElement, d.getComment() )

  def toggleLayer( self, item, column ):
    if self.config:
      if item.checkState( 0 ) == Qt.Checked:
        utils.addLayerToConfig( self.config, self.cfgRoot, item.text( 0 ) )

        layerElement = utils.findLayerInConfig( self.cfgRoot, item.text( 0 ) )

        vLayer = utils.getVectorLayerByName( item.text( 0 ) )
        vProvider = vLayer.dataProvider()

        # check layer renderer and determine classification field
        fieldName = None
        fieldIndex = None

        if vLayer.isUsingRendererV2():
          renderer = vLayer.rendererV2()
          rendererType = renderer.type()
          fieldName = renderer.classAttribute()
          fieldIndex = utils.fieldIndexByName( vProvider, fieldName )
        else:
          renderer = vLayer.renderer()
          rendererType = renderer.name()
          fieldIndex = renderer.classificationField()
          fieldName = utils.fieldNameByIndex( vProvider, fieldIndex )

        d = layersettingsdialog.LayerSettingsDialog( self, vLayer )

        d.setAreasReport( utils.hasReport( layerElement, "area" ) )
        d.setObjectsReport( utils.hasReport( layerElement, "objects" ) )
        tmp = utils.labelFieldName( layerElement )
        if tmp.isEmpty():
          d.setLabelField( fieldName )
        else:
          d.setLabelField( tmp )

        d.setComment( utils.layerComment( layerElement ) )

        if not d.exec_() == QDialog.Accepted:
          item.setCheckState( 0, Qt.Unchecked )
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

        utils.setLabelFieldName( self.config, layerElement, d.getLabelField() )
        utils.setLayerComment( self.config, layerElement, d.getComment() )
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
    self.chkLoadLastProfile.setChecked( settings.value( "loadLastProfile", False ).toBool() )
    self.chkCreateMaps.setChecked( settings.value( "createMaps", True ).toBool() )
    self.chkAddMapsToReport.setChecked( settings.value( "mapsInReport", True ).toBool() )
    if self.chkLoadLastProfile.isChecked():
      self.lblProfilePath.setText( self.tr( "Config file: %1" ) .arg( settings.value( "lastProfile", "" ).toString() ) )
    else:
      self.lblProfilePath.setText( self.tr( "No profile loaded" ) )
    self.txtComment.setPlainText( settings.value( "comment", "" ).toString() )

    # dimensioning buttons
    if settings.value( "dimensioning", "none" ).toString() == "none":
      self.rbSimpleUnits.setChecked( True )
    elif settings.value( "dimensioning", "none" ).toString() == "kilo":
      self.rbKiloUnits.setChecked( True )
    else:
      self.rbMegaUnits.setChecked( True )

  def saveSettings( self ):
    settings = QSettings( "NextGIS", "reporter" )
    settings.setValue( "loadLastProfile", self.chkLoadLastProfile.isChecked() )
    settings.setValue( "createMaps", self.chkCreateMaps.isChecked() )
    settings.setValue( "mapsInReport", self.chkAddMapsToReport.isChecked() )
    if self.lblProfilePath.text().split( ": " ).count() > 1:
      settings.setValue( "lastProfile", self.lblProfilePath.text().split( ": " )[ 1 ] )
    settings.setValue( "comment", self.txtComment.toPlainText() )

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
    self.saveSettings()

    # get layer count
    layerCount = 0
    layerNames = []
    for i in xrange( self.lstLayers.topLevelItemCount() ):
      item = self.lstLayers.topLevelItem( i )
      if item.checkState( 0 ) == Qt.Checked:
        layerCount += 1
        layerNames.append( item.text( 0 ) )

    self.progressBar.setRange( 0, layerCount )

    QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
    self.btnOk.setEnabled( False )

    # ***************** create reports ************************
    overlayLayer = utils.getVectorLayerByName( self.cmbAnalysisRegion.currentText() )
    overlayProvider = overlayLayer.dataProvider()

    isFirst = True
    mapCRS = self.iface.mapCanvas().mapRenderer().destinationCrs()
    hasOTFR = self.iface.mapCanvas().hasCrsTransformEnabled()
    crsTransform = QgsCoordinateTransform( overlayLayer.crs(), mapCRS )
    needTransform = ( overlayLayer.crs() != mapCRS )
    dirName = QFileInfo( self.leOutput.text() ).absolutePath()

    # get dimensioning coefficient
    coef = 1.0
    settings = QSettings( "NextGIS", "reporter" )
    if settings.value( "dimensioning", "none" ).toString() == "none":
      coef = 1.0
    elif settings.value( "dimensioning", "none" ).toString() == "kilo":
      coef = 0.00001
    else:
      coef = 0.0000001

    # variables to store information used in reports
    dataArea = dict()
    dataObjects = dict()

    # init report writer
    writer = wordmlwriter.WordMLWriter()

    for layerName in layerNames:
      self.progressBar.setFormat( self.tr( "%p% processing: %1" ).arg( layerName ) )
      QCoreApplication.processEvents()

      layerElement = utils.findLayerInConfig( self.cfgRoot, layerName )
      labelFieldName = utils.labelFieldName( layerElement )

      vLayer = utils.getVectorLayerByName( layerName )
      vProvider = vLayer.dataProvider()

      vProvider.rewind()
      vProvider.select( vProvider.attributeIndexes() )

      # check layer renderer and determine classification field
      rendererType = None
      fieldName = None
      fieldIndex = None
      categories = None

      if vLayer.isUsingRendererV2():
        renderer = vLayer.rendererV2()
        rendererType = renderer.type()

        fieldName = renderer.classAttribute()
        fieldIndex = utils.fieldIndexByName( vProvider, fieldName )
        categories = renderer.categories()
      else:
        renderer = vLayer.renderer()
        rendererType = renderer.name()

        fieldIndex = renderer.classificationField()
        fieldName = utils.fieldNameByIndex( vProvider, fieldIndex )
        categories = renderer.symbolMap()

      # override fieldIndex using layer from config
      tryLegendLabels = False
      labelFieldIndex = utils.fieldIndexByName( vProvider, labelFieldName )
      if labelFieldIndex == fieldIndex:
        tryLegendLabels = True
      else:
        fieldIndex = labelFieldIndex

      # unsupported renderer, process next layer
      if rendererType not in [ "categorizedSymbol", "Unique Value" ]:
        print "Invalid renderer type! Skip this layer..."
        continue

      # prepare to collect information
      overlayFeat = QgsFeature()
      currentFeat = QgsFeature()
      geom = QgsGeometry()

      spatialIndex = utils.createSpatialIndex( vProvider )

      if overlayLayer.selectedFeatureCount() != 0:
        sel = overlayLayer.selectedFeaturesIds()
        overlayProvider.featureAtId( max( sel ), overlayFeat )
      else:
        overlayProvider.featureAtId( overlayProvider.featureCount() - 1, overlayFeat )

      dataArea.clear()
      dataObjects.clear()
      featureClass = None
      category = None

      geom = QgsGeometry( overlayFeat.geometry() )
      if needTransform:
        if geom.transform( crsTransform ) != 0:
          print "Unable transform geometry"
          continue

      dataArea[ "totalArea" ] = float( geom.area() * coef )

      # find intersections in data layer
      intersections = spatialIndex.intersects( geom.boundingBox() )
      for i in intersections:
        vProvider.featureAtId( int( i ), currentFeat, True, [ fieldIndex ] )
        tmpGeom = QgsGeometry( currentFeat.geometry() )
        # precision test for intersection
        if geom.intersects( tmpGeom ):
          # get data for area report
          attrMap = currentFeat.attributeMap()
          featureClass = attrMap.values()[ 0 ].toString()
          if tryLegendLabels:
            if vLayer.isUsingRendererV2():
              category = categories[ renderer.categoryIndexForValue( attrMap.values()[ 0 ] ) ].label()
            else:
              category = categories[ attrMap.values()[ 0 ].toString() ].label()

            if category.isEmpty():
              category = featureClass
          else:
            category = featureClass

          # count objects
          if category not in dataObjects:
            dataObjects[ category ] = 1
          else:
            dataObjects[ category ] += 1

          # calculate intersection area
          intGeom = QgsGeometry( geom.intersection( tmpGeom ) )
          if intGeom.wkbType() == 7:
            intCom = geom.combine( tmpGeom )
            intSym = geom.symDifference( tmpGeom )
            intGeom = QgsGeometry( intCom.difference( intSym ) )

          if category not in dataArea:
            dataArea[ category ] = float( intGeom.area() * coef )
          else:
            dataArea[ category ] += float( intGeom.area() * coef )

      # get extent of the overlay geometry (for reports)
      rect = geom.boundingBox()
      dw = rect.width() * 0.025
      dh = rect.height() * 0.025
      rect.setXMinimum( rect.xMinimum() - dw )
      rect.setXMaximum( rect.xMaximum() + dw )
      rect.setYMinimum( rect.yMinimum() - dh )
      rect.setYMaximum( rect.yMaximum() + dh )

      # create map
      mapImage = utils.createMapImage( overlayLayer, vLayer, rect, mapCRS, hasOTFR, dataObjects.keys() )

      # create all necessary reports
      layerConfig = utils.findLayerInConfig( self.cfgRoot, layerName )

      # add page break after first layer
      if not isFirst:
        writer.addPageBreak()
      isFirst = False

      # print title
      writer.addTitle( layerName )
      writer.addDescription( self.txtComment.toPlainText() )

      if utils.hasReport( layerConfig, "area" ):
        writer.addAreaTable( fieldName, dataArea )

      if utils.hasReport( layerConfig, "objects" ):
        writer.addObjectsTable( dataObjects )

      # embed image in report if requested
      if self.chkAddMapsToReport.isChecked():
        imgData = QByteArray()
        buff = QBuffer( imgData )
        buff.open( QIODevice.WriteOnly )
        mapImage.save( buff, "png" )
        writer.addThematicImage( layerName, QString.fromLatin1( imgData.toBase64() ) )

      # save separate map if requested
      if self.chkCreateMaps.isChecked():
        mapImage.save( dirName + "/" + layerName + ".png", "png" )

      self.progressBar.setValue( self.progressBar.value() + 1 )
      QCoreApplication.processEvents()

    # save report to files
    writer.closeReport()
    writer.write( self.leOutput.text() )

    # restore UI
    self.progressBar.setFormat( "%p%" )
    self.progressBar.setRange( 0, 1 )
    self.progressBar.setValue( 0 )

    QApplication.restoreOverrideCursor()
    self.btnOk.setEnabled( True )
