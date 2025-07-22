from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from tqdm import tqdm
import pandas as pd
import argparse
import os


def load_corpus_disease_only(path):

    df = pd.read_csv(path + f'RADLEX.csv')
    
    corpus = []

    for idx in range(len(df)):

        name = df.at[idx, 'Preferred Label']

        if not pd.isna(df.at[idx, 'Synonyms']) and df.at[idx, 'Synonyms'] != name:
            terms = df.at[idx, 'Synonyms'].split('|')
        else:
            terms = ''
            
        if terms == '':
            synonyms_str = ' '
        else:
            if len(terms) > 1:
                synonyms = ', '.join(terms[:-1]) + f' and {terms[-1]}'
            elif len(terms) == 1:
                synonyms = f'{terms[-1]}'
            synonyms_str = f'It is also known as {synonyms}.\n'

        if not pd.isna(df.at[idx, 'Definitions']):
            definition = df.at[idx, 'Definitions']
        else:
            definition = ''

        txt_doc = f'{name}\n{definition}\n{synonyms_str}'

        code = df.at[idx, 'Class ID'].split('#')[-1]
        
        metadata={'source_code':code, 'name':name}
        corpus.append(Document(page_content=txt_doc, metadata=metadata))
            
    
    return corpus

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--emb_model', type=str, default='nvemb')
    parser.add_argument('--device', type=str, default='cuda:0')
    args = parser.parse_args()
    emb_model = args.emb_model
    device = args.device

    if emb_model == 'nvemb':
        model_name = 'nvidia/NV-Embed-v2'
    else:
        emb_model == 'nvemb'
        model_name = 'nvidia/NV-Embed-v2'
    
    print("Loading data...")
    path = 'MedOntoAlignment/'

    # create documents

    print("Generating corpus ...")
    documents = load_corpus_disease_only(path)

    print("Loading embeddings ...")

    embeddings_model = HuggingFaceEmbeddings(
        model_name=model_name,
        #model=model,
        #multi_process=True,
        model_kwargs={
            "device": device, 
            "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True}) # Set `True` for cosine similarity

    print("Creating vector store ...")

    vectorstore = FAISS.from_documents(documents=[documents[0]], embedding=embeddings_model)
    for doc in tqdm(documents[1:]):
        vectorstore.add_documents(documents=[doc], embedding=embeddings_model)

    os.makedirs(f"{path}VDB_radlex/", exist_ok=True)
    vectorstore.save_local(f"{path}VDB_radlex/"+emb_model)
    

