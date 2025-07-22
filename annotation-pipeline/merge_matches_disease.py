from tqdm import tqdm
import pandas as pd
import evaluate
import pickle
import os

def calculate_metric(metric, preds, refs, bertscore=False):
    if bertscore:
        return metric.compute(predictions=preds, references=refs, lang="en", model_type='dmis-lab/biosyn-biobert-ncbi-disease', device='cuda:1', num_layers=12)
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
    
    path = 'MedOntoAlignment/'
    exact_matches = pd.read_csv(f'{path}/Results-diseases/mpx_matches.tsv', sep='\t')
    with open(f'{path}/Results-diseases/retrieved_diseases.pickle', 'rb') as f:
        retrieved = pickle.load(f)

    bertscore = evaluate.load("bertscore")

    diseases_values = {}
    diseases_values_list = []
    diseases_values_list_w_borderlines = []
    borderline_results = []
    borderline_cases = []

    for idx in tqdm(range(len(exact_matches))):
        if type(exact_matches.at[idx, 'title-syns']) == str:
            
            diseases_values[exact_matches.at[idx, 'uid']] = {
                'disease_icd' : exact_matches.at[idx, 'title-syns'],
                'code_icd' : exact_matches.at[idx, 'id_code'],
                'mpx_disease' : exact_matches.at[idx, 'match'],
                                                            }
            diseases_values_list.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))
            diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], exact_matches.at[idx, 'title-syns'], exact_matches.at[idx, 'id_code'],exact_matches.at[idx, 'match']))

        else:
            case_mpx = retrieved[idx]['case_t'].lower()
            topic_mpx = retrieved[idx]['topic_t'].lower()

            if case_mpx == topic_mpx:
                
                bert_scores = calculate_scores(retrieved[idx], case_mpx)

                bert_scores_ordered = sorted(bert_scores, key=lambda x: x[3], reverse=True)
                if bert_scores_ordered[0][3] >= 0.85:
                    diseases_values[exact_matches.at[idx, 'uid']] = {
                        'disease_icd' : bert_scores_ordered[0][1],
                        'code_icd' : bert_scores_ordered[0][0],
                        'mpx_disease' : case_mpx,
                                                                    }
                    diseases_values_list.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], case_mpx))
                    diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], case_mpx))
                else:
                    diseases_values[exact_matches.at[idx, 'uid']] = {
                        'disease_icd' : '',
                        'code_icd' : '',
                        'mpx_disease' : case_mpx,
                                                                    }
                    diseases_values_list.append((exact_matches.at[idx, 'uid'], '', '', case_mpx))
                    diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered[0][1], bert_scores_ordered[0][0], case_mpx))
                    borderline_cases.append(exact_matches.at[idx, "uid"])
                    borderline_results.append((exact_matches.at[idx, 'uid'], case_mpx, bert_scores_ordered))

            else: #case_mpx != topic_mpx

                bert_scores_case = calculate_scores(retrieved[idx], case_mpx)
                bert_scores_topic = calculate_scores(retrieved[idx], topic_mpx)
                bert_scores_ordered_case = sorted(bert_scores_case, key=lambda x: x[3], reverse=True)
                bert_scores_ordered_topic = sorted(bert_scores_topic, key=lambda x: x[3], reverse=True)

                if bert_scores_ordered_case[0][3] >= 0.85:
                    diseases_values[exact_matches.at[idx, 'uid']] = {
                        'disease_icd' : bert_scores_ordered_case[0][1],
                        'code_icd' : bert_scores_ordered_case[0][0],
                        'mpx_disease' : case_mpx}
                    diseases_values_list.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_case[0][1], bert_scores_ordered_case[0][0], case_mpx))
                    diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_case[0][1], bert_scores_ordered_case[0][0], case_mpx))
                
                elif bert_scores_ordered_topic[0][3] >= 0.85:
                    diseases_values[exact_matches.at[idx, 'uid']] = {
                        'disease_icd' : bert_scores_ordered_topic[0][1],
                        'code_icd' : bert_scores_ordered_topic[0][0],
                        'mpx_disease' : case_mpx}
                    diseases_values_list.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_topic[0][1], bert_scores_ordered_topic[0][0], case_mpx))
                    diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_topic[0][1], bert_scores_ordered_topic[0][0], case_mpx))
                
                else:
                    diseases_values[exact_matches.at[idx, 'uid']] = {
                        'disease_icd' : '',
                        'code_icd' : '',
                        'mpx_disease' : case_mpx,
                                                                    }
                    diseases_values_list.append((exact_matches.at[idx, 'uid'], '', '', case_mpx))
                    if bert_scores_ordered_case[0][3] >= bert_scores_ordered_topic[0][3]:
                        diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_case[0][1], bert_scores_ordered_case[0][0], case_mpx))
                    else:
                        diseases_values_list_w_borderlines.append((exact_matches.at[idx, 'uid'], bert_scores_ordered_topic[0][1], bert_scores_ordered_topic[0][0], case_mpx))
                    
                    borderline_cases.append(exact_matches.at[idx, "uid"])
                    borderline_results.append((exact_matches.at[idx, 'uid'], case_mpx, bert_scores_ordered_case, bert_scores_ordered_topic))
    
    os.makedirs(f'{path}/Final_annotation/', exist_ok=True)
    diseases_values_df = pd.DataFrame(diseases_values_list, columns=['uid', 'disease_icd', 'code_icd', 'mpx_disease'])
    diseases_values_df.to_csv(f'{path}/Final_annotation/mpx_diseases_icd11.tsv', sep='\t', index=False)

    diseases_values_df_w_borderlines = pd.DataFrame(diseases_values_list_w_borderlines, columns=['uid', 'disease_icd', 'code_icd', 'mpx_disease'])
    diseases_values_df_w_borderlines.to_csv(f'{path}/Final_annotation/mpx_diseases_icd11_borderlines.tsv', sep='\t', index=False)

    with open(f'{path}/Final_annotation/mpx_diseases_icd11.pickle', 'wb') as f:
        pickle.dump(diseases_values, f)
    with open(f'{path}/Final_annotation/borderline_mpx_diseases_icd11.pickle', 'wb') as f:
        pickle.dump(borderline_results, f)

    print(f'Bordeline cases #{len(borderline_cases)}\n{borderline_cases}')

