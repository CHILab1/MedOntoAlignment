from datasets import load_dataset
import pandas as pd
import argparse
import os

def load_custom_dataset(split):
    path = 'MedPix/'
    if split == 'case-topic':
        file = 'case-topic.jsonl'
    elif split == 'descriptions':
        file = 'descriptions.jsonl'
    return load_dataset("json", data_files=path+file)

def create_dict(field_df):
    syns = []
    syns_dict = {}

    for i in range(len(field_df)):
        icd_dict = eval(field_df.at[i, 'icd'])
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

    data=load_custom_dataset('descriptions')
    path = 'MedOntoAlignment/'

    df = pd.read_csv(path+'icd11/icd11-mms-sex.tsv', sep='\t')
    df = df[df['classKind']=='category']
    df = df.reset_index(drop=True)
    _, fields = create_dict(df)
    target_field = 'Sex'
    save_str = f'{target_field}_results_mms'

    matches = 0
    predictions = []
    for sample in data['train']:
        uid = sample['U_id']
        uid_img = sample['image']
        if sample['Description'][target_field] != None:
            target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').replace('-', '').replace('  ', ' ').lower()
        else:
            target_value = None

        if target_value == None:
            predictions.append((uid, uid_img, 'biological sex not specified', '', ''))
        elif target_value in fields:
            if len(fields[target_value])>1:
                predictions.append((uid, uid_img, target_value, fields[target_value], target_value))
                matches += 1
            elif len(fields[target_value])==1:
                predictions.append((uid, uid_img, target_value, fields[target_value][0], target_value))
                matches += 1
            else:
                print('err')
        else:
            predictions.append((uid, uid_img, 'biological sex not specified', '', target_value))
    
    os.makedirs(f'{path}Results-{target_field}/', exist_ok=True)
    with open(f'{path}Results-{target_field}/{save_str}_category.tsv', 'w') as f:
        f.write(f'uid\tuid_img\tmatch\tsynonym\t{target_field}\n')
        for element in predictions:
            f.write('\t'.join([str(e) for e in element])+'\n')
    
    print(f'Found {matches} matches')