# -*- coding: utf-8 -*-
#pip3 install owlready2
#pip3 install sparqlwrapper


"""# File ExtractRelationshipLocationCategoriesDeseaseCategories.py"""

from owlready2 import *
import csv
import json
import unicodedata
import re

ontologyICD11 = "ICD-11.owl"
scanDeseaseICD11_associationFile = "def_mpx_diseases_icd11.tsv"
scanLocationICD11_associationFile = "def_mpx_Location_icd11.tsv"

DictMPXDesease = {} #contains the desease category for each case of medpix
DictMPXLocation = {} #contains the location category for each scan of medpix

def getDeseaseCategory(individuoDesease):
    ontoICD = get_ontology(ontologyICD11).load()
    refOntIndividuoDesease = ontoICD[individuoDesease]
    root_class = ontoICD["ICD-11_Popolata.mms"]
    direct_classes = [cls for cls in refOntIndividuoDesease.is_a if isinstance(cls, ThingClass)]
    if not direct_classes:
        return {
            "all_classes": set(),
            "last_class_before_root": None,
            "direct_class": None
        }
    current_class = direct_classes[0]
    hyperclass_chain = [current_class]
    while True:
        superclasses = [cls for cls in current_class.is_a if isinstance(cls, ThingClass)]
        if not superclasses:
            break
        next_class = superclasses[0]
        if next_class == root_class:
            break
        hyperclass_chain.append(next_class)
        current_class = next_class
    last_class_before_root = hyperclass_chain[-3] if len(hyperclass_chain) >= 3 else None
    return {
        "all_classes": set(hyperclass_chain),
        "last_class_before_root": direct_classes[0]
    }



def getLocationCategory(EntityLocation):
    ontoICD = get_ontology(ontologyICD11).load()
    refOntEntityLocation = ontoICD[EntityLocation]
    root_class = ontoICD["ICD-11_populated.mms"]
    direct_classes = [cls for cls in refOntEntityLocation.is_a if isinstance(cls, ThingClass)]
    if not direct_classes:
        return {
            "all_classes": set(),
            "last_class_before_root": None
        }
    current_class = direct_classes[0]
    hyperclass_chain = [current_class]
    while True:
        superclasses = [cls for cls in current_class.is_a if isinstance(cls, ThingClass)]
        if not superclasses:
            break
        next_class = superclasses[0]
        if next_class == root_class:
            break
        hyperclass_chain.append(next_class)
        current_class = next_class
    last_class_before_root = hyperclass_chain[-4] if hyperclass_chain else None
    if(last_class_before_root.name != "1154280071"): #anatomy and topography
      last_class_before_root = None
    else:
      if len(hyperclass_chain) >= 6: # I SET THIS CHECK BECAUSE SURFACE TOPOGRAPHY ONLY HAS INDIVIDUALS AND NOT CLASSES
        last_class_before_root = hyperclass_chain[-6]
      else:
        last_class_before_root = hyperclass_chain[-5]

    return {
        "all_classes": set(hyperclass_chain),
        "last_class_before_root": last_class_before_root
    }



with open(scanDeseaseICD11_associationFile, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    for row in reader:
      if row:
        scan = row[0]
        desease = row[2]
        if desease:
          deseaseCategory = getDeseaseCategory(desease)
          DictMPXDesease[scan] = deseaseCategory
        else:
          DictMPXDesease[scan] = None




with open(scanLocationICD11_associationFile, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    for row in reader:
      if row:
        scan = row[0]
        locationICD = row[2]
        if locationICD.endswith('.0'):
          locationICD = locationICD[:-2]
        LocationCategory = getLocationCategory(locationICD)
        if LocationCategory:
          DictMPXLocation[scan] = LocationCategory["last_class_before_root"]
        else:
          DictMPXLocation[scan] = None


#################### Extraction of relationship betweem body parts and desease #############
bodyPartsDeseases_associations = set()

for scan in DictMPXLocation:
  bodyPart = DictMPXLocation[scan]
  desease = None
  scanIDDeseasesDict = scan[0:7]
  if scanIDDeseasesDict in DictMPXDesease:
    if(DictMPXDesease[scanIDDeseasesDict]):
      desease = DictMPXDesease[scanIDDeseasesDict]["last_class_before_root"]
      listTutteClassiRif = DictMPXDesease[scanIDDeseasesDict]["all_classes"]
  if(bodyPart and desease):
    associazione = (bodyPart.name, bodyPart.label[0], desease.name, desease.label[0])
    bodyPartsDeseases_associations.add(associazione)

# SAVE IN A TSV FILE
with open("locationCategory_deseaseCategory_relationship.tsv", mode="w", encoding="utf-8", newline="") as file_tsv:
    writer = csv.writer(file_tsv, delimiter='\t')
    writer.writerow(["LocationCategoryCode", "LocationCategoryLabel", "DeseaseCategoryCode", "DeseaseCategoryLabel"])
    for bodyPartName, bodyPartNameLabel, deseaseName, deseaseLabel in bodyPartsDeseases_associations:
        writer.writerow([bodyPartName, bodyPartNameLabel, deseaseName, deseaseLabel])

print("TSV file successfully saved!")
