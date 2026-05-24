import numpy as np

def calculate_ndvi(red, nir):
    return (nir - red) / (nir + red + 1e-8)

def calculate_ndwi(green, nir):
    return (green - nir) / (green + nir + 1e-8)

def calculate_mndwi(green, swir1):
    return (green - swir1) / (green + swir1 + 1e-8)

def calculate_dnbr(nbr_pre, nbr_post):
    return nbr_pre - nbr_post

def calculate_nbr(nir, swir2):
    return (nir - swir2) / (nir + swir2 + 1e-8)

def calculate_evi(blue, red, nir):
    return 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))

def calculate_clay_index(swir1, swir2):
    return swir1 / (swir2 + 1e-8)

def calculate_ferrous_index(swir1, red):
    return swir1 / (red + 1e-8)
