from langchain.text_splitter import TokenTextSplitter, TextSplitter, Tokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from transformers import AutoTokenizer
from tqdm import tqdm
import pandas as pd
import argparse
import pickle
import json
import os

def load_corpus_disease_only(path):

    df = pd.read_csv(path, sep='\t')
    disease = df[df['classKind']=='category']
    disease = disease.reset_index(drop=True)
    corpus = []

    for idx in range(len(disease)):
    
        icd_dict = eval(disease.at[idx, 'icd'])
        if 'inclusion' in icd_dict.keys():
            incs = [x['label']['@value'] for x in icd_dict['inclusion']]
        else:
            incs = []
        if 'indexTerm' in icd_dict.keys():
            terms = [x['label']['@value'] for x in icd_dict['indexTerm']]
        else:
            terms = []
            
        syns_list = incs + terms
        syns_list = list(set(syns_list))

        if syns_list == []:
            synonyms_str = ' '
        else:
            if len(syns_list) > 1:
                synonyms = ', '.join(syns_list[:-1]) + f' and {syns_list[-1]}'
            elif len(syns_list) == 1:
                synonyms = f'{syns_list[-1]}'
            synonyms_str = f'It is also known as {synonyms}.\n'

        if type(disease.at[idx, 'definition']) == str:
            txt_doc = f'{disease.at[idx, "title"]}\n{disease.at[idx, "definition"]}\n{synonyms_str}'
        else:
            txt_doc = f'{disease.at[idx, "title"]}\n{synonyms_str}'
        
        metadata={'source_code':disease.at[idx, 'id'], 'name':disease.at[idx, "title"], 'code_mms':disease.at[idx, 'code_mms'], 'exclusion':disease.at[idx, 'exclusion']}
        corpus.append(Document(page_content=txt_doc, metadata=metadata))
            
    
    return corpus

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--emb_model', type=str, default='nvemb')
    parser.add_argument('--diseases', action='store_true')
    parser.add_argument('--no-diseases', dest='diseases', action='store_false')
    parser.add_argument('--locations', action='store_true')
    parser.add_argument('--no-locations', dest='locations', action='store_false')
    parser.add_argument('--device', type=str, default='cuda:0')
    parser.set_defaults(diseases=False, locations=True, mms=True)
    args = parser.parse_args()
    emb_model = args.emb_model
    mms = args.mms
    diseases = args.diseases
    locations = args.locations
    device = args.device

    if emb_model == 'nvemb':
        model_name = 'nvidia/NV-Embed-v2'
    else:
        emb_model == 'nvemb'
        model_name = 'nvidia/NV-Embed-v2'
    
    print("Loading data...")
    path = 'OntoMedPix/'

    # create documents

    print("Generating corpus ...")
    if locations:
        documents = load_corpus_disease_only(path+'icd11/icd11-mms-locations.tsv')
    elif diseases:
        documents = load_corpus_disease_only(path+'icd11/icd11-mms-diseases.tsv')

    print("Loading embeddings ...")

    embeddings_model = HuggingFaceEmbeddings(
        model_name=model_name,
        #model=model,
        #multi_process=True,
        model_kwargs={
            #"device_map": "auto",
            "device": device, 
            "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True}) # Set `True` for cosine similarity

    print("Creating vector store ...")

    vectorstore = FAISS.from_documents(documents=[documents[0]], embedding=embeddings_model)
    for doc in tqdm(documents[1:]):
        vectorstore.add_documents(documents=[doc], embedding=embeddings_model)

    if locations:
        os.makedirs(f"{path}icd11/VDB_mms_locations_syns/", exist_ok=True)
        vectorstore.save_local(f"{path}icd11/VDB_mms_locations_syns/"+emb_model)
    elif diseases:
        os.makedirs(f"{path}icd11/VDB_mms_diseases_syns/", exist_ok=True)
        vectorstore.save_local(f"{path}icd11/VDB_mms_diseases_syns/"+emb_model)