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

from ui_layersettingsdialogbase import Ui_LayerSettingsDialog
import reporter_utils as utils

class LayerSettingsDialog( QDialog, Ui_LayerSettingsDialog ):
  def __init__( self, parent, layer ):
    QDialog.__init__( self, parent )
    self.setupUi( self )

    self.layer = layer

    self.cmbLabelField.addItems( utils.getFieldNames( self.layer ) )

  def setAreasReport( self, isChecked ):
    self.chkAreasTable.setChecked( isChecked )

  def setObjectsReport( self, isChecked ):
    self.chkObjectsTable.setChecked( isChecked )

  def setLabelField( self, fieldName ):
    self.cmbLabelField.setCurrentIndex( self.cmbLabelField.findText( fieldName ) )

  def setComment( self, text ):
    self.leComment.setText( text )

#***********************************************************************

  def areasReport( self ):
    return self.chkAreasTable.isChecked()

  def objectsReport( self ):
    return self.chkObjectsTable.isChecked()

  def getLabelField( self ):
    return self.cmbLabelField.currentText()

  def getComment( self ):
    return self.leComment.text()
