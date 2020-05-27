#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:31:55 2020
@author: Nathaniel Kabat

"""

import sys
import os 
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QHBoxLayout,QVBoxLayout, QFileDialog,QWidget, QGridLayout,  QTextBrowser,QTableWidget,QTableWidgetItem
import matplotlib
import numpy as np
import h5py
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from ImageLoadLibraries_v0 import *
matplotlib.use('Qt5Agg')

progname = os.path.basename(sys.argv[0])
progversion = "0.1"   

class figureWindow(QWidget):  
    def __init__(self,parent=None):
        super(figureWindow, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        self.figure = Figure(figsize=(12,12))
        self.canvas = FigureCanvas(self.figure)
        self.button = QPushButton('Load File and Plot')
        #self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
        self.layout().addWidget(self.button)
        #self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        #self.canvas.updateGeometry()
        
    
class logWindow(QWidget):
    def __init__(self,parent=None):
        super(logWindow, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        self.textw = QTextBrowser()
        self.saveLogButton = QPushButton('Save Log File')
        self.saveLogButton.clicked.connect(self.saveLogFile) 
        self.layout().addWidget(QtWidgets.QLabel("Log File"))
        self.layout().addWidget(self.textw)
        self.layout().addWidget(self.saveLogButton)
    def saveLogFile(self):
        np.savetxt('LogFileOutPut.txt',[self.textw.toPlainText()], fmt='%s')
    

        
class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("NUScope Image Analysis (GUI v0)")
        self.setGeometry(800,200,1200,600)
        self.setLayout(QHBoxLayout())
      
        #Create widget for figure plotting
        figwig = QWidget()
        figwig.resize(600, 600)
        figwig.setLayout(QVBoxLayout())
        figwig.figure = Figure()
        figwig.canvas = FigureCanvas(figwig.figure)
        figwig.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        figwig.setMinimumSize(200,200)
        figwig.canvas.updateGeometry()           
        figwig.button = QPushButton('Load File and Plot')

        #self.ax = self.figure.add_subplot(111)
        figwig.toolbar = NavigationToolbar(figwig.canvas, figwig)
        figwig.layout().addWidget(figwig.toolbar)
        figwig.layout().addWidget(figwig.canvas)
        figwig.layout().addWidget(figwig.button)

        #Create widget for metadata:
        metawidget =QWidget()
        metawidget.resize(150,600)
        metawidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        metawidget.setMinimumSize(350,50)               
        metawidget.setLayout(QVBoxLayout())
        metawidget.table = QTableWidget()
        metawidget.table.setColumnCount(1)
        metawidget.table.setRowCount(0)
        metawidget.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)        
        metawidget.layout().addWidget(QtWidgets.QLabel("Metadata Table"))
        metawidget.layout().addWidget(metawidget.table)         
        
        #Create widget for log file show
        logwidget = QWidget()
        logwidget.resize(250,600)
        logwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        logwidget.setMinimumSize(150,50)
        logwidget.setLayout(QVBoxLayout())
        logwidget.textw = QTextBrowser()
        logwidget.saveLogButton = QPushButton('Save Log File')
        logwidget.layout().addWidget(QtWidgets.QLabel("Log File"))
        logwidget.layout().addWidget(logwidget.textw)
        logwidget.layout().addWidget(logwidget.saveLogButton)


        #Button commands that reference both the figure widget and the log widget
        figwig.button.clicked.connect(self.clickedFilewMetaDataLoad(figwig,logwidget,metawidget)) 
        logwidget.saveLogButton.clicked.connect(self.saveLogFile(logwidget))         


        # set the layout
        self.layout().addWidget(figwig,0)
        self.layout().addWidget(metawidget,1)
        self.layout().addWidget(logwidget,2)

    def saveLogFile(self,logwidget):
        def runsave():
            np.savetxt('Output.txt',[logwidget.textw.toPlainText()], fmt='%s')
        return runsave
    def clickedFilewMetaDataLoad(self,specificFig,logwidget,metawidget):
        def openFile():
            self.dlg = QFileDialog()
            #filters = "Hitachi SEM Image (*.tif *.tiff);;JEOL SEM Image (*.tif *.tiff);;FEI Quanta SEM Image (*.tif *.tiff)"
            filters = "Generic Image File (*.tiff *.tif *.png *.jpg *.jpeg);; Hitachi SEM Image (*.tif *.tiff);;JEOL SEM Image (*.tif *.tiff);;FEI Quanta SEM Image (*.tif *.tiff);; Bruker AFM (*.spm)"
            self.fname, self.filterChoice = self.dlg.getOpenFileName(self, "Select an Image file...",filter=filters,options=QFileDialog.DontUseNativeDialog)            
             
            #select correct image loading function based on choice from file menu
            if "Hitachi" in self.filterChoice:
                self.metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
                self.imdata,self.metadata = HitachiSEMImageLoad(self.fname,self.metafname)          
            elif "Quanta" in self.filterChoice:
                self.metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
                self.imdata,self.metadata = QuantaSEMImageLoad(self.fname,self.metafname)                
            elif "JEOL" in self.filterChoice:
                self.metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
                self.imdata,self.metadata = JEOL7900SEMImageLoad(self.fname,self.metafname)
            elif "Generic Image" in self.filterChoice:
                self.imdata,self.metadata = GenericImageOpenTIFF(self.fname)
            elif "Bruker" in self.filterChoice:
                self.imdata,self.metadata = BrukerAFMImageLoad(self.fname)
            
            #convert metadata to table
            vertHeaders = []
            print(self.metadata.keys())
            for n,key in enumerate(self.metadata.keys()):
                vertHeaders.append(key)
                newitem = QTableWidgetItem(self.metadata[key])
                metawidget.table.setItem(0, n, newitem)
                metawidget.table.setVerticalHeaderLabels(vertHeaders)
                metawidget.table.resizeColumnsToContents()
                metawidget.table.resizeRowsToContents()
                metawidget.table.setRowCount(len(self.metadata))
            
            logwidget.textw.append(f"Opened file: {self.fname} \n")                      
            logwidget.textw.append(f"File Type Selected: {self.filterChoice} \n")
            

            specificFig.figure.clear() #clear figure
            # create an axis
            ax = specificFig.figure.add_subplot(111)


            ax.imshow(self.imdata)  # plot data
            ax.axis("off")
            specificFig.figure.tight_layout()
            specificFig.canvas.draw() # refresh canvas

        return openFile



def main():
    app = QApplication(sys.argv)
    mainWindow = Window()
    mainWindow.show()
    sys.exit(app.exec_())        
        
        
        
if __name__ == "__main__":
    main()

