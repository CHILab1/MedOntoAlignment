# Annotation pipeline

Code for the proposed annotation pipeline for the alignment of MedPix 2.0 and ICD-11 ontologies

File in this folder, listed according to their execution order:

- `simple_classification_matches_disease.py` classifies input from MedPix 2.0 to corresponding entries in ICD-11 with an exact match strategy for disease field
- `simple_classification_matches_location.py` classifies input from MedPix 2.0 to corresponding entries in ICD-11 with an exact match strategy for location field
- `parsing_results_disease.py` parses the results of exact matches, and retrieves information of the corresponding ICD-11 entities
- `parsing_results_location.py` parses the results of exact matches, and retrieves information of the corresponding ICD-11 entities
- `ingest_vdb.py` creates the Vector DataBase, adding synonyms information for disease and location fields, from ICD-11
- `retrieve_disease.py` retrieve most similars disease to corresponding MedPix 2.0 field from created vdb 
- `retrieve_location.py` retrieve most similars location to corresponding MedPix 2.0 field from created vdb 
- `merge_matches_disease.py` merge matches obtained after after parsing with the retrieved ones, which are selected accortind to the best bertscore f1
- `merge_matches_location.py` merge matches obtained after after parsing with the retrieved ones, which are selected accortind to the best bertscore f1