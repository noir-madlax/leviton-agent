import os
from functools import partial
import re
import datetime

import pandas as pd
import random
random.seed(0)
from src.util.gpts import claude
from src.util.run_gpt_reviews import get_prompt_from_path, run_with_prompted_inputs

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(SRC_DIR)
OUTPUT_ROOT_DIR = os.path.join(ROOT_DIR, "tmp")    

# Helper function to extract info from URL
def extract_review_id(url):
    match = re.search(r'customer-reviews/(\w+)/', url)
    return match.group(1) if match else None

# Helper function to extract and format date
def extract_date(date_str):
    if pd.isna(date_str):
        return None
    
    # Pattern for "Reviewed in the United States on April 7, 2019"
    pattern = r".*on\s+(\w+)\s+(\d+),\s+(\d{4})"
    match = re.search(pattern, date_str)
    
    if match:
        month_name, day, year = match.groups()
        # Convert month name to number
        month_dict = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = month_dict.get(month_name)
        
        if month:
            try:
                # Format as YYYY-MM-DD
                return f"{year}-{month:02d}-{int(day):02d}"
            except (ValueError, TypeError):
                return None
    
    return None

if __name__ == '__main__':
    # Define file paths and corresponding ASINs (adjust paths as needed)
    file_info = [
        {"path": "/Users/maoc/Downloads/B08RSM1KYN - Leviton Decora Smart Switch, Wi-Fi 2nd Gen, Neutra 2025-04-14.csv", "asin": "B08RSM1KYN"},
        {"path": "/Users/maoc/Downloads/B079775ZZQ - Kasa Smart Dimmer Switch HS220, Single Pole, Needs 2025-04-14.csv", "asin": "B079775ZZQ"}
    ]

    all_dfs = []
    for info in file_info:
        file_path = info['path']
        asin = info['asin']
        try:
            df_temp = pd.read_csv(file_path)
            df_temp['asin'] = asin # Add asin column from filename info
            all_dfs.append(df_temp)
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}. Skipping this file.")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}. Skipping this file.")

    if not all_dfs:
        print("No valid CSV files were read. Exiting.")
        exit()

    # Concatenate the dataframes
    df = pd.concat(all_dfs, ignore_index=True)

    # Extract review_id from URL
    df['review_id'] = df['URL'].apply(extract_review_id)
    
    # Extract and format date
    df['review_date'] = df['Date'].apply(extract_date)

    # Rename columns to match the existing script logic
    # Map 'Title' to 'review_title' and 'Body' to '评论内容'
    df.rename(columns={'Title': 'review_title', 'Body': '评论内容', 'Rating': '评论星级'}, inplace=True)
    # Drop rows where essential info couldn't be extracted
    df.dropna(subset=['asin', 'review_id', '评论内容'], inplace=True)
    
    df.to_excel("/Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/UX168 data and code/data/raw/Leviton_smart_switches_reviews.xlsx", index=False)

    out_folder_name = 'smart_switches'
    PRODUCT = 'smart switches'
    
    # Group by 'asin'
    grouped = df.groupby('asin')
    asin_title = grouped.agg({"review_title": "first"}).reset_index()

    
    # Shuffle the groups
    shuffled_groups = [group for _, group in grouped]
    random.shuffle(shuffled_groups)
    shuffled_df = pd.concat(shuffled_groups).reset_index(drop=True)
    all_review_ids = []
    all_inputs = []
    all_asins = []
    def append_to_all(group_input_str, group_review_id_str, group_asin_str):
        all_review_ids.append(group_review_id_str.strip())
        all_inputs.append(group_input_str.strip())
        all_asins.append(group_asin_str.strip())

    group_input_str = ''
    group_review_id_str = ''
    group_asin_str = ''
    idx = 0
    for _, row in shuffled_df.iterrows():
        # first check whether the review_title ends with a punctuation
        if pd.isna(row['review_title']):
            title = ''
        elif isinstance(row['review_title'], str) and not row['review_title'].endswith(('.', '?', '!', ',', ';', ':')):
            title = str(row['review_title']) + '. '
        else:
            title = str(row['review_title']) + ' '
        body = str(row['评论内容']) if pd.notna(row['评论内容']) else ''
        input_text = f"{title}{body}\n"
        if len(group_input_str+input_text) > 4000:
            append_to_all(group_input_str, group_review_id_str, group_asin_str)
            idx = 0
            group_input_str = ''
            group_review_id_str = ''
            group_asin_str = ''
        input_text = f"{idx}#{input_text}"
        idx += 1
        group_input_str += input_text
        group_review_id_str += f"{str(row['review_id'])}\n"
        group_asin_str += f"{str(row['asin'])}\n"
    append_to_all(group_input_str, group_review_id_str, group_asin_str)
    run_indexes = list(range(len(all_inputs)))
    input_df = pd.DataFrame({'review_id': all_review_ids, 'asin': all_asins, 'input': all_inputs})
    prompt_file = "multiple_review_hierarchy-MRO_v4"
    prompt_template = get_prompt_from_path(prompt_file)
    prompt_template = prompt_template.replace("{{PRODUCT}}", PRODUCT)
    input_df['prompted_input'] = input_df.apply(lambda x: prompt_template.replace('{{INPUT}}', x['input']), axis=1)

    model_name="claude-3-5-sonnet-20240620"
    model = partial(claude, model=model_name)
    output_folder = os.path.join(OUTPUT_ROOT_DIR, out_folder_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    infos = run_with_prompted_inputs(input_df, 'prompted_input', model,idxs=run_indexes, batch_size=5, save_every=25, out_folder=output_folder, output_prefix=f"{prompt_file}_{model_name}")