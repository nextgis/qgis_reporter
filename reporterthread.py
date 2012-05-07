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

from qgis.core import *
from qgis.gui import *

import wordmlwriter
import reporter_utils as utils

class ReporterThread( QThread ):
  def __init__( self, inLayerNames, overlayName, mapCRS, hasOTFR, reportConfig, outFile ):
    QThread.__init__( self, QThread.currentThread() )

    self.inLayers = inLayerNames
    self.overlayLayer = utils.getVectorLayerByName( overlayName )
    self.overlayProvider = self.overlayLayer.dataProvider()
    self.mapCRS = mapCRS
    self.hasOTFR = hasOTFR
    self.cfgRoot = reportConfig
    self.outFile = outFile

    self.mutex = QMutex()
    self.stopMe = 0

  def run( self ):
    self.mutex.lock()
    self.stopMe = 0
    self.mutex.unlock()

    interrupted = False

    # read settings
    settings = QSettings( "NextGIS", "reporter" )
    useSelection = settings.value( "useSelection", False ).toBool()
    createMaps = settings.value( "createMaps", True ).toBool()
    mapsInReport = settings.value( "mapsInReport", True ).toBool()

    # get dimensioning coefficient
    coef = 1.0
    if settings.value( "dimensioning", "none" ).toString() == "none":
      coef = 1.0
    elif settings.value( "dimensioning", "none" ).toString() == "kilo":
      coef = 0.00001
    else:
      coef = 0.0000001

    crsTransform = QgsCoordinateTransform( self.overlayLayer.crs(), self.mapCRS )
    dirName = QFileInfo( self.outFile ).absolutePath()
    isFirst = True
    needTransform = ( self.overlayLayer.crs() != self.mapCRS )

    # variables to store information used in reports
    dataArea = dict()
    dataObjects = dict()

    # init report writer
    writer = wordmlwriter.WordMLWriter()

    for layerName in self.inLayers:
      print "Processing", unicode( layerName )
      vLayer = utils.getVectorLayerByName( layerName )
      vProvider = vLayer.dataProvider()

      vProvider.rewind()
      vProvider.select( vProvider.attributeIndexes() )

      # check layer renderer and determine classification field
      rendererType = None
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

      # unsupported renderer, process next layer
      if rendererType not in [ "categorizedSymbol", "Unique Value" ]:
        print "Invalid renderer type! Skip this layer..."
        continue

      # prepare to collect information
      overlayFeat = QgsFeature()
      currentFeat = QgsFeature()

      spatialIndex = utils.createSpatialIndex( vProvider )

      if useSelection:
        pass
      else:
        dataArea.clear()
        dataObjects.clear()
        featureClass = None
        self.overlayProvider.featureAtId( 0, overlayFeat )

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
            intGeom = QgsGeometry( geom.intersection( tmpGeom ) )
            if intGeom.wkbType() == 7:
              intCom = geom.combine( tmpGeom )
              intSym = geom.symDifference( tmpGeom )
              intGeom = QgsGeometry( intCom.difference( intSym ) )

            if featureClass not in dataArea:
              dataArea[ featureClass ] = float( intGeom.area() * coef )
            else:
              dataArea[ featureClass ] += float( intGeom.area() * coef )

      # get extent of the overlay geometry (for reports)
      rect = overlayFeat.geometry().boundingBox()
      #dw = rect.width() * 0.05
      #dh = rect.height() * 0.05
      #rect.setXMinimum( rect.xMinimum() - dw )
      #rect.setXMaximum( rect.xMaximum() + dw )
      #rect.setYMinimum( rect.yMinimum() - dh )
      #rect.setYMaximum( rect.yMaximum() + dh )
      # create map
      mapImage = utils.createMapImage( self.overlayLayer, vLayer, rect,
                                       self.mapCRS, self.hasOTFR )

      # create all necessary reports
      layerConfig = utils.findLayerInConfig( self.cfgRoot, layerName )

      # add page break after first layer
      if not isFirst:
        writer.addPageBreak()
      isFirst = False

      # print title
      writer.addTitle( layerName )
      if utils.hasReport( layerConfig, "area" ):
        print "Write area report"
        writer.addAreaTable( fieldName, dataArea )
        # embed image in report if requested
        if mapsInReport:
          print "Embed image in report"
          imgData = QByteArray()
          buff = QBuffer( imgData )
          buff.open( QIODevice.WriteOnly )
          mapImage.save( buff, "png" )
          writer.addThematicImage( layerName, QString.fromLatin1( imgData.toBase64() ) )
          print "image embedded"

      # save separate map if requested
      if createMaps:
        print "Save separate image"
        mapImage.save( dirName + "/" + layerName + ".png", "png" )
        print "Separate image saved"

      self.emit( SIGNAL( "updateProgress()" ) )

      self.mutex.lock()
      s = self.stopMe
      self.mutex.unlock()
      if s == 1:
        interrupted = True
        break

    # save report to file
    print "Closing report"
    writer.closeReport()
    writer.write( self.outFile )
    print "Done"

    if not interrupted:
      self.emit( SIGNAL( "processFinished()" ) )
    else:
      self.emit( SIGNAL( "processInterrupted()" ) )

  def stop( self ):
    self.mutex.lock()
    self.stopMe = 1
    self.mutex.unlock()

    QThread.wait( self )
