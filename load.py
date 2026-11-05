import os


def load_data(merge_tables):
    os.makedirs("parquet_data", exist_ok=True)

    for name, table in merge_tables.items():
        file_path = f"parquet_data/{name}.parquet"
        table.write_parquet(file_path)
        #print(f"✅ {name} saved successfully -> {file_path}")