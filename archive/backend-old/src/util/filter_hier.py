import json
import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from collections import defaultdict
from typing import Dict, List, Union, Any
from nltk.stem import PorterStemmer
import re
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
stop_words.remove('no')
stop_words.remove('not')


stemmer = PorterStemmer()

# split string by all punctuations and spaces
def split_string(s):
    return [word for word in re.split(r'[^\w]+|_', s) if word]

stem_cache = {}
def stem_with_cache(word):
    if word not in stem_cache:
        stem_cache[word] = stemmer.stem(word)
    return stem_cache[word]

def merge_values(val1, val2):
    if val1 is None or len(val1) == 0:
        return val2
    if val2 is None or len(val2) == 0:
        return val1
    if isinstance(val1, int) or isinstance(val1, str):
        val1 = [val1]
    if isinstance(val2, int) or isinstance(val2, str):
        val2 = [val2]
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

def analyze_hierarchy_terms(
    hierarchies: Union[Dict, List[Dict]], 
    min_similarity: float = 0.6,
    model_name: str = 'all-MiniLM-L6-v2'
) -> pd.DataFrame:
    """
    Analyze terms in hierarchical JSON data, cluster similar terms, and create a DataFrame
    with cluster assignments and path information.
    
    Args:
        hierarchies: Single hierarchy dict or list of hierarchy dicts
        min_similarity: Minimum similarity threshold for clustering (default: 0.6)
        model_name: Name of the sentence-transformer model to use
    
    Returns:
        DataFrame with columns: cluster_id, term (where term contains dict of {term: paths})
    """
    
    def collect_terms(
        data: Dict[str, Any], 
        current_path: List[str], 
        terms_dict: Dict[str, List[str]]
    ) -> None:
        """
        Recursively collect terms and their paths from the hierarchy.
        
        Args:
            data: Current level of the hierarchy
            current_path: List of terms leading to current position
            terms_dict: Dictionary to store terms and their paths
        """
        for key, value in data.items():
            # Convert current path to string format
            path_str = "=>".join(current_path) if current_path else ""
            
            # Add the current term and its path
            if key not in terms_dict:
                terms_dict[key] = []
            if path_str:
                terms_dict[key].append(path_str)
                
            # Recurse if value is a dictionary
            if isinstance(value, dict):
                collect_terms(value, current_path + [key], terms_dict)
            # Handle leaf nodes that are lists of attributes
            elif isinstance(value, list):
                # If the list contains attribute IDs, we don't process them
                continue
            # Handle leaf nodes that are single attributes
            elif isinstance(value, str) and value.startswith('ATTR_'):
                continue

    def cluster_terms(
        terms: List[str], 
        min_similarity: float,
        model: SentenceTransformer
    ) -> np.ndarray:
        """
        Cluster terms based on their sentence embeddings.
        
        Args:
            terms: List of terms to cluster
            min_similarity: Minimum similarity threshold
            model: Sentence transformer model
            
        Returns:
            Array of cluster assignments
        """
        # Generate embeddings
        embeddings = model.encode(terms)
        
        # Calculate distance threshold from similarity threshold
        # Cosine similarity = 1 - distance
        distance_threshold = 1 - min_similarity
        
        # Perform hierarchical clustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric='cosine',
            linkage='complete'
        )
        
        return clustering.fit_predict(embeddings)

    # Initialize sentence transformer model
    model = SentenceTransformer(model_name)
    
    # Convert single hierarchy to list
    if isinstance(hierarchies, dict):
        hierarchies = [hierarchies]
    
    # Collect terms and paths from all hierarchies
    terms_dict = defaultdict(list)
    for hierarchy in hierarchies:
        collect_terms(hierarchy, [], terms_dict)
    
    # Get unique terms
    unique_terms = list(terms_dict.keys())
    
    if not unique_terms:
        return pd.DataFrame(columns=['cluster_id', 'term'])
    
    # Perform clustering
    cluster_assignments = cluster_terms(unique_terms, min_similarity, model)
    
    # Create term dictionaries for each cluster
    cluster_terms_dict = defaultdict(dict)
    for term, cluster_id in zip(unique_terms, cluster_assignments):
        cluster_terms_dict[int(cluster_id)][term] = terms_dict[term]
    
    # Create DataFrame
    df_data = [
        {'cluster_id': cluster_id, 'term': terms}
        for cluster_id, terms in cluster_terms_dict.items()
    ]
    
    df = pd.DataFrame(df_data)
    df = df.sort_values('cluster_id').reset_index(drop=True)
    
    return df


# Example usage and testing function
def print_df(df):    
    # Print detailed information about each cluster
    for _, row in df.iterrows():
        print(f"\nCluster {row['cluster_id']}:")
        for term, paths in row['term'].items():
            print(f"  Term: {term}")
            print(f"  Paths: {paths}")
            print()
            

def get_all_paths(d, current_path=None):
    """Get all paths in a dictionary with their values."""
    if current_path is None:
        current_path = []
    paths = {}
    
    if not isinstance(d, dict):
        paths[tuple(current_path)] = d
        return paths
        
    for k, v in d.items():
        paths.update(get_all_paths(v, current_path + [k]))
    return paths

def get_path_stems(path):
    """Convert a path into sorted unique stems, excluding stop words."""
    all_stems = []
    for segment in path:
        words = split_string(segment.lower())
        stems = [stem_with_cache(word) for word in words if word not in stop_words]
        all_stems.extend(stems)
    return tuple(sorted(set(all_stems)))

def get_path_str(path):
    """Convert path tuple to string representation."""
    return ' -> '.join(path)

