# -*- coding: utf-8 -*-
#pip3 install owlready2
#pip3 install sparqlwrapper

"""#File CreateOntoMedPix.*OWL*"""

###################################### POPULATION OF MEDPIX WITH CASE, SCAN AND PATIENTS ###################################
from owlready2 import *
import csv
import json
import unicodedata
import re

file_ontologyICD11 = "ICD-11.owl"
file_ontologyMedPix = "MedPix.owl"
file_ontologyRadLex = "radlex.owl"
file_pathCaseTopic = "Case_topic.json"
file_pathDescriptions = "Descriptions.json"
deseaseBodyPart_associationFile = "locationCategory_deseaseCategory_relationship.tsv"
scanDeseaseICD11_associationFile = "def_mpx_diseases_icd11.tsv"
scanLocationICD11_associationFile = "def_mpx_Location_icd11.tsv"
ontoICD = get_ontology(file_ontologyICD11).load()
ontoMedPix = get_ontology(file_ontologyMedPix).load()
ontoRadLex = get_ontology(file_ontologyRadLex).load()

classPatient = ontoMedPix.Patient
classCase = ontoMedPix.Case
classTAC = ontoMedPix.CT_Scan
classMRI = ontoMedPix.MRI_Scan

associations_dict = {} #dictionary with associations between location categories and desease categories


dictPlane = {"Axial": "RID10579",   #axial plane
            "Coronal": "RID10570", #coronal plane
            "Sagittal": "RID10574", #sagittal plane
            "Transverse": "RID10579", #axial plane - Transverse è un sinonimo di Axial
            "Frontal": "RID10570", #coronal plane. Frontal e Coronal sono sinonimi
            "AP": "RID10513", #AP axial projection
            "Lateral": "RID5821", #lateral
            "PA": "RID10530", #PA axial projection
            "3D Reconstruction": "RID10930", #volume imaging
            "Photograph": "RID12774", #surface rendering, elenco dei sinonimi: photo, clinical photo, external image, photographic image, clinical photograph, surface photo
            "Gross Pathology": "RID10579", #axial plane. Siccome appare solo nelle 4 scansioni indica che l’immagine è un collage o una serie con più viste in un’unica figura (tipico nei paper radiologici).
            }

dictModality = {"MR - T2 weighted": "RID10795",   #T2 weighted
               "MR T2* gradient,GRE,MPGR,SWAN,SWI": "RID10796",   #T2* weighted
               "MR - T1W - noncontrast": "RID10794",   #T1 weighted
               "MR - T1W w/Gadolinium": "RID10794",   #T1 weighted
               "MR - T1W w/Gd (fat suppressed)": "RID10794",   #T1 weighted
               "MRS - Spectroscopy": "RID10316",   #magnetic resonance spectroscopy
               "Virtual Colonoscopy": "RID11228",   #virtual endoscopy
               "MRA - MR Angiography/Venography": "RID10320",   #magnetic resonance angiography
               "CT - noncontrast": "RID10606",   #CT scan mode
               "CT - GI & IV Contrast": "RID10606",   #CT scan mode
               "CT w/contrast (IV)": "RID10606",   #CT scan mode
               "CT - GI Contrast": "RID10606",   #CT scan mode
               "CT": "RID10606",   #CT scan mode
               "CT - Montage": "RID10606",   #CT scan mode
               "CT - Montage of Images": "RID10606",   #CT scan mode
               "CTA - CT Angiography": "RID12305",   #CT revolutional angiography mode
               "MR - FLAIR": "RID10795",    #T2 weighted, FLAIR = T2-weighted con soppressione del liquido (CSF).
               "MR - STIR": "RID10794", #T1 weighted, STIR (Short TI Inversion Recovery) è tecnicamente una sequenza T1-weighted modificata.
               "MR - FIESTA": "RID10730", #balanced SSFP, FIESTA (SSFP): Una sequenza che utilizza un meccanismo di imaging diverso, progettato per visualizzare flussi rapidi e tessuti in movimento come il flusso sanguigno o i muscoli.
               "MR": "RID10313", #MRI
               "MRI": "RID10313", #MRI
               "MR - Montage": "RID10313", #MRI
               "MR - Montage of Images": "RID10313", #MRI
               " MR - Montage of Images": "RID10313", #MRI
               "MR - DWI Diffusion Weighted": "RID12697", #diffusion-weighted image reconstruction
               "MR - ADC Map (App Diff Coeff)": "RID12698", #apparent diffusion coefficient map
               "MR - PDW Proton Density": "RID10793", #proton density weighted
               "MR - Other Pulse Seq.": "RID10313", #MRI
               }


