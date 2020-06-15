#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:31:55 2020
@author: Nathaniel Kabat

"""

import sys
import os 
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QComboBox, QLabel,QPushButton, QMessageBox, QHBoxLayout,QVBoxLayout, QMainWindow,QFileDialog,QWidget, QGridLayout,  QTextBrowser,QTableWidget,QTableWidgetItem, qApp,QMenu,QAction
from PyQt5.QtGui import QIcon
import matplotlib as mpl
import numpy as np
import h5py
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from ImageLoadLibraries_v0 import *
from ImageFilteringLibraries_v0 import *
matplotlib.use('Qt5Agg')
progname = os.path.basename(sys.argv[0])
progversion = "0.1"   
mpl.rc('image',cmap='gray') 
            

        
class Window(QMainWindow):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.setWindowTitle("NUScope Image Analysis (GUI v0)")
        self.setGeometry(300,250,1250,600)
        mainw = QWidget()
        self.setCentralWidget(mainw)
        mainw.setLayout(QHBoxLayout())
        
        #Initalize hf backend to save data
        #has to remove file if file exists (HDF storage issue)
        global tempHF
        self.hdf5name = "TempHDF5File.hdf5"
        try:
            os.remove(self.hdf5name)
        except:
            pass
        tempHF = h5py.File(self.hdf5name,"a")
      
        #Create widget for figure plotting
        self.figwidget = QWidget()
        figwidget = self.figwidget
        figwidget.resize(600, 600)
        figwidget.setLayout(QVBoxLayout())
        figwidget.figure = Figure()
        figwidget.canvas = FigureCanvas(figwidget.figure)
        figwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        figwidget.setMinimumSize(200,200)
        figwidget.canvas.updateGeometry()           
        #self.ax = self.figure.add_subplot(111)
        figwidget.toolbar = NavigationToolbar(figwidget.canvas, figwidget)
        figwidget.layout().addWidget(figwidget.toolbar)
        figwidget.layout().addWidget(figwidget.canvas)

        #Create widget for metadata:
        self.metawidget =QWidget()
        metawidget = self.metawidget
        metawidget.resize(150,600)
        metawidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        metawidget.setMinimumSize(350,50)               
        metawidget.setLayout(QVBoxLayout())
        metawidget.table = QTableWidget()
        metawidget.table.setColumnCount(1)
        metawidget.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)        
        metawidget.layout().addWidget(QtWidgets.QLabel("Metadata Table"))
        metawidget.layout().addWidget(metawidget.table)         
        
        #Create widget for log file show
        self.logwidget = QWidget()
        logwidget = self.logwidget
        logwidget.resize(250,600)
        logwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        logwidget.setMinimumSize(150,50)
        logwidget.setLayout(QVBoxLayout())
        logwidget.textw = QTextBrowser()
        logwidget.layout().addWidget(QtWidgets.QLabel("Log File"))
        logwidget.layout().addWidget(logwidget.textw)

        #Create file menu
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)       
        loadFile = QAction('&Load File', self)
        loadFile.setShortcut('Ctrl+O')
        loadFile.setStatusTip('Open File')
        loadFile.triggered.connect(self.clickedFilewMetaDataLoad)
        saveLog = QAction('&Save Log File',self)
        saveLog.setShortcut('Ctrl+L')
        saveLog.setStatusTip('Save Log File')
        saveLog.triggered.connect(self.saveLogFile)        
        saveHDF5 = QAction('&Save HDF5 File', self)
        saveHDF5.setShortcut('Ctrl+H')
        saveHDF5.setStatusTip('Save HDF5 File')
        saveHDF5.triggered.connect(self.saveHDFFile("TESTOUTPUT"))        
        abtAct = QAction('&About',self)
        abtAct.setStatusTip('About: ')
        abtAct.triggered.connect(self.openAboutPopup)
        filteract = QAction('&Basic Gaussian',self)
        filteract.triggered.connect(BasicGaussianFilter(self,tempHF))
        clearfilteract = QAction('&Clear All Filters',self)
        clearfilteract.triggered.connect(clearAllFilters(self))
        
        #setup menu bar with basic actions
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)        
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(loadFile)
        fileMenu.addAction(saveLog)
        fileMenu.addAction(saveHDF5)
        fileMenu.addAction(exitAct)
        toolMenu = menuBar.addMenu('&Tools')
        filtersubMenu = QMenu('&Filters',self)
        toolMenu.addMenu(filtersubMenu)
        filtersubMenu.addAction(filteract)
        filtersubMenu.addAction(clearfilteract)
        helpMenu = menuBar.addMenu('&Help')
        helpMenu.addAction(abtAct)        
        

        # set the layout
        mainw.layout().addWidget(figwidget,0)
        mainw.layout().addWidget(metawidget,1)
        mainw.layout().addWidget(logwidget,2)

    def openAboutPopup(self):
        abtwin = QMessageBox()
        abtwin.setWindowTitle("About")
        abtwin.setText("Information about the project goes here.")
        abtwin.setInformativeText("Northwestern University / NUANCE Center. 2020. ")
        abtwin.button = QPushButton('Okay')
        abtwin.button.clicked.connect(abtwin.close)
        abtwin.setDefaultButton(abtwin.button)        
        abtwin.exec_()
        
    def saveLogFile(self):
        logfname = 'Output.txt'
        np.savetxt(logfname,[self.logwidget.textw.toPlainText()], fmt='%s',encoding='utf-8')
        self.logwidget.textw.append(f"Saved log to file: {logfname}\n")
        
    def clickedFilewMetaDataLoad(self):
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
        
        global tempHF
        nhdfkeys = len(tempHF.keys())
        tempHF.close()
        if nhdfkeys != 0:
            os.remove(self.hdf5name)
            
        tempHF = h5py.File(self.hdf5name,"a")            
        #Save data/metadata into HF backend
        tempHF['filename'] = self.fname
        #tempHF['RawIm']= self.imdata
        tempHF['Im'] = self.imdata
        grp = tempHF.create_group("MetadataGroup")
        for item in self.metadata.items():
            grp[item[0]] = item[1]     
        
        #convert metadata to table
        vertHeaders = []
        #print(self.metadata.keys())
        self.metawidget.table.setRowCount(len(self.metadata))
        for n,key in enumerate(self.metadata.keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(self.metadata[key])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()

        
        self.logwidget.textw.append(f"Opened file: {self.fname} \n")                      
        self.logwidget.textw.append(f"File Type Selected: {self.filterChoice} \n")
        

        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis


        self.ax.imshow(self.imdata)  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas             
    def saveHDFFile(self,defaultFileName):
        def saveFile():
            self.dlg = QFileDialog()
            savename,_ = self.dlg.getSaveFileName(self,"TEST",options=QFileDialog.DontUseNativeDialog)
            if savename[-5:] != ".hdf5":
                savename += ".hdf5"
            else:
                pass         
            if os.path.exists(savename) == True:
                os.remove(savename)
            else:
                pass

            with h5py.File(savename,"a") as hfsave:
                for item in tempHF.keys():                    
                    tempHF.copy(item,hfsave) 
            self.logwidget.textw.append(f"Saved data as HDF5 File: {savename}\n")
        return saveFile
    def closeEvent(self,*args,**kwargs):
        super(QMainWindow,self).closeEvent(*args,**kwargs)
        #print("Close main window and close hdf file(s)")
        tempHF.close()

def clearAllFilters(self):
    def run():
        self.figwidget.figure.clear() #clear figure
        ax = self.figwidget.figure.add_subplot(111) # create an axis
        ax.imshow(self.imdata)  #plot data
        ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Reset figure to raw data \n")        
    return run    

def BasicGaussianFilter(self,tempHF,sigma=6):
    #there is an issue with saving to the HDF file within this function. Fix TBD.
    def run():
        prevcmap = mpl.cm.get_cmap().name
        imagedata = self.imdata
        fdata = gaussian_filter(imagedata,sigma)
        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        self.ax.imshow(fdata)  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        #self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigma}\n")
    return run        

def main():
    app = QApplication(sys.argv)
    mainWindow = Window()
    mainWindow.show()
    sys.exit(app.exec_())
        
        
        
if __name__ == "__main__":
    main()

