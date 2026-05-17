import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################

import json
import re
from smolagents import ToolCallingAgent, OpenAIServerModel, tool

dotenv.load_dotenv()

model = OpenAIServerModel(
    model_id=os.getenv("MODEL_ID"),
    api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
    api_base="https://openai.vocareum.com/v1",
)

# Maps common customer phrasing to exact catalog item names.
CUSTOMER_ITEM_ALIASES = {
    "a4 glossy paper": "Glossy paper",
    "glossy a4 paper": "Glossy paper",
    "a4 glossy": "Glossy paper",
    "glossy paper": "Glossy paper",
    "heavy cardstock": "Heavyweight paper",
    "heavyweight cardstock": "Heavyweight paper",
    "sturdy cardstock": "Cardstock",
    "white cardstock": "Cardstock",
    "cardstock": "Cardstock",
    "recycled cardstock": "250 gsm cardstock",
    "colored paper": "Colored paper",
    "colorful paper": "Colored paper",
    "colorful cardstock": "Cardstock",
    "colorful construction paper": "Construction paper",
    "construction paper": "Construction paper",
    "colorful poster paper": "Poster paper",
    "poster paper": "Poster paper",
    "poster board": "Large poster paper (24x36 inches)",
    "poster boards": "Large poster paper (24x36 inches)",
    "a4 paper": "A4 paper",
    "a4 white paper": "A4 paper",
    "a4 printer paper": "A4 paper",
    "a4 printing paper": "A4 paper",
    "a4 white printer paper": "A4 paper",
    "a4 matte paper": "Matte paper",
    "a4 matte": "Matte paper",
    "a3 glossy paper": "Glossy paper",
    "a3 matte paper": "Matte paper",
    "a3 colored paper": "Colored paper",
    "matte a3 paper": "Matte paper",
    "glossy a4": "Glossy paper",
    "standard printer paper": "Standard copy paper",
    "standard printing paper": "Standard copy paper",
    "white printer paper": "Standard copy paper",
    "printer paper": "Standard copy paper",
    "copy paper": "Standard copy paper",
    "a4 recycled paper": "Recycled paper",
    "a4 recycled": "Recycled paper",
    "recycled paper": "Recycled paper",
    "kraft paper": "Kraft paper",
    "envelopes": "Envelopes",
    "paper napkins": "Paper napkins",
    "table napkins": "Paper napkins",
    "paper cups": "Paper cups",
    "paper plates": "Paper plates",
    "party streamers": "Party streamers",
    "streamers": "Party streamers",
    "washi tape": "Decorative adhesive tape (washi tape)",
    "decorative washi tape": "Decorative adhesive tape (washi tape)",
    "flyers": "Flyers",
    "posters": "Flyers",
}


def _inventory_item_names() -> List[str]:
    return pd.read_sql("SELECT item_name FROM inventory", db_engine)["item_name"].tolist()


def resolve_item_name(item_name: str) -> tuple:
    """Resolve a customer item name to an exact inventory catalog name."""
    inventory_items = _inventory_item_names()
    cleaned = item_name.strip()
    if cleaned in inventory_items:
        return cleaned, ""

    key = cleaned.lower()
    if key in CUSTOMER_ITEM_ALIASES:
        candidate = CUSTOMER_ITEM_ALIASES[key]
        if candidate in inventory_items:
            return candidate, f"(mapped '{item_name}' to '{candidate}')"

    for alias, catalog_name in CUSTOMER_ITEM_ALIASES.items():
        if alias in key or key in alias:
            if catalog_name in inventory_items:
                return catalog_name, f"(mapped '{item_name}' to '{catalog_name}')"

    for name in inventory_items:
        if name.lower() == key:
            return name, ""

    best_match = None
    best_score = 0
    query_tokens = set(re.findall(r"[a-z0-9]+", key))
    for name in inventory_items:
        name_tokens = set(re.findall(r"[a-z0-9]+", name.lower()))
        overlap = len(query_tokens & name_tokens)
        if overlap > best_score:
            best_score = overlap
            best_match = name

    if best_match and best_score >= 2:
        return best_match, f"(matched '{item_name}' to '{best_match}')"

    return None, (
        f"Unknown item '{item_name}'. Available items: "
        f"{', '.join(sorted(inventory_items))}"
    )


def bulk_discount_rate(quantity: int) -> float:
    if quantity >= 1000:
        return 0.15
    if quantity >= 500:
        return 0.10
    if quantity >= 100:
        return 0.05
    return 0.0


def _get_unit_price(item_name: str) -> float:
    row = pd.read_sql(
        "SELECT unit_price FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": item_name},
    )
    if row.empty:
        for supply in paper_supplies:
            if supply["item_name"] == item_name:
                return float(supply["unit_price"])
        raise ValueError(f"No unit price for {item_name}")
    return float(row.iloc[0]["unit_price"])


