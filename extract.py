import polars as pl

customers = pl.read_csv("Datasets/olist_customers.csv")
orders = pl.read_csv("Datasets/olist_orders.csv")
order_items = pl.read_csv("Datasets/olist_order_items.csv")
products = pl.read_csv("Datasets/olist_products.csv")
payments = pl.read_csv("Datasets/olist_order_payments.csv")
reviews = pl.read_csv("Datasets/olist_order_reviews.csv")
sellers = pl.read_csv("Datasets/olist_sellers.csv")

def extract_data():
    datasets = {
        "Orders": orders,
        "Customers": customers,
        "Order Items": order_items,
        "Products": products,
        "Payments": payments,
        "Reviews": reviews,
        "Sellers": sellers
    }
    return datasets

def explore_data(df):
    print("=" * 100)
    print("\nShape:", df.shape)
    print("Columns:", df.columns)
    print("Data Types:", df.dtypes)
    print("Missing Values:", df.null_count())
    print(df.head())

def all_data_explore(datasets):
    for name, df in datasets.items():
        print("=" * 20, "\n", name,"Dataset", "\n", "=" * 20)
        print("\nShape:", df.shape)
        print("Columns:", df.columns)
        print("Data Types:", df.dtypes)
        print("Missing Values sum:", df.null_count().sum_horizontal().item())
        print("Missing Values:", df.null_count())
        print("First 5 Rows:", df.head())
        print("\n")

#explore_data(sellers)