# Ontologies
OWL Ontologies and Files Used to Create OntoMedPix

- `ICD-11Schema.owl` schema defining the classes, object properties and data properties used to create ICD-11.owl
- `MedPixSchema.owl` schema defining the classes, object properties and data properties used to create MedPix.owl

- `CreateICD-11.py` Python file to create the ICD-11.owl. It requires as input the files ‘icd11-mms-complete.tsv’, ‘icd11-synonyms.tsv’ and ‘ICD-11Schema.owl’.
- `CreateMedPixOWL.py` Python file to create the MedPix.owl. It requires as input the files ‘Case_topic.json’, ‘Descriptions.json’ and ‘MedPixSchema.owl’.
- `Extract_Relationship_LocationCategories_DeseaseCategories.py` Python code to search for all relationships between desease categories and location categories. It requires as input the files ‘def_mpx_diseases_icd11.tsv’, ‘def_mpx_Location_icd11.tsv’ and ‘ICD-11.owl’.
- `CreateOntoMedPix.py` Python code to create OntoMedPix. This is the final ontology that imports the ‘ICD-11.owl’, ‘MedPix.owl’ and ‘radlex.owl’ ontologies. It requires as input also the files ‘Case_topic.json’, ‘Descriptions.json’, ‘locationCategory_deseaseCategory_relationship.tsv’, ‘def_mpx_diseases_icd11.tsv’ and ‘def_mpx_Location_icd11.tsv’.

- `ICD-11.owl` Semantic representation in OWL of ICD-11. This ontology is imported from OntoMedPix
- `MedPix.owl` Semantic representation in OWL of MedPix. This ontology is imported from OntoMedPix
- `locationCategory_deseaseCategory_relationship.tsv` output of the SWRL rule to infer relationships between Location Categories and Desease Categories
- `OntoMedPix.owl` final ontology that imports ‘ICD-11.owl’, ‘MedPix.owl’ and ‘radlex.owl’ and acts as a bridge to link MedPix clinical cases with diseases and body parts defined in ICD-11 and with clinical concepts (Plane and Modality of Scan) defined in RadLex.
- `SPARQLQueries.txt` SPARQL queries that can be executed on the final ontology.

_Following files are required and can be downloaded from their corresponding repository_

- `MedPix/Case_topic.json` json file containing the description of all clinical cases defined in Medpix 2.0 https://github.com/CHILab1/MedPix-2.0 
- `MedPix/Descriptions.json` json file containing the description of all scan defined in Medpix 2.0 https://github.com/CHILab1/MedPix-2.0 
- `radlex.owl` Radiology Lexicon containing definitions of radiological terms. https://bioportal.bioontology.org/ontologies/RADLEX  