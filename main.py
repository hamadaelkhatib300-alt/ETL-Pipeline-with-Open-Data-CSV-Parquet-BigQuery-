from extract import extract_data
from transform import transform, merge_tables
from load import load_data

datasets = extract_data()
datasets = transform(datasets)
mergetables = merge_tables(datasets)
load_data(mergetables)


