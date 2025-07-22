import pandas as pd

if __name__ == '__main__':

    category = False
    path = 'MedOntoAlignment/'

    if category:
        df = pd.read_csv(f'{path}Results-diseases/results_mms_diseases_synonyms_category.tsv', sep='\t', index_col=False)
    else:
        df = pd.read_csv(f'{path}Results-diseases/results_mms_diseases_synonyms.tsv', sep='\t', index_col=False)

    matches = {}
    for i in range(len(df)):
        if type(df.at[i, 'match'])==str and df.at[i, 'match'] == df.at[i, 'case_title']:
            if type(df.at[i, 'synonym'])==str:
                matches[df.at[i, 'uid']] = df.at[i, 'synonym']
            else:
                matches[df.at[i, 'uid']] = df.at[i, 'match']
        elif type(df.at[i, 'match'])==str and df.at[i, 'match'] == df.at[i, 'topic_title']:
            if type(df.at[i, 'synonym'])==str:
                matches[df.at[i, 'uid']] = df.at[i, 'synonym']
            else:
                matches[df.at[i, 'uid']] = df.at[i, 'match']
        elif type(df.at[i, 'match'])==str and df.at[i, 'match'] == df.at[i, 'category']:
            if type(df.at[i, 'synonym'])==str:
                matches[df.at[i, 'uid']] = df.at[i, 'synonym']
            else:
                matches[df.at[i, 'uid']] = df.at[i, 'match']
        else:
            matches[df.at[i, 'uid']] = ""

    df_icd11 = pd.read_csv(f'{path}icd11/icd11-mms-diseases.tsv', sep='\t')
    df_icd11 = df_icd11[df_icd11['classKind']=='category']
    df_icd11 = df_icd11.reset_index(drop=True)

    mpx_matches = []

    #for k,v in matches.items():
    for idx, (k,v) in enumerate(matches.items()):
        if v != "":
            for i in range(len(df_icd11)):
                if df_icd11.at[i, 'title'].lower() == v:
                    if df_icd11.at[i, 'id'].split('/')[-1] == 'other' or df_icd11.at[i, 'id'].split('/')[-1] == 'unspecified':
                        id_code = "-".join(df_icd11.at[i, 'id'].split('/')[-2:])
                    else:
                        id_code = df_icd11.at[i, 'id'].split('/')[-1]
                    if category:
                        mpx_matches.append((k, df_icd11.at[i, 'title'], df.at[idx, 'match'], id_code, df_icd11.at[i, 'id'], df_icd11.at[i, 'code_mms'], df.at[idx, 'case_title'], df.at[idx, 'topic_title'], df.at[idx, 'category']))
                    else:
                        mpx_matches.append((k, df_icd11.at[i, 'title'], df.at[idx, 'match'], id_code, df_icd11.at[i, 'id'], df_icd11.at[i, 'code_mms'], df.at[idx, 'case_title'], df.at[idx, 'topic_title']))
                    break
        else:
            if category:
                mpx_matches.append((k, '', '', '', '', '', df.at[idx, 'case_title'], df.at[idx, 'topic_title'], df.at[idx, 'category']))
            else:
                mpx_matches.append((k, '', '', '', '', '', df.at[idx, 'case_title'], df.at[idx, 'topic_title']))

    if category:
        mpx_matches_df = pd.DataFrame(mpx_matches, columns=['uid', 'title-syns', 'match', 'id_code', 'id', 'code_mms', 'case_title', 'topic_title', 'category'])
        mpx_matches_df.to_csv(f'{path}Results-diseases/mpx_matches_category.tsv', sep='\t', index=False)
    else:
        mpx_matches_df = pd.DataFrame(mpx_matches, columns=['uid', 'title-syns', 'match', 'id_code', 'id', 'code_mms', 'case_title', 'topic_title'])
        mpx_matches_df.to_csv(f'{path}Results-diseases/mpx_matches.tsv', sep='\t', index=False)