def remove_no_UNICODE(s):
    if not isinstance(s, str):
        return s
    s_clean = re.sub(r'[^\x20-\x7E]', '', s)
    s_clean = re.sub(r'[<>#"\']', '', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()

    return s_clean

patientCouunter = 1
associationsDict_patientsClinicalCases = {}

with open(file_pathCaseTopic, "r", encoding="utf-8") as file:
    data = json.load(file)
for item in data:
    idCase = "case_" + item["U_id"]
    nodeIDCase = classCase(idCase)
    listTac = item["TAC"]
    for tac in listTac:
      nodeTAC = classTAC(tac)
      ontoMedPix[idCase].hasScan.append(nodeTAC)
      ontoMedPix[tac].isScanOf.append(nodeIDCase)
    listMri = item["MRI"]
    for mri in listMri:
      nodeMRI = classMRI(mri)
      ontoMedPix[idCase].hasScan.append(nodeMRI)
      ontoMedPix[mri].isScanOf.append(nodeIDCase)
    namePatient = f"patient_{patientCouunter:04d}"
    patientCouunter += 1
    nodePatient = classPatient(namePatient)
    ontoMedPix[idCase].hasPatient.append(nodePatient)
    ontoMedPix[namePatient].isPatientOf.append(nodeIDCase)
    associationsDict_patientsClinicalCases[idCase] = namePatient
    JSONPropertiesCase = item["Case"]
    title = JSONPropertiesCase["Title"]
    ontoMedPix[idCase].title = [remove_no_UNICODE(title)]
    if "History" in JSONPropertiesCase:
        history = JSONPropertiesCase["History"]
        ontoMedPix[idCase].history = [remove_no_UNICODE(history)]
    if "Exam" in JSONPropertiesCase:
        exam = JSONPropertiesCase["Exam"]
        ontoMedPix[idCase].exam = [remove_no_UNICODE(exam)]
    if "Findings" in JSONPropertiesCase:
        Findings = JSONPropertiesCase["Findings"]
        ontoMedPix[idCase].finding = [remove_no_UNICODE(Findings)]
    if "Differential Diagnosis" in JSONPropertiesCase:
        DifferentialDiagnosis = JSONPropertiesCase["Differential Diagnosis"]
        ontoMedPix[idCase].differential_diagnosis = [remove_no_UNICODE(DifferentialDiagnosis)]
    if "Case Diagnosis" in JSONPropertiesCase:
        CaseDiagnosis = JSONPropertiesCase["Case Diagnosis"]
        ontoMedPix[idCase].case_diagnosis = [CaseDiagnosis]
    if "Diagnosis By" in JSONPropertiesCase:
        DiagnosisBy = JSONPropertiesCase["Diagnosis By"]
        ontoMedPix[idCase].diagnosis_by = [remove_no_UNICODE(DiagnosisBy)]
    if "Discussion" in JSONPropertiesCase:
        Discussion = JSONPropertiesCase["Discussion"]
        ontoMedPix[idCase].discussion = [remove_no_UNICODE(Discussion)]
    if "Treatment & Follow Up" in JSONPropertiesCase:
        TreatmentFollowUp = JSONPropertiesCase["Treatment & Follow Up"]
        ontoMedPix[idCase].treatment_follow_up = [remove_no_UNICODE(TreatmentFollowUp)]

with open(file_pathDescriptions, "r", encoding="utf-8") as file:
    data = json.load(file)
for item in data:
  idScan = item["image"]
  idRifCase = "case_" + item["U_id"]
  url = "https://github.com/CHILab1/MedPix-2.0/blob/main/images/" + idScan + ".png"
  ontoMedPix[idScan].url = [url]
  namePatient = associationsDict_patientsClinicalCases[idRifCase]
  jsonDescription = item["Description"]
  if "Age" in jsonDescription:
    age = jsonDescription["Age"]
    ontoMedPix[namePatient].age = [age]
  if "Caption" in jsonDescription:
    caption = jsonDescription["Caption"]
    ontoMedPix[idScan].caption = [remove_no_UNICODE(caption)]

ontoMedPix.save(file = "MedPix.owl", format = "rdfxml")



###################################### CREATION OF ONTOMEDPIX AND RELATIONSHIP WITH ICD-11 AND MEDPIX ###################################
##################################### haseSex, hasPlane and hasModality #################################################################

ontoMedPix = get_ontology("http://example.org/MedPix3.0.owl")

entityICDMale = ontoICD.search_one(iri="*1591498088")
entityICDFemale = ontoICD.search_one(iri="*990378205")
entityICDSessoNonSpecificato = ontoICD.search_one(iri="*16562053")

with ontoMedPix:
    ontoMedPix.imported_ontologies.append(ontoMedPix)
    ontoMedPix.imported_ontologies.append(ontoICD)
    ontoMedPix.imported_ontologies.append(ontoRadLex)

    with open(file_pathDescriptions, "r", encoding="utf-8") as file:
      data = json.load(file)
      for item in data:
        idRifCase = "case_" + item["U_id"]
        idScan = item["image"]
        entityScan = ontoMedPix[idScan]
        namePatient = associationsDict_patientsClinicalCases[idRifCase]
        jsonDescription = item["Description"]
        entityPatient = ontoMedPix[namePatient]
        hasSex = ontoMedPix.hasSex
        if "Sex" in jsonDescription:
          sex = jsonDescription["Sex"]
          if sex == "male":
            hasSex[entityPatient].append(entityICDMale)
          elif sex == "female":
            hasSex[entityPatient].append(entityICDFemale)
          else:
            hasSex[entityPatient].append(entityICDSessoNonSpecificato)
        else:
          print("NO SEX INFORMATION FOR THE GIVEN CLINICAL CASE")
        if "Plane" in jsonDescription:
          plane = jsonDescription["Plane"]
          if plane in dictPlane:
            entityPlane = ontoRadLex.search_one(iri="*" + dictPlane[plane])
            hasPlane = ontoMedPix.hasPlane
            hasPlane[entityScan].append(entityPlane)
        if "Modality" in jsonDescription:
          modality = jsonDescription["Modality"]
          if modality in dictModality:
            entityModality = ontoRadLex.search_one(iri="*" + dictModality[modality])
            hasModality = ontoMedPix.hasModality
            hasModality[entityScan].append(entityModality)


###################################### CREATION OF relationship between location categories and desease category in ontology ###################################
##################################### hasPossibleDesease #################################################################
with open(deseaseBodyPart_associationFile, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)  # salta l'header
    for row in reader:
      if row:
        locationCategory = row[0]
        deseaseCategory = row[2]

        if locationCategory not in associations_dict:
          associations_dict[locationCategory] = {deseaseCategory}
        else:
          associations_dict[locationCategory].add(deseaseCategory)


with ontoMedPix:
  property_name = "hasPossibleDesease"
  new_property = types.new_class(property_name, (ObjectProperty,))
  new_property.comment.append("Can be used at inference time")

counter = 1
with ontoMedPix:
  for association in associations_dict:
    locationCategory = association
    ListDeseaseCategories = associations_dict[association]
    class_dominio = ontoICD[locationCategory]
    class_range = [ontoICD[nome] for nome in ListDeseaseCategories]
    property_name = f"hasPossibleDesease{str(counter)}"
    counter = counter + 1
    new_property = types.new_class(property_name, (ObjectProperty,))
    new_property.domain = [class_dominio]
    new_property.range = class_range
    name_superproperty = "hasPossibleDesease"
    super_property = ontoMedPix[name_superproperty]
    new_property.is_a.append(super_property)


###################################### CREATION OF relationship between scan and location (body part) ###################################
##################################### hasBodyPart #################################################################
with ontoMedPix:
  with open(scanLocationICD11_associationFile, newline='', encoding='utf-8') as tsvfile:
      reader = csv.reader(tsvfile, delimiter='\t')
      next(reader)
      for row in reader:
        if row:
          scan = row[0]
          locationICD = row[2]
          if locationICD.endswith('.0'):
            locationICD = locationICD[:-2]
          if(scan and locationICD):
            entityScan = ontoMedPix[scan]
            entityLocation = ontoICD[locationICD]
            hasLocation = ontoMedPix.hasBodyPart
            hasLocation[entityScan].append(entityLocation)

###################################### CREATION OF relationship between case and desease ###################################
##################################### hasDesease #################################################################
with ontoMedPix:
  with open(scanDeseaseICD11_associationFile, newline='', encoding='utf-8') as tsvfile:
      reader = csv.reader(tsvfile, delimiter='\t')
      next(reader)
      for row in reader:
        if row:
          ClinicalCase = "case_" + row[0]
          deseaseICD = row[2]
          if(ClinicalCase and deseaseICD):
            entityClinicalCase = ontoMedPix[ClinicalCase]
            entityDesease = ontoICD[deseaseICD]
            hasTopic = ontoMedPix.hasDesease
            hasTopic[entityClinicalCase].append(entityDesease)

ontoMedPix.save(file="ontoMedPix.owl", format="rdfxml")

