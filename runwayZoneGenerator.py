# ----------------------------------------------------------------
# ----------------- RUNWAY PROTECT ZONE LIBRARY ------------------
# ----------------------------------------------------------------
# Australian Communications Media Authority
# Navnith Reddy, November 2022

# The GEODATA library provides helper functions which extract
# and format data from the Geoscience Australia Topographic
# database.

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from numpy import arctan2, random, sin, cos, degrees
import math
from shapely.geometry import LineString
from shapely import affinity
import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

# FUNCTION NAMING CONVENTION:
# -> 'get' functions download assets from Geoscience Australia website
# -> 'build' functions create assets based on downloaded assets
# -> 'read' functions are build functions that return variables

def buildRunways():

    # Read centreline dataset and filter for runways centrelines
    centrelines = gpd.read_file("TOPO_250k/Vector_data/Cartography/cartographiclines.shp")
    centrelines = centrelines.loc[centrelines['FEATTYPE'] == 'Runway Centreline']
    centrelines.reset_index(drop=True, inplace=True)
    centrelines.to_file('centrelines/centrelines.shp')
    centrelines.to_csv('centreline_data.csv', index=False)

    # Read airport data and filter for airports
    airports = gpd.read_file("TOPO_250k/Vector_data/Transport/aircraftfacilitypoints.shp")
    airports = airports.loc[airports['FEATTYPE'] == 'Airport']
    airports.reset_index(drop=True, inplace=True)
    airports.to_file('airports/airports.shp')
    airports.to_csv('airports_data.csv', index=False)

    # Reproject both datasets for geometric operations
    airports.to_crs(crs=3857, inplace=True)
    centrelines.to_crs(crs=3857, inplace=True)

    # Create 2 km buffer around airport points and spatial join
    airports['geometry'] = airports.geometry.buffer(2000,3)
    runways = gpd.sjoin(centrelines, airports, how='inner', predicate='intersects')

    # Tidy and save output dataset
    runways = runways[['NAME', 'geometry']]
    runways.reset_index(drop=True, inplace=True)
    runways.to_file('runways/runways.shp')
    runways.to_csv('runways.csv', index=False)

def readRunways():
    
    # Read built runway dataset
    return gpd.read_file("runways/runways.shp")


def perpendicular(lineString, len, side):
    
    left = lineString.parallel_offset(len, 'left')
    right = lineString.parallel_offset(len, 'right')
    
    if (side == 'top'):
        
        leftEnd = left.boundary[1]
        rightEnd = right.boundary[0]
        return LineString([leftEnd, rightEnd])
    
    elif (side == 'bottom'):
        
        leftEnd = left.boundary[0]
        rightEnd = right.boundary[1]
        return LineString([leftEnd, rightEnd])
    
    else:
        
        raise ValueError("Invalid value for side")

def zoneConstructor (lineString):
    
    # Zone Dimensions
    b_len = 2890
    c_len = 1760
    d1_len = 5310
    d2_len = 680

    name = []
    geometry = []
    name.append('Runway Centreline')
    geometry.append(lineString)

    # Exclusion zone
    len = lineString.length
    scale = (len + 2*b_len)/len 
    lenPlus2b = affinity.scale(lineString, xfact=scale, yfact=scale)
    left = lenPlus2b.parallel_offset(c_len, 'left')
    exclusionZone = left.buffer(-2*c_len, single_sided=True)
    name.append('Exclusion Zone')
    geometry.append(exclusionZone)

    # Restriction zone
    scale = (len + 2*b_len + 2*d1_len)/len
    rstLen = affinity.scale(lineString, xfact=scale, yfact=scale)
    left = rstLen.parallel_offset(d2_len/2, 'left')
    restrictionZone = left.buffer(-d2_len, single_sided=True)
    restrictionZone = restrictionZone.difference(exclusionZone)
    name.append('Restriction Zone')
    geometry.append(restrictionZone)

    df = {'Polygon Name' : name , 'geometry': geometry}
    gdf = gpd.GeoDataFrame(df, crs="EPSG:3857")
    
    return gdf

def asymmetricZones (lineString, side):
    
    b_len = 2890
    c_len = 1760
    d1_len = 5310
    d2_len = 680

    name = []
    geometry = []
    name.append('Runway')
    geometry.append(lineString)

    # Exclusion zone
    len = lineString.length
    scale = (len + 2*b_len)/len 
    lenPlus2b = affinity.scale(lineString, xfact=scale, yfact=scale)
    left = lenPlus2b.parallel_offset(c_len, 'left')
    exclusionZone = left.buffer(-2*c_len, single_sided=True)

    # Restriction zone
    scale = (len + 2*b_len + 2*d1_len)/len
    rstLen = affinity.scale(lineString, xfact=scale, yfact=scale)
    left = rstLen.parallel_offset(d2_len/2, 'left')
    restrictionZone = left.buffer(-d2_len, single_sided=True)
    restrictionZone = restrictionZone.difference(exclusionZone)

    if side == 1:
        
        top = perpendicular(rstLen, 2*c_len, 'top')
        top = top.buffer(-((d1_len)+(b_len - c_len)), single_sided=True)
        
    elif side == 0:
        
        top = perpendicular(rstLen, 2*c_len, 'bottom')
        top = top.buffer(((d1_len)+(b_len - c_len)), single_sided=True)
        
    else:

        raise ValueError("Invalid side value")

    exclusionZone = exclusionZone.difference(top)
    name.append('Exclusion Zone')
    geometry.append(exclusionZone)

    restrictionZone = restrictionZone.difference(top)
    name.append('Restriction Zone')
    geometry.append(restrictionZone)

    df = {'Polygon Name' : name , 'geometry': geometry}
    gdf = gpd.GeoDataFrame(df, crs="EPSG:3857")
    
    return gdf