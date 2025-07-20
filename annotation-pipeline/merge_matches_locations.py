from tqdm import tqdm
import pandas as pd
import evaluate
import pickle
import os

def calculate_metric(metric, preds, refs, bertscore=False):
    if bertscore:
        return metric.compute(predictions=preds, references=refs, lang="en", model_type='dmis-lab/biosyn-biobert-ncbi-disease', device='cuda:0', num_layers=12)
    else:
        return metric.compute(predictions=preds, references=refs)

def calculate_scores(retrieved_idx, target_mpx):
    bert_scores = []

    for k,v in retrieved_idx['ans'].items():
        code_icd = k
        disease_icd = v['name']
        synonym = v['synonym']
        if synonym != [] :
            for syn in synonym:
                bert_scores.append((code_icd, disease_icd.lower(), syn.lower(), calculate_metric(bertscore, [syn.lower()], [target_mpx], bertscore=True)["f1"][0]))
        
        bert_scores.append((code_icd, disease_icd.lower(), disease_icd.lower(), calculate_metric(bertscore, [disease_icd.lower()], [target_mpx], bertscore=True)["f1"][0]))
    
    return bert_scores

if __name__ == '__main__':
    
    target_field = 'Location'
    path = 'OntoMedPix/'

    exact_matches = pd.read_csv(f'{path}Results-locations/{target_field}_mpx_matches.tsv', sep='\t')
    with open(f'{path}Results-locations/retrieved_{target_field}.pickle', 'rb') as f:
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
                'code_icd' : exact_matches.at[idx, 'id_code'],
                f'mpx_{target_field}' : exact_matches.at[idx, 'match'],
                                                            }
            target_values_list.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))
            target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))

        elif type(retrieved[idx][target_field])==str:
            target_value = retrieved[idx][target_field].lower()
                
            bert_scores = calculate_scores(retrieved[idx], target_value)

            bert_scores_ordered = sorted(bert_scores, key=lambda x: x[3], reverse=True)
            if bert_scores_ordered[0][3] >= 0.85:
                target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : bert_scores_ordered[0][1],
                    'code_icd' : bert_scores_ordered[0][0],
                    f'mpx_{target_field}' : target_value,
                                                                }
                target_values_list.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
                target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
            
            else:
                target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : '',
                    'code_icd' : '',
                    f'mpx_{target_field}' : target_value,
                                                                }
                target_values_list.append((exact_matches.at[idx, 'uid'], '', '', target_value))
                target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], target_value))
                borderline_cases.append(exact_matches.at[idx, "uid"])
                borderline_results.append((exact_matches.at[idx, 'uid'], target_value, bert_scores_ordered))
        else:
            target_values[exact_matches.at[idx, 'uid']] = {

                    f'{target_field}_icd' : '',
                    'code_icd' : '',
                    f'mpx_{target_field}' : '',
                                                                }
            target_values_list.append((exact_matches.at[idx, 'uid'], '', '', target_value))
            target_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], '' , '', target_value))
            borderline_cases.append(exact_matches.at[idx, "uid"])
            borderline_results.append((exact_matches.at[idx, 'uid'], target_value, '' ))
    
    os.makedirs(f'{path}Final_annotation/', exist_ok=True)
    target_values_df = pd.DataFrame(target_values_list, columns=['uid', f'{target_field}_icd', 'code_icd', f'mpx_{target_field}'])
    target_values_df.to_csv(f'{path}Final_annotation/mpx_{target_field}_icd11.tsv', sep='\t', index=False)
    target_values_df_borderlines = pd.DataFrame(target_values_list_w_borderlines, columns=['uid', f'{target_field}_icd', 'code_icd', f'mpx_{target_field}'])
    target_values_df_borderlines.to_csv(f'{path}Final_annotation/mpx_{target_field}_icd11_borderlines.tsv', sep='\t', index=False)
    with open(f'{path}Final_annotation/mpx_{target_field}_icd11.pickle', 'wb') as f:
        pickle.dump(target_values, f)
    with open(f'{path}Final_annotation/refined_borderline_mpx_{target_field}_icd11.pickle', 'wb') as f:
        pickle.dump(borderline_results, f)

    print(f'Bordeline cases #{len(borderline_cases)}\n{borderline_cases}')