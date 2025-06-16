#!/usr/bin/env python
# coding: utf-8


import argparse
import os
import time
from collections import defaultdict
from functools import partial
import json
from tqdm import tqdm

import pandas as pd
from src.util.gpts import gpts

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

def get_prompt_from_path(promptpath):
    if len(promptpath) == 0:
        return ''
    with open(os.path.join(ROOT_DIR, f"prompts/{promptpath}.txt"), "r") as fin:
        prompt = fin.read() 
    return prompt

def extract_brackets(s):
    start = s.find('{')
    end = s.rfind('}')
    if start != -1 and end != -1:
        return s[start:end+1]
    else:
        return s

def parse_label(x):
    try:
        return json.loads(extract_brackets(x))
    except:
        return None

def run(out_df, task_col, idxs, gpts, output_prefix, promptpath='', out_folder='tmp'):
    prompt = get_prompt_from_path(promptpath)
    return run_with_single_prompt(out_df, task_col, idxs, gpts, output_prefix, f"{output_prefix}_{promptpath}", prompt, out_folder)

def run_with_single_prompt(out_df, task_col, idxs, gpts, output_prefix, prompt, out_folder='tmp'):
    out_df = out_df.iloc[idxs]
    questions = out_df[task_col].tolist()
    prompted_inputs = [prompt + question + "\n" for question in questions]
    infos = {}
    i_range = list(range(0, len(prompted_inputs), 50))
    for i in i_range:
        trial = 0
        while trial < 3:
            try:
                raw_responses = gpts(prompted_inputs[i:i+50])
                break
            except Exception as e:
                print(e)
                time.sleep(60)
            trial += 1
        for j in range(len(raw_responses)):
            infos[idxs[i+j]] = {'input': prompted_inputs[i+j], 'answer': raw_responses[j]}        
        # create a dictionary that returns 'NotFound' when a key is not found
        review_to_info = defaultdict(lambda: {'answer':'[]'})
        for info in infos.values():
            review_to_info[info['input'].strip()] = info
        if (i > 0 and i%200 == 0) or i == i_range[-1]:
            out_df['label'] = out_df[task_col].apply(lambda x: review_to_info[x.strip()]['answer'])
            out_filename = f"{output_prefix}_{idxs[0]}-{idxs[i+len(raw_responses)-1]}.xlsx"
            out_path = os.path.join(out_folder, out_filename)
            out_df.to_excel(out_path, index=False)
    return infos


def run_with_prompted_inputs(out_df, input_col, model, output_prefix, idxs=None, out_folder='tmp', batch_size=15, save_every=50):
    if idxs is None:
        idxs = list(range(len(out_df)))
    out_df = out_df.iloc[idxs].copy().reset_index(drop=True)
    prompted_inputs = out_df[input_col].tolist()
    infos = []
    i_range = list(range(0, len(prompted_inputs), batch_size))
    
    # Add outer progress bar
    pbar = tqdm(i_range, desc=">>>> Processing batches", position=0, leave=True)
    
    for i in pbar:
        trial = 0
        while trial < 3:
            try:
                # The inner progress bar is handled by tqdm_asyncio in gpts.py
                raw_responses = model(prompted_inputs[i:i+batch_size])
                break
            except Exception as e:
                print(e)
                time.sleep(60)
            trial += 1
            
        for j in range(len(raw_responses)):
            infos.append({'input': prompted_inputs[i+j], 'response': raw_responses[j]})
        
        review_to_info = defaultdict(lambda: {'response':''})
        for info in infos:
            review_to_info[info['input'].strip()] = info
            
        if (i > 0 and i % save_every == 0) or i == i_range[-1]:
            out_df.loc[:, 'response'] = out_df[input_col].apply(lambda x: review_to_info[x.strip()]['response'])
            out_filename = f"{output_prefix}_{idxs[0]}-{idxs[i+len(raw_responses)-1]}.xlsx"
            out_path = os.path.join(out_folder, out_filename)
            out_df.to_excel(out_path, index=False)
            
        pbar.set_postfix({'last_batch': i+batch_size})
        time.sleep(2)
        
    return out_df


def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument('--backend', type=str, default='gpt-4')
    args.add_argument('--temperature', type=float, default=0.01)

    args.add_argument('--task', type=str, required=True)
    args.add_argument('--task_split', type=str, default='train')
    args.add_argument('--task_start_index', type=int, default=0)
    args.add_argument('--task_end_index', type=int, default=100)

    args.add_argument('--evaluate', action='store_true')
    args.add_argument('--add_lora', action='store_true')
    args.add_argument('--random', action='store_true')
    
    args.add_argument('--modelpath', type=str, default='meta-llama/Llama-2-7b-chat-hf')
    args.add_argument('--peftpath', type=str, default='forestai/lora_hotpot_v2')
    args.add_argument('--promptpath', type=str, default='')

    args = args.parse_args()
    return args



    
# python generation_io.py --task hotpotqa --task_end_index 100 --backend llama --evaluate --task_split dev 


if __name__ == '__main__':
    ribbon_df = pd.read_excel("/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/ribbon_lace_review_v4_20240215.xlsx")
    sale_df = ribbon_df[(~ribbon_df['price'].isna()) &(~ribbon_df['estimated_montly_sales'].isna())]
    # get the top 50 most revenue generating products
    grouped_df = sale_df.groupby('asin').agg({'price':'first', 'estimated_montly_sales':'first'}).reset_index()
    grouped_df['revenue'] = grouped_df['price'] * grouped_df['estimated_montly_sales']
    TOP_NUM = 2
    # get the top 51-150 most revenue generating products
    top_revenue_df = grouped_df.sort_values('revenue', ascending=False).head(TOP_NUM)
    
    selected_df = ribbon_df[ribbon_df['asin'].isin(top_revenue_df['asin'])]
    selected_df = selected_df[selected_df['review_text'].apply(lambda x: type(x) == str and len(x) > 10 and len(x.strip().split()) > 3)]
    
    # model_name = "gpt-4"
    model_name = "gpt-3.5-turbo-0125"
    model = partial(gpts, model=model_name, temperature=0.01)
    # prompt_file = "zero-shot_single_review-summary_v0"
    # prompt_file = "few-shot_single_review-summary_v1"
    prompt_file = "few-shot_single_review-summary_v4"
    infos = run(selected_df.copy(), 'review_text', list(range(len(selected_df['review_text']))), model, output_prefix=f"ribbon-prompt_top-rev-{TOP_NUM}", promptpath=prompt_file)