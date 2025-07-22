from tqdm import tqdm
import pandas as pd
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--target_field', type=str, default='Plane')
    # parser.add_argument('--target_field', type=str, default='Modality')
    args = parser.parse_args()
    target_field = args.target_field

    path = 'MedOntoAlignment/'
    save_str = f'results_RADLEX_{target_field}'

    df = pd.read_csv(f'{path}Results-{target_field}/{save_str}.tsv', sep='\t', index_col=False)
    
    matches = {}
    for i in range(len(df)):
        if type(df.at[i, 'match'])==str and df.at[i, target_field]:
            if type(df.at[i, 'synonym'])==str:
                matches[df.at[i, 'uid_img']] = df.at[i, 'synonym']
            else:
                matches[df.at[i, 'uid_img']] = df.at[i, 'match']
        else:
            matches[df.at[i, 'uid_img']] = ""

    radlex_df = pd.read_csv(path + f'RADLEX.csv')

    mpx_matches = []

    #for k,v in matches.items():
    for idx, (k,v) in enumerate(tqdm(matches.items())):
        if v != "":
            for i in range(len(radlex_df)):
                if type(radlex_df.at[i, 'Preferred Label'])==str and radlex_df.at[i, 'Preferred Label'].lower() == v:
                    code = radlex_df.at[idx, 'Class ID'].split('#')[-1]

                    mpx_matches.append((k, radlex_df.at[i, 'Preferred Label'], df.at[idx, 'match'], code))
                    break
        else:
            mpx_matches.append((k, '', '', ''))

    mpx_matches_df = pd.DataFrame(mpx_matches, columns=['uid', 'title-syns', 'match',  'id_code'])
    mpx_matches_df.to_csv(f'{path}Results-{target_field}/{target_field}_RADLEX_matches.tsv', sep='\t', index=False)