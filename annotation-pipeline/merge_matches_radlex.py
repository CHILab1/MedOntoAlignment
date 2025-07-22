import os
from tqdm import tqdm
import pandas as pd
import evaluate
import argparse
import pickle

def calculate_metric(metric, preds, refs, device, bertscore=False):
    if bertscore:
        return metric.compute(predictions=preds, references=refs, lang="en", model_type='dmis-lab/biosyn-biobert-ncbi-disease', device=device, num_layers=12)
    else:
        return metric.compute(predictions=preds, references=refs)

def calculate_scores(retrieved_idx, target_mpx, device):
    bert_scores = []

    for k,v in retrieved_idx['ans'].items():
        code_radlex = k
        disease_icd = v['name']
        synonym = v['synonym']
        if synonym != [] :
            for syn in synonym:
                bert_scores.append((code_radlex, disease_icd.lower(), syn.lower(), calculate_metric(bertscore, [syn.lower()], [target_mpx], device, bertscore=True)["f1"][0]))
        
        bert_scores.append((code_radlex, disease_icd.lower(), disease_icd.lower(), calculate_metric(bertscore, [disease_icd.lower()], [target_mpx], device, bertscore=True)["f1"][0]))
    
    return bert_scores

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_field', type=str, default='Modality')
    parser.add_argument('--device', type=str, default='cuda:1')
    args = parser.parse_args()
    target_field = args.target_field
    device = args.device

    path = 'MedOntoAlignment/'

    exact_matches = pd.read_csv(f'{path}Results-{target_field}/{target_field}_RADLEX_matches.tsv', sep='\t')
    with open(f'{path}Results-{target_field}/retrieved_{target_field}_RADLEX.pickle', 'rb') as f:
        retrieved = pickle.load(f)

    bertscore = evaluate.load("bertscore")

    target_values = {}
    target_values_list = []
    target_values_list_w_borderlines = []
    borderline_results = []
    borderline_cases = []

    for idx in tqdm(range(len(exact_matches))):
        if type(exact_matches.at[idx, 'title-syns']) == str:
            
            target_values[exact_matches.at[idx, 'uid']] = {
                f'{target_field}_icd' : exact_matches.at[idx, 'title-syns'],
                'code_radlex' : exact_matches.at[idx, 'id_code'],
                f'mpx_{target_field}' : exact_matches.at[idx, 'match'],
                                                            }
            target_values_list.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))
            target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))

        elif type(retrieved[idx][target_field])==str:
            target_value = retrieved[idx][target_field].lower()
                
            bert_scores = calculate_scores(retrieved[idx], target_value, device)

            bert_scores_ordered = sorted(bert_scores, key=lambda x: x[3], reverse=True)
            if bert_scores_ordered[0][3] >= 0.85:
                target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : bert_scores_ordered[0][1],
                    'code_radlex' : bert_scores_ordered[0][0],
                    f'mpx_{target_field}' : target_value,
                                                                }
                target_values_list.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
                target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
            
            else:
                target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : '',
                    'code_radlex' : '',
                    f'mpx_{target_field}' : target_value,
                                                                }
                target_values_list.append((exact_matches.at[idx, 'uid'], '', '', target_value))
                target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
                borderline_cases.append(exact_matches.at[idx, "uid"])
                borderline_results.append((exact_matches.at[idx, 'uid'], target_value, bert_scores_ordered))
        else:
            target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : '',
                    'code_radlex' : '',
                    f'mpx_{target_field}' : '',
                                                                }
            target_values_list.append((exact_matches.at[idx, 'uid'], '', '', target_value))
            target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], '' , '', target_value))
            borderline_cases.append(exact_matches.at[idx, "uid"])
            borderline_results.append((exact_matches.at[idx, 'uid'], target_value, '' ))
    
    os.makedirs(f'{path}Results-{target_field}', exist_ok=True)
    
    target_values_df = pd.DataFrame(target_values_list, columns=['uid', f'{target_field}_icd', 'code_radlex', f'mpx_{target_field}'])
    target_values_df.to_csv(f'{path}Results-{target_field}/def_mpx_{target_field}_RADLEX_no_borderline.tsv', sep='\t', index=False)
    
    target_values_df_borderlines = pd.DataFrame(target_values_list_w_borderlines, columns=['uid', f'{target_field}_icd', 'code_radlex', f'mpx_{target_field}'])
    target_values_df_borderlines.to_csv(f'{path}Results-{target_field}/def_mpx_{target_field}_RADLEX.tsv', sep='\t', index=False)
    
    with open(f'{path}Results-{target_field}/def_mpx_{target_field}_RADLEX.pickle', 'wb') as f:
        pickle.dump(target_values, f)
    
    with open(f'{path}Results-{target_field}/borderline_mpx_{target_field}_RADLEX.pickle', 'wb') as f:
        pickle.dump(borderline_results, f)

    print(f'Bordeline cases #{len(borderline_cases)}\n{borderline_cases}')
