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


def GenericImageOpenTIFF(filename):
    '''
    Generic TIFF Open function
    '''      
    meta_data = {"e1":"TEST1","e2":"TEST"}
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data

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
    with open(meta_filename) as f:
        keys = []
        values = []
        next(f)
        for line in f:
            templine = line.strip("\n").split("=")
            keys.append(templine[0])
            values.append(templine[1])
    meta_data = dict(zip(keys,values))   
    
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data
    

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
    with open(meta_filename) as f:
        keys = []
        values = []
        next(f)
        for line in f:
            templine = line.strip("\n").split("=")
            print(templine)
            try:
                keys.append(templine[0])
            except:
                keys.append("")
            try:
                values.append(templine[1])
            except:
                values.append("")
    meta_data = dict(zip(keys,values))

    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data



def JEOL7900SEMImageLoad(filename,meta_filename):
    '''
    This SHOULD work for the following JEOL SEM Models:
        - 7900
        - TBD
    This function requires:
        - The original TIFF (or other image format) as exported from the SEM
        - The metadata file (as exported by the SEM)   
    '''
    meta_data = {}
    with open(meta_filename) as f:
        keys = []
        values = []
        for line in f:
            templine = line.strip("\n").strip("$").split(" ")
            if len(templine) <= 2:
                tempValues = templine[-1]
            else:
                tempValues = [i for i in templine[1:]]
            try:
                keys.append(templine[0])
            except:
                keys.append("")
            try:
                values.append(tempValues)
            except:
                values.append("")
    meta_data = dict(zip(keys,values))
    
    image_data = io.imread(filename)
    image_data = skimage.img_as_float(image_data)
    return image_data,meta_data


def BrukerAFMImageLoad(filename):
    import pySPM
    scan = pySPM.Bruker(filename)
    meta_data = scan.layers[0]
    new_meta_data ={}
    for item in meta_data.items():
        tempValue = item[1][0].decode('UTF-8')
        print(tempValue)
        new_meta_data[item[0].decode('UTF-8')]=tempValue   
    try:
        scan_data = scan.get_channel()
    except:
        scan_data = scan.get_channel(backward=True)
    return scan_data.pixels, new_meta_data

def dmImageLoad(filename):
    from ncempy.io import dm

    data = dm.dmReader(filename)
    image_data = im0['data'] 

    return image_data

def main():
    sharedLocation = "/Users/nathaniel_wk/Documents/NUANCE Files/NuScope/Sample File Formats/"
    
    #Hitachi Test File
    hitachiS4800_filename = sharedLocation+"S4800/" + "tin.tif"
    hitachiS4800_metafilename = sharedLocation+"S4800/"+"tin.TXT"
    
    #Quanta Test File 
    quanta_filename = sharedLocation + "Quanta/"+"ResolutionTest_SE_10kx_5kv_008.tif"
    quanta_metafilename = sharedLocation + "Quanta/"+"ResolutionTest_SE_10kx_5kv_008-COPIED.TXT"
    
    #JEOL 7900 Test File 
    location = "/Users/nathaniel_wk/Documents/NUANCE Files/NuScope/Sample File Formats/7900/"
    jeol7900_filename = sharedLocation +"7900/"+"tt_LED_2.tif"
    jeol7900_metafilename = sharedLocation + "7900/"+ "tt_LED_2.TXT"   
    
    S4800_idata,S4800_mdata = HitachiSEMImageLoad(hitachiS4800_filename,hitachiS4800_metafilename)
    quanta_idata,quanta_mdata = QuantaSEMImageLoad(quanta_filename,quanta_metafilename)
    jeol7900_idata,jeol7900_mdata = JEOL7900SEMImageLoad(jeol7900_filename, jeol7900_metafilename)
    plt.imshow(S4800_idata)

if __name__ == "__main__":
    main()



