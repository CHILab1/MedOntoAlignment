# -*- coding: utf-8 -*-
#pip3 install owlready2
#pip3 install sparqlwrapper

"""#File CreateICD-11.py"""

import csv
from owlready2 import *
import types
import json
import ast


def remove_no_UNICODE(s):
    if not isinstance(s, str):
        return s
    s_clean = re.sub(r'[^\x20-\x7E]', '', s)
    s_clean = re.sub(r'[<>#"\']', '', s_clean)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()

    return s_clean

def get_category_code(category_name):
    return categories_icd.get(category_name, "Category not found")

def search_parent_class(entity):
    for cls in entity.is_a:
        if isinstance(cls, ThingClass):
            return cls
    for rel in entity.is_a:
        if isinstance(rel, Individual):
            return search_parent_class(rel)
    return None


file_pathICD11 = 'icd11/icd11-mms-complete.tsv'
file_ontologyICD11 = "ICD-11Schema.owl"
file_synonyms = "icd11/icd11-synonyms.tsv"

onto = get_ontology(file_ontologyICD11)
onto.load()

categories_icd = {
    "Certain infectious or parasitic diseases": "01",
    "Neoplasms": "02",
    "Diseases of the blood or blood-forming organs": "03",
    "Diseases of the immune system": "04",
    "Endocrine, nutritional or metabolic diseases": "05",
    "Mental, behavioural or neurodevelopmental disorders": "06",
    "Sleep-wake disorders": "07",
    "Diseases of the nervous system": "08",
    "Diseases of the visual system": "09",
    "Diseases of the ear or mastoid process": "10",
    "Diseases of the circulatory system": "11",
    "Diseases of the respiratory system": "12",
    "Diseases of the digestive system": "13",
    "Diseases of the skin": "14",
    "Diseases of the musculoskeletal system or connective tissue": "15",
    "Diseases of the genitourinary system": "16",
    "Conditions related to sexual health": "17",
    "Pregnancy, childbirth or the puerperium": "18",
    "Certain conditions originating in the perinatal period": "19",
    "Developmental anomalies": "20",
    "Symptoms, signs or clinical findings, not elsewhere classified": "21",
    "Injury, poisoning or certain other consequences of external causes": "22",
    "External causes of morbidity or mortality": "23",
    "Factors influencing health status or contact with health services": "24",
    "Codes for special purposes": "25",
    "Supplementary Chapter Traditional Medicine Conditions": "26",
    "Supplementary section for functioning assessment": "27",
    "Extension Codes": "28"
}


#----------------POPULATE ICD-11.OWL WITH CLASSES---------------
with open(file_pathICD11, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    with onto:
        for row in reader:
            if row:
                idCode = row[0]
                title = row[1]
                parent_code = row[2]
                parent = row[3]
                depth = row[4]
                synonym = row[5]
                definition = row[6]
                classKind = row[11]
                if idCode == "mms":
                    NewClass = types.new_class(idCode, (Thing,))
                    NewClass.label = [title]
                if classKind == "chapter":
                    parent_entity = onto[parent_code]
                    NewClass = types.new_class(idCode, (parent_entity,))
                    numeroCapitolo = get_category_code(title)
                    NewClass.label = [str(numeroCapitolo) + " " + title]
                    NewClass.comment = [definition]
                if (classKind == "block"):
                  parent_entity = onto[parent_code]
                  if parent_entity is not None:
                    NewClass = types.new_class(idCode, (parent_entity,))
                    NewClass.label = [title]
                    NewClass.comment = [definition]
                  else:
                    print(f"[MISSING PARENT] Block '{idCode}' not created, parent '{parent_code}' not found in the ontology.")


#----------------POPULATE ICD-11.OWL WITH INDIVIDUAL---------------
with open(file_pathICD11, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    with onto:
        for row in reader:
            if row:
                idCode = row[0]
                title = row[1]
                parent_code = row[2]
                parent = row[3]
                depth = row[4]
                synonym = row[5]
                definition = row[6]
                idUri = row[7]
                classKind = row[11]
                code = row[9]

                if (classKind == "category"):
                  parent_entity = onto[parent_code]
                  if parent_entity is not None:
                    if isinstance(parent_entity, ThingClass):
                      if(idCode == "other" or idCode == "unspecified"):
                        idCode = parent_code + "-" + idCode
                      NewEntity = parent_entity(idCode)
                      NewEntity.label = [title]
                      onto[idCode].hasDefinition = [remove_no_UNICODE(definition)]
                      onto[idCode].hasCode = [code]
                    else:
                        print(f"{parent_entity} is a entity.")
                        if(idCode == "other" or idCode == "unspecified"):
                          idCode = parent_code + "-" + idCode
                        classe_parent_entity = search_parent_class(parent_entity)
                        print(classe_parent_entity)
                        NewEntity = classe_parent_entity(idCode)
                        NewEntity.label = [title]
                        onto[idCode].hasDefinition = [remove_no_UNICODE(definition)]
                        onto[idCode].hasCode = [code]
                        onto[parent_entity.name].hasVariant.append(NewEntity)
                        onto[NewEntity.name].isVariantOf.append(parent_entity)
                  else:
                    print("parent does not exist")


#-----------POPULATE ICD-11.OWL WITH OBJECT PROPERTIES HASEXCLUSION ---------------
with open(file_pathICD11, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    with onto:
        for row in reader:
            if row:
                idCode = row[0]
                title = row[1]
                parent_code = row[2]
                parent = row[3]
                depth = row[4]
                synonym = row[5]
                definition = row[6]
                idUri = row[7]
                classKind = row[11]
                code = row[9]
                jsonEsclusioni = row[12]

                if (classKind == "category"):
                  genitore = onto[parent_code]
                  if genitore is not None:
                    if(len(jsonEsclusioni) > 0):
                      datajsonEsclusioni = ast.literal_eval(jsonEsclusioni)
                      for item in datajsonEsclusioni:
                        if isinstance(item, dict) and 'foundationReference' in item:
                          idEsclusion = item['foundationReference'].rsplit('/', 1)[-1]
                          nodeIdEsclusion = onto[idEsclusion]
                          value = ""
                          if('label' in item):
                            value = item['label'].get('@value')
                          if nodeIdEsclusion is not None:
                            onto[idCode].hasExclusion.append(nodeIdEsclusion)
                          else:
                            print(f"[MISSING EXCLUDED ITEM] Exclusion '{idEsclusion}' - '{value}' of element '{idCode}' does not exist in the ontology.")


#-----------------POPULATE ICD-11.OWL WITH SYNONYMS------------------------
with open(file_synonyms, newline='', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)
    with onto:
        for row in reader:
            if row:
                idCode = row[1]
                inclusion = row[2]
                indexTerm = row[3]
                refElement = onto[idCode]
                if refElement is not None:
                  list_inclusion = ast.literal_eval(inclusion)
                  list_indexTerm = ast.literal_eval(indexTerm)
                  listSinonimi = list(set(list_inclusion + list_indexTerm))
                  for el in listSinonimi:
                    onto[idCode].hasSynonym = [remove_no_UNICODE(el)]
                else:
                  print(f"[MISSING ELEMENT] '{idCode}' does not exist in the ontology.")


# SAVE FINAL ONTOLOGY
onto.save(file="ICD-11.owl", format="rdfxml")

