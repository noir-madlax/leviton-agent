import os
from pandarallel import pandarallel
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from collections import Counter
import numpy as np
import pandas as pd
import string

# Initialize global variables
nltk.download('stopwords')
pandarallel.initialize(progress_bar=True)
ps = PorterStemmer()
stop_words = set(stopwords.words('english'))

def get_stems(text):
    tokens = word_tokenize(str(text).lower())
    return {ps.stem(token) for token in tokens 
            if not all(char in string.punctuation for char in token) 
            and token not in stop_words}

def calculate_stem_info(df):
    # Calculate stem frequencies across the entire corpus
    all_stems = Counter()
    total_stem_occurrences = 0
    
    for stems_set in df['stems']:
        for stem in stems_set:
            all_stems[stem] += 1
            total_stem_occurrences += 1
    
    # Calculate information content for each stem
    stem_info = {}
    for stem, count in all_stems.items():
        probability = count / total_stem_occurrences
        information_content = -np.log2(probability)
        stem_info[stem] = information_content
    
    return stem_info

def calculate_total_information(stems, stem_info):
    return sum(stem_info.get(stem, 0) for stem in stems)

def get_stems_without_numbers(text):
    """Get stems excluding any tokens that contain numbers"""
    tokens = word_tokenize(str(text).lower())
    return {ps.stem(token) for token in tokens 
            if not any(char.isdigit() for char in token)
            and not all(char in string.punctuation for char in token) 
            and token not in stop_words}

def group_by_title_stems(df, min_group_size=10):
    """Group titles by their stemmed words and filter small groups"""
    init_len = len(df)
    df = df.dropna(subset='title')
    # Get stems for titles
    df['title_stems'] = df['title'].parallel_apply(get_stems_without_numbers)
    
    # Convert stems to sorted tuple for grouping
    df['title_stems_sorted'] = df['title_stems'].apply(lambda x: tuple(sorted(x)))
    
    # Group by sorted stems and get group sizes
    group_sizes = df.groupby('title_stems_sorted').size()
    valid_groups = group_sizes[group_sizes >= min_group_size].index
    
    # Filter df to keep only reviews in valid groups
    df = df[df['title_stems_sorted'].isin(valid_groups)]
    
    # Add group ID
    df['title_group_id'] = pd.factorize(df['title_stems_sorted'])[0]
    
    df = df.drop(['title_stems_sorted'], axis=1)
    final_len = len(df)

    print(f"{(init_len-final_len)/init_len*100}% of the reviews dropped due to too few reviews per group")
    return df


def filter_reviews(input_path, min_year=2021, min_information=30, min_group_size=10):
    # Read data
    df = pd.read_excel(input_path)
    
    # Filter by year
    df['year'] = pd.to_datetime(df['review_date']).dt.year
    df = df[df['year'] >= min_year]
    
    # Process text
    df['combined_text'] = df['title'].fillna('') + ' ' + df['评论内容'].fillna('')
    df['stems'] = df['combined_text'].parallel_apply(get_stems)
    df['stem_count'] = df['stems'].parallel_apply(len)
    
    # Calculate and apply information content filter
    stem_info = calculate_stem_info(df)
    df['stem_information'] = df['stems'].parallel_apply(
        lambda x: calculate_total_information(x, stem_info)
    )
    df = df[df['stem_information'] > min_information]
    df = group_by_title_stems(df, min_group_size)

    return df


if __name__ == "__main__":
    input_path = "/Users/maoc/Dropbox (MIT)/JMP/UX168 data and code/data/raw/电线电缆_495310_asin_review明细.xlsx"
    min_year = 2020
    min_information = 30
    min_group_size = 20
    
    # Generate output filename based on filtering conditions
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{base_name}_filtered_yr{min_year}_info{min_information}_group{min_group_size}.xlsx"
    output_path = os.path.join(os.path.dirname(input_path), "filtered", output_filename)
    
    # Create processed directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Filter and save
    filtered_df = filter_reviews(input_path, min_year, min_information, min_group_size)
    filtered_df.to_excel(output_path, index=False)
    print(f"Filtered data saved to: {output_path}")