def set_value_at_path(d, path, value):
    """Set a value at a specific path in a dictionary."""
    current = d
    for segment in path[:-1]:
        if segment not in current:
            current[segment] = {}
        current = current[segment]
    current[path[-1]] = value

def determine_target_dict(types, dicts):
    """Determine target dictionary and type based on priority rules."""
    target_type = 'use' if 'use' in types else \
                 'perf' if 'perf' in types else 'attr'
    return dicts[target_type], target_type

def merge_path_group(paths_group, target_dict, label=""):
    """Merge a group of paths and their values into target dictionary."""
    if len(paths_group) <= 1:
        return paths_group[0] if paths_group else None
        
    all_paths = [p[0] for p in paths_group]
    merged_value = None
    
    print(f"\n{label}:")
    for path, _, type_name in paths_group:
        print(f"  - [{type_name}] {get_path_str(path)}")
        
    for _, value, _ in paths_group:
        merged_value = merge_values(merged_value, value)
        
    target_path = min(all_paths, key=len)
    print(f"Using shortest path as target: {get_path_str(target_path)}")
    set_value_at_path(target_dict, target_path, merged_value)
    
    return target_path, merged_value, paths_group[0][2]

def merge_by_stems(attr_dict, perf_dict, use_dict):
    """
    First stage: Merge paths based on exact stem matches.
    Returns merged dictionaries and all merged paths for clustering.
    """
    # Get all paths from each dictionary
    all_paths = {
        'attr': get_all_paths(attr_dict),
        'perf': get_all_paths(perf_dict),
        'use': get_all_paths(use_dict)
    }

    # Group paths by stems
    stems_to_paths = defaultdict(lambda: {'attr': [], 'perf': [], 'use': []})
    for dict_type, paths in all_paths.items():
        for path, value in paths.items():
            stems_to_paths[get_path_stems(path)][dict_type].append((path, value))

    # Create intermediate dictionaries
    merged_dicts = {
        'attr': {},
        'perf': {},
        'use': {}
    }
    
    all_merged_paths = []
    
    # Process each group of matching stems
    for stems, type_paths in stems_to_paths.items():
        total_paths = sum(len(paths) for paths in type_paths.values())
        paths_group = []
        
        for type_name, paths in type_paths.items():
            for path, value in paths:
                paths_group.append((path, value, type_name))
                
        if total_paths > 1:
            target_dict, _ = determine_target_dict(
                {p[2] for p in paths_group}, 
                merged_dicts
            )
            result = merge_path_group(
                paths_group, 
                target_dict, 
                f"Merging paths with matching stems {stems}"
            )
            if result:
                all_merged_paths.append(result)
        else:
            for path, value, type_name in paths_group:
                set_value_at_path(merged_dicts[type_name], path, value)
                all_merged_paths.append((path, value, type_name))
                
    return merged_dicts, all_merged_paths

def cluster_paths(merged_paths, threshold=0.02):
    """
    Second stage: Cluster paths based on semantic similarity.
    Returns clustered path groups.
    """
    if not merged_paths:
        return {}
        
    path_strs = [get_path_str(p[0]) for p in merged_paths]
    cluster_ids = cluster_keys(path_strs, threshold=threshold)
    
    # Group paths by cluster
    clusters = defaultdict(list)
    for path_info, cluster_id in zip(merged_paths, cluster_ids):
        clusters[cluster_id].append(path_info)
        
    return clusters

def merge_clusters(clusters):
    """
    Third stage: Merge paths within each cluster.
    Returns final merged dictionaries.
    """
    final_dicts = {
        'attr': {},
        'perf': {},
        'use': {}
    }

    # Process each cluster
    for cluster_id, cluster_paths in clusters.items():
        target_dict, _ = determine_target_dict(
            {p[2] for p in cluster_paths}, 
            final_dicts
        )
        if len(cluster_paths) > 1:
            merge_path_group(
                cluster_paths, 
                target_dict, 
                f"Clustering similar paths (cluster {cluster_id})"
            )
        else:
            path, value, type_name = cluster_paths[0]
            set_value_at_path(final_dicts[type_name], path, value)

    return final_dicts['attr'], final_dicts['perf'], final_dicts['use']

def unified_cleanup(attr_dict, perf_dict, use_dict):
    """
    Main function that coordinates the entire cleanup process.
    """
    # Stage 1: Merge by stems
    merged_dicts, merged_paths = merge_by_stems(attr_dict, perf_dict, use_dict)
    
    if not merged_paths:
        return merged_dicts['attr'], merged_dicts['perf'], merged_dicts['use']
    
    # Stage 2: Cluster paths
    clusters = cluster_paths(merged_paths)
    
    # Stage 3: Merge clusters
    return *merge_clusters(clusters), merged_dicts, merged_paths, clusters

if __name__ == '__main__':
    PRODUCT = 'Cables_495310_v2'
    PRODUCT_NAME = 'cables and cords'
    OUTPUT_DIR = os.path.join("/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/tmp", f"{PRODUCT}_hierarchy_merged")
    attr_dict = json.load(open("/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/tmp/Cables_495310_v2_hierarchy_merged/attr_dict.json"))
    perf_dict = json.load(open("/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/tmp/Cables_495310_v2_hierarchy_merged/perf_dict.json"))
    use_dict = json.load(open("/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/tmp/Cables_495310_v2_hierarchy_merged/use_dict.json"))
    attr_dict_cleaned, perf_dict_cleaned, use_dict_cleaned, merged_dicts, merged_paths, clusters = unified_cleanup(attr_dict, perf_dict, use_dict)
    clusters = cluster_paths(merged_paths, 0.4)
    import matplotlib.pyplot as plt
    # Create the histogram
    plt.hist([len(v) for v in clusters.values()], bins=30)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Histogram Example')
    plt.show()
    print(clusters)