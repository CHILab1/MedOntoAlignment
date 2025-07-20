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

def gen_test_str(sample, desc, target_field, cases):

    if desc:
        if sample['Description'][target_field] != None:
            target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '')
        else:
            target_value = None
    else:
        target_value = sample[target_field].strip().replace('\n', ' ').replace('\r', '')

    sample_test = "{target_value} is a typology of {target_field}.{case_test}"

    for case in cases['train']:
        if case['U_id'] == sample['U_id']:
            case_t = case['Case']['Title'].strip().replace('\n', ' ')
            topic_t = case['Topic']['Title'].strip().replace('\n', ' ')
            category = case['Topic']['Category'].strip().replace('\n', ' ')
            discussion = case['Topic']['Disease Discussion'].strip().replace('\n', ' ')

            if case_t != topic_t:
                case_test = "{case_title}, or {case_topic} which belongs to the category named {category}, is a disease affecting {target_value}.\n{discussion}\n"
            else:
                case_test = "{case_title}, which belongs to the category named {category}, is a disease affecting {target_value}.\n{discussion}\n"

            return sample_test.format(target_value=target_value, target_field=target_field, case_test=case_test.format(case_title=case_t, case_topic=topic_t, category=category, discussion=discussion, target_value=target_value))

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
    parser.add_argument('--device0', type=str, default='cuda:1')
    parser.add_argument('--threshold', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=50)

    parser.add_argument('--target_field', type=str, default='Location')

    args = parser.parse_args()
    emb_model = args.emb_model
    device0 = args.device0
    threshold = args.threshold
    top_k = args.top_k
    target_field = 'Location'

    desc = False
        
    data=load_custom_dataset('descriptions')
    cases=load_custom_dataset('case-topic')
    
    print(len(data['train']))

    model_path = 'nvidia/NV-Embed-v2'
    emb_model = 'nvemb'

    path = 'OntoMedPix/'
    print('Loading retriever ...')

    search = 'cosine similarity'

    vectorstore = load_vstore(f"{path}icd11/VDB_mms_locations_syns/{emb_model}", device0, model_path)
    tot_snippets = len(vectorstore.index_to_docstore_id)

    df_icd11 = pd.read_csv(path+'icd11/icd11-mms-locations.tsv', sep='\t')
    df_icd11 = df_icd11[df_icd11['classKind']=='category']
    df_icd11 = df_icd11.reset_index(drop=True)

    if top_k == -1:
        top_k = tot_snippets

    print('Loading inference model ...')
    
    path_res = f'{path}icd11/Results-locations/'
    os.makedirs(path_res, exist_ok=True)
    file_res = f'retrieved_{target_field}.jsonl'
    path_file_res = path_res + file_res

    with open(path_file_res, 'w') as f:
        f.write('')

    QA = []
    counter = 0

    for sample in tqdm(data['train']):

        question = gen_test_str(sample, desc, target_field, cases)
        raw_retrieved_docs = retrieve_threshold(vectorstore, question, tot_snippets, threshold=threshold)
        retrieved_docs = [retrieved_doc[0] for retrieved_doc in raw_retrieved_docs]

        # for r in raw_retrieved_docs:
        #     print(r)

        if top_k != tot_snippets:
            top_retrieved_docs = retrieved_docs[:top_k]
        else:
            top_retrieved_docs = retrieved_docs
            
        #labels_list = [str(d.metadata['name']) for d in top_retrieved_docs]
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
                        labels_dict[("-".join(df_icd11.at[i, 'id'].split('/')[-2:]))] = {'name' : df_icd11.at[i, 'title'], 'synonym' : df_icd11.at[i, 'synonym']}
                    else:
                        labels_dict[(df_icd11.at[i, 'id'].split('/')[-1])] = {'name' : df_icd11.at[i, 'title'], 'synonym' : df_icd11.at[i, 'synonym']}
        
        print(f'questioning {counter} / {len(data["train"])} w/ {len(top_retrieved_docs)} docs\n')
        counter += 1

        uid = sample['U_id']
        uid_img = sample['image']
        
        if desc:
            if sample['Description'][target_field] != None:
                target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').replace('-', '').replace('  ', ' ').lower()
            else:
                target_value = None
        else:
            target_value = sample[target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').lower()

        sample_ans = {'uid': uid, 'uid_img': uid_img, 'instruction_retrieve': question, 'ans': labels_dict, target_field: target_value, }
        QA.append(sample_ans)
        with open(path_file_res, 'a') as f:
            f.write(str(sample_ans))
            f.write('\n')

    pickle_path = path_file_res.replace('.jsonl', f'.pickle')
    with open(pickle_path, 'wb') as f:
        pickle.dump(QA, f)


