#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:31:55 2020
@author: Nathaniel Kabat
"""

import sys
import os 
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtWidgets import QDialog, QListWidget, QApplication, QCheckBox, QComboBox, QLabel,QPushButton, QMessageBox, QHBoxLayout,QVBoxLayout, QMainWindow,QFileDialog,QWidget, QGridLayout, QLineEdit, QTextBrowser,QTableWidget,QTableWidgetItem,QMenu,QAction
from PyQt5.QtGui import QPixmap
import matplotlib as mpl
import numpy as np
import h5py
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib_scalebar.scalebar import ScaleBar
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from scipy.ndimage import gaussian_filter, laplace, sobel, gaussian_laplace
from matplotlib.widgets import Slider, Button, RadioButtons
from ImageLoadLibraries_v0 import *

#Default plotting settings. Setting globally so all figures/images use these.
mpl.use('Qt5Agg')
mpl.rc('image',cmap='gray')
mpl.rc('savefig',transparent=True,dpi=1500)


class plotSettingsWindow(QDialog):
    def __init__(self,*args,**kwargs):
        super(plotSettingsWindow,self).__init__(*args,**kwargs)
        ScaleSizeList = ["1 mm","1000 um","500 um","100 um","10 um","1 um","100 nm","10 nm","10 A","N/A"]
        global temphdf
        imglist = list(temphdf.keys())                   
        imgOrd = [temphdf[imglistv].attrs['n'] for imglistv in imglist]
        self.imglist = [x for _,x in sorted(zip(imgOrd,imglist))]
        self.size = len(self.imglist)
        self.scalelist = ["N/A"]*self.size
        self.cflist = ["N/A"]*self.size
        self.ind = 0
        
        self.setLayout(QGridLayout())
        self.setGeometry(400,400,300,200)
        self.imgChoiceC = QComboBox(self)
        self.imgChoiceC.addItems(self.imglist)
        self.imgChoiceC.currentIndexChanged.connect(self.updateSublayout)        
        
        self.imgScaleSet = QWidget(self)
        self.imgScaleSet.setLayout(QGridLayout())
        self.ScaleBarCombo = QComboBox(self)
        self.ScaleBarCombo.addItems(ScaleSizeList)
        self.ScaleBarCombo.setCurrentIndex(ScaleSizeList.index('N/A'))
        self.ScaleBarCombo.setEditable(True)
        self.ScaleBarCombo.currentTextChanged.connect(self.updateScaleV)        
        self.conversionf = QLineEdit(self)
        self.conversionf.setText("N/A")
        self.imgScaleSet.layout().addWidget(QLabel("Scale Bar Size"),0,0)
        self.imgScaleSet.layout().addWidget(self.ScaleBarCombo,0,1)
        self.imgScaleSet.layout().addWidget(QLabel("# Pixels\nAcross Scalebar"),1,0)        
        self.imgScaleSet.layout().addWidget(self.conversionf,1,1) 
               
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Custom Scalebar Settings")
        self.layout().addWidget(QLabel("Select Image: "),0,0)
        self.layout().addWidget(self.imgChoiceC,0,1)
        self.layout().addWidget(self.imgScaleSet,1,1)   
        
        
        self.layout().addWidget(self.applysettings,5,0)
        self.layout().addWidget(self.cancel,5,1)
        
    def updateSublayout(self):
        #Copied from other function, needs modification for this..
        if self.imgChoiceC.currentText() in self.imglist:
            self.ind = self.imglist.index(self.imgChoiceC.currentText())
                    
        if self.imgChoiceC.currentText() == self.imglist[0]:
            index = self.ScaleBarCombo.findText(self.scalelist[0], QtCore.Qt.MatchFixedString)
            self.ScaleBarCombo.setCurrentIndex(index)
        else:
            pass
    def updateScaleV(self):
        self.scalelist[self.ind] = self.ScaleBarCombo.currentText()
        self.cflist[self.ind] = self.conversionf.text()
        
    def clicktoapply(self):
        self.labelApplied = True
        self.close()
        
    def cancelClick(self):
        self.labelApplied = False
        self.scalelist = ["N/A"]*self.size
        self.cflist = ["N/A"]*self.size
        self.close()

class filteringWindow(QDialog):
    def __init__(self,*args,**kwargs):
        super(filteringWindow,self).__init__(*args,**kwargs)
        filterlist = ['Gaussian',"Gaussian-laplace","Laplace","Sobel"] #Need to expand
        self.setLayout(QVBoxLayout())
        self.setGeometry(550,550,300,200)
        self.combo = QComboBox(self)
        self.combo.addItems(filterlist)
        self.combo.setEditable(True) 
        self.combo.currentIndexChanged.connect(self.updateSublayout)
        self.filterOptions = QWidget()
        self.filterOptions.setLayout(QHBoxLayout()) 
        self.sigmaset = QLineEdit(self)
        self.sigmaset.setText("3")
        self.filterOptions.layout().addWidget(QLabel("Sigma: "),0)
        self.filterOptions.layout().addWidget(self.sigmaset,1)
        self.filterValues = [self.combo.currentText(),int(self.sigmaset.text())]                       

        self.sigmaset.textChanged.connect(self.updateFilterVar)

        global temphdf
        nimgs = len(temphdf.keys())
        self.applytoimgs = QWidget()
        self.applytoimgs.setLayout(QGridLayout()) 
        self.qc1 = QCheckBox(self)
        self.qc2 = QCheckBox(self)
        self.qc3 = QCheckBox(self)
        self.qc4 = QCheckBox(self)
        qclist = [self.qc1,self.qc2,self.qc3,self.qc4]
        for i in range(1,nimgs+1):
            #print(i)
            try:
                qclist[i-1].setEnabled(True)
                qclist[i-1].setCheckState(True)
            except:
                pass
        diff = 4 - nimgs        
        if diff != 0:
            for j in range(1,diff+1):
                qclist[4-j].setEnabled(False)


        self.applytoimgs.layout().addWidget(QLabel("Apply to Images:"),1,0)
        self.applytoimgs.layout().addWidget(QLabel("1"),0,1)
        self.applytoimgs.layout().addWidget(QLabel("2"),0,2)
        self.applytoimgs.layout().addWidget(QLabel("3"),0,3)
        self.applytoimgs.layout().addWidget(QLabel("4"),0,4)
        
        self.applytoimgs.layout().addWidget(self.qc1,1,1)    
        self.applytoimgs.layout().addWidget(self.qc2,1,2)            
        self.applytoimgs.layout().addWidget(self.qc3,1,3)    
        self.applytoimgs.layout().addWidget(self.qc4,1,4)    
        
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Image Filter Settings")
        self.layout().addWidget(self.combo,0)
        self.layout().addWidget(QLabel("Filter Specific Settings:"),1)
        self.layout().addWidget(self.filterOptions,2)
        self.layout().addWidget(self.applytoimgs,3)        
        self.layout().addWidget(self.applysettings,4)
        self.layout().addWidget(self.cancel,5)
    def updateFilterVar(self):
        self.filterValues = [self.combo.currentText(),int(self.sigmaset.text())]    
    def updateSublayout(self):
        for i in reversed(range(self.filterOptions.layout().count())):
            self.filterOptions.layout().takeAt(i).widget().setParent(None)
        if self.combo.currentText() == "Gaussian":
            self.sigmaset = QLineEdit(self)
            self.sigmaset.setText("3")
            self.filterOptions.layout().addWidget(QLabel("Sigma: "))
            self.filterOptions.layout().addWidget(self.sigmaset)
            self.filterValues = [self.combo.currentText(),int(self.sigmaset.text())]
        elif self.combo.currentText() == "Gaussian-laplace":
            self.sigmaset = QLineEdit(self)
            self.sigmaset.setText("3")
            self.filterOptions.layout().addWidget(QLabel("Sigma: "))
            self.filterOptions.layout().addWidget(self.sigmaset)
            self.filterValues = [self.combo.currentText(),int(self.sigmaset.text())]            
        elif self.combo.currentText() == "Laplace":
            self.filterOptions.layout().addWidget(QLabel("No Further Settings"))
            self.filterValues = [self.combo.currentText()]
        elif self.combo.currentText() == "Sobel":
            self.filterOptions.layout().addWidget(QLabel("No Further Settings"))
            self.filterValues = [self.combo.currentText()]
        else:
            pass
    
    def clicktoapply(self):     
        self.close()
        
    def cancelClick(self):
        self.filterValues = ["None"]
        self.close()    
        
class fftWindow(QDialog):
    def __init__(self,*args,**kwargs):
        super(fftWindow,self).__init__(*args,**kwargs)
        zscalinglist = ['None',"Log","Log10"] #Need to expand
        self.setLayout(QVBoxLayout())
        self.setGeometry(550,550,300,200)
        self.fftzscaling = QComboBox(self)
        self.fftzscaling.addItems(zscalinglist)
        self.fftzscaling.setEditable(True)         
        self.filterOptions = QWidget()
        self.filterOptions.setLayout(QHBoxLayout()) 
        self.sigmaset = QLineEdit(self)
        self.sigmaset.setText("3")
        self.filterOptions.layout().addWidget(QLabel("Sigma: "),0)
        self.filterOptions.layout().addWidget(self.sigmaset,1)                       
        
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Image FFT Settings")
        self.layout().addWidget(self.fftzscaling,0)        
        self.layout().addWidget(self.applysettings,3)
        self.layout().addWidget(self.cancel,4)
    
    def clicktoapply(self):
        self.fftapplied = "True"
        self.close()
        
    def cancelClick(self):
        self.fftapplied = "False"
        self.close()    

#Copied fftWindow class. Needs to be modified for image stack reg
class AlignImageStackWindow(QDialog):  
    def __init__(self,*args,**kwargs):
        super(AlignImageStackWindow,self).__init__(*args,**kwargs)
        zscalinglist = ['None',"Log","Log10"] #Need to expand
        self.setLayout(QVBoxLayout())
        self.setGeometry(550,550,300,200)
        self.fftzscaling = QComboBox(self)
        self.fftzscaling.addItems(zscalinglist)
        self.fftzscaling.setEditable(True)         
        self.filterOptions = QWidget()
        self.filterOptions.setLayout(QHBoxLayout()) 
        self.sigmaset = QLineEdit(self)
        self.sigmaset.setText("3")
        self.filterOptions.layout().addWidget(QLabel("Sigma: "),0)
        self.filterOptions.layout().addWidget(self.sigmaset,1)                       
        
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Image FFT Settings")
        self.layout().addWidget(self.fftzscaling,0)        
        self.layout().addWidget(self.applysettings,3)
        self.layout().addWidget(self.cancel,4)
    
    def clicktoapply(self):
        self.fftapplied = "True"
        self.close()
        
    def cancelClick(self):
        self.fftapplied = "False"
        self.close()        
      
class Window(QMainWindow):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.setWindowTitle("NUScope Image Analysis (GUI v0)")
        self.setGeometry(300,250,1350,700) #X,Y, Width, Height
        mainw = QWidget()
        self.setCentralWidget(mainw)
        mainw.setLayout(QHBoxLayout())
        
        #Initalize hf backend to save data
        #has to remove file if file exists (HDF storage issue)
        global temphdf
        self.hdf5name = "TempHDF5File.hdf5"
        try:
            os.remove(self.hdf5name)
        except:
            pass
        temphdf = h5py.File(self.hdf5name,"a")
      
        #Create widget for figure plotting
        self.figwidget = QWidget()
        figwidget = self.figwidget

        figwidget.setLayout(QVBoxLayout())
        figwidget.figure = Figure()
        figwidget.canvas = FigureCanvas(figwidget.figure)
        figwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        figwidget.setMinimumSize(400,500)
        figwidget.canvas.updateGeometry()           
        figwidget.toolbar = NavigationToolbar(figwidget.canvas, figwidget)
        figwidget.layout().addWidget(figwidget.toolbar)
        figwidget.layout().addWidget(figwidget.canvas)  

        #Create widget for metadata:
        self.metawidget =QWidget()
        metawidget = self.metawidget
        #metawidget.resize(150,600)
        metawidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        metawidget.setMinimumSize(250,500) 
        metawidget.setMaximumWidth(400)              
        metawidget.setLayout(QVBoxLayout())
        metawidget.fql = QListWidget()
        #metawidget.fql.setMinimumSize(300,100)
        metawidget.fql.setMaximumHeight(250)
        metawidget.fql.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        metawidget.fql.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)          
        metawidget.fql.clicked.connect(self.showmetatable)
        metawidget.table = QTableWidget()
        metawidget.table.setColumnCount(1)
        metawidget.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  
        metawidget.metaChoice = QComboBox(self)
        metawidget.metaChoice.addItems(["Simplified Metadata","Full Metadata"])           
        metawidget.metaChoice.currentIndexChanged.connect(self.changeMetadataType)
        metawidget.layout().addWidget(QLabel("Image List"))
        metawidget.layout().addWidget(metawidget.fql)
        metawidget.layout().addWidget(metawidget.metaChoice)
        metawidget.layout().addWidget(metawidget.table)                  
        #Create widget for log file show
        self.logwidget = QWidget()
        logwidget = self.logwidget
        #logwidget.resize(50,50) #formerly 250,600
        #logwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        logwidget.setMinimumSize(150,500)
        logwidget.setMaximumWidth(300) #x,y
        logwidget.setLayout(QVBoxLayout())
        logwidget.textw = QTextBrowser()
        logwidget.layout().addWidget(QtWidgets.QLabel("Log File"))
        logwidget.layout().addWidget(logwidget.textw)     

        #Create file menu
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)       
        loadFile = QAction('&Load New File', self)
        loadFile.setShortcut('Ctrl+O')
        loadFile.setStatusTip('Open File')
        loadFile.triggered.connect(self.clickedFilewMetaDataLoad)
        addFile = QAction('&Add New File', self)
        addFile.setShortcut('Ctrl+A')
        addFile.setStatusTip('Open File')
        addFile.triggered.connect(self.addFilewMetaDataLoad)
        loadVideo = QAction('&Load Video File', self)
        loadVideo.setShortcut('Ctrl+V')
        loadVideo.setStatusTip('Open File')
        loadVideo.triggered.connect(self.addVideoFileLoad)    
        loadHDF5 = QAction('&Load HDF File', self)
        loadHDF5.setShortcut('Ctrl+H')
        loadHDF5.setStatusTip('Open File')
        loadHDF5.triggered.connect(self.loadSavedHDF5)            
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
        filteract = QAction('&Filter Settings',self)
        filteract.triggered.connect(self.openFilterSettings)
        gaussfilteract = QAction('&Basic Gaussian',self)
        gaussfilteract.triggered.connect(BasicGaussianFilter(self,temphdf))
        clearfilteract = QAction('&Clear All Filters',self)
        clearfilteract.triggered.connect(clearAllFilters(self))
        fftfilteract = QAction('&FFT',self)
        fftfilteract.triggered.connect(self.applyFFT)
        videofilteract = QAction('&Filter Settings',self)
        videofilteract.triggered.connect(self.openFilterSettingsVideo)
        videofftfilteract = QAction('&FFT',self)
        videofftfilteract.triggered.connect(self.applyFFTVideo)   
        videoalignact = QAction('&Align Stack',self)
        videoalignact.triggered.connect(self.align3DImageStack)         
        plotsettingsact = QAction('&Plot Settings',self)
        plotsettingsact.triggered.connect(self.OpenPlotSettingsWindow)
        refreshfigact = QAction('&Refresh Figure',self)
        refreshfigact.triggered.connect(self.refreshfigurecanvas)
        #setup menu bar with basic actions
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)        
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(loadFile)
        fileMenu.addAction(addFile)
        fileMenu.addAction(loadVideo)
        fileMenu.addAction(loadHDF5)
        fileMenu.addAction(saveLog)
        fileMenu.addAction(saveHDF5)
        fileMenu.addAction(exitAct)
        toolMenu = menuBar.addMenu('&Tools')
        imagesubMenu = QMenu('& Image Functions',self)
        toolMenu.addMenu(imagesubMenu)
        imagesubMenu.addAction(filteract)
        imagesubMenu.addAction(gaussfilteract)
        imagesubMenu.addAction(clearfilteract)
        imagesubMenu.addAction(fftfilteract)
        imagesubMenu.addAction(plotsettingsact)
        videosubMenu = QMenu('& Video Functions', self)
        videosubMenu.addAction(videofilteract)     
        videosubMenu.addAction(videofftfilteract)
        videosubMenu.addAction(videoalignact)          
        toolMenu.addMenu(videosubMenu)
        toolMenu.addAction(refreshfigact)
        helpMenu = menuBar.addMenu('&Help')
        helpMenu.addAction(abtAct)        
        

        # set the layout
        mainw.layout().addWidget(figwidget,0)
        mainw.layout().addWidget(metawidget,1)
        mainw.layout().addWidget(logwidget,2)
        
    def showmetatable(self):
        state = self.metawidget.metaChoice.currentText()
        self.metawidget.table.setRowCount(0)
        cfn = self.metawidget.fql.currentItem().text()
        #select which metadata variable to use
        usedMetaData = temphdf[cfn]['SimpleMetadata']           
        vertHeaders = []
        self.metawidget.table.setRowCount(len(usedMetaData.keys()))
        for n,key in enumerate(usedMetaData.keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(usedMetaData[key][()])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()               
            
    def openAboutPopup(self):
        #Popup  window with details about GUI 
        dir_path = os.path.dirname(os.path.realpath(__file__))        
        logofname = os.path.join(dir_path, r'northwestern-thumb')
        abtwin = QMessageBox()
        nulogo = QPixmap(logofname).scaled(100,100,QtCore.Qt.KeepAspectRatio)
        abtwin.setIconPixmap(nulogo)
        abtwin.setWindowTitle("About")
        abtwin.setText("Information about the project goes here.")
        abtwin.setInformativeText("Northwestern University / NUANCE Center. 2020. ")
        abtwin.button = QPushButton('Okay')
        abtwin.button.clicked.connect(abtwin.close)
        abtwin.setDefaultButton(abtwin.button)        
        abtwin.exec_()

    def changeMetadataType(self):
        state = self.metawidget.metaChoice.currentText()
        self.metawidget.table.setRowCount(0)
        global temphdf
        cfn = self.metawidget.fql.currentItem().text()
        #select which metadata variable to use
        if state == "Simplified Metadata":
            try:
                usedMetaData = temphdf[cfn]['SimpleMetadata']
            except IndexError:
                pass
        elif state == "Full Metadata":
            try:
                usedMetaData = temphdf[cfn]['OriginalMetadata']
            except IndexError:
                pass                    
        
        vertHeaders = []
        self.metawidget.table.setRowCount(len(usedMetaData.keys()))
        for n,key in enumerate(usedMetaData.keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(usedMetaData[key][()])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()             
                
    def saveLogFile(self):
        #Saves everything on the log widget to a text file with pre-defined name
        logfname = 'Output.txt'
        np.savetxt(logfname,[self.logwidget.textw.toPlainText()], fmt='%s',encoding='utf-8')
        self.logwidget.textw.append(f"Saved log to file: {logfname}\n")
    
    def loadSavedHDF5(self):
        self.dlg = QFileDialog()
        filefilters = "HDF5 (*.hdf5)"
        self.fname, self.filterChoice = self.dlg.getOpenFileName(self, "Select an Image file...",filter=filefilters,options=QFileDialog.DontUseNativeDialog)            
        
        if self.fname == "":
            print("EMPTY!")
        
        self.metawidget.fql.clear()
        self.metawidget.fql.setCurrentRow(0)        

        #select correct image loading function based on choice from file menu
        try: del imdata, metadata, simplemdata
        except: pass

        global temphdf
        nhdfkeys = len(temphdf.keys())
        temphdf.close()
        if nhdfkeys != 0:
            os.remove(self.hdf5name)
        temphdf = h5py.File(self.hdf5name,"a") 
        
        hfdata = h5py.File(self.fname,"a")
        imglist = list(hfdata.keys())
        imgOrd = [hfdata[imglistv].attrs['n'] for imglistv in imglist]
        imglistOrd = [x for _,x in sorted(zip(imgOrd,imglist))]   
        self.ordimglist = [x for _,x in sorted(zip(imgOrd,imglist))] 
        imgN = len(hfdata.keys())
        for n,item in enumerate(self.ordimglist):
            self.metawidget.fql.insertItem(n,item)          
        for item in hfdata.keys():
                hfdata.copy(item,temphdf)            
        hfdata.close()

        vertHeaders = []
        self.metawidget.metaChoice.setCurrentIndex(0)
        self.metawidget.table.setRowCount(len(temphdf[imglistOrd[0]]['SimpleMetadata'].keys()))
        for n,key in enumerate(temphdf[imglistOrd[0]]['SimpleMetadata'].keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(temphdf[imglistOrd[0]]['SimpleMetadata'][key][()])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()      

        self.figwidget.figure.clear() #clear figure
        self.axs = []

        #convert imgN to subplot size
        sps_arr = [[1,1],[1,2],[1,3],[2,2],[2,2],[2,2],[2,2],[2,2]]
        sps = sps_arr[imgN-1]

        for i in range(imgN):
            tempax = self.figwidget.figure.add_subplot(sps[0],sps[1],i+1)
            self.axs.append(tempax)

        for i in range(len(self.axs)):
            self.axs[i].imshow(temphdf[imglistOrd[i]]['Im'][()])  #plot data
            self.axs[i].axis("off")            

        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas

    def addVideoFileLoad(self):
        self.fname,self.filterChoice, self.imdata,self.metadata,self.simplemdata = chooseVideoType(self)      
        fndir,fn = os.path.split(self.fname)
        self.metawidget.fql.clear()
        #self.metawidget.fql.insertItem(0,fn)
        self.metawidget.fql.setCurrentRow(0)        
        #self.metawidget.metaChoice.clear()
        #self.metawidget.metaChoice.addItem("Full Metadata")
        #self.metawidget.metaChoice.addItem("Simplified Metadata")   
        
        global temphdf
        nhdfkeys = len(temphdf.keys())
        temphdf.close()
        if nhdfkeys != 0:
            os.remove(self.hdf5name)
            
        temphdf = h5py.File(self.hdf5name,"a")            
        #Save data/metadata into HF backend
        imgrp = temphdf.create_group(fn)
        imgrp.attrs['n'] = 1      
        imgrp['filename'] = self.fname
        imgrp['Im'] = self.imdata
        imgrp['Raw Im'] = self.imdata        
        ogrp = imgrp.create_group("OriginalMetadata")
        for item in self.metadata.items():
            ogrp[item[0]] = item[1]     
        sgrp = imgrp.create_group("SimpleMetadata")
        for item in self.simplemdata.items():
            sgrp[item[0]] = item[1]     

        self.ordimglist = list(temphdf.keys())            


        #convert metadata to table
        vertHeaders = []
        self.metawidget.metaChoice.setCurrentIndex(0)
        self.metawidget.table.setRowCount(len(temphdf[fn]['SimpleMetadata'].keys()))
        for n,key in enumerate(temphdf[fn]['SimpleMetadata'].keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(temphdf[fn]['SimpleMetadata'][key][()])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()
            

        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        axsl = self.figwidget.figure.add_axes([0.19,0.06,0.65,0.05])
        samp = Slider(axsl,'Frame: ', 0, temphdf[fn]['Im'][()].shape[0]-1, valinit=0,valstep=1)

        def slideupdate(val):
            amp = samp.val
            ampind = np.int(amp)
            currentim = temphdf[fn]['Im'][()][ampind,:,:]
            self.ax.imshow(currentim)
            self.figwidget.canvas.draw() # refresh canvas    
        
        samp.on_changed(slideupdate)

        self.ax.imshow(temphdf[fn]['Im'][()][0,:,:])  #plot data
        self.ax.axis("off")
        self.figwidget.canvas.draw() # refresh canvas              
    
    def clickedFilewMetaDataLoad(self):
        self.fname,self.filterChoice, self.imdata,self.metadata,self.simplemdata = chooseFileType(self)      
        fndir,fn = os.path.split(self.fname)
        self.metawidget.fql.clear()
        self.metawidget.fql.insertItem(0,fn)
        self.metawidget.fql.setCurrentRow(0)        
        #self.metawidget.metaChoice.clear()
        #self.metawidget.metaChoice.addItem("Full Metadata")
        #self.metawidget.metaChoice.addItem("Simplified Metadata")   
        
        global temphdf
        nhdfkeys = len(temphdf.keys())
        temphdf.close()
        if nhdfkeys != 0:
            os.remove(self.hdf5name)
            
        temphdf = h5py.File(self.hdf5name,"a")            
        #Save data/metadata into HF backend
        imgrp = temphdf.create_group(fn)
        imgrp.attrs['n'] = 1      
        imgrp['filename'] = self.fname
        imgrp['Im'] = self.imdata
        imgrp['Raw Im'] = self.imdata        
        ogrp = imgrp.create_group("OriginalMetadata")
        for item in self.metadata.items():
            ogrp[item[0]] = item[1]     
        sgrp = imgrp.create_group("SimpleMetadata")
        for item in self.simplemdata.items():
            sgrp[item[0]] = item[1]     

        self.ordimglist = list(temphdf.keys())            


        #convert metadata to table
        vertHeaders = []
        self.metawidget.metaChoice.setCurrentIndex(0)
        self.metawidget.table.setRowCount(len(temphdf[fn]['SimpleMetadata'].keys()))
        for n,key in enumerate(temphdf[fn]['SimpleMetadata'].keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(temphdf[fn]['SimpleMetadata'][key][()])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()
            

        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        self.ax.imshow(temphdf[fn]['Im'][()])  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas   

    def addFilewMetaDataLoad(self):
        self.fname,self.filterChoice, self.imdata,self.metadata,self.simplemdata = chooseFileType(self)      
        fndir,fn = os.path.split(self.fname)        
          
        global temphdf
        temphdf = h5py.File(self.hdf5name,"a") 
        imglist = list(temphdf.keys())            
        imgN = len(temphdf.keys())

        self.metawidget.fql.insertItem(imgN,fn)

        if fn in imglist:
            try:
                fn = fn + "Copy" 
            except:
                fn = fn + "Copy2"                     
        #Save data/metadata into HF backend
        imgrp = temphdf.create_group(fn) 
        imgrp.attrs['n'] = imgN+1
        imgrp['filename'] = self.fname
        imgrp['Im'] = self.imdata
        imgrp['Raw Im'] = self.imdata
        ogrp = imgrp.create_group("OriginalMetadata")
        for item in self.metadata.items():
            ogrp[item[0]] = item[1]     
        sgrp = imgrp.create_group("SimpleMetadata")
        for item in self.simplemdata.items():
            sgrp[item[0]] = item[1]   
        imglist = list(temphdf.keys())            
        imgN = len(temphdf.keys())        
        imgOrd = [temphdf[imglistv].attrs['n'] for imglistv in imglist]
        imglistOrd = [x for _,x in sorted(zip(imgOrd,imglist))]   
        self.ordimglist = [x for _,x in sorted(zip(imgOrd,imglist))] 
        
        #convert metadata to table
        vertHeaders = []
        self.metawidget.table.setRowCount(len(self.simplemdata))
        for n,key in enumerate(self.simplemdata.keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(self.simplemdata[key])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()
    
        self.figwidget.figure.clear() #clear figure
        self.axs = []

        #convert imgN to subplot size
        sps_arr = [[1,1],[1,2],[1,3],[2,2],[2,2],[2,2],[2,2],[2,2]]
        sps = sps_arr[imgN-1]

        for i in range(imgN):
            tempax = self.figwidget.figure.add_subplot(sps[0],sps[1],i+1)
            self.axs.append(tempax)

        for i in range(len(self.axs)):
            self.axs[i].imshow(temphdf[imglistOrd[i]]['Im'][()])  #plot data
            self.axs[i].axis("off")            

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
                for item in temphdf.keys():                    
                    temphdf.copy(item,hfsave) 
            self.logwidget.textw.append(f"Saved data as HDF5 File: {savename}\n")
        return saveFile
    def closeEvent(self,*args,**kwargs):
        super(QMainWindow,self).closeEvent(*args,**kwargs)
        temphdf.close()

    def openFilterSettings(self):
        self.fw = filteringWindow()
        self.fw.show()
        self.fw.exec_()
        isCheckedChoice = [self.fw.qc1.isChecked(),self.fw.qc2.isChecked(),self.fw.qc3.isChecked(),self.fw.qc4.isChecked()]
        filterValues = self.fw.filterValues
        sigmav = filterValues[1]            
        global temphdf
        imglist = self.ordimglist
        if filterValues[0] == "Gaussian":
            for n,i in enumerate(isCheckedChoice):
                if i == True:
                    try:
                        temphdf[imglist[n]]['fIm'] = gaussian_filter(temphdf[imglist[n]]['Im'],sigmav)
                    except:
                        temphdf[imglist[n]]['fIm'][()] = gaussian_filter(temphdf[imglist[n]]['Im'],sigmav)                            
                    temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]
                elif i == False:
                    continue                    
            self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigmav}\n")                 
        elif filterValues[0] == "Gaussian-laplace":
            for n,i in enumerate(isCheckedChoice):
                if i == True:
                    try:
                        temphdf[imglist[n]]['fIm'] = gaussian_laplace(temphdf[imglist[n]]['Im'],sigmav)
                    except:
                        temphdf[imglist[n]]['fIm'][()] = gaussian_laplace(temphdf[imglist[n]]['Im'],sigmav)                            
                    temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]
                elif i == False:
                    continue
            self.logwidget.textw.append(f"Applied Gaussian-Laplace Filter with \u03C3 = {sigmav}\n")             
        
        elif filterValues[0] == "Laplace":
            for n,i in enumerate(isCheckedChoice):
                if i == True:
                    try:
                        temphdf[imglist[n]]['fIm'] = laplace(temphdf[imglist[n]]['Im'])
                    except:
                        temphdf[imglist[n]]['fIm'][()] = laplace(temphdf[imglist[n]]['Im'])                            
                    temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]
                elif i == False:
                    continue                    
            self.logwidget.textw.append(f"Applied {filterValues[0]} Filter\n") 
        elif filterValues[0] == "Sobel":
            for n,i in enumerate(isCheckedChoice):
                if i == True:
                    try:
                        temphdf[imglist[n]]['fIm'] = sobel(temphdf[imglist[n]]['Im'])
                    except:
                        temphdf[imglist[n]]['fIm'][()] = sobel(temphdf[imglist[n]]['Im'])                            
                    temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]
                elif i == False:
                    continue                   
            self.logwidget.textw.append(f"Applied {filterValues[0]} Filter\n") 
        elif filterValues[0] == "None":
            pass
        else:
            pass
    
        self.figwidget.figure.clear() #clear figure
        self.axs = []

        #convert imgN to subplot size
        imgN = len(imglist)
        sps_arr = [[1,1],[1,2],[1,3],[2,2],[2,2],[2,2],[2,2],[2,2]]
        sps = sps_arr[imgN-1]

        for i in range(imgN):
            tempax = self.figwidget.figure.add_subplot(sps[0],sps[1],i+1)
            self.axs.append(tempax)

        for i in range(len(self.axs)):
            self.axs[i].imshow(temphdf[imglist[i]]['Im'][()])  #plot data
            self.axs[i].axis("off")            

        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas        
        
                 
    def openFilterSettingsVideo(self):
        self.fw = filteringWindow()
        self.fw.show()
        self.fw.exec_()
        filterValues = self.fw.filterValues
        sigmav = filterValues[1]
        n = 0 
        global temphdf
        imglist = self.ordimglist
        if filterValues[0] == "Gaussian":
            tempflt = np.zeros(temphdf[imglist[n]]['Im'].shape)    
            for i in range(temphdf[imglist[n]]['Im'].shape[0]):
                temp_fr = temphdf[imglist[n]]['Im'][i,:,:]
                temp_fr = gaussian_filter(temp_fr,sigmav)
                tempflt[i,:,:] = temp_fr
            try:
                temphdf[imglist[n]]['fIm'] = tempflt
            except:
                temphdf[imglist[n]]['fIm'][()] = tempflt                            
            temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]                  
            self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigmav}\n")                 
        elif filterValues[0] == "Gaussian-laplace":
            pass
        elif filterValues[0] == "None":
            pass
        else:
            pass
        
        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        axsl = self.figwidget.figure.add_axes([0.19,0.06,0.65,0.05])
        samp = Slider(axsl,'Frame: ', 0, temphdf[imglist[n]]['Im'][()].shape[0]-1, valinit=0,valstep=1)

        def slideupdate(val):
            amp = samp.val
            ampind = np.int(amp)
            currentim = temphdf[imglist[n]]['Im'][()][ampind,:,:]
            self.ax.imshow(currentim)
            self.figwidget.canvas.draw() # refresh canvas    
        
        samp.on_changed(slideupdate)

        self.ax.imshow(temphdf[imglist[n]]['Im'][()][0,:,:])  #plot data
        self.ax.axis("off")
        self.figwidget.canvas.draw() # refresh canvas                   
         
                 
    def OpenPlotSettingsWindow(self):
        #issue with using >4 images..
        self.ps = plotSettingsWindow()
        self.ps.show()
        self.ps.exec_()
        def run():
            global temphdf
            try:
                for axn in self.figwidget.figure.axes:
                    axn.artists.pop(0)
            except IndexError:
                pass
            axes = self.figwidget.figure.axes                    
            for n,barlabel in enumerate(self.ps.scalelist):       
                if barlabel == "N/A":
                    continue
                    print("N/A Skipped")
                barunit = barlabel[-2:]                
                if barunit == "um":
                    barvalue = float(barlabel[:-2])*1e-6
                    barlabel=barlabel[:-2]+"\u03BCm"
                elif barunit == "nm":
                    barvalue = float(barlabel[:-2])*1e-9
                elif barunit == "mm":
                    barvalue = float(barlabel[:-2])*1e-3
                elif (barunit[-1] == "A") or (barunit[-1] == "a") :
                    barvalue = float(barlabel[:-1])*1e-10
                    barlabel=barlabel[:-1]+"A"                
                try:
                    if self.ps.conversionf.text() == "N/A":
                        cf = float(temphdf[self.ordimglist[n]]['SimpleMetadata']['Conversion Factor (m per px)'][()])
                        barsize = barvalue/cf                    
                    else:
                        barsize = float(self.ps.conversionf.text()) #Update this..
                    
                    scalebar = AnchoredSizeBar(axes[n].transData,
                                   barsize, barlabel, 'lower left', 
                                   pad=0.25,
                                   color='black',frameon=True,
                                   size_vertical=18,
                                   fontproperties=fm.FontProperties(size=25, family='Arial'))
        
                    axes[n].add_artist(scalebar)
                    self.figwidget.canvas.draw() # refresh canvas
                except:
                    self.logwidget.textw.append("Cannot add scalebar. Check metadata for conversion factor.\n")
        if self.ps.labelApplied == True:
            run()
        else:
            pass
    def applyFFT(self):
        self.fftw = fftWindow()
        self.fftw.show()
        self.fftw.exec_()
        def run():
            global temphdf
            imglist = self.ordimglist
            for img in imglist:
                rawfftData = np.fft.fft2(temphdf[img]['Im'][()])
                shiftedfftData = np.fft.fftshift(rawfftData)
                absShiftedfftData = np.abs(shiftedfftData)
                if self.fftw.fftzscaling.currentText() == "None":
                    plotfftData= absShiftedfftData
                elif self.fftw.fftzscaling.currentText() == "Log":                    
                    plotfftData = np.log(absShiftedfftData)
                elif self.fftw.fftzscaling.currentText() == "Log10":                    
                    plotfftData = np.log10(absShiftedfftData)
                temphdf[img]['FFT'] = plotfftData
                temphdf[img].attrs['FFTType'] = self.fftw.fftzscaling.currentText()  

            self.figwidget.figure.clear() #clear figure
            self.axs = []
    
            #convert imgN to subplot size
            imgN = len(imglist)
            sps_arr = [[1,2],[2,2],[2,2],[2,2],[2,2],[2,2],[2,2]]
            sps = sps_arr[imgN-1]
    
            for i in range(sps[0]*sps[1]):
                tempax = self.figwidget.figure.add_subplot(sps[0],sps[1],i+1)
                self.axs.append(tempax)
            print(sps,len(self.axs))
            for i in range(int(len(self.axs)/2)):
                if sps[0]*sps[1] == 2:
                    ii = 1
                else:
                    ii = 2
                self.axs[i].imshow(temphdf[imglist[i]]['Im'][()])  #plot data
                self.axs[i].set_title('Original Image')
                self.axs[i].axis("off")       
                self.axs[i+ii].imshow(temphdf[imglist[i]]['FFT'][()])  #plot data
                self.axs[i+ii].set_title('FFT')
                self.axs[i+ii].axis("off")                
    
            self.figwidget.figure.tight_layout()
            self.figwidget.canvas.draw() # refresh canvas  
            
        if self.fftw.fftapplied == "True":
            run()
        else:
            print("pass!")
              
    def applyFFTVideo(self):
        self.fftw = fftWindow()
        self.fftw.show()
        self.fftw.exec_()
        def run():
            global temphdf
            imglist = self.ordimglist
            n = 0
            tempfft = np.zeros(temphdf[imglist[n]]['Im'].shape)
            for i in range(0,temphdf[imglist[n]]['Im'].shape[0]):
                temp_fr = temphdf[imglist[n]]['Im'][i,:,:]
                rawfftData = np.fft.fft2(temp_fr)
                shiftedfftData = np.fft.fftshift(rawfftData)
                absShiftedfftData = np.abs(shiftedfftData)
                if self.fftw.fftzscaling.currentText() == "None":
                    plotfftData= absShiftedfftData
                elif self.fftw.fftzscaling.currentText() == "Log":                    
                    plotfftData = np.log(absShiftedfftData)
                elif self.fftw.fftzscaling.currentText() == "Log10":                    
                    plotfftData = np.log10(absShiftedfftData)
                tempfft[i,:,:] = plotfftData
            try:
                temphdf[imglist[n]]['FFT'] = tempfft
            except:
                temphdf[imglist[n]]['FFT'][()] = tempfft
            temphdf[imglist[n]].attrs['FFTType'] = self.fftw.fftzscaling.currentText()  
                         
            self.figwidget.figure.clear() #clear figure
            self.ax = self.figwidget.figure.add_subplot(121) # create an axis
            self.ax2 = self.figwidget.figure.add_subplot(122)
            axsl = self.figwidget.figure.add_axes([0.19,0.06,0.65,0.05])
            samp = Slider(axsl,'Frame: ', 0, temphdf[imglist[n]]['FFT'][()].shape[0]-1, valinit=0,valstep=1)
    
            def slideupdate(val):
                amp = samp.val
                ampind = np.int(amp)
                currentim = temphdf[imglist[n]]['Im'][()][ampind,:,:]
                currentfft = temphdf[imglist[n]]['FFT'][()][ampind,:,:]
                self.ax.imshow(currentim)
                self.ax2.imshow(currentfft)
                self.figwidget.canvas.draw() # refresh canvas    
            
            samp.on_changed(slideupdate)
    
            self.ax.imshow(temphdf[imglist[n]]['Im'][()][0,:,:])  #plot data
            self.ax2.imshow(temphdf[imglist[n]]['FFT'][()][0,:,:])  #plot data            
            self.ax.axis("off")
            self.ax2.axis("off")
            self.figwidget.canvas.draw() # refresh canvas 

                    
        if self.fftw.fftapplied == "True":
            run()
        else:
            pass                

    def align3DImageStack(self):
        self.fftw = fftWindow()
        self.fftw.show()
        self.fftw.exec_()
        def run():
            global temphdf
            imglist = self.ordimglist
            n = 0
            tempfft = np.zeros(temphdf[imglist[n]]['Im'].shape)
            for i in range(0,temphdf[imglist[n]]['Im'].shape[0]):
                temp_fr = temphdf[imglist[n]]['Im'][i,:,:]
                rawfftData = np.fft.fft2(temp_fr)
                shiftedfftData = np.fft.fftshift(rawfftData)
                absShiftedfftData = np.abs(shiftedfftData)
                if self.fftw.fftzscaling.currentText() == "None":
                    plotfftData= absShiftedfftData
                elif self.fftw.fftzscaling.currentText() == "Log":                    
                    plotfftData = np.log(absShiftedfftData)
                elif self.fftw.fftzscaling.currentText() == "Log10":                    
                    plotfftData = np.log10(absShiftedfftData)
                tempfft[i,:,:] = plotfftData
            try:
                temphdf[imglist[n]]['FFT'] = tempfft
            except:
                temphdf[imglist[n]]['FFT'][()] = tempfft
            temphdf[imglist[n]].attrs['FFTType'] = self.fftw.fftzscaling.currentText()  
                         
            self.figwidget.figure.clear() #clear figure
            self.ax = self.figwidget.figure.add_subplot(121) # create an axis
            self.ax2 = self.figwidget.figure.add_subplot(122)
            axsl = self.figwidget.figure.add_axes([0.19,0.06,0.65,0.05])
            samp = Slider(axsl,'Frame: ', 0, temphdf[imglist[n]]['FFT'][()].shape[0]-1, valinit=0,valstep=1)
    
            def slideupdate(val):
                amp = samp.val
                ampind = np.int(amp)
                currentim = temphdf[imglist[n]]['Im'][()][ampind,:,:]
                currentfft = temphdf[imglist[n]]['FFT'][()][ampind,:,:]
                self.ax.imshow(currentim)
                self.ax2.imshow(currentfft)
                self.figwidget.canvas.draw() # refresh canvas    
            
            samp.on_changed(slideupdate)
    
            self.ax.imshow(temphdf[imglist[n]]['Im'][()][0,:,:])  #plot data
            self.ax2.imshow(temphdf[imglist[n]]['FFT'][()][0,:,:])  #plot data            
            self.ax.axis("off")
            self.ax2.axis("off")
            self.figwidget.canvas.draw() # refresh canvas 

                    
        if self.fftw.fftapplied == "True":
            run()
        else:
            pass                
    def refreshfigurecanvas(self):     
        #Resizes figure when changing size of main window
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas 


            
def chooseFileType(self):
    #Test function so multiple files can be opened?
    self.dlg = QFileDialog()
    filefilters = "Generic Image File (*.tiff *.tif *.png *.jpg *.jpeg);; Hitachi SEM Image (*.tif *.tiff);;JEOL SEM Image (*.tif *.tiff);;FEI Quanta SEM Image (*.tif *.tiff);; Bruker AFM (*.spm);; Gatan (*.dm3 *.dm4);; Thermofischer (*.ser)"
    fname, filterChoice = self.dlg.getOpenFileName(self, "Select an Image file...",filter=filefilters,options=QFileDialog.DontUseNativeDialog)            
    #select correct image loading function based on choice from file menu
    try: del imdata, metadata, simplemdata
    except: pass
    if "Hitachi" in filterChoice:
        try:
            metafname = fname[0:-3]+'txt'
            imdata,metadata,simplemdata = HitachiSEMImageLoad(fname,metafname)
        except:                
            metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
            imdata,metadata,simplemdata = HitachiSEMImageLoad(fname,metafname)          
    elif "Quanta" in filterChoice:
        metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
        imdata,metadata,simplemdata = QuantaSEMImageLoad(fname,metafname)                
    elif "JEOL" in filterChoice:
        try:
            metafname = fname[0:-3]+'txt' 
            imdata,metadata,simplemdata = JEOL7900SEMImageLoad(fname,metafname)                
        except:
            metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
            imdata,metadata,simplemdata = JEOL7900SEMImageLoad(fname,metafname)
    elif "Generic Image" in filterChoice:
        imdata,metadata,simplemdata = GenericImageOpenTIFF(fname)
    elif "Bruker" in filterChoice:
        imdata,metadata,simplemdata = BrukerAFMImageLoad(fname)
    elif "Gatan" in filterChoice:
        imdata,metadata,simplemdata = dmImageLoad(fname)
    elif "Thermofischer" in filterChoice:
        imdata,metadata,simplemdata = SERImageLoad(fname) 
    self.logwidget.textw.append(f"Opened file: {fname} \n")                      
    self.logwidget.textw.append(f"File Type Selected: {filterChoice} \n")                 
    return fname, filterChoice, imdata, metadata, simplemdata

def chooseVideoType(self):
    #Test function so multiple files can be opened?
    self.dlg = QFileDialog()
    filefilters = f"Generic AVI (*.avi);; Quanta AVI (*.avi);; Gatan (*.dm3 *.dm4);; Thermofischer (*.ser)"
    fname, filterChoice = self.dlg.getOpenFileName(self, "Select an Image file...",filter=filefilters,options=QFileDialog.DontUseNativeDialog)            
    #select correct image loading function based on choice from file menu
    try: del imdata, metadata, simplemdata
    except: pass
    if "AVI" in filterChoice:
        if "Generic" in filterChoice:                          
            imdata,metadata,simplemdata = AVIreader(fname,"Generic")
        elif "Quanta" in filterChoice:
            imdata,metadata,simplemdata = AVIreader(fname,"Quanta")                
    elif "Gatan" in filterChoice:
        imdata,metadata,simplemdata = dm3DLoad(fname)
    elif "Thermofischer" in filterChoice:
        imdata,metadata,simplemdata = SERImageLoad(fname) 
    self.logwidget.textw.append(f"Opened file: {fname} \n")                      
    self.logwidget.textw.append(f"File Type Selected: {filterChoice} \n")                 
    return fname, filterChoice, imdata, metadata, simplemdata
        
def clearAllFilters(self):
    def run():
        #self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        global temphdf
        #self.ax.imshow(temphdf[imglist[0]]['Im'][()])  #plot data
        #self.ax.axis("off")
        #self.figwidget.figure.tight_layout()
        imglist = self.ordimglist
        for n,axn in enumerate(self.figwidget.figure.axes):
            axn.clear()
            temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['Raw Im'][()]            
            axn.imshow(temphdf[imglist[n]]['Im'][()])
            axn.axis("Off")
        self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Reset figure to raw data \n")        
    return run    

def BasicGaussianFilter(self,temphdf,sigmav=3):
    def run():
        prevcmap = mpl.cm.get_cmap().name
        imagedata = self.imdata
        fdata = gaussian_filter(imagedata,sigmav)
        self.ax.imshow(fdata)  #plot data
        global temphdf
        imglist = self.ordimglist
        for n,axn in enumerate(self.figwidget.figure.axes):
            try:
                temphdf[imglist[n]]['fIm'] = gaussian_filter(temphdf[imglist[n]]['Im'],sigmav)
            except:
                temphdf[imglist[n]]['fIm'][()] = gaussian_filter(temphdf[imglist[n]]['Im'],sigmav)                            
            temphdf[imglist[n]]['Im'][()] = temphdf[imglist[n]]['fIm'][()]      
            axn.imshow(temphdf[imglist[n]]['Im'][()])        
        
        self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigma}\n")
    return run        

def main():
    app = QApplication(sys.argv)
    mainWindow = Window()
    mainWindow.showMaximized()
    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

