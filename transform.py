import polars as pl
from extract import all_data_explore
def clean_orders(df):
    df = df.unique()
    #df = df.unique(subset=["order_id"])
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    df = df.with_columns([
        pl.col(col).str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False)
        for col in date_columns
    ])
    df = df.filter(
        pl.col("order_delivered_customer_date").is_not_null()
    )
    df = df.with_columns([
        (
            pl.col("order_delivered_customer_date") -
            pl.col("order_purchase_timestamp")
        ).dt.total_days().alias("delivery_days"),

        (
            pl.col("order_delivered_customer_date") >
            pl.col("order_estimated_delivery_date")
        ).alias("late_delivery"),
    ])

    return df

def clean_customers(df):
    df = df.unique()
    #df = df.unique(subset=["customer_id"])
    df = df.with_columns([
        pl.col("customer_city").str.strip_chars().str.to_lowercase(),
        pl.col("customer_state").str.strip_chars().str.to_lowercase()
    ])

    return df


def clean_order_items(df):
    df = df.unique()
    #df = df.unique(
    #    subset=["order_id", "order_item_id"]
    #)
    df = df.with_columns(
        pl.col("shipping_limit_date").str.to_datetime("%Y-%m-%d %H:%M:%S")
    )
    df = df.with_columns(
        pl.col("order_item_id")
        .cast(pl.String)
    )
    df = df.with_columns(
        (pl.col("price") + pl.col("freight_value")).alias("total_price")
    )
    df = df.filter(
        (pl.col("price") > 0) &
        (pl.col("freight_value") >= 0)
    )

    return df

def clean_products(df):
    df = df.unique()
    #df = df.unique(subset=["product_id"])
    df = df.rename({
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length"
    })
    df = df.drop_nulls(
        subset=[
            "product_category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty"
        ]
    )
    numeric_cols = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    ]
    df = df.with_columns([
        pl.col(col).fill_null(pl.col(col).median())
        for col in numeric_cols
    ])
    df = df.with_columns(pl.col("product_category_name").str.to_lowercase().str.strip_chars())
    return df


def clean_payments(df):
    df = df.unique()
    df = df.filter(
        (pl.col("payment_installments") >= 0)
        &(pl.col("payment_value") > 0)
    )
    df = df.with_columns(
        pl.col("payment_type").str.to_lowercase().str.strip_chars().cast(pl.Categorical)
    )
    return df


def clean_reviews(df):
    df = df.filter()
    df = df.unique()
    #df = df.select(pl.col("review_id").n_unique())
    df = df.with_columns([
        pl.col("review_comment_title")
        .fill_null("No Title"),

        pl.col("review_comment_message")
        .fill_null("No Comment")
    ])
    df = df.with_columns([
        pl.col("review_creation_date")
        .str.to_datetime("%Y-%m-%d %H:%M:%S"),

        pl.col("review_answer_timestamp")
        .str.to_datetime("%Y-%m-%d %H:%M:%S")
    ])
    df = df.filter(
        (pl.col("review_score") > 1) &
        (pl.col("review_score") < 5)
    )
    df = df.with_columns(
        pl.when(pl.col("review_score") >= 4)
        .then(pl.lit("positive"))
        .when(pl.col("review_score") == 3)
        .then(pl.lit("neutral"))
        .otherwise(pl.lit("negative"))
        .alias("sentiment")
    )
    return df


def clean_sellers(df):

    df = df.unique(subset=["seller_id"])

    df = df.with_columns([
        pl.col("seller_city").str.strip_chars().str.to_lowercase(),

        pl.col("seller_state").str.strip_chars().str.to_lowercase().cast(pl.Categorical)
    ])

    df = df.filter(
        pl.col("seller_zip_code_prefix") > 0
    )

    return df

def transform(datasets):

    datasets["Orders"] = clean_orders(datasets["Orders"])
    datasets["Customers"] = clean_customers(datasets["Customers"])
    datasets["Order Items"] = clean_order_items(datasets["Order Items"])
    datasets["Products"] = clean_products(datasets["Products"])
    datasets["Payments"] = clean_payments(datasets["Payments"])
    datasets["Reviews"] = clean_reviews(datasets["Reviews"])
    datasets["Sellers"] = clean_sellers(datasets["Sellers"])

    return datasets


def merge_tables(datasets):

    order_Customers = (
        datasets["Orders"]
        .join(
            datasets["Customers"],
            on="customer_id",
            how="left"
        ).select([
            "order_id",
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",  #x
            "order_delivered_customer_date", #x
            "order_estimated_delivery_date", #x
            "customer_zip_code_prefix",      #x
            "delivery_days",
            "late_delivery"
        ])
    )
    orderItems_product_sellers = (
        datasets["Order Items"]
        .join(
            datasets["Products"],
            on="product_id",
            how="left"
        )
        .join(
            datasets["Sellers"],
            on="seller_id",
            how="left"
        ).select([
            "order_id",
            "order_item_id",
            "product_id",
            "product_category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
            "shipping_limit_date",
            "price",
            "freight_value",
            "total_price"
        ])
    )
    payments_order = (
        datasets["Payments"]
        .join(
            datasets["Orders"].select(
                ["order_id", "customer_id", "order_status"]
            ),
            on="order_id",
            how="left"
        ).select([
            "order_id",
            "customer_id",
            "order_status",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value"
        ])
    )
    reviews_order = (
        datasets["Reviews"]
        .join(
            datasets["Orders"].select(
                ["order_id", "customer_id", "order_status"]
            ),
            on="order_id",
            how="left"
        ).select([
            "review_id",
            "order_id",
            "customer_id",
            "order_status",
            "review_score",
            "sentiment",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp"
        ])
    )

    orderItems_product_sellers = orderItems_product_sellers.drop_nulls(subset=["product_id", "product_category_name"])
    order_Customers = order_Customers.drop_nulls()
    reviews_order = reviews_order.drop_nulls()
    payments_order = payments_order.drop_nulls()


    #print(payments_order.schema)
    #print(payments_order.null_count().sum_horizontal().item())

    merged_tables = {
        "order_Customers": order_Customers,
        "orderItems_product_sellers": orderItems_product_sellers,
        "payments_order": payments_order,
        "reviews_order": reviews_order
    }
    #all_data_explore(merged_tables)

    return merged_tables







# def remove_outliers(df,column_name):
#  q1=df[column_name].quantile(0.25)
#  q3=df[column_name].quantile(0.75)
#  iqr=q3-q1
#  lower_bound=q1-1.5*iqr
#  upper_bound=q3+1.5*iqr
#  filtered_df = df[(df[column_name] >= lower_bound) & (df[column_name] <= upper_bound)]
#  return filtered_df
#
# def handle_outliers(data):
#
#     num_cols = data.select_dtypes(include="number").columns
#
#     for col in num_cols:
#
#         Q1=data[col].quantile(0.25)
#         Q3=data[col].quantile(0.75)
#         IQR=Q3-Q1
#
#         lower_bound=Q1-(1.5*IQR)
#         upper_bound=Q3+(1.5*IQR)
#
#         data[col]=np.where(data[col]<lower_bound,lower_bound,data[col])
#         data[col]=np.where(data[col]>upper_bound,upper_bound,data[col])