# --- Inventory agent tools ---


@tool
def check_item_stock(item_name: str, as_of_date: str) -> str:
    """
    Check current stock for one catalog item as of a date.

    Args:
        item_name: Exact or customer-facing item name.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Stock summary for the item.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    stock_df = get_stock_level(resolved, as_of_date)
    stock = int(stock_df["current_stock"].iloc[0])
    min_row = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": resolved},
    )
    min_stock = int(min_row.iloc[0]["min_stock_level"]) if not min_row.empty else 0
    return json.dumps(
        {
            "item_name": resolved,
            "current_stock": stock,
            "min_stock_level": min_stock,
            "needs_reorder": stock < min_stock,
            "note": note,
        }
    )


@tool
def list_available_inventory(as_of_date: str) -> str:
    """
    List all items with positive stock as of a date.

    Args:
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: JSON inventory snapshot.
    """
    inventory = get_all_inventory(as_of_date)
    return json.dumps(inventory, indent=2)


@tool
def check_reorder_needed(item_name: str, as_of_date: str) -> str:
    """
    Compare stock to minimum level and suggest reorder quantity.

    Args:
        item_name: Item to evaluate.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Reorder recommendation.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    stock_df = get_stock_level(resolved, as_of_date)
    stock = int(stock_df["current_stock"].iloc[0])
    min_row = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": resolved},
    )
    min_stock = int(min_row.iloc[0]["min_stock_level"])
    reorder_qty = max(0, (min_stock * 2) - stock)
    return json.dumps(
        {
            "item_name": resolved,
            "current_stock": stock,
            "min_stock_level": min_stock,
            "reorder_needed": stock < min_stock,
            "suggested_reorder_quantity": reorder_qty,
            "note": note,
        }
    )


@tool
def place_stock_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """
    Place a supplier stock order for an item.

    Args:
        item_name: Catalog item name.
        quantity: Units to order from supplier.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Order confirmation.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    unit_price = _get_unit_price(resolved)
    total_price = quantity * unit_price
    txn_id = create_transaction(
        resolved, "stock_orders", quantity, total_price, as_of_date
    )
    delivery = get_supplier_delivery_date(as_of_date, quantity)
    return (
        f"Stock order placed: {quantity} x {resolved} for ${total_price:.2f}. "
        f"Transaction ID {txn_id}. Supplier ETA: {delivery}. {note}"
    )


# --- Quoting agent tools ---


@tool
def get_quote_history(search_terms: str, limit: int = 5) -> str:
    """
    Search historical quotes by comma-separated keywords.

    Args:
        search_terms: Comma-separated keywords (e.g. ceremony,glossy).
        limit: Max records to return.

    Returns:
        str: JSON list of similar past quotes.
    """
    terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    if not terms:
        terms = ["paper"]
    quotes = search_quote_history(terms, limit=limit)
    return json.dumps(quotes, indent=2, default=str)


@tool
def get_unit_price(item_name: str) -> str:
    """
    Get list unit price for a catalog item.

    Args:
        item_name: Catalog item name.

    Returns:
        str: Unit price details.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    price = _get_unit_price(resolved)
    return json.dumps({"item_name": resolved, "unit_price": price, "note": note})


@tool
def calculate_quote(item_name: str, quantity: int, as_of_date: str) -> str:
    """
    Calculate a line-item quote with bulk discount tiers.

    Args:
        item_name: Item to quote.
        quantity: Requested units.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Quote breakdown with discount explanation.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    unit_price = _get_unit_price(resolved)
    discount = bulk_discount_rate(quantity)
    subtotal = quantity * unit_price
    total = subtotal * (1 - discount)
    stock_df = get_stock_level(resolved, as_of_date)
    stock = int(stock_df["current_stock"].iloc[0])
    return json.dumps(
        {
            "item_name": resolved,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": round(subtotal, 2),
            "discount_rate": discount,
            "discount_amount": round(subtotal - total, 2),
            "total": round(total, 2),
            "current_stock": stock,
            "in_stock": stock >= quantity,
            "explanation": (
                f"{int(discount * 100)}% bulk discount applied for quantity {quantity}."
                if discount > 0
                else "No bulk discount for this quantity."
            ),
            "note": note,
        }
    )


# --- Fulfillment agent tools ---


@tool
def get_delivery_timeline(as_of_date: str, quantity: int) -> str:
    """
    Estimate supplier delivery date for a quantity.

    Args:
        as_of_date: Starting ISO date (YYYY-MM-DD).
        quantity: Units in the shipment.

    Returns:
        str: Estimated delivery date.
    """
    delivery = get_supplier_delivery_date(as_of_date, quantity)
    return f"Estimated delivery for {quantity} units: {delivery} (from {as_of_date})."


@tool
def check_can_fulfill(item_name: str, quantity: int, as_of_date: str) -> str:
    """
    Check whether an order can be fulfilled from current stock.

    Args:
        item_name: Item to fulfill.
        quantity: Requested units.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Fulfillment feasibility summary.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    stock = int(get_stock_level(resolved, as_of_date)["current_stock"].iloc[0])
    cash = get_cash_balance(as_of_date)
    return json.dumps(
        {
            "item_name": resolved,
            "requested_quantity": quantity,
            "current_stock": stock,
            "can_fulfill": stock >= quantity,
            "cash_balance": cash,
            "note": note,
        }
    )


