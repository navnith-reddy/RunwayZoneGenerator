# Runway Protection Zone Generator

Regulating the impact of 5G base stations on Radio altimeters involves the drawing of exclusion and restriction zones around airport runways. The Runway Protection Zone Generator is investigation of the ease of automation of this process.

## Working with Topographic Data

Automation of the zone creation relies on accurate data from a reliable source. The Geoscience Australia GEODATA TOPO 250K Series 3 dataset was chosen as the source for this project. Whilst the dataset contains information on runway centrelines, it does not provide appropriate context. The GEODATA.py file contains functions which builds a composite dataset containing runway centrelines and airport name.

GEODATA TOPO 250K Shapefile:

<https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/64058>
