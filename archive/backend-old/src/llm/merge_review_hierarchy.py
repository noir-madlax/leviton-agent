#!/usr/bin/env python
# coding: utf-8


import hashlib
import json
import os
import pickle
import random
import re
import copy  # Add this import for deep copying
from collections import defaultdict
from functools import partial
import math
import numpy as np
import pandas as pd
from k_means_constrained import KMeansConstrained
from nltk.stem import PorterStemmer
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
stop_words.remove('not')

from src.util.gpts import claude
from src.util.run_gpt_reviews import (
    get_prompt_from_path,
    parse_label,
    run_with_prompted_inputs,
)
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


random.seed(42)

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(SRC_DIR)
OUTPUT_ROOT_DIR = os.path.join(ROOT_DIR, "tmp")
PRODUCT = 'leviton'
PRODUCT_NAME = 'smart switches'
OUTPUT_DIR = os.path.join(OUTPUT_ROOT_DIR, f"{PRODUCT}_hierarchy_merged")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def sort_dict(d):
    if isinstance(d, list):
        return sorted(d)
    elif not isinstance(d, dict):
        return d
    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}  

stemmer = PorterStemmer()

# split string by all punctuations and spaces
def split_string(s):
    return [word for word in re.split(r'[^\w]+', s) if word]

stem_cache = {}
def stem_with_cache(word):
    if word not in stem_cache:
        stem_cache[word] = stemmer.stem(word)
    return stem_cache[word]

def stem_key(key):
    return ' '.join([stem_with_cache(w) for w in split_string(key.lower())])



def get_shortest_key(stemmed_to_original, stemmed_key):
    return min(stemmed_to_original[stemmed_key], key=len)

def print_stemmed_key_info(stemmed_to_original):
    for stemmed_key, original_keys in stemmed_to_original.items():
        shortest_key = get_shortest_key(stemmed_to_original, stemmed_key)
        other_keys = [key for key in original_keys if key != shortest_key]
        if len(other_keys) > 0:
            print(f"Key: {shortest_key} ## {set(other_keys)} || Stem: {stemmed_key}")

