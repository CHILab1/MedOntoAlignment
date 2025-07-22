# -*- coding: utf-8 -*-
#pip3 install owlready2
#pip3 install sparqlwrapper


"""#FILE CreateMedPix.OWL"""

from owlready2 import *
import csv
import json
import unicodedata
import re

file_pathCaseTopic = "MedPix/Case_topic.json"
file_pathDescriptions = "MedPix/Descriptions.json"
file_ontologiaMedPix = "MedPixSchema.owl"

def remove_no_UNICODE(s):
    if not isinstance(s, str):
        return s
    s_clean = re.sub(r'[^\x20-\x7E]', '', s)
    s_clean = re.sub(r'[<>#"\']', '', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()

    return s_clean



###################################### POPULATION OF MEDPIX WITH CASE, SCAN AND PATIENTS ###################################
ontoMedPix = get_ontology(file_ontologiaMedPix)
ontoMedPix.load()

classPatient = ontoMedPix.Patient
classCase = ontoMedPix.Case
classTAC = ontoMedPix.CT_Scan
classMRI = ontoMedPix.MRI_Scan

patient_counter = 1
dictPatientsClinicalCases = {}

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
    patientName = f"patient_{patient_counter:04d}" 
    patient_counter += 1
    nodePatient = classPatient(patientName)
    ontoMedPix[idCase].hasPatient.append(nodePatient) 
    ontoMedPix[patientName].isPatientOf.append(nodeIDCase) 
    dictPatientsClinicalCases[idCase] = patientName
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
  idRifCaso = "case_" + item["U_id"]
  url = "https://github.com/CHILab1/MedPix-2.0/blob/main/images/" + idScan + ".png"
  ontoMedPix[idScan].url = [url]
  patientName = dictPatientsClinicalCases[idRifCaso]
  jsonDescription = item["Description"]
  if "Age" in jsonDescription:
    age = jsonDescription["Age"]
    ontoMedPix[patientName].age = [age]
  if "Caption" in jsonDescription:
    caption = jsonDescription["Caption"]
    ontoMedPix[idScan].caption = [remove_no_UNICODE(caption)]

ontoMedPix.save(file = "MedPix.owl", format = "rdfxml")