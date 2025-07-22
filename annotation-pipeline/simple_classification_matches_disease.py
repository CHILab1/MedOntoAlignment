from datasets import load_dataset
import pandas as pd
import os

def load_custom_dataset(split):
    path = 'MedPix/'
    if split == 'case-topic':
        file = 'case-topic.jsonl'
    elif split == 'descriptions':
        file = 'descriptions.jsonl'
    return load_dataset("json", data_files=path+file)

def create_dict(disease_df):
    syns = []
    syns_dict = {}

    for i in range(len(disease_df)):
        icd_dict = eval(disease_df.at[i, 'icd'])
        if 'inclusion' in icd_dict.keys():
            incs = [x['label']['@value'].lower() for x in icd_dict['inclusion']]
            for inc in incs:
                syns.append((inc, icd_dict['title']['@value'].lower(), icd_dict['code']))
                if inc not in syns_dict.keys():
                    syns_dict[inc] = [icd_dict['title']['@value'].lower()]
                elif icd_dict['title']['@value'].lower() not in syns_dict[inc]:
                    syns_dict[inc].append(icd_dict['title']['@value'].lower())
        if 'indexTerm' in icd_dict.keys():
            terms = [x['label']['@value'].lower() for x in icd_dict['indexTerm']]
            for term in terms:
                syns.append((term, icd_dict['title']['@value'].lower(), icd_dict['code']))
                if term not in syns_dict.keys():
                    syns_dict[term] = [icd_dict['title']['@value'].lower()]
                elif icd_dict['title']['@value'].lower() not in syns_dict[term]:
                    syns_dict[term].append(icd_dict['title']['@value'].lower())
    
    return syns, syns_dict

if __name__ == '__main__':

    data=load_custom_dataset('case-topic')
    path = 'MedOntoAlignment/'

    df = pd.read_csv(path+'icd11/icd11-mms-diseases.tsv', sep='\t')
    df = df[df['classKind']=='category']
    df = df.reset_index(drop=True)
    syns, diseases = create_dict(df)
    save_str = 'results_mms_diseases_synonyms'
    
    matches = 0
    predictions = []
    predictions_plain = []
    for sample in data['train']:
        uid = sample['U_id']
        case_t = sample['Case']['Title'].strip().replace('\n', ' ').replace('\r', '').lower()
        topic_t = sample['Topic']['Title'].strip().replace('\n', ' ').replace('\r', '').lower()
        category = sample['Topic']['Category'].strip().replace('\n', ' ').replace('\r', '').lower()
        if case_t in diseases:
            if len(diseases[case_t])>1:
                predictions.append((uid, case_t, diseases[case_t], case_t, topic_t, category))
                predictions_plain.append((uid, case_t, diseases[case_t], case_t, topic_t))
                matches += 1
            elif len(diseases[case_t])==1:
                predictions.append((uid, case_t, diseases[case_t][0], case_t, topic_t, category))
                predictions_plain.append((uid, case_t, diseases[case_t][0], case_t, topic_t))
                matches += 1
            else:
                print('err case_t')

        elif topic_t in diseases:
            if len(diseases[topic_t])>1:
                predictions.append((uid, topic_t, diseases[topic_t], case_t, topic_t, category))
                predictions_plain.append((uid, topic_t, diseases[topic_t], case_t, topic_t))
                matches += 1
            elif len(diseases[topic_t])==1:
                predictions.append((uid, topic_t, diseases[topic_t][0], case_t, topic_t, category))
                predictions_plain.append((uid, topic_t, diseases[topic_t][0], case_t, topic_t))
                matches += 1
            else:
                print('err topic_t')

        elif category in diseases:

            if len(diseases[category])>1:
                predictions.append((uid, category, diseases[category], case_t, topic_t, category))
                predictions_plain.append((uid, '', '', case_t, topic_t))
                matches += 1
            elif len(diseases[category])==1:
                predictions.append((uid, category, diseases[category][0], case_t, topic_t, category))
                predictions_plain.append((uid, '', '', case_t, topic_t))
                matches += 1
            else:
                print('err category')       
        else:
            predictions.append((uid, '', '', case_t, topic_t, category))
            predictions_plain.append((uid, '', '', case_t, topic_t))


    os.makedirs(f'{path}Results-diseases/', exist_ok=True)
    with open(f'{path}Results-diseases/{save_str}.tsv', 'w') as f:
        f.write('uid\tmatch\tsynonym\tcase_title\ttopic_title\n')
        for element in predictions_plain:
            f.write('\t'.join([str(e) for e in element])+'\n')
    
    with open(f'{path}Results-diseases/{save_str}_category.tsv', 'w') as f:
        f.write('uid\tmatch\tsynonym\tcase_title\ttopic_title\tcategory\n')
        for element in predictions:
            f.write('\t'.join([str(e) for e in element])+'\n')