def merge_jsons(df, extract_english=False):
    attr_dict = defaultdict(dict)
    perf_dict = defaultdict(dict)
    use_dict = defaultdict(lambda: str(f"use_{len(use_dict)}"))
    
    attr_ids = defaultdict(lambda: str(f"ATTR_{len(attr_ids)}"))
    perf_ids = defaultdict(lambda: str(f"perf_{len(perf_ids)}"))

    attr_id_to_detail = {}
    perf_id_to_detail = {}
    attr_id_to_values = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    perf_id_to_values = defaultdict(lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    use_id_to_values = defaultdict(lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    
    for i_th, row in df.iterrows():
        data = row.json_response
        if data is None:
            continue
        orig_id_to_new_id = {}  # Mapping from original D_IDs to new D_IDs
        idxs = [int(l.split('#')[0]) for l in row.input.split('\n')]
        # TODO: 
        idxs_to_review_ids = dict(zip(idxs, row.review_id.split('\n')))
        # change the extraction script to have idxs to start from 0, so that the above line can be changed to the following
        # idxs_to_review_ids = {idx: review_id for idx, review_id in enumerate(row.review_id.split('\n'))}
        
        # Process physical attributes
        if "phy" in data:
            for attr, detail_dict in data["phy"].items():
                for d_id_desc, detail_dict in detail_dict.items():
                    original_d_id, detail = d_id_desc.split('@', 1)
                    new_attr_id = attr_ids[f"{attr}||{detail}"]
                    attr_dict[attr][detail] = new_attr_id
                    attr_id_to_detail[new_attr_id] = detail
                    for key, val in detail_dict.items():
                        if isinstance(val, dict):
                            original_subdetail_id, subdetail = key.split('@', 1)
                            new_sub_detail_id = attr_ids[f"{attr}||{detail} {subdetail}"]
                            for sent, ids in val.items():
                                attr_id_to_values[new_sub_detail_id][sent][subdetail].extend([idxs_to_review_ids[idx] for idx in ids if idx in idxs_to_review_ids])
                            orig_id_to_new_id[original_subdetail_id] = new_sub_detail_id
                        elif isinstance(val, list):
                            sent = key
                            ids = val
                            attr_id_to_values[new_attr_id][sent][detail].extend([idxs_to_review_ids[idx] for idx in ids if idx in idxs_to_review_ids])
                        else:
                            raise ValueError(f"unknown val type {type(val)} of {val}")  
                    orig_id_to_new_id[original_d_id] = new_attr_id  
        
        # Process performances
        if "perf" in data:
            for perf, detail_dict in data["perf"].items():
                for d_id_desc, detail_dict in detail_dict.items():
                    original_d_id, detail = d_id_desc.split('@', 1)
                    new_perf_id = perf_ids[f"{perf}||{detail}"]
                    perf_dict[perf][detail] = new_perf_id
                    perf_id_to_detail[new_perf_id] = detail
                    for sent, reasons in detail_dict.items():
                        if isinstance(reasons, dict):
                            for reason, ids in reasons.items():
                                new_reason = "?" if reason == "?" else orig_id_to_new_id.get(reason, "?")
                                perf_id_to_values[new_perf_id][sent][detail][new_reason].extend([idxs_to_review_ids[idx] for idx in ids if idx in idxs_to_review_ids])
                        elif isinstance(reasons, list):
                            new_reason = "?"
                            perf_id_to_values[new_perf_id][sent][detail][new_reason].extend([idxs_to_review_ids[idx] for idx in reasons if idx in idxs_to_review_ids])
                        else:
                            raise ValueError(f"unknown reasons type {type(reasons)} of {reasons}")
                    orig_id_to_new_id[original_d_id] = new_perf_id
        
        # Process uses
        if "use" in data:
            for use, detail_dict in data["use"].items():
                for sent, reasons in detail_dict.items():
                    use_id = use_dict[use]
                    for reason, ids in reasons.items():
                        new_reason = "?" if reason == "?" else orig_id_to_new_id.get(reason, "?")
                        use_id_to_values[use_id][sent][use][new_reason].extend([idxs_to_review_ids[idx] for idx in ids if idx in idxs_to_review_ids])
    cleaned_attr_dict = clean_up_dict_by_path_stems(attr_dict, extract_english)
    cleaned_perf_dict = clean_up_dict_by_path_stems(perf_dict, extract_english)
    cleaned_use_dict = clean_up_dict_by_path_stems(use_dict, extract_english)
    return cleaned_attr_dict, cleaned_perf_dict, cleaned_use_dict, attr_id_to_values, perf_id_to_values, use_id_to_values, attr_id_to_detail, perf_id_to_detail

def merge_values(val1, val2):
    if isinstance(val1, int) or isinstance(val1, str):
        val1 = [val1]
    if isinstance(val2, int) or isinstance(val2, str):
        val2 = [val2]
    if val1 is None or len(val1) == 0:
        return val2
    if val2 is None or len(val2) == 0:
        return val1
    if isinstance(val1, list) or isinstance(val2, list):
        if isinstance(val1, list) and isinstance(val2, list):
            return list(set(val1+val2))
        elif hasattr(val1, 'keys'):
            return merge_values(val1, {'_': val2})
        else:
            return merge_values({'_': val1}, val2)
    elif hasattr(val1, 'keys') and hasattr(val2, 'keys'):
        new_dict = {}
        for key in set(list(val1.keys())+list(val2.keys())):
            new_dict[key] = merge_values(val1.get(key, None), val2.get(key, None))
        return new_dict
    else:
        raise ValueError(f"Invalid value type: {type(val1)} of {val1} and {type(val2)} of {val2}")

def convert_ids_recursively(input_d, id_val_map):
    if isinstance(input_d, list):
        new_val = None
        for idx in input_d:
            if isinstance(idx, str):
                idx = int(idx)
            for val in id_val_map[idx]:
                new_val = merge_values(new_val, val)
        return new_val
    elif hasattr(input_d, 'items'):
        return {k: convert_ids_recursively(v, id_val_map) for k, v in input_d.items()}
    else:
        return input_d

def merge_merged_jsons(input_df, key_suffix):
    input_df['json_response'] = input_df.response.apply(parse_label)
    input_df['id_val_map_json'] = input_df.id_val_map.apply(lambda x: json.loads(x))
    input_df['id_val_map_json'] = input_df.id_val_map_json.apply(lambda x: {int(k): v for k, v in x.items()})
    
    # Initialize attr_perf_dict as before
    attr_perf_dict = {'attr': defaultdict(lambda: defaultdict(dict)), 
                      'perf': defaultdict(lambda: defaultdict(dict))}
    
    # Initialize use_dict that can handle both 2-level and 3-level structures
    def dict_factory():
        return defaultdict(lambda: defaultdict(list))  # Default to 2 levels ending in list
    use_dict = defaultdict(dict_factory)  # First level is regular dict for flexibility
    
    for _, row in input_df.iterrows():
        data = convert_ids_recursively(row.json_response, row['id_val_map_json'])
        if row.in_class in ['attr', 'perf']:
            attr_perf_dict[row.in_class] = merge_values(attr_perf_dict[row.in_class], data)
        elif row.in_class == 'use':
            use_dict = merge_values(use_dict, data)

    return attr_perf_dict, use_dict

def get_attributes_df(final_attributes_ids):
    new_attributes = []
    for s in final_attributes_ids.keys():
        attributes, detail = s.split('||')
        new_attributes.append(attributes +'; '+ detail)
    return pd.DataFrame({'input': new_attributes, 'orig': list(final_attributes_ids.keys()), 'orig_id': list(final_attributes_ids.values())})

def get_use_df(final_uses):
    return pd.DataFrame({'input': list(final_uses.keys()), 'orig': list(final_uses.keys()), 'orig_id': list(range(len(final_uses)))})

emb_model = SentenceTransformer('all-mpnet-base-v2')

def get_unique_identifier(input_df, target_cluster_size, chunk_size):
    # Create a hash of the input dataframe
    df_hash = hashlib.md5(pd.util.hash_pandas_object(input_df).values).hexdigest()
    # Combine with other parameters
    return f"{df_hash}_{target_cluster_size}_{chunk_size}"

def get_embedding_cluster_path(output_dir, unique_id):
    return os.path.join(output_dir, f'embeddings_and_clusters_{unique_id}.pkl')

def save_embeddings_and_clusters(input_df, asp_emb, output_dir, unique_id):
    data = {
        'input_df': input_df,
        'asp_emb': asp_emb
    }
    file_path = get_embedding_cluster_path(output_dir, unique_id)
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved embeddings and clusters to {file_path}")

def load_embeddings_and_clusters(output_dir, unique_id):
    file_path = get_embedding_cluster_path(output_dir, unique_id)
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        print(f"Loaded embeddings and clusters from {file_path}")
        return data['input_df'], data['asp_emb']
    except FileNotFoundError:
        print(f"No existing embeddings and clusters found at {file_path}")
        return None, None

def get_merged_remove_cat_output(in_dict, prompt_file, prefix, target_chunk_size=50):
    input_strs = []
    in_ids = []
    for cat, detail_dict in in_dict.items():
        for detail, id in detail_dict.items():
            input_strs.append(f"{cat}|{detail}")
            in_ids.append(id)
    num_chunks = len(input_strs) // target_chunk_size + 1
    chunk_ids = np.random.randint(0, num_chunks, len(input_strs))
    tmp_df = pd.DataFrame({'input_str': input_strs, 'input_id': in_ids, 'chunk_id': chunk_ids})
    prompt_template = get_prompt_from_path(prompt_file)
    prompted_inputs = []
    chunk_input_ids = []
    for cid, group in tmp_df.groupby('chunk_id'):
        inputs = []
        for i, input in enumerate(group.input_str):
            inputs.append(f"{i}|{input}")
        chunk_input_ids.append(group.input_id.tolist())
        prompted_inputs.append(prompt_template.replace('{{PRODUCT}}', PRODUCT_NAME).replace('{{INPUT}}', '\n'.join(inputs)))
    input_df = pd.DataFrame({'prompted_input': prompted_inputs, 'id': chunk_input_ids})
    out_df = run_with_prompted_inputs(input_df, 'prompted_input', model, out_folder=OUTPUT_DIR, output_prefix=prefix)
    orig_id_to_new_phrase = {}
    for i, row in out_df.iterrows():
        out_idx_phrases = row.response.split('\n')
        for orig_id, idx_phrase in zip(row.id, out_idx_phrases):
            orig_id_to_new_phrase[orig_id] = idx_phrase.split(':')[1].strip()
    return orig_id_to_new_phrase

# split string by all punctuations and spaces
def split_string(s):
    return [word for word in re.split(r'[^\w]+', s) if word]

emb_model = SentenceTransformer('all-mpnet-base-v2')

keys_emb_cache = {}
def emb_with_cache(keys):
    keys_str = "|".join(keys)   
    if keys_str in keys_emb_cache:
        keys_emb = keys_emb_cache[keys_str]
    else:
        keys_emb = emb_model.encode(keys)
        keys_emb_cache[keys_str] = keys_emb
    return keys_emb

def cluster_keys(keys, threshold=0.1):  
    keys_emb = emb_with_cache(keys)
    agg_clustering_narrow = AgglomerativeClustering(n_clusters=None, metric='cosine', linkage='complete', distance_threshold=threshold)
    cluster_ids = agg_clustering_narrow.fit_predict(keys_emb)
    return cluster_ids

def km_cluster_keys(keys, target_group_size=80):
    keys_emb = emb_with_cache(keys)
    n_samples = len(keys)
    
    # Calculate minimum number of clusters needed
    n_clusters = max(1, math.ceil(n_samples / target_group_size))
    
    # Calculate size_max to ensure size_max * n_clusters >= n_samples
    size_max = max(
        target_group_size,
        math.ceil(n_samples / n_clusters)
    )
    
    # Set size_min to be slightly below size_max but ensure it's at least 1
    size_min = max(1, min(size_max - 1, math.floor(n_samples / (n_clusters * 1.2))))
    
    # Perform constrained KMeans clustering
    kmeans = KMeansConstrained(
        n_clusters=n_clusters,
        size_min=size_min,
        size_max=size_max,
        n_init=1,
        tol=1e-2,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    result = kmeans.fit_predict(keys_emb)
    return result

def get_clustered_input_df(attr_dict, perf_dict, use_dict):
    all_rows = []
    for full_dict in [attr_dict, perf_dict]:
        for k, v_dict in full_dict.items():
            for v, id in v_dict.items():
                all_rows.append({'full_val': f"{k}: {v}", 'value': f"{v}", 'id': id})
    for v, id in use_dict.items():
        all_rows.append({'full_val': v, 'value': v, 'id': id})
    full_df = pd.DataFrame(all_rows)
    full_df['stemmed_val'] = full_df.value.apply(lambda x: ' '.join([stemmer.stem(w).lower() for w in split_string(x)]))
    stem_groups = full_df.groupby('stemmed_val')
    full_df['unique_value'] = ''
    for stemmed_val, group in stem_groups:
        shortest_val = group.value.apply(len).idxmin()
        full_df.loc[group.index, 'unique_value'] = full_df.value.iloc[shortest_val]
    unique_vals = full_df.unique_value.unique()
    agg_narrow_cluster_ids = cluster_keys(unique_vals, threshold=0.15)
    unique_val_to_cluster_id = dict(zip(unique_vals, agg_narrow_cluster_ids))
    full_df['agg_narrow_cluster_id'] = full_df.unique_value.apply(lambda x: unique_val_to_cluster_id[x])
    full_df['agg_narrow_cluster_value'] = ''
    full_df['agg_narrow_cluster_value_class'] = ''
    full_df['agg_narrow_cluster_full_value'] = ''
    full_df['agg_narrow_cluster_value'] = ''
    for cluster_id in full_df.agg_narrow_cluster_id.unique():
        cluster_df = full_df[full_df.agg_narrow_cluster_id == cluster_id]
        cluster_id_prefixes = cluster_df.id.apply(lambda x: x.split("_")[0])
        prefix_counts = cluster_id_prefixes.value_counts()
        formatted_prefix_counts = [f"{prefix}({count})" for prefix, count in prefix_counts.items()]
        if len(cluster_df) >= 2:
            print(f"Cluster {cluster_id}::{';'.join(formatted_prefix_counts)}#{cluster_df.full_val.nunique()} {'||'.join(cluster_df.full_val.unique())}")
        # pick the longest unique value as the cluster value
        longest_full_value_idx = cluster_df.full_val.apply(len).idxmax()
        if 'use' in prefix_counts.index:
            full_df.loc[cluster_df.index, 'agg_narrow_cluster_value_class'] = 'use'
        elif 'perf' in prefix_counts.index:
            full_df.loc[cluster_df.index, 'agg_narrow_cluster_value_class'] = 'perf'
        else:
            full_df.loc[cluster_df.index, 'agg_narrow_cluster_value_class'] = 'attr'
        full_df.loc[cluster_df.index, 'agg_narrow_cluster_full_value'] = full_df.full_val.iloc[longest_full_value_idx]
        full_df.loc[cluster_df.index, 'agg_narrow_cluster_value'] = full_df.unique_value.iloc[longest_full_value_idx]
    full_df['km_cluster_id'] = ''
    for class_name in ['use', ['attr', 'perf']]:
        if class_name == 'use':
            class_df = full_df[full_df['agg_narrow_cluster_value_class'] == class_name]
        else:
            class_df = full_df[full_df['agg_narrow_cluster_value_class'].isin(class_name)]
            class_name = '+'.join(class_name)
        unique_cluster_values = class_df['agg_narrow_cluster_value'].unique()
        if class_name == 'use':
            class_cluster_ids = km_cluster_keys(unique_cluster_values, target_group_size=60)
        else:
            class_cluster_ids = km_cluster_keys(unique_cluster_values, target_group_size=30)
        km_ids = [f"km_{class_name}_{i}" for i in class_cluster_ids]
        uniq_val_to_cluster_id = dict(zip(unique_cluster_values, km_ids))
        full_df.loc[class_df.index, 'km_cluster_id'] = class_df['agg_narrow_cluster_value'].apply(lambda x: uniq_val_to_cluster_id[x])
    return full_df

# iterate through all levels of the dict and replace the values with the ids
def replace_values_with_ids(in_dict, level, id_to_val_dict=None, id_to_keys=None, prev_keys=[], start_id=[0]):
    if id_to_val_dict is None:
        id_to_val_dict = {}
    if id_to_keys is None:
        id_to_keys = {}
    
    # Only decrement level if it's not None (representing "traverse to last level")
    if level is not None:
        level -= 1
        
    for k, v in in_dict.items():
        phrase = ' '.join(k.split('_'))
        unique_keys = prev_keys+[phrase] if phrase not in prev_keys else prev_keys
        # Check if v is a dict AND (we haven't reached target level OR level is None) AND dict is not empty
        if isinstance(v, dict) and (level is None or level > 0) and len(v) > 0:
            replace_values_with_ids(v, level, id_to_val_dict, id_to_keys, unique_keys, start_id)
        else:
            # Either we've reached target level, or v is not a dict, or v is an empty dict
            in_dict[k] = start_id[0]
            id_to_val_dict[start_id[0]] = v
            id_to_keys[start_id[0]] = unique_keys
            start_id[0] += 1
    return id_to_val_dict, id_to_keys

def replace_values_with_ids_at_level(in_dict, level=None, with_examples=False):
    id_to_val_dict, id_to_keys = replace_values_with_ids(in_dict, level)
    if level == 0:
        return id_to_val_dict, {id: ', '.join(keys) for id, keys in id_to_keys.items()}
    else:  # level is None or level > 0
        key_str_to_ids = defaultdict(list)
        for id, keys in id_to_keys.items():
            # If level is None, use all keys, otherwise use up to level keys
            actual_level = len(keys) if level is None else min(level, len(keys))
            key_str = '||'.join(keys[:actual_level]) if actual_level > 0 else '||'.join(keys)
            key_str_to_ids[key_str].append(id)
        
        new_id_to_val_dict = {}
        new_id_to_keys = {}
        for i, (key_str, ids) in enumerate(key_str_to_ids.items()):
            val_dict = None
            for id in ids:
                val_dict = merge_values(val_dict, id_to_val_dict[id])
            new_id_to_val_dict[i] = val_dict
            new_id_to_keys[i] = ', '.join(key_str.split('||'))
            if with_examples and isinstance(val_dict, dict) and len(val_dict) > 0:
                new_id_to_keys[i] += f"|| <<{'; '.join(list(val_dict.keys())[:4])}>>"
        return new_id_to_val_dict, new_id_to_keys

def get_clustered_input_df_from_merged(attr_dict, perf_dict, use_dict, level=None, target_group_size=None, with_examples=False):
    if target_group_size is None:
        target_group_size = {'attr': 80, 'perf': 80, 'use': 120}
    all_rows = []
    for id_prefix, orig_dict in zip(['attr', 'perf', 'use'], [attr_dict, perf_dict, use_dict]):
        id_to_val_dict, id_to_keys = replace_values_with_ids_at_level(orig_dict, level=level, with_examples=with_examples)
        for id, key in id_to_keys.items():
            all_rows.append({'value': key, 'id': f"{id_prefix}_{id}", 'orig_vals': id_to_val_dict[id]})
    full_df = pd.DataFrame(all_rows)
    full_df['stemmed_val'] = full_df.value.apply(lambda x: ' '.join([stemmer.stem(w).lower() for w in split_string(x)]))
    stem_groups = full_df.groupby('stemmed_val')
    full_df['unique_value'] = ''
    for stemmed_val, group in stem_groups:
        shortest_val = group.value.apply(len).idxmin()
        full_df.loc[group.index, 'unique_value'] = full_df.value.iloc[shortest_val]
    unique_vals = full_df.unique_value.unique()
    narrow_cluster_ids = cluster_keys(unique_vals, threshold=0.02)
    unique_val_to_cluster_id = dict(zip(unique_vals, narrow_cluster_ids))
    full_df['narrow_cluster_id'] = full_df.unique_value.apply(lambda x: unique_val_to_cluster_id[x])
    full_df['narrow_cluster_value'] = ''
    full_df['narrow_cluster_value_class'] = ''
    for cluster_id in full_df.narrow_cluster_id.unique():
        cluster_df = full_df[full_df.narrow_cluster_id == cluster_id]
        cluster_id_prefixes = cluster_df.id.apply(lambda x: x.split("_")[0])
        prefix_counts = cluster_id_prefixes.value_counts()
        formatted_prefix_counts = [f"{prefix}({count})" for prefix, count in prefix_counts.items()]
        if len(cluster_df) >= 2:
            print(f"Cluster {cluster_id}::{';'.join(formatted_prefix_counts)}#{cluster_df.value.nunique()} {'||'.join(cluster_df.value.unique())}")
        # pick the longest unique value as the cluster value
        longest_value_idx = cluster_df.value.apply(len).idxmax()
        if 'use' in prefix_counts.index:
            full_df.loc[cluster_df.index, 'narrow_cluster_value_class'] = 'use'
        elif 'perf' in prefix_counts.index:
            full_df.loc[cluster_df.index, 'narrow_cluster_value_class'] = 'perf'
        else:
            full_df.loc[cluster_df.index, 'narrow_cluster_value_class'] = 'attr'
        full_df.loc[cluster_df.index, 'narrow_cluster_value'] = full_df.unique_value.iloc[longest_value_idx]
    full_df['km_cluster_id'] = ''
    for class_name in ['use', 'attr', 'perf']:
        class_df = full_df[full_df['narrow_cluster_value_class'] == class_name]
        unique_cluster_values = class_df['narrow_cluster_value'].unique()
        target_group_size_for_class = target_group_size[class_name]
        if len(unique_cluster_values)//target_group_size_for_class > 1:
            class_cluster_ids = km_cluster_keys(unique_cluster_values, target_group_size=target_group_size_for_class)
        else:
            class_cluster_ids = [0]*len(unique_cluster_values)
        km_ids = [f"km_{class_name}_{i}" for i in class_cluster_ids]
        uniq_val_to_cluster_id = dict(zip(unique_cluster_values, km_ids))
        full_df.loc[class_df.index, 'km_cluster_id'] = class_df['narrow_cluster_value'].apply(lambda x: uniq_val_to_cluster_id[x])
    return full_df

CATEGORY_MAP = {
    'attr': 'a specific component or physical property',
    'perf': 'a specific performance or behavior',
    # 'attr+perf': 'a specific attribute or performance',
    'use': 'a specific application, applicable object, method, tool, or environment'
}

def get_merged_hier_df(attr_perf_dict, use_dict, out_suffix, level=None, target_group_size = {'attr': 80, 'perf': 80, 'use': 120},prompt_file=None, prompt_file_dict=None, with_examples=False, shuffle=False, extract_english=False):
    level_display = "all levels" if level is None else f"level={level}"
    print(f"Merging at {level_display} for output {out_suffix}; with_examples={with_examples}")
    attr_dict = attr_perf_dict['attr']
    perf_dict = attr_perf_dict['perf']
    full_df = get_clustered_input_df_from_merged(attr_dict, perf_dict, use_dict, level=level, target_group_size=target_group_size, with_examples=with_examples)
    if prompt_file:
        prompt = get_prompt_from_path(prompt_file)
        prompt_dict = {'attr': prompt, 'perf': prompt, 'use': prompt}
    else:
        prompt_dict = {in_class: get_prompt_from_path(p_file) for in_class, p_file in prompt_file_dict.items()}

    all_inputs = []
    for km_cluster_id, group in full_df.groupby('km_cluster_id'):
        uniq_vals = group.narrow_cluster_value.unique().tolist()  # Convert to list
        if shuffle:
            random.shuffle(uniq_vals)  # Shuffle the list
        input_str = '\n'.join([f"{i}: {v}" for i, v in enumerate(uniq_vals)])
        in_class = group['narrow_cluster_value_class'].iloc[0]
        # if in_class == 'use':
        #     prompted_input = prompt_extract_2_level.replace('{{PRODUCT}}', PRODUCT_NAME).replace('{{CATEGORY}}', CATEGORY_MAP[in_class]).replace('{{INPUT}}', input_str)
        # else:
        #     # in_class = 'attr+perf'
        #     prompted_input = prompt_extract_3_level.replace('{{PRODUCT}}', PRODUCT_NAME).replace('{{CATEGORY}}', CATEGORY_MAP[in_class]).replace('{{INPUT}}', input_str)
        prompt = prompt_dict[in_class]
        prompted_input = prompt.replace('{{PRODUCT}}', PRODUCT_NAME).replace('{{CATEGORY}}', CATEGORY_MAP[in_class]).replace('{{INPUT}}', input_str)
        uniq_val_idx_to_orig_vals_list = {idx: group[group.narrow_cluster_value == val].orig_vals.tolist() for idx, val in enumerate(uniq_vals)}
        all_inputs.append({'input': input_str, 'prompted_input': prompted_input, 'in_class': in_class, 'id_val_map': json.dumps(uniq_val_idx_to_orig_vals_list)})
    input_df = pd.DataFrame(all_inputs)
    print(f">>>>>>>>> Running {len(input_df)} inputs with [[[LLM {model_name}]]] <<<<<<<<")
    out_df = run_with_prompted_inputs(input_df, 'prompted_input', model, out_folder=OUTPUT_DIR, output_prefix=f'merged_hier_{out_suffix}', batch_size=5)
    out_df.to_excel(os.path.join(OUTPUT_DIR, f'merged_hier_{out_suffix}.xlsx'), index=False)
    out_df = pd.read_excel(os.path.join(OUTPUT_DIR, f'merged_hier_{out_suffix}.xlsx'))

    attr_perf_dict, use_dict = merge_merged_jsons(out_df, f'merged_hier_{out_suffix}')
    cleaned_attr_perf_dict = clean_up_dict_by_path_stems(attr_perf_dict, extract_english)
    cleaned_use_dict = clean_up_dict_by_path_stems(use_dict, extract_english)
    json.dump(cleaned_attr_perf_dict, open(os.path.join(OUTPUT_DIR, f'cleaned_attr_perf_dict_{out_suffix}.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    json.dump(cleaned_use_dict, open(os.path.join(OUTPUT_DIR, f'cleaned_use_dict_{out_suffix}.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    return attr_perf_dict, use_dict

def extract_content_in_parentheses(s):
    # Find the position of the first opening parenthesis
    open_pos = s.find('(')
    if open_pos == -1:
        return s
    
    right_pos = s.rfind(')')
    if right_pos == -1:
        return s
    return s[open_pos+1:right_pos]

def get_path_stems(path, extract_english=False):
    """Convert a path list into a sorted set of stemmed words, excluding stop words."""
    
    all_stems = []
    for segment in path:
        if extract_english:
            words = split_string(extract_content_in_parentheses(segment.lower()))
        else:
            words = split_string(segment.lower())
        stems = [stem_with_cache(word) for word in words if word not in stop_words]
        all_stems.extend(stems)
    return tuple(sorted(set(all_stems)))

def get_stem_set(key, extract_english=False):
    if extract_english:
        words = split_string(extract_content_in_parentheses(key.lower()))
    else:
        words = split_string(key.lower())
    stems = [stem_with_cache(word) for word in words if word not in stop_words]
    return set(stems)

def split_by_parentheses(s):
    # Find the position of the first opening parenthesis
    open_pos = s.find('(')
    if open_pos == -1:
        return s, ''
    close_pos = s.rfind(')')
    if close_pos == -1:
        return s, ''
    return s[:open_pos], s[open_pos+1:close_pos]


def merge_matching_paths(d, current_path=None, extract_english=False):
    """
    Recursively traverse dictionary and merge entries with matching stemmed paths.
    Returns (cleaned_dict, paths_to_stems_map)
    """
    if current_path is None:
        current_path = []
    
    if not isinstance(d, dict):
        return d, {tuple(current_path): get_path_stems(current_path, extract_english)}
    
    # First pass: recursively clean children and collect path information
    cleaned = {}
    paths_map = {}
    
    for k, v in d.items():
        new_path = current_path + [k]
        paths_map[tuple(new_path)] = get_path_stems(new_path, extract_english)
        cleaned_child, child_paths = merge_matching_paths(v, new_path, extract_english)
        cleaned[k] = cleaned_child
        paths_map.update(child_paths)

    
    # Second pass: identify and merge paths with matching stems
    stems_to_paths = defaultdict(list)
    for path, stems in paths_map.items():
        stems_to_paths[stems].append(path)
    
    # Merge paths with matching stems
    for stems, matching_paths in stems_to_paths.items():
        if len(matching_paths) > 1:
            # Print original paths being merged
            print("\nMerging paths with matching stems:")
            for path in matching_paths:
                print(f"  - {' -> '.join(path)}")
            
            # Get the values at each path
            values = []
            for path in matching_paths:
                curr = cleaned
                for segment in path[len(current_path):-1]:  # Navigate to parent
                    if segment in curr:
                        curr = curr[segment]
                if path[-1] in curr:
                    values.append(curr[path[-1]])
                    del curr[path[-1]]  # Remove old entry
            
            # Only merge if we actually collected values
            if values:  # Add this check
                # Merge values
                merged_value = values[0]
                for val in values[1:]:
                    merged_value = merge_values(merged_value, val)
                
                # Use shortest path as target
                shortest_path = min(matching_paths, key=len)
                print(f"Using shortest path as target: {' -> '.join(shortest_path)}\n")
                
                curr = cleaned
                for segment in shortest_path[len(current_path):-1]:
                    if segment not in curr:
                        curr[segment] = {}
                    curr = curr[segment]
                curr[shortest_path[-1]] = merged_value
    
    # # Create a deep copy to avoid modifying what we're iterating over
    # final_cleaned = copy.deepcopy(cleaned)
    # final_paths_map = copy.deepcopy(paths_map)
    # for k, v in cleaned.items():
    #     if isinstance(v, dict):
    #         if len(v) == 1:
    #             child_key = list(v.keys())[0]
    #             child_value = v[child_key]
    #             if extract_english:
    #                 parent_out, parent_in = split_by_parentheses(k)
    #                 child_out, child_in = split_by_parentheses(child_key)
    #                 if child_in or parent_in:
    #                     parent_in_stem = get_stem_set(parent_in, extract_english)
    #                     child_in_stem = get_stem_set(child_in, extract_english)
    #                     if parent_in_stem.issubset(child_in_stem):
    #                         merged_key = child_key
    #                     elif child_in_stem.issubset(parent_in_stem):
    #                         merged_key = k
    #                     else:
    #                         merged_key = f"{parent_out} : {child_out} ({child_in} {parent_in})"
    #                 else:
    #                     merged_key = f"{parent_out} : {child_out}"
    #             else:
    #                 path_stem = set(get_path_stems(current_path+[k], extract_english))
    #                 child_stem = get_stem_set(child_key, extract_english)
    #                 if path_stem.issubset(child_stem):
    #                     merged_key = child_key
    #                 elif child_stem.issubset(path_stem):
    #                     merged_key = k
    #                 else:
    #                     merged_key = f"{k} : {child_key}"
    #             final_cleaned[merged_key] = child_value
    #             if merged_key != k:
    #                 del final_cleaned[k]
    #             print(f'Merging "{k}" and "{child_key}" into "{merged_key}"')
    #             final_paths_map[tuple(current_path + [merged_key])] = get_path_stems(current_path + [merged_key], extract_english)
    #             del final_paths_map[tuple(current_path + [k, child_key])]
    #         else:
    #             path_stem = set(get_path_stems(current_path+[k], extract_english))
    #             for child_key, child_value in v.items():
    #                 child_stem = get_stem_set(child_key, extract_english)
    #                 if path_stem.issubset(child_stem) or child_stem.issubset(path_stem):
    #                     if isinstance(child_value, dict):
    #                         final_cleaned[k].update(child_value)
    #                         del final_cleaned[k][child_key]
    #                         print(f'Merging "{child_key}" into "{" -> ".join(current_path+[k])}"')
    #                         del final_paths_map[tuple(current_path + [k, child_key])]
    #                         final_paths_map[tuple(current_path + [k])] = get_path_stems(current_path + [k], extract_english)
        
    return  cleaned, paths_map

def clean_up_dict_by_path_stems(in_dict, extract_english=False):
    """
    Clean up dictionary by merging entries with matching stemmed paths.
    """
    cleaned_dict, _ = merge_matching_paths(in_dict, extract_english=extract_english)
    return cleaned_dict

model_name="claude-3-5-sonnet-20241022"
model = partial(claude, model=model_name)
if __name__ == '__main__':
    df = pd.read_excel("/Users/maoc/MIT Dropbox/Chengfeng Mao/JMP/UX168 data and code/tmp/smart_switches/multiple_review_hierarchy-MRO_v4_claude-3-5-sonnet-20240620_0-224.xlsx")
    df['json_response'] = df.response.apply(parse_label)
    attr_dict, perf_dict, use_dict, attr_id_to_values, perf_id_to_values, use_id_to_values, attr_id_to_detail, perf_id_to_detail = merge_jsons(df)
    json.dump(attr_dict, open(os.path.join(OUTPUT_DIR, 'attr_dict.json'), 'w'))
    json.dump(perf_dict, open(os.path.join(OUTPUT_DIR, 'perf_dict.json'), 'w'))
    json.dump(use_dict, open(os.path.join(OUTPUT_DIR, 'use_dict.json'), 'w'))
    json.dump(attr_id_to_values, open(os.path.join(OUTPUT_DIR, 'attr_id_to_values.json'), 'w'))
    json.dump(perf_id_to_values, open(os.path.join(OUTPUT_DIR, 'perf_id_to_values.json'), 'w'))
    json.dump(use_id_to_values, open(os.path.join(OUTPUT_DIR, 'use_id_to_values.json'), 'w'))
    json.dump(attr_id_to_detail, open(os.path.join(OUTPUT_DIR, 'attr_id_to_detail.json'), 'w'))
    json.dump(perf_id_to_detail, open(os.path.join(OUTPUT_DIR, 'perf_id_to_detail.json'), 'w'))

    attr_perf_dict_it0 = {'attr': attr_dict, 'perf': perf_dict}
    attr_perf_dict_it1, use_dict_it1 = get_merged_hier_df(attr_perf_dict_it0, use_dict, out_suffix='it1', level=None, target_group_size={'attr': 60, 'perf': 60, 'use': 60}, prompt_file_dict={'attr': 'merge_attr_hier_extract_3_level_MRO_v2', 'perf': 'merge_perf_hier_extract_3_level_MRO_v2', 'use': 'merge_use_hier_extract_3_level_MRO_v2'},
    with_examples=False) 
    attr_perf_dict_it1 = json.load(open(os.path.join(OUTPUT_DIR, 'cleaned_attr_perf_dict_it1.json'), 'r'))
    use_dict_it1 = json.load(open(os.path.join(OUTPUT_DIR, 'cleaned_use_dict_it1.json'), 'r'))
    attr_perf_dict_it2, use_dict_it2 = get_merged_hier_df(attr_perf_dict_it1, use_dict_it1, out_suffix='it2', level=2, target_group_size={'attr': 60, 'perf': 60, 'use': 60}, prompt_file_dict={'attr': 'merge_attr_hier_extract_2_level_MRO_v2', 'perf': 'merge_perf_hier_extract_2_level_MRO_v2', 'use': 'merge_use_hier_extract_2_level_MRO_v2'}, with_examples=False)
    attr_perf_dict_it2 = json.load(open(os.path.join(OUTPUT_DIR, 'cleaned_attr_perf_dict_it2.json'), 'r'))
    use_dict_it2 = json.load(open(os.path.join(OUTPUT_DIR, 'cleaned_use_dict_it2.json'), 'r'))
    attr_perf_dict_it3_CN, use_dict_it3_CN = get_merged_hier_df(attr_perf_dict_it2, use_dict_it2, out_suffix='it3_CN', level=None, target_group_size={'attr': 60, 'perf': 60, 'use': 60}, prompt_file_dict={'attr': 'merge_attr_hier_extract_3_level_MRO_CN_v1', 'perf': 'merge_perf_hier_extract_3_level_MRO_CN_v1', 'use': 'merge_use_hier_extract_3_level_MRO_CN_v1'}, with_examples=False, extract_english=True)
    






    

    
    

    







    
    