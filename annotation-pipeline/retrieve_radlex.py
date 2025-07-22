from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from datasets import load_dataset
from tqdm import tqdm
import pandas as pd
import argparse
import pickle
import os

def load_custom_dataset(split):
    path = 'MedPix/'
    if split == 'case-topic':
        file = 'case-topic.jsonl'
    elif split == 'descriptions':
        file = 'descriptions.jsonl'
    return load_dataset("json", data_files=path+file)

def gen_test_str(sample, target_field):

    if sample['Description'][target_field] != None:
        target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '')
    else:
        target_value = None
    sample_test = "{target_value} is a typology of {target_field}.\n{case_test}"

    return sample_test.format(target_value=target_value, target_field=target_field, case_test='')


def disable_wanrs():
    import torchvision
    torchvision.disable_beta_transforms_warning()

def retrieve_threshold(vs, question, tot_snippets, threshold=0.80):
    raw_answer = vs.similarity_search_with_relevance_scores(question, k=tot_snippets)

    max_dist = raw_answer[0][1]
    if threshold != None:
        max_threshold = (max_dist + 1) * threshold
    else:
        max_threshold = raw_answer[-1][1]
    
    answers = []

    for ans in raw_answer:
        candidate_value = ans[1] + 1
        if candidate_value >= max_threshold:
            answers.append(ans)
        else:
            break
    
    return answers

def load_vstore(path, device, model_name):

    embeddings_model = HuggingFaceEmbeddings(
        model_name=model_name,
        #multi_process=True,
        model_kwargs={"device": device, "trust_remote_code": True, 'local_files_only': True},
        encode_kwargs={"normalize_embeddings": True}) # Set `True` for cosine similarity
        
    vectorstore = FAISS.load_local(path, embeddings_model, allow_dangerous_deserialization = True, distance_strategy = DistanceStrategy.COSINE)

    return vectorstore

if __name__ == '__main__':

    disable_wanrs()

    parser = argparse.ArgumentParser()
    parser.add_argument('--emb_model', type=str, default='nvemb')
    parser.add_argument('--device', type=str, default='cuda:1')
    parser.add_argument('--threshold', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)
    parser.add_argument('--target_field', type=str, default='Plane')

    args = parser.parse_args()
    emb_model = args.emb_model
    device = args.device
    threshold = args.threshold
    top_k = args.top_k
    target_field = args.target_field
        
    data=load_custom_dataset('descriptions')
    cases=load_custom_dataset('case-topic')
    
    print(len(data['train']))

    model_path = 'nvidia/NV-Embed-v2'
    emb_model = 'nvemb'

    path = 'MedOntoAlignment/'
    print('Loading retriever ...')

    search = 'cosine similarity'

    vectorstore = load_vstore(f"{path}VDB_radlex/{emb_model}", device, model_path)
    tot_snippets = len(vectorstore.index_to_docstore_id)

    radlex_df = pd.read_csv(path + f'RADLEX.csv')

    if top_k == -1:
        top_k = tot_snippets

    print('Loading inference model ...')
    
    path_res = f'{path}Results-{target_field}/'
    os.makedirs(path_res, exist_ok=True)
    file_res = f'retrieved_{target_field}_RADLEX.jsonl'
    path_file_res = path_res + file_res

    with open(path_file_res, 'w') as f:
        f.write('')

    QA = []
    counter = 0

    for sample in tqdm(data['train']):

        question = gen_test_str(sample, target_field)
        raw_retrieved_docs = retrieve_threshold(vectorstore, question, tot_snippets, threshold=threshold)
        retrieved_docs = [retrieved_doc[0] for retrieved_doc in raw_retrieved_docs]

        if top_k != tot_snippets:
            top_retrieved_docs = retrieved_docs[:top_k]
        else:
            top_retrieved_docs = retrieved_docs
            
        labels_id = [x.metadata['source_code'] for x in top_retrieved_docs]
        
        labels_dict = {}

        for label_id in labels_id:
            for i in range(len(radlex_df)):
                code = radlex_df.at[i, 'Class ID'].split('#')[-1]

                if not pd.isna(radlex_df.at[i, 'Synonyms']):
                    syns = radlex_df.at[i, 'Synonyms'].split('|')
                else:
                    syns = []

                if label_id == code:
                    labels_dict[code] = {'name' : radlex_df.at[i, 'Preferred Label'], 'synonym' : syns}
        
        print(f'questioning {counter} / {len(data["train"])} w/ {len(top_retrieved_docs)} docs\n')
        counter += 1

        uid = sample['U_id']
        uid_img = sample['image']
        
        if sample['Description'][target_field] != None:
            target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').replace('-', '').replace('  ', ' ').lower()
        else:
            target_value = None
        
        sample_ans = {'uid': uid, 'uid_img': uid_img, 'instruction_retrieve': question, 'ans': labels_dict, target_field: target_value, }
        QA.append(sample_ans)
        with open(path_file_res, 'a') as f:
            f.write(str(sample_ans))
            f.write('\n')

    pickle_path = path_file_res.replace('.jsonl', f'.pickle')
    with open(pickle_path, 'wb') as f:
        pickle.dump(QA, f)