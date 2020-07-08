#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:31:55 2020
@author: Nathaniel Kabat
"""

import sys
import os 
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QCheckBox, QComboBox, QLabel,QPushButton, QMessageBox, QHBoxLayout,QVBoxLayout, QMainWindow,QFileDialog,QWidget, QGridLayout, QLineEdit, QTextBrowser,QTableWidget,QTableWidgetItem, qApp,QMenu,QAction
from PyQt5.QtGui import QIcon, QPixmap
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
from ImageLoadLibraries_v0 import *
mpl.use('Qt5Agg')
progname = os.path.basename(sys.argv[0])
progversion = "0.1"

#Default plotting settings. Setting globally so all figures/images use these.
#We probably GUI window to modify these.
mpl.rc('image',cmap='gray')
mpl.rc('savefig',transparent=True,dpi=1500)


class plotSettingsWindow(QDialog):
    def __init__(self,*args,**kwargs):
        super(plotSettingsWindow,self).__init__(*args,**kwargs)
        ScaleSizeList = ["1 mm","1000 um","500 um","100 um","10 um","1 um","100 nm","10 nm","10 A"]
        self.setLayout(QGridLayout())
        self.setGeometry(400,400,300,200)
        self.ScaleBarCombo = QComboBox(self)
        self.ScaleBarCombo.addItems(ScaleSizeList)
        self.ScaleBarCombo.setCurrentIndex(ScaleSizeList.index('1 um'))
        self.ScaleBarCombo.setEditable(True)
        self.conversionf = QLineEdit(self)
        self.conversionf.setText("N/A")

                       
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Custom Scalebar Settings")
        self.layout().addWidget(QLabel("Scale Bar Size"),0,0)
        self.layout().addWidget(self.ScaleBarCombo,0,1)
        self.layout().addWidget(QLabel("# Pixels\nAcross Scalebar"),1,0)        
        self.layout().addWidget(self.conversionf,1,1)        
        self.layout().addWidget(self.applysettings,3,0)
        self.layout().addWidget(self.cancel,3,1)
    
    def clicktoapply(self):
        self.close()
        
    def cancelClick(self):
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
        
        self.applysettings = QPushButton('Apply')
        self.applysettings.clicked.connect(self.clicktoapply) 
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.cancelClick)

        self.setWindowTitle("Image Filter Settings")
        self.layout().addWidget(self.combo,0)
        self.layout().addWidget(QLabel("Filter Specific Settings:"),1)
        self.layout().addWidget(self.filterOptions,2)
        self.layout().addWidget(self.applysettings,3)
        self.layout().addWidget(self.cancel,4)
    
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
    
class Window(QMainWindow):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.setWindowTitle("NUScope Image Analysis (GUI v0)")
        self.setGeometry(300,250,1350,700)
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

        figwidget.setLayout(QVBoxLayout())
        figwidget.figure = Figure()
        figwidget.canvas = FigureCanvas(figwidget.figure)
        figwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        figwidget.setMinimumSize(700,200)
        figwidget.canvas.updateGeometry()           
        #self.ax = self.figure.add_subplot(111)
        figwidget.toolbar = NavigationToolbar(figwidget.canvas, figwidget)
        figwidget.layout().addWidget(figwidget.toolbar)
        figwidget.layout().addWidget(figwidget.canvas)
        #figwidget.resize(900, 600)        

        #Create widget for metadata:
        self.metawidget =QWidget()
        metawidget = self.metawidget
        #metawidget.resize(150,600)
        metawidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        metawidget.setMinimumSize(350,50)               
        metawidget.setLayout(QVBoxLayout())
        metawidget.table = QTableWidget()
        metawidget.table.setColumnCount(1)
        metawidget.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  
        metawidget.metaChoice = QComboBox(self)
        metawidget.metaChoice.currentIndexChanged.connect(self.changeMetadataType)
        metawidget.layout().addWidget(QtWidgets.QLabel("Metadata Table"))
        metawidget.layout().addWidget(metawidget.metaChoice)
        metawidget.layout().addWidget(metawidget.table)         
        
        #Create widget for log file show
        self.logwidget = QWidget()
        logwidget = self.logwidget
        #logwidget.resize(50,50) #formerly 250,600
        logwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        logwidget.setMinimumSize(250,50)
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
        TwoFileLoad = QAction('&Load Two Files - Correlation', self)
        TwoFileLoad.setShortcut('Ctrl+T')
        TwoFileLoad.setStatusTip('Open File')
        TwoFileLoad.triggered.connect(self.clickedTwoFileDataLoad)        
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
        gaussfilteract.triggered.connect(BasicGaussianFilter(self,tempHF))
        clearfilteract = QAction('&Clear All Filters',self)
        clearfilteract.triggered.connect(clearAllFilters(self))
        fftfilteract = QAction('&FFT',self)
        fftfilteract.triggered.connect(applyFFT(self))
        
        plotsettingsact = QAction('&Plot Settings',self)
        plotsettingsact.triggered.connect(self.OpenPlotSettingsWindow)
        #setup menu bar with basic actions
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)        
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(loadFile)
        fileMenu.addAction(TwoFileLoad)
        fileMenu.addAction(saveLog)
        fileMenu.addAction(saveHDF5)
        fileMenu.addAction(exitAct)
        toolMenu = menuBar.addMenu('&Tools')
        filtersubMenu = QMenu('&Filters',self)
        toolMenu.addMenu(filtersubMenu)
        filtersubMenu.addAction(filteract)
        filtersubMenu.addAction(gaussfilteract)
        filtersubMenu.addAction(clearfilteract)
        toolMenu.addAction(fftfilteract)
        toolMenu.addAction(plotsettingsact)
        helpMenu = menuBar.addMenu('&Help')
        helpMenu.addAction(abtAct)        
        

        # set the layout
        mainw.layout().addWidget(figwidget,0)
        mainw.layout().addWidget(metawidget,1)
        mainw.layout().addWidget(logwidget,2)

    def openAboutPopup(self):
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
        #select which metadata variable to use
        usedMetaData = {}
        if state == "Simplified Metadata":
            usedMetaData = self.simplemdata       
        elif state == "Full Metadata":
            usedMetaData = self.metadata         
        elif state == "Simplified Metadata 2":
            usedMetaData = self.simplemdata2     
        elif state == "Full Metadata 2":
            usedMetaData = self.metadata2                
        vertHeaders = []
        #print(self.metadata.keys())
        self.metawidget.table.setRowCount(len(usedMetaData))
        for n,key in enumerate(usedMetaData.keys()):
            vertHeaders.append(key)
            newitem = QTableWidgetItem(usedMetaData[key])
            self.metawidget.table.setVerticalHeaderLabels(vertHeaders)
            self.metawidget.table.setItem(0, n, newitem)
            self.metawidget.table.resizeColumnsToContents()
            self.metawidget.table.resizeRowsToContents()        
                
    def saveLogFile(self):
        logfname = 'Output.txt'
        np.savetxt(logfname,[self.logwidget.textw.toPlainText()], fmt='%s',encoding='utf-8')
        self.logwidget.textw.append(f"Saved log to file: {logfname}\n")
        
    def clickedFilewMetaDataLoad(self):
        self.fname,self.filterChoice, self.imdata,self.metadata,self.simplemdata = chooseFileType(self)      
        self.metawidget.metaChoice.clear()
        self.metawidget.metaChoice.addItem("Full Metadata")
        self.metawidget.metaChoice.addItem("Simplified Metadata")   
        global tempHF
        nhdfkeys = len(tempHF.keys())
        tempHF.close()
        if nhdfkeys != 0:
            os.remove(self.hdf5name)
            
        tempHF = h5py.File(self.hdf5name,"a")            
        #Save data/metadata into HF backend
        tempHF['filename'] = self.fname
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
    
    
        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(111) # create an axis


        self.ax.imshow(self.imdata)  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas      

    def clickedTwoFileDataLoad(self):

        self.fname,self.filterChoice, self.imdata,self.metadata,self.simplemdata = chooseFileType(self)
        self.fname2,self.filterChoice2,self.imdata2,self.metadata2,self.simplemdata2=chooseFileType(self)
        self.metawidget.metaChoice.clear()
        self.metawidget.metaChoice.addItem("Full Metadata")
        self.metawidget.metaChoice.addItem("Simplified Metadata")
        self.metawidget.metaChoice.addItem("Full Metadata 2")
        self.metawidget.metaChoice.addItem("Simplified Metadata 2")
        
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
        

        self.figwidget.figure.clear() #clear figure
        self.ax = self.figwidget.figure.add_subplot(121) # create an axis
        self.ax.imshow(self.imdata)  #plot data
        self.ax.axis("off")

        self.ax2 = self.figwidget.figure.add_subplot(122)
        self.ax2.imshow(self.imdata2)  #plot data
        self.ax2.axis("off")
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

    def openFilterSettings(self):
            self.fw = filteringWindow()
            self.fw.show()
            self.fw.exec_()
            sigmav = np.int(self.fw.sigmaset.text())
            filterValues = self.fw.filterValues
            if filterValues[0] == "Gaussian":
                self.fdata = gaussian_filter(self.imdata,sigmav)
                self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigmav}\n")                 
            elif filterValues[0] == "Gaussian-laplace":
                self.fdata = gaussian_laplace(self.imdata,sigmav)
                self.logwidget.textw.append(f"Applied Gaussian-Laplace Filter with \u03C3 = {sigmav}\n")             
            elif filterValues[0] == "Laplace":
                self.fdata = laplace(self.imdata)
                self.logwidget.textw.append(f"Applied {filterValues[0]} Filter\n") 
            elif filterValues[0] == "Sobel":
                self.fdata = sobel(self.imdata)
                self.logwidget.textw.append(f"Applied {filterValues[0]} Filter\n") 
            elif filterValues[0] == "None":
                pass
            else:
                self.fdata = np.zeros((1200,1200))
            
            try:
                self.ax.imshow(self.fdata)  #plot data
            except AttributeError:
                pass
            self.ax.axis("off")
            self.figwidget.figure.tight_layout()
            self.figwidget.canvas.draw() # refresh canvas 
    
    def OpenPlotSettingsWindow(self):
            self.ps = plotSettingsWindow()
            self.ps.show()
            self.ps.exec_()
            try:
                for axn in self.figwidget.figure.axes:
                    axn.artists.pop(0)
            except IndexError:
                pass
            barlabel = self.ps.ScaleBarCombo.currentText()
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
                    cf = float(self.simplemdata['Conversion Factor (m/px)'])
                    barsize = barvalue/cf                    
                else:
                    barsize = float(self.ps.conversionf.text())
                
                scalebar = AnchoredSizeBar(self.ax.transData,
                               barsize, barlabel, 'lower left', 
                               pad=0.25,
                               color='black',frameon=True,
                               size_vertical=18,
                               fontproperties=fm.FontProperties(size=25, family='Arial'))
    
                self.ax.add_artist(scalebar)
                self.figwidget.canvas.draw() # refresh canvas
            except:
                self.logwidget.textw.append("Cannot add scalebar. Check metadata for conversion factor.\n") 
            
def chooseFileType(self):
        #Test function so multiple files can be opened?
        self.dlg = QFileDialog()
        filefilters = "Generic Image File (*.tiff *.tif *.png *.jpg *.jpeg);; Hitachi SEM Image (*.tif *.tiff);;JEOL SEM Image (*.tif *.tiff);;FEI Quanta SEM Image (*.tif *.tiff);; Bruker AFM (*.spm);; Gatan (*.dm3 *.dm4)"
        fname, filterChoice = self.dlg.getOpenFileName(self, "Select an Image file...",filter=filefilters,options=QFileDialog.DontUseNativeDialog)            
        #select correct image loading function based on choice from file menu
        try: del imdata
        except: pass
        try: del metadata
        except: pass
        try: del simplemdata
        except: pass
        if "Hitachi" in filterChoice:
            metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
            imdata,metadata,simplemdata = HitachiSEMImageLoad(fname,metafname)          
        elif "Quanta" in filterChoice:
            metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
            imdata,metadata,simplemdata = QuantaSEMImageLoad(fname,metafname)                
        elif "JEOL" in filterChoice:
            metafname, _ = self.dlg.getOpenFileName(self, "Select an Image file...",filter="Text File (*.txt)",options=QFileDialog.DontUseNativeDialog)                            
            imdata,metadata,simplemdata = JEOL7900SEMImageLoad(fname,metafname)
        elif "Generic Image" in filterChoice:
            imdata,metadata,simplemdata = GenericImageOpenTIFF(fname)
        elif "Bruker" in filterChoice:
            imdata,metadata,simplemdata = BrukerAFMImageLoad(fname)
        elif "Gatan" in filterChoice:
            imdata,metadata,simplemdata = dmImageLoad(fname)
        self.logwidget.textw.append(f"Opened file: {fname} \n")                      
        self.logwidget.textw.append(f"File Type Selected: {filterChoice} \n")                 
        return fname, filterChoice, imdata, metadata, simplemdata

def applyFFT(self):
    def run():
        pass
        #add fft function details here
        #image data should be loaded as self.imdata
    return run
    
def clearAllFilters(self):
    def run():
        #self.ax = self.figwidget.figure.add_subplot(111) # create an axis
        self.ax.imshow(self.imdata)  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Reset figure to raw data \n")        
    return run    

def BasicGaussianFilter(self,tempHF,sigma=3):
    #there is an issue with saving to the HDF file within this function. Fix TBD.
    def run():
        prevcmap = mpl.cm.get_cmap().name
        imagedata = self.imdata
        fdata = gaussian_filter(imagedata,sigma)
        self.ax.imshow(fdata)  #plot data
        self.ax.axis("off")
        self.figwidget.figure.tight_layout()
        self.figwidget.canvas.draw() # refresh canvas 
        self.logwidget.textw.append(f"Applied Gaussian Filter with \u03C3 = {sigma}\n")
    return run        

def main():
    app = QApplication(sys.argv)
    mainWindow = Window()
    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

