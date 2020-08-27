#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: Nathaniel Kabat

"""
import numpy as np
import matplotlib.pyplot as plt
import skimage
from skimage import io
import pySPM
import os


def GenericImageOpenTIFF(filename):
    '''
    Generic TIFF Open function
    '''      
    meta_data = {"Error":"No metadata for generic image file"}
    simple_meta_data = meta_data
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data,simple_meta_data

def HitachiSEMImageLoad(filename,meta_filename):
    '''
    This SHOULD work for the the follwing Hitach SEM models:   
        - 4800 (VERIFIED as .TIFF + Metadata .txt)
        - 3400 (NOT verified)
        - 8030 (Partially verified)
    
    You must use the original TIFF file as exported from the SEM. 
    This code assumes that the metadata file has the same name as the image file (This is how the microscope exports)        
    '''    
    meta_data = {}
    simple_meta_data = {}
    with open(meta_filename) as f:
        keys = []
        values = []
        next(f)
        for line in f:
            templine = line.strip("\n").split("=")
            keys.append(templine[0])
            if templine[1] == "":
                values.append("N/A")
            else:
                values.append(templine[1])
    meta_data = dict(zip(keys,values))   
    #Create custom metadata
    simple_meta_data['Instrument']=meta_data['InstructName']
    simple_meta_data['Date']=meta_data['Date']
    simple_meta_data['Time']=meta_data['Time']
    simple_meta_data['Detector'] = meta_data['SignalName']
    simple_meta_data['Accelerating Voltage (V)'] =meta_data['AcceleratingVoltage']
    simple_meta_data['Magnification'] = meta_data['Magnification']
    simple_meta_data['Working Distance'] = meta_data['WorkingDistance']
    simple_meta_data['Emission Current'] = meta_data['EmissionCurrent']
    simple_meta_data['Image Size (px)'] = meta_data['DataSize']
    simple_meta_data['Conversion Factor (m per px)'] = str(float(meta_data['PixelSize'])*1e-9)
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data,simple_meta_data
    

def QuantaSEMImageLoad(filename,meta_filename):
    '''
    This SHOULD work with the following FEI SEM Models:
        - Quanta 650
        - TBD
    This function requires:
        - the original TIFF (or other image format) as exported from the SEM
        - a text file with the COPIED metadata that is embedded at the end of the original tiff file. 
    
    '''
    meta_data = {}
    simple_meta_data = {}
    with open(meta_filename) as f:
        keys = []
        values = []
        for line in f:
            templine = line.strip("\n").split("=")
            if templine[0] == "":   
                pass
            else:
                try:
                    keys.append(templine[0])
                except:
                    keys.append("")
                try:
                    values.append(templine[1])
                except:
                    values.append(templine[0])
    meta_data = dict(zip(keys,values))
    simple_meta_data['Instrument']=meta_data['SystemType']
    simple_meta_data['Date']=meta_data['Date']
    simple_meta_data['Time']=meta_data['Time']
    simple_meta_data['Detector'] = meta_data['Signal']
    simple_meta_data['Accelerating Voltage (V)'] =meta_data['HV']
    simple_meta_data['Magnification'] = "N/A"
    simple_meta_data['Working Distance'] = meta_data['WorkingDistance']
    simple_meta_data['Emission Current'] = meta_data['EmissionCurrent']
    simple_meta_data['Image Size (px)'] = meta_data['ResolutionX']+'x'+meta_data['ResolutionY']
    simple_meta_data['Conversion Factor (m per px)'] = meta_data['PixelWidth'] 
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data,simple_meta_data



def JEOL7900SEMImageLoad(filename,meta_filename):
    '''
    This SHOULD work for the following JEOL SEM Models:
        - 7900
        - TBD
    This function requires:
        - The original TIFF (or other image format) as exported from the SEM
        - The metadata file (as exported by the SEM)   
    NOTE: Issue with loading metadata into PyQT5 table function. Something with lists.
    '''
    meta_data = {}
    simple_meta_data = {}    
    with open(meta_filename) as f:
        keys = []
        values = []
        for line in f:
            templine = line.strip("\n").strip("$").split(" ")
            if len(templine) <= 2:
                tempValues = templine[-1]
            else:
                tempValues = str([i for i in templine[1:]])
            try:
                keys.append(templine[0])
            except:
                keys.append("")
            try:
                values.append(tempValues)
            except:
                values.append("")
    meta_data = dict(zip(keys,values))
    if meta_data['SM_MICRON_MARKER'][-2:] == 'um':
        um2mConversionFactor = 1e-6
        cf = um2mConversionFactor
    elif meta_data['SM_MICRON_MARKER'][-2:] == 'nm':
        nm2mConversionFactor = 1e-9
        cf = um2mConversionFactor        
    elif meta_data['SM_MICRON_MARKER'][-2:] == 'mm':
        mm2mConversionFactor = 1e-3
        cf = um2mConversionFactor        
    simple_meta_data['Instrument']=meta_data['CM_INSTRUMENT']
    simple_meta_data['Date']=meta_data['CM_DATE']
    simple_meta_data['Time']=meta_data['CM_TIME']
    simple_meta_data['Detector'] = meta_data['CM_DETECTOR_NAME']
    simple_meta_data['Accelerating Voltage (kV)'] =meta_data['CM_ACCEL_VOLT']
    simple_meta_data['Magnification'] = meta_data['CM_MAG']
    simple_meta_data['Working Distance'] = meta_data['SM_WD']
    simple_meta_data['Emission Current'] = meta_data['SM_EMI_CURRENT']
    simple_meta_data['Image Size (px)'] = meta_data['CM_FULL_SIZE']
    simple_meta_data['Conversion Factor (m per px)'] = str(cf*float(meta_data['SM_MICRON_MARKER'][:-2])/float(meta_data['SM_MICRON_BAR']))
    
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data,simple_meta_data


def BrukerAFMImageLoad(filename):
    import pySPM
    scan = pySPM.Bruker(filename)
    mdata = scan.layers[0]
    simple_meta_data = {}    
    meta_data ={}
    for item in mdata.items():
        print(item)
        tempValue = item[1][0].decode('UTF-8')
        print(tempValue)
        meta_data[item[0].decode('UTF-8')]=tempValue   
    try:
        scan_data = scan.get_channel()
    except:
        scan_data = scan.get_channel(backward=True)
    
    simple_meta_data['Image Type'] = meta_data['Data type']
    #simple_meta_data['Conversion Factor (m per px)'] = meta_data['Scan Size']
        
    return scan_data.pixels, meta_data, simple_meta_data

def dmImageLoad(filename):
    '''
    This should work for any Digital Micrograph file (dm3,dm4) that is an image.
    3D Datasets will only show 1st image in series (time series, etc).
    Assumes that x & y pixel size are equal. 
    '''
    from ncempy.io import dm

    data = dm.dmReader(filename)

    image_data = data['data']
    meta_data = {} 
    [data.pop(k) for k in ['data','coords']]
    pxSize = data['pixelSize'][1] 
    for k,v in data.items():
        meta_data[k] = str(v)
    simple_meta_data = meta_data
    simple_meta_data['Conversion Factor (m per px)'] =str(float(pxSize)*1e-9)        
    if len(image_data.shape) > 2: #if dataset is 3D, return 1st image
        image_data = image_data[0,:,:]
    return image_data, meta_data, simple_meta_data

def SERImageLoad(filename):
    '''
    ????
    '''
    from ncempy.io import ser
    
    data = ser.serReader(filename)
    
    image_data = data['data']
    meta_data = {} 
    data.pop('data')
    pxSize = data['pixelSize'][1] 
    for k,v in data.items():
        meta_data[k] = str(v)
    simple_meta_data = meta_data
    simple_meta_data['Conversion Factor (m per px)'] =str(float(pxSize))        
    if len(image_data.shape) > 2: #if dataset is 3D, return 1st image
        image_data = image_data[0,:,:]
    return image_data, meta_data, simple_meta_data

def main():
    '''
    Will load data for test images outside of GUI if this file is run separately. 
    This is useless if image load functions are called in the GUI.
    '''
    codeDir = os.path.dirname(os.path.realpath(__file__))       
    sharedLocation = os.path.join(codeDir,r'samplefiles')
    HS4800_fn = os.path.join(sharedLocation, r'S4800',r'tin.tif')    #Hitachi Test File
    HS4800_mfn = os.path.join(sharedLocation, r'S4800',r'tin.TXT')    #Hitachi Test File
    q_fn = os.path.join(sharedLocation, r'Quanta',r'ResolutionTest_SE_10kx_5kv_008.tif')    #Quanta Test File 
    q_mfn = os.path.join(sharedLocation, r'Quanta',r'ResolutionTest_SE_10kx_5kv_008-COPIED.TXT')    #Quanta Test File 
    j7900_fn = os.path.join(sharedLocation, r'7900',r'tt_LED_2.tif')    #JEOL 7900 Test File 
    j7900_mfn = os.path.join(sharedLocation,r'7900',r'tt_LED_2.TXT')      #JEOL 7900 Test File 
    bruker_fn = os.path.join(sharedLocation,r'BrukerFastScanAFM',r'test.0_00000.spm')    #Bruker test file
    gatan_fn = os.path.join(sharedLocation,r'Gatan',r'Image.dm3') #Gatan test file 


    HS4800_idata,HS4800_mdata,HS4800_simple_mdata = HitachiSEMImageLoad(HS4800_fn,HS4800_mfn)
    q_idata,q_mdata,q_simple_mdata = QuantaSEMImageLoad(q_fn,q_mfn)
    j7900_idata,j7900_mdata,j7900_simple_mdata = JEOL7900SEMImageLoad(j7900_fn, j7900_mfn)
    bruker_idata,bruker_mdata,bruker_simple_mdata = BrukerAFMImageLoad(bruker_fn)
    dm3_idata,dm3_mdata,dm3_simple_mdata = dmImageLoad(gatan_fn)
    print(bruker_mdata)
    
    '''
    fig, ax = plt.subplots(1,5, figsize=(14,3))
    plt.suptitle('Sample Images')
    plt.subplot(151)
    plt.title('Hitachi SEM')
    plt.imshow(HS4800_idata)
    plt.axis('off')
    plt.subplot(152)
    plt.title('FEI Quanta SEM')
    plt.imshow(q_idata)
    plt.axis('off')    
    plt.subplot(153)
    plt.title('JEOL SEM')    
    plt.imshow(j7900_idata)
    plt.axis('off')    
    plt.subplot(154)
    plt.title('Bruker AFM')
    plt.imshow(bruker_idata)
    plt.axis('off')    
    plt.subplot(155)
    plt.title('Gatan .dm3')   
    plt.imshow(dm3_idata)   
    plt.axis('off')          
    plt.show()
    '''
    
if __name__ == "__main__":
    main()



