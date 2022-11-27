# ----------------------------------------------------------------
# -------------- RUNWAY PROTECTION ZONE LIBRARY ------------------
# ----------------------------------------------------------------
# Australian Communications Media Authority
# Navnith Reddy, November 2022

# The Runway Protection Zone library provides helper functions 
# for the automation of protection zone creation. The library
# also contains functions which process GEODATA TOPO 250K
# Series 3 data.

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely import ops
from shapely import affinity

# Pre-emptive Deprecation Warning as Shapely moves to 2.0 
import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

# FUNCTION NAMING CONVENTION:
# -> 'get' functions download assets
# -> 'build' functions create assets based on downloaded assets
# -> 'read' functions are build functions that return variables

def buildRunways():
    
    """
    Builds runway dataframe using centrelines and airport shapefiles.
    Saves dataframe as csv and shapefile. Does not return output.
    """

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
    
    """
    Reads runway shapefile, must be run after buildRunways().
    
    Returns:
        DataFrame: Dataframe containing runway data
    """
    
    # Read built runway dataset
    return gpd.read_file("runways/runways.shp")


def perpendicular(lineString, len, side):
    
    """
    Creates perpendicular line at the end of input
    lineSting with length len. Different orientation 
    can be specificed.
    
    Parameters:
        LineString: linestring of two coordinate points
        len: integer, length of perpendicular line
        side: string, 'top' or 'bottom'

    Raises:
        ValueError: invalid side value

    Returns:
        _type_: _description_
    """
    
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
        
        raise ValueError("Invalid value for side, try 'top' or 'bottom")

def zoneConstructor (lineString):
    
    """
    Creates two-sided protection zones for runways.
    
    Parameters:
        lineString: Runway centreline LineString

    Returns:
        DataFrame: Dataframe containing protection zone polygons
    """
    
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
    
    """
    Creates one-sided protection zones for runways.
    
    Parameters:
        lineString: Runway centreline
        side: Integer, 1 or 0
    
    Raises:
        ValueError: Invalid 'side' value

    Returns:
        DataFrame: Protection zone polygons
    """
    
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

        raise ValueError("Invalid side value, try 1 or 0")

    exclusionZone = exclusionZone.difference(top)
    name.append('Exclusion Zone')
    geometry.append(exclusionZone)

    restrictionZone = restrictionZone.difference(top)
    name.append('Restriction Zone')
    geometry.append(restrictionZone)

    df = {'Polygon Name' : name , 'geometry': geometry}
    gdf = gpd.GeoDataFrame(df, crs="EPSG:3857")
    
    return gdf

def makeCentreline (lat1, lon1, lat2, lon2):
    
    """
    Creates centreline with given coordinates 
    which is compatible with other functions.

    Returns:
        centreline : LineString of runway centreline
    """
    
    centreline = LineString([lat1, lon1],[lat2, lon2])
    
    return centreline

def weldRunways (runway1, runway2):
    
    """
    Merges two runways, required for GEODATA
    TOPO 250k Series 3 dataset.

    Returns:
        welded : LineString of two two runways
    """
    
    welded = MultiLineString([runway1, runway2])
    welded = ops.linemerge(welded)
    
    return welded