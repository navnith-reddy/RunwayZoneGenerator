import GEODATA as gd
from shapely.geometry import LineString
from shapely import affinity
import geopandas as gpd

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

runways = gd.readRunways()