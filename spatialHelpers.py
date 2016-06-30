# Helper methods to do spatial and shapefile-related manipulations
# amg 23/06/2016
from osgeo import ogr
import string
import os
import numpy as np


def loadShapeFile(file):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    try:
        ds = driver.Open(file, 0)
    except Exception, e:
        print str(e)

    return ds

def to_shapefile(templateShapeFile, outputFileName, dataPoint, componentLabels, dataAreas, areaFieldName):
    # Take template shapefile (greaterQF must know which data belongs in which region)
    # Write new template shapefile with this greaterQF outputs
    # Inputs: TemplateShapeFile filename (no leading directory)
    #         dataPoint: One time step from GreaterQF outputs (array: Nareas * Ncomponents)
    #         outputFileName: name of shapefile to output (related files are also produced with the same name)
    #         componentLabels: Labels for each GreaterQF component
    #         dataAreas: Nareas labels so that shapefile can be matched to outputs
    #         areaFieldName: The field name in the shapefile that contains the area ID (should == dataAreas)

    # Read template shapefile
    ds = loadShapeFile(templateShapeFile)
    templateLayer = ds.GetLayer()

    # Create output file (delete if already exists)
    out_data = initializeShapefile(outputFileName)

    newLayerName = string.split(outputFileName, '.')[0]
    out_layer = out_data.CreateLayer(newLayerName,
                                     templateLayer.GetSpatialRef(),
                                     geom_type=templateLayer.GetGeomType(),
                                     )

    # Clone layer of shapefile to another file; add (blank) greaterQF fields
    templateLayerDef = templateLayer.GetLayerDefn()
    out_layer_def = out_layer.GetLayerDefn()

    # Identify which field is the primary key in the template layer
    primaryKeyIndex = findPrimaryKeyField(areaFieldName, templateLayerDef)

    # Copy each feature from the input file and add greaterQF output fields
    setUpFields(componentLabels, templateLayerDef, out_layer)

    # Copy data and model outputs to fields (
    QFpopulateFields(componentLabels,
                     dataAreas,
                     dataPoint,
                     out_layer,
                     out_layer_def,
                     primaryKeyIndex,
                     templateLayer,
                     templateLayerDef)

    out_data.Destroy()
    return True

def spatialAverageField(mappings, fieldNum, inLayer):
    # Take input features (each has a set of fields) and does a spatial average of the features within inLayer falling inside
    # each feature within outLayer. Results are weighted by the area intersected
    # fieldNum is the thing that is averaged
    # mappings: dictionary of dictionaries: {output feature index: {input feature index:area intersected}}
    #           Relates output areas to input areas (this takes a long time to do)
    # Returns dict {outFeatureIndex:value}
    featureVals = {}
    for m in mappings.keys():
        if len(mappings[m]) == 0: featureVals[m] = None
        m=int(m)
        weighting = np.divide(mappings[m].values(), sum(mappings[m].values()))
        invals = [inLayer.GetFeature(int(featNum)).GetFieldAsDouble(fieldNum) for featNum in mappings[m].keys()]
        result = np.sum(np.multiply(invals, weighting))
        featureVals[m] = result

    return featureVals

def QFpopulateFields(componentLabels, dataAreas, dataPoint, out_layer, out_layer_def, primaryKeyIndex, templateLayer,
                     templateLayerDef):
    # Populate the fields
    for i in range(0, templateLayer.GetFeatureCount()):
        orig_feature = templateLayer.GetFeature(i)
        out_feature = ogr.Feature(out_layer_def)

        # Set geometry
        out_feature.SetGeometry(orig_feature.GetGeometryRef())

        # Copy its attributes from original file
        for j in range(0, templateLayerDef.GetFieldCount()):
            # Set fields
            out_feature.SetField(out_layer_def.GetFieldDefn(j).GetNameRef(),
                                 orig_feature.GetField(j))

        # Add greaterQF outputs to the attributes
        # Just one time step for now
        if primaryKeyIndex is None:
            raise ValueError('Could not identify primary key in shapefile')
        # Find the correct element of the data matrix
        try:
            correctEntry = map(unicode, map(str, dataAreas)).index(unicode(str(orig_feature.GetField(primaryKeyIndex))))
        except Exception, e:
            print 'Warning: Cannot find GreaterQF output for output area ID ' + str(
                orig_feature.GetField(primaryKeyIndex)) + '. It will be null in the outputs'
            continue

        for j in range(templateLayerDef.GetFieldCount(), templateLayerDef.GetFieldCount() + len(componentLabels)):
            out_feature.SetField(out_layer_def.GetFieldDefn(j).GetNameRef(),
                                 dataPoint[correctEntry, j - templateLayerDef.GetFieldCount()])

        out_layer.CreateFeature(out_feature)


def setUpFields(componentLabels, templateLayerDef, out_layer):
    # Clone exising fields
    cloneFields(out_layer, templateLayerDef)
    addQFFields(componentLabels, out_layer)

def addQFFields(componentLabels, out_layer):
    # Add new fields (greaterQF components)
    for comp in componentLabels.values():
        out_layer.CreateField(ogr.FieldDefn(comp, ogr.OFTReal))

def cloneFields(out_layer, templateLayerDef):
    # Copy existing input fields to output layer
    for i in range(templateLayerDef.GetFieldCount()):
        fDef = templateLayerDef.GetFieldDefn(i)
        out_layer.CreateField(fDef)
    return i # Return number of fields cloned

def findPrimaryKeyField(primaryKeyName, layerDefinition):
    # Identify which numeric field in a LayerDefinition is the primary key
    # Inputs: primaryKeyName: name of the primary key; layerDefiniton: layer definition object containing fields

    primaryKeyIndex = None
    for i in range(layerDefinition.GetFieldCount()):
        fDef = layerDefinition.GetFieldDefn(i)
        if fDef.GetNameRef() == primaryKeyName:
            primaryKeyIndex = i

    return primaryKeyIndex

def initializeShapefile(outputFileName):
    # Create a new shapefile of name filename based on a template shapefile's layer
    # Inputs: output shapefile name
    # Returns: out_data (shapefile Object)
    #          out_layer (
    # TODO: Fix hard-coded path

    out_driver = ogr.GetDriverByName('ESRI Shapefile')
    out_file = 'c:/testOutput/' + outputFileName
    out_file_prefix = string.split(outputFileName, '.')[0]
    if os.path.exists(out_file):
        out_driver.DeleteDataSource(out_file)
    out_data = out_driver.CreateDataSource(out_file)
    # Duplicate the input layer for the output file

    return out_data


def geometryOverlap(newGeo, origGeos):
    # Takes a "big" geometry and returns the area of each "small" geometry with which it intersects
    # origGeos with no overlap are omitted to save memory
    # Inputs: newGeo = "big" geometry (singleton)
    #         origGe = "small" geometries (list)
    # Value: Dict of intersected geometries indexed by origGeo ogr objects

    result = {}
    for og in origGeos:
        inter = newGeo.Intersection(origGeos)
        if inter.Area() > 0:
            result[origGeos] = newGeo.Intersection(origGeos)

    return result

def mapGeometries(newGeos, origGeos):
    # Spatially joins origGeos to newGeos, showing the area of each origGeos corresponding to newGeos
    overlaps = {}
    for ng in newGeos:
        overlaps[ng] = geometryOverlap(ng, origGeos)

    # Get areas intersecting each newGeos
    areas = {}
    for ov in overlaps.keys():
        areas[ov] = []
        for int in ov: # For each intersection
            areas[ov].append(ov.Area())

    return areas