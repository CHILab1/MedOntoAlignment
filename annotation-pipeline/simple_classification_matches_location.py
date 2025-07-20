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

    data=load_custom_dataset('descriptions')
    path = 'OntoMedPix/'

    df = pd.read_csv(path+'icd11/icd11-mms-locations.tsv', sep='\t')
    df = df[df['classKind']=='category']
    df = df.reset_index(drop=True)
    syns, locations = create_dict(df)
    target_field = 'Location'
    save_str = 'results_mms_locations_synonyms'

    matches = 0
    predictions = []
    for sample in data['train']:
        uid = sample['U_id']
        uid_img = sample['image']
        target_value = sample[target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').lower()
        if target_value in locations:
            if len(locations[target_value])>1:
                predictions.append((uid, uid_img, target_value, locations[target_value], target_value))
                matches += 1
            elif len(locations[target_value])==1:
                predictions.append((uid, uid_img, target_value, locations[target_value][0], target_value))
                matches += 1
            else:
                print('err target_value')

        else:
            predictions.append((uid, uid_img, '', '', target_value))

    os.makedirs(f'{path}Results-locations/', exist_ok=True)
    with open(f'{path}Results-locations/{save_str}.tsv', 'w') as f:
        f.write('uid\tuid_img\tmatch\tsynonym\tLocation\n')
        for element in predictions:
            f.write('\t'.join([str(e) for e in element])+'\n')

            