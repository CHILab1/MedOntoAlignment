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

def create_dict(df):
    syns = []
    syns_dict = {}

    for idx in range(len(df)):

        name = df.at[idx, 'Preferred Label']
    
        if not pd.isna(df.at[idx, 'Synonyms']) and df.at[idx, 'Synonyms'] != name:
            terms = df.at[idx, 'Synonyms'].split('|')
        else:
            terms = []

        syns.append((name, name))
        if name not in syns_dict.keys():
            syns_dict[name] = [name]
        elif name not in syns_dict[name]:
            syns_dict[name].append(name)

        for term in terms:
            syns.append((term, name))
            if term not in syns_dict.keys():
                syns_dict[term] = [name]
            elif name not in syns_dict[term]:
                syns_dict[term].append(name)
    
    return syns, syns_dict

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--target_field', type=str, default='Plane')
    # parser.add_argument('--target_field', type=str, default='Modality')
    args = parser.parse_args()
    radlex = args.radlex
    target_field = args.target_field

    data = load_custom_dataset('descriptions')
    path = 'MedOntoAlignment/'

    df = pd.read_csv(path + f'RADLEX_{radlex}.csv')

    _, fields = create_dict(df, radlex)
    save_str = f'results_RADLEX_{radlex}_{target_field}'
    
    matches = 0
    predictions = []
    predictions_plain = []
    for sample in data['train']:
        uid = sample['U_id']
        uid_img = sample['image']
        
        if sample['Description'][target_field] == None:
            target_value = ''
        else:
            target_value = sample['Description'][target_field].strip().replace('\n', ' ').replace('\r', '').replace('_', '').lower()
        
        if target_value in fields:
            if len(fields[target_value])>1:
                predictions.append((uid, uid_img, target_value, fields[target_value], target_value))
                matches += 1
            elif len(fields[target_value])==1:
                predictions.append((uid, uid_img, target_value, fields[target_value][0], target_value))
                matches += 1
            else:
                print('err target_value')

        else:
            predictions.append((uid, uid_img, '', '', target_value))


    os.makedirs(f'{path}Results-{target_field}/', exist_ok=True)
    with open(f'{path}Results-{target_field}/{save_str}.tsv', 'w') as f:
        f.write(f'uid\tuid_img\tmatch\tsynonym\t{target_field}\n')
        for element in predictions:
            f.write('\t'.join([str(e) for e in element])+'\n')
    
    print(f'Found {matches} matches')