# Bordeline cases #84
# ['MPX1031', 'MPX1115', 'MPX1139', 'MPX1151', 'MPX1205', 'MPX1214', 'MPX1237', 'MPX1238', 'MPX1268', 'MPX1256', 'MPX1289', 'MPX1279', 'MPX1297', 'MPX1389', 'MPX1457', 'MPX1506', 'MPX1528', 'MPX1531', 'MPX1548', 'MPX1560', 'MPX1617', 'MPX1625', 'MPX1646', 'MPX1654', 'MPX1683', 'MPX1771', 'MPX1809', 'MPX1865', 'MPX1905', 'MPX1937', 'MPX1950', 'MPX1954', 'MPX2018', 'MPX2046', 'MPX2060', 'MPX2049', 'MPX2114', 'MPX2144', 'MPX2158', 'MPX2270', 'MPX2278', 'MPX2282', 'MPX2294', 'MPX2307', 'MPX2319', 'MPX2327', 'MPX2376', 'MPX2384', 'MPX2385', 'MPX2427', 'MPX2446', 'MPX2461', 'MPX2480', 'MPX2483', 'MPX2558', 'MPX2601', 'MPX1022', 'MPX1074', 'MPX1124', 'MPX1220', 'MPX1401', 'MPX1467', 'MPX1500', 'MPX1550', 'MPX1551', 'MPX1608', 'MPX1613', 'MPX1701', 'MPX1709', 'MPX1791', 'MPX1796', 'MPX1851', 'MPX1884', 'MPX2043', 'MPX2083', 'MPX2193', 'MPX2367', 'MPX2372', 'MPX2390', 'MPX2454', 'MPX2428', 'MPX2460', 'MPX2527', 'MPX2574']