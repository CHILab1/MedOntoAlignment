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

def gen_test_str(sample):

    case_t = sample['Case']['Title'].strip().replace('\n', ' ')
    topic_t = sample['Topic']['Title'].strip().replace('\n', ' ')
    category = sample['Topic']['Category'].strip().replace('\n', ' ')
    discussion = sample['Topic']['Disease Discussion'].strip().replace('\n', ' ')

    if case_t != topic_t:
        sample_test = "{case_title}, or {case_topic}.\nIt belongs to the category named {category}.\n{discussion}\n"
    else:
        sample_test = "{case_title}.\nIt belongs to the category named {category}.\n{discussion}\n"

    return sample_test.format(case_title=case_t, case_topic=topic_t, category=category, discussion=discussion)

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
    parser.add_argument('--device0', type=str, default='cuda:0')
    parser.add_argument('--threshold', type=float, default=0.8)
    parser.add_argument('--n_exp', type=int, default=1)
    parser.add_argument('--top_k', type=int, default=50)

    args = parser.parse_args()
    emb_model = args.emb_model
    device0 = args.device0
    threshold = args.threshold
    n_exp = args.n_exp
    top_k = args.top_k

    data=load_custom_dataset('case-topic')
    
    print(len(data['train']))
    
    model_path = 'nvidia/NV-Embed-v2'
    emb_model = 'nvemb'
        
    path = 'OntoMedPix/'
    print('Loading retriever ...')

    search = 'cosine similarity'

    vectorstore = load_vstore(f"{path}icd11/VDB_mms_diseases_syns/{emb_model}", device0, model_path)
    tot_snippets = len(vectorstore.index_to_docstore_id)

    df_icd11 = pd.read_csv(f'{path}icd11/icd11-mms-diseases.tsv', sep='\t')
    df_icd11 = df_icd11[df_icd11['classKind']=='category']
    df_icd11 = df_icd11.reset_index(drop=True)

    if top_k == -1:
        top_k = tot_snippets

    path_res = f'{path}icd11/Results-diseases/'
    os.makedirs(path_res, exist_ok=True)
    file_res = 'retrieved_diseases.jsonl'
    path_file_res = path_res + file_res

    with open(path_file_res, 'w') as f:
        f.write('')

    QA = []
    counter = 0

    for sample in tqdm(data['train']):

        question = gen_test_str(sample)
        raw_retrieved_docs = retrieve_threshold(vectorstore, question, tot_snippets, threshold=threshold)
        retrieved_docs = [retrieved_doc[0] for retrieved_doc in raw_retrieved_docs]
        if top_k != tot_snippets:
            top_retrieved_docs = retrieved_docs[:top_k]
        else:
            top_retrieved_docs = retrieved_docs
        
        labels_id = [x.metadata['source_code'] for x in top_retrieved_docs]

        labels_dict = {}

        for label_id in labels_id:
            for i in range(len(df_icd11)):
                if type(df_icd11.at[i, 'id'])==str and df_icd11.at[i, 'id'] == label_id:
                    icd_dict = eval(df_icd11.at[i, 'icd'])

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

                    if df_icd11.at[i, 'id'].split('/')[-1] == 'other' or df_icd11.at[i, 'id'].split('/')[-1] == 'unspecified':
                        labels_dict[("-".join(df_icd11.at[i, 'id'].split('/')[-2:]))] = {'name' : df_icd11.at[i, 'title'], 'synonym' : syns_list}
                    else:
                        labels_dict[(df_icd11.at[i, 'id'].split('/')[-1])] = {'name' : df_icd11.at[i, 'title'], 'synonym' : syns_list}

        print(f'questioning {counter} / {len(data["train"])}\n')
        counter += 1

        uid = sample['U_id']
        case_t = sample['Case']['Title'].strip().replace('\n', ' ')
        topic_t = sample['Topic']['Title'].strip().replace('\n', ' ')
        category = sample['Topic']['Category'].strip().replace('\n', ' ')

        sample_ans = {'uid': uid, 'instruction_retrieve': question, 'ans': labels_dict, 'case_t': case_t, 'topic_t': topic_t, 'category': category}
        QA.append(sample_ans)
        with open(path_file_res, 'a') as f:
            f.write(str(sample_ans))
            f.write('\n')

    pickle_path = path_file_res.replace('.jsonl', f'.pickle')
    with open(pickle_path, 'wb') as f:
        pickle.dump(QA, f)
