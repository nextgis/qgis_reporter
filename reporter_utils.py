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

import locale

# *****************************************************************************
# working with layers
# *****************************************************************************

def getVectorLayerByName( layerName ):
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  for name, layer in layerMap.iteritems():
    if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
      if layer.isValid():
        return layer
      else:
        return None

def getVectorLayersNames( vectorTypes = "all" ):
  layerList = []
  layerMap = QgsMapLayerRegistry.instance().mapLayers()
  if vectorTypes == "all":
    for name, layer in layerMap.iteritems():
      if layer.type() == QgsMapLayer.VectorLayer:
        layerList.append( unicode( layer.name() ) )
  else:
    for name, layer in layerMap.iteritems():
      if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in vectorTypes:
        layerList.append( unicode( layer.name() ) )

  return sorted( layerList, cmp=locale.strcoll )

def createSpatialIndex( provider ):
  ft = QgsFeature()
  index = QgsSpatialIndex()

  provider.rewind()
  while provider.nextFeature( ft ):
    index.insertFeature( ft )

  return index

def fieldIndexByName( provider, fieldName ):
  fMap = provider.fieldNameMap()
  return fMap[ fieldName ]

def fieldNameByIndex( provider, fieldIndex ):
  fMap = provider.fieldNameMap()
  for k, v in fMap.iteritems():
    if v == fieldIndex:
      return k

# *****************************************************************************
# various filedialogs
# *****************************************************************************

def getExistingDirectory( parent, title = "Select output directory" ):
  settings = QSettings( "NextGIS", "reporter" )
  lastDir = settings.value( "lastReportsDir", QVariant( "." ) ).toString()

  d = QFileDialog.getExistingDirectory( parent, title, lastDir )

  if d.isEmpty():
    return None

  settings.setValue( "lastReportsDir", QFileInfo( d ).absolutePath() )
  return d

def saveConfigFile( parent, title = "Save configuration", fileFilter = "XML file (*.xml *.XML)" ):
  settings = QSettings( "NextGIS", "reporter" )
  lastDir = settings.value( "lastConfigDir", QVariant( "." ) ).toString()

  f = QFileDialog.getSaveFileName( parent, title, lastDir, fileFilter )

  if f.isEmpty():
    return None

  if not f.toLower().endsWith( ".xml" ):
    f += ".xml"

  settings.setValue( "lastConfigDir", QFileInfo( f ).absolutePath() )
  return f

def openConfigFile( parent, title = "Load configuration", fileFilter = "XML file (*.xml *.XML)" ):
  settings = QSettings( "NextGIS", "reporter" )
  lastDir = settings.value( "lastConfigDir", QVariant( "." ) ).toString()

  f = QFileDialog.getOpenFileName( parent, title, lastDir, fileFilter )

  if f.isEmpty():
    return None

  settings.setValue( "lastConfigDir", QFileInfo( f ).absolutePath() )
  return f

def saveReportFile( parent, title = "Save report to", fileFilter = "Microsoft Word 2003 (*.doc *.DOC)" ):
  settings = QSettings( "NextGIS", "reporter" )
  lastDir = settings.value( "lastReportDir", QVariant( "." ) ).toString()

  f = QFileDialog.getSaveFileName( parent, title, lastDir, fileFilter )

  if f.isEmpty():
    return None

  if not f.toLower().endsWith( ".doc" ):
    f += ".doc"

  settings.setValue( "lastReportDir", QFileInfo( f ).absolutePath() )
  return f

# *****************************************************************************
# helper xml functions
# *****************************************************************************

def addLayerToConfig( doc, root, layerName ):
  # first check if layer already in config
  child = root.firstChildElement()
  while not child.isNull():
    if child.attribute( "name" ) == layerName:
      return
    child = child.nextSiblingElement()

  el = doc.createElement( "layer" )
  el.setAttribute( "name", layerName )
  root.appendChild( el )

def removeLayerFromConfig( root, layerName ):
  child = root.firstChildElement()
  while not child.isNull():
    if child.attribute( "name" ) == layerName:
      root.removeChild( child )
      return
    child = child.nextSiblingElement()

def findLayerInConfig( root, layerName ):
  child = root.firstChildElement()
  while not child.isNull():
    if child.attribute( "name" ) == layerName:
      return child
    child = child.nextSiblingElement()
  return None

def addLayerReport( doc, elem, rptName ):
  rpt = doc.createElement( "report" )
  rpt.setAttribute( "name", rptName )
  elem.appendChild( rpt )

def removeLayerReport( elem, rptName ):
  child = elem.firstChildElement()
  while not child.isNull():
    if child.attribute( "name" ) == rptName:
      elem.removeChild( child )
      return
    child = child.nextSiblingElement()

def hasReport( elem, rptName ):
  child = elem.firstChildElement()
  while not child.isNull():
    if child.attribute( "name" ) == rptName:
      return True
    child = child.nextSiblingElement()
  return False

def layersWithoutReports( root ):
  missed = []
  child = root.firstChildElement()
  while not child.isNull():
    if not child.hasChildNodes():
      missed.append( child.attribute( "name" ) )
    child = child.nextSiblingElement()
  return missed

# *****************************************************************************
# helper map print functions
# *****************************************************************************

def createMapImage( boundLayer, thematicLayer, rectangle, outPath ):
  renderer = QgsMapRenderer()
  renderer.setLayerSet( [ boundLayer.id(), thematicLayer.id() ] )
  renderer.setExtent( rectangle )

  composition = QgsComposition( renderer )
  composition.setPlotStyle( QgsComposition.Print )

  legend = QgsComposerLegend( composition )
  legend.model().setLayerSet( renderer.layerSet() )
  composition.addItem( legend )

  # an idiotic workaround to get legend size
  dpi = composition.printResolution()
  dpmm = dpi / 25.4
  width = int( dpmm * composition.paperWidth() )
  height = int( dpmm * composition.paperHeight() )
  image = QImage( QSize( width, height ), QImage.Format_ARGB32 )
  image.setDotsPerMeterX( dpmm * 1000 )
  image.setDotsPerMeterY( dpmm * 1000 )
  legend.paintAndDetermineSize( QPainter( image ) )

  x, y = legend.rect().width(), 0
  w, h = composition.paperWidth() - x, composition.paperHeight()
  composerMap = QgsComposerMap( composition, x, y, w, h )
  composition.addItem( composerMap )

  #dpi = composition.printResolution()
  #dpmm = dpi / 25.4
  #width = int( dpmm * composition.paperWidth() )
  #height = int( dpmm * composition.paperHeight() )

  # create and init output image
  image = QImage( QSize( width, height ), QImage.Format_ARGB32 )
  image.setDotsPerMeterX( dpmm * 1000 )
  image.setDotsPerMeterY( dpmm * 1000 )
  image.fill( 0 )

  # draw composition
  imagePainter = QPainter( image )
  sourceArea = QRectF( 0, 0, composition.paperWidth(), composition.paperHeight() )
  targetArea = QRectF( 0, 0, width, height )
  composition.render( imagePainter, targetArea, sourceArea )
  imagePainter.end()

  image.save( outPath + ".png", "png" )
