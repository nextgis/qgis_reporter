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

  return layerList

# *****************************************************************************
# various filedialogs
# *****************************************************************************

def getExistingDirectory( parent, title="Select output directory" ):
  settings = QSettings( "NextGIS", "reporter" )
  lastReportsDir = settings.value( "lastReportsDir", QVariant( "." ) ).toString()
  d = QFileDialog.getExistingDirectory( parent,
                                        title,
                                        lastReportsDir )
  if d.isEmpty():
    return None

  settings.setValue( "lastReportsDir", d )
  return d