@tool
def fulfill_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """
    Record a sales transaction when stock is sufficient.

    Args:
        item_name: Item sold.
        quantity: Units sold.
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Fulfillment result.
    """
    resolved, note = resolve_item_name(item_name)
    if not resolved:
        return note
    stock = int(get_stock_level(resolved, as_of_date)["current_stock"].iloc[0])
    if stock < quantity:
        shortfall = quantity - stock
        delivery = get_supplier_delivery_date(as_of_date, shortfall)
        return (
            f"Cannot fulfill {quantity} x {resolved}: only {stock} in stock. "
            f"Shortfall {shortfall}; restock ETA {delivery}. {note}"
        )
    unit_price = _get_unit_price(resolved)
    discount = bulk_discount_rate(quantity)
    total_price = round(quantity * unit_price * (1 - discount), 2)
    txn_id = create_transaction(resolved, "sales", quantity, total_price, as_of_date)
    delivery = get_supplier_delivery_date(as_of_date, quantity)
    return (
        f"Order fulfilled: {quantity} x {resolved} for ${total_price:.2f} "
        f"(transaction {txn_id}). Estimated delivery: {delivery}. {note}"
    )


@tool
def get_cash_on_hand(as_of_date: str) -> str:
    """
    Return company cash balance as of a date.

    Args:
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: Cash balance message.
    """
    cash = get_cash_balance(as_of_date)
    return f"Cash balance as of {as_of_date}: ${cash:,.2f}"


@tool
def get_financial_snapshot(as_of_date: str) -> str:
    """
    Generate a financial report snapshot as of a date.

    Args:
        as_of_date: ISO date (YYYY-MM-DD).

    Returns:
        str: JSON financial report.
    """
    report = generate_financial_report(as_of_date)
    return json.dumps(report, indent=2, default=str)


# --- Specialist agents ---


class InventoryAgent(ToolCallingAgent):
    """Checks stock levels and places supplier reorders."""

    def __init__(self, model_to_use: OpenAIServerModel):
        super().__init__(
            tools=[
                check_item_stock,
                list_available_inventory,
                check_reorder_needed,
                place_stock_order,
            ],
            model=model_to_use,
            name="inventory_agent",
            description="Inventory specialist for stock checks and reorders.",
        )

    def handle_request(self, request: str, as_of_date: str) -> str:
        self.memory.steps = []
        prompt = f"""
        You are the Munder Difflin inventory specialist.
        Request date (use as as_of_date in every tool call): {as_of_date}
        Task: {request}
        Use exact catalog item names from tool outputs. Summarize stock and reorder actions clearly.
        """
        return str(self.run(prompt))


class QuotingAgent(ToolCallingAgent):
    """Generates competitive quotes with bulk discounts."""

    def __init__(self, model_to_use: OpenAIServerModel):
        super().__init__(
            tools=[get_quote_history, get_unit_price, calculate_quote],
            model=model_to_use,
            name="quoting_agent",
            description="Quoting specialist for prices and historical context.",
        )

    def handle_request(self, request: str, as_of_date: str) -> str:
        self.memory.steps = []
        prompt = f"""
        You are the Munder Difflin quoting specialist.
        Request date (use as as_of_date in calculate_quote): {as_of_date}
        Task: {request}
        Search quote history with relevant keywords. Apply bulk discounts via calculate_quote.
        Explain pricing clearly for the orchestrator.
        """
        return str(self.run(prompt))


class FulfillmentAgent(ToolCallingAgent):
    """Validates and records customer orders."""

    def __init__(self, model_to_use: OpenAIServerModel):
        super().__init__(
            tools=[
                get_delivery_timeline,
                check_can_fulfill,
                fulfill_order,
                get_cash_on_hand,
            ],
            model=model_to_use,
            name="fulfillment_agent",
            description="Fulfillment specialist for order processing.",
        )

    def handle_request(self, request: str, as_of_date: str) -> str:
        self.memory.steps = []
        prompt = f"""
        You are the Munder Difflin fulfillment specialist.
        Request date (use as as_of_date in every tool call): {as_of_date}
        Task: {request}
        Check stock before fulfilling. Use fulfill_order only when stock is sufficient.
        """
        return str(self.run(prompt))


