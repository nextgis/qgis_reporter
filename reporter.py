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

from __init__ import version

import reporterdialog

import resources_rc

class ReporterPlugin( object ):
  def __init__( self, iface ):
    self.iface = iface
    self.iface = iface

    try:
      self.QgisVersion = unicode( QGis.QGIS_VERSION_INT )
    except:
      self.QgisVersion = unicode( QGis.qgisVersion )[ 0 ]

    # For i18n support
    userPluginPath = QFileInfo( QgsApplication.qgisUserDbFilePath() ).path() + "/python/plugins/reporter"
    systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/reporter"

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    if QFileInfo( userPluginPath ).exists():
      translationPath = userPluginPath + "/i18n/reporter_" + localeFullName + ".qm"
    else:
      translationPath = systemPluginPath + "/i18n/reporter_" + localeFullName + ".qm"

    self.localePath = translationPath
    if QFileInfo( self.localePath ).exists():
      self.translator = QTranslator()
      self.translator.load( self.localePath )
      QCoreApplication.installTranslator( self.translator )

  def initGui( self ):
    if int( self.QgisVersion ) < 10000:
      QMessageBox.warning( self.iface.mainWindow(), "Reporter",
                           QCoreApplication.translate( "Reporter", "Quantum GIS version detected: " ) + unicode( self.QgisVersion ) + ".xx\n" +
                           QCoreApplication.translate( "Reporter", "This version of Reporter requires at least QGIS version 1.0.0\nPlugin will not be enabled." ) )
      return None

    self.actionRun = QAction( QIcon( ":/icons/reporter.png" ), "Reporter", self.iface.mainWindow() )
    self.actionRun.setStatusTip( QCoreApplication.translate( "Reporter", "Generates report" ) )
    self.actionAbout = QAction( QIcon( ":/icons/about.png" ), "About Reporter", self.iface.mainWindow() )

    QObject.connect( self.actionRun, SIGNAL( "triggered()" ), self.run )
    QObject.connect( self.actionAbout, SIGNAL( "triggered()" ), self.about )

    if hasattr( self.iface, "addPluginToVectorMenu" ):
      self.iface.addPluginToVectorMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionRun )
      self.iface.addPluginToVectorMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionAbout )
      self.iface.addVectorToolBarIcon( self.actionRun )
    else:
      self.iface.addPluginToMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionRun )
      self.iface.addPluginToMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionAbout )
      self.iface.addToolBarIcon( self.actionRun )

  def unload( self ):
    if hasattr( self.iface, "addPluginToVectorMenu" ):
      self.iface.removePluginVectorMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionRun )
      self.iface.removePluginVectorMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionAbout )
      self.iface.removeVectorToolBarIcon( self.actionRun )
    else:
      self.iface.removePluginMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionRun )
      self.iface.removePluginMenu( QCoreApplication.translate( "Reporter", "Reporter" ), self.actionAbout )
      self.iface.removeToolBarIcon( self.actionRun )

  def about( self ):
    dlgAbout = QDialog()
    dlgAbout.setWindowTitle( QApplication.translate( "Reporter", "About Reporter" ) )
    lines = QVBoxLayout( dlgAbout )
    title = QLabel( QApplication.translate( "Reporter", "<b>Reporter</b>" ) )
    title.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( title )
    ver = QLabel( QApplication.translate( "Reporter", "Version: %1" ).arg( version() ) )
    ver.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( ver )
    lines.addWidget( QLabel( QApplication.translate( "Reporter", "Generates report." ) ) )
    lines.addWidget( QLabel( QApplication.translate( "Reporter", "<b>Developers:</b>" ) ) )
    lines.addWidget( QLabel( "  Alexander Bruy (NextGIS)" ) )
    lines.addWidget( QLabel( QApplication.translate( "Reporter", "<b>Homepage:</b>") ) )

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    localeShortName = localeFullName[ 0:2 ]
    if localeShortName in [ "ru", "uk" ]:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/reporter.html\">http://gis-lab.info/qa/reporter.html</a>" )
    else:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/reporter-eng.html\">http://gis-lab.info/qa/reporter-eng.html</a>" )

    link.setOpenExternalLinks( True )
    lines.addWidget( link )

    btnClose = QPushButton( QApplication.translate( "Reporter", "Close" ) )
    lines.addWidget( btnClose )
    QObject.connect( btnClose, SIGNAL( "clicked()" ), dlgAbout, SLOT( "close()" ) )

    dlgAbout.exec_()

  def run( self ):
    dlg = reporterdialog.ReporterDialog( self.iface )
    dlg.exec_()
