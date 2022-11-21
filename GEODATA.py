# --------------------------------------------------------------
# ----------------- GEODATA TOPO 250K Library ------------------
# --------------------------------------------------------------
# Australian Communications Media Authority
# Navnith Reddy, November 2022

# The GEODATA library provides helper functions which extract
# and format data from the Geoscience Australia Topographic
# database.

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

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
    runways = runways[['NAME' , 'geometry']]
    runways.reset_index(drop=True, inplace=True)
    runways.to_file('runways/runways.shp')
    runways.to_csv('runways.csv', index=False)

def readRunways():
    
    # Read built runway dataset
    return gpd.read_file("runways/runways.shp")