class Orchestrator(ToolCallingAgent):
    """Coordinates inventory, quoting, and fulfillment specialists."""

    def __init__(self, model_to_use: OpenAIServerModel):
        self.inventory_agent = InventoryAgent(model_to_use)
        self.quoting_agent = QuotingAgent(model_to_use)
        self.fulfillment_agent = FulfillmentAgent(model_to_use)

        inventory = self.inventory_agent
        quoting = self.quoting_agent
        fulfillment = self.fulfillment_agent

        @tool
        def consult_inventory_agent(task: str, as_of_date: str) -> str:
            """
            Delegate inventory or stock questions to the inventory specialist.

            Args:
                task: What to check or reorder.
                as_of_date: ISO date (YYYY-MM-DD).

            Returns:
                str: Inventory specialist response.
            """
            return inventory.handle_request(task, as_of_date)

        @tool
        def consult_quoting_agent(task: str, as_of_date: str) -> str:
            """
            Delegate pricing or quote requests to the quoting specialist.

            Args:
                task: Quote details to price.
                as_of_date: ISO date (YYYY-MM-DD).

            Returns:
                str: Quoting specialist response.
            """
            return quoting.handle_request(task, as_of_date)

        @tool
        def consult_fulfillment_agent(task: str, as_of_date: str) -> str:
            """
            Delegate order fulfillment to the fulfillment specialist.

            Args:
                task: Order lines to fulfill.
                as_of_date: ISO date (YYYY-MM-DD).

            Returns:
                str: Fulfillment specialist response.
            """
            return fulfillment.handle_request(task, as_of_date)

        super().__init__(
            tools=[
                consult_inventory_agent,
                consult_quoting_agent,
                consult_fulfillment_agent,
                get_financial_snapshot,
            ],
            model=model_to_use,
            name="orchestrator",
            description="Customer-facing coordinator for Munder Difflin.",
        )

    def _extract_final_answer(self) -> str:
        for step in reversed(self.memory.steps):
            if hasattr(step, "tool_calls") and step.tool_calls:
                for tc in step.tool_calls:
                    if tc.name == "final_answer":
                        if hasattr(step, "action_output") and step.action_output is not None:
                            return str(step.action_output)
                        if hasattr(tc, "arguments") and tc.arguments.get("answer"):
                            return str(tc.arguments["answer"])
            if hasattr(step, "observations") and step.observations is not None:
                if not (
                    hasattr(step, "tool_calls")
                    and step.tool_calls
                    and step.tool_calls[0].name == "final_answer"
                ):
                    return str(step.observations)
        return "Thank you for contacting Munder Difflin. We are reviewing your request."

    def handle_customer_request(self, request_with_date: str) -> str:
        """Process a customer request and return a single customer-facing reply."""
        date_match = re.search(
            r"\(Date of request:\s*(\d{4}-\d{2}-\d{2})\)", request_with_date
        )
        as_of_date = date_match.group(1) if date_match else "2025-04-01"

        self.memory.steps = []
        prompt = f"""
        You are the Munder Difflin customer service orchestrator.

        Customer request:
        {request_with_date}

        Request date for all tools: {as_of_date}

        Specialists (call via your tools, always pass as_of_date):
        - consult_inventory_agent: stock checks, availability, reorders
        - consult_quoting_agent: prices, quotes, bulk discounts, quote history
        - consult_fulfillment_agent: place/confirm orders when customer wants to buy
        - get_financial_snapshot: internal snapshot if needed

        Workflow:
        1. Extract items, quantities, and delivery deadlines from the request.
        2. For price/quote questions → consult_quoting_agent (include quantities).
        3. For stock/availability → consult_inventory_agent.
        4. For confirmed orders → consult_inventory_agent first, then consult_fulfillment_agent.
        5. If stock is low, inventory may reorder; then quote or fulfill as appropriate.
        6. Some items may be unavailable—explain clearly with alternatives or partial fulfillment.
        7. Do not reveal internal profit margins or raw system errors.

        Provide one helpful customer-facing reply using the final_answer tool.
        Include prices, delivery estimates, and brief rationale (e.g. bulk discounts).
        """
        self.run(prompt)
        return self._extract_final_answer()


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############
    orchestrator = Orchestrator(model)

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############
        response = orchestrator.handle_customer_request(request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
