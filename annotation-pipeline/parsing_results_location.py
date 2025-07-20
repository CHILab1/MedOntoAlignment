import pandas as pd

if __name__ == '__main__':

    target_field = 'Location'
    path = 'OntoMedPix/'

    df = pd.read_csv(f'{path}Results-locations/results_mms_locations_synonyms.tsv', sep='\t', index_col=False)

    matches = {}
    for i in range(len(df)):
        if type(df.at[i, 'match'])==str and df.at[i, target_field]:
            if type(df.at[i, 'synonym'])==str:
                matches[df.at[i, 'uid_img']] = df.at[i, 'synonym']
            else:
                matches[df.at[i, 'uid_img']] = df.at[i, 'match']
        else:
            matches[df.at[i, 'uid_img']] = ""

    df_icd11 = pd.read_csv(f'{path}icd11-mms-locations.tsv', sep='\t')
    df_icd11 = df_icd11[df_icd11['classKind']=='category']
    df_icd11 = df_icd11.reset_index(drop=True)

    mpx_matches = []

    #for k,v in matches.items():
    for idx, (k,v) in enumerate(matches.items()):
        if v != "":
            for i in range(len(df_icd11)):
                if type(df_icd11.at[i, 'title'])==str and df_icd11.at[i, 'title'].lower() == v:
                    if df_icd11.at[i, 'id'].split('/')[-1] == 'other' or df_icd11.at[i, 'id'].split('/')[-1] == 'unspecified':
                        id_code = "-".join(df_icd11.at[i, 'id'].split('/')[-2:])
                    else:
                        id_code = df_icd11.at[i, 'id'].split('/')[-1]
                    mpx_matches.append((k, df_icd11.at[i, 'title'], df.at[idx, 'match'], id_code, df_icd11.at[i, 'id'], df_icd11.at[i, 'code_mms']))
                    break
        else:
            mpx_matches.append((k, '', '', '', '', ''))

    mpx_matches_df = pd.DataFrame(mpx_matches, columns=['uid', 'title-syns', 'match',  'id_code', 'id', 'code_mms'])
    mpx_matches_df.to_csv(f'{path}Results-locations/{target_field}_mpx_matches.tsv', sep='\t', index=False)