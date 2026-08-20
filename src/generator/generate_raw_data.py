"""
ARGOS-360: Synthetic Raw Data Generator (Bronze Layer)
Generates realistic, messy e-commerce enterprise data:
- Multi-source customer records with intentional duplicates, typos, and address changes.
- Product catalog with categories, costs, and pricing tiers.
- Transactional orders with realistic statuses, discounts, and date distributions.
Outputs Parquet files to data/01_raw/.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from faker import Faker

fake = Faker(['es_ES', 'en_US'])
Faker.seed(31)
random.seed(31)
np.random.seed(10)

def get_data_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    raw_dir = repo_root / "data" / "01_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def generate_products(num_products: int = 150) -> pd.DataFrame:
    categories = {
        "Electronics": ["Smartphones", "Laptops", "Audio", "Wearables", "Gaming"],
        "Clothing": ["T-Shirts", "Jeans", "Jackets", "Footwear", "Accessories"],
        "Home & Kitchen": ["Cookware", "Furniture", "Lighting", "Bedding", "Decor"],
        "Sports & Fitness": ["Yoga", "Running", "Gym Equipment", "Cycling", "Outdoor"],
        "Books & Media": ["Fiction", "Technology", "Business", "Self-Help", "Comics"]
    }
    
    products = []
    prod_id = 1
    for cat, subcats in categories.items():
        items_per_cat = num_products // len(categories)
        for _ in range(items_per_cat):
            subcat = random.choice(subcats)
            name = f"{fake.word().capitalize()} {subcat[:-1] if subcat.endswith('s') else subcat} Pro"
            cost = round(random.uniform(5.0, 350.0), 2)
            margin = random.uniform(1.3, 2.5)
            price = round(cost * margin, 2)
            
            products.append({
                "product_id": f"PRD-{prod_id:04d}",
                "product_name": name,
                "category": cat,
                "subcategory": subcat,
                "unit_cost": cost,
                "unit_price": price,
                "created_at": datetime(2024, 1, 1) + timedelta(days=random.randint(0, 30))
            })
            prod_id += 1
            
    df = pd.DataFrame(products)
    return df

def generate_customers_with_duplicates(num_true_identities: int = 2000) -> pd.DataFrame:
    """
    Generates a messy customer dataset where ~30% of records are duplicates or updates
    coming from 3 different source systems (WEB_SHOPIFY, CRM_SALESFORCE, MARKETING_LIST).
    """
    sources = ["SHOPIFY_STORE", "SALESFORCE_CRM", "MARKETING_HUBSPOT"]
    records = []
    
    cities = [
        ("Madrid", "Comunidad de Madrid", "España"),
        ("Barcelona", "Cataluña", "España"),
        ("Valencia", "Comunidad Valenciana", "España"),
        ("Sevilla", "Andalucía", "España"),
        ("Bilbao", "País Vasco", "España"),
        ("Zaragoza", "Aragón", "España"),
        ("Málaga", "Andalucía", "España"),
        ("Lisboa", "Lisboa", "Portugal"),
        ("Oporto", "Norte", "Portugal"),
        ("Bogotá", "Cundinamarca", "Colombia"),
        ("Ciudad de México", "CDMX", "México")
    ]

    record_id = 100001
    
    for i in range(1, num_true_identities + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        domain = random.choice(["gmail.com", "outlook.com", "yahoo.es", "empresa.com", "hotmail.com"])
        clean_email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        clean_phone = f"+34{random.randint(600000000, 699999999)}"
        city, state, country = random.choice(cities)
        street = fake.street_address()
        base_registration = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 400))

        # 1. Primary Record (Source 1)
        records.append({
            "source_record_id": f"SRC-{record_id}",
            "source_system": "SHOPIFY_STORE",
            "first_name": first_name,
            "last_name": last_name,
            "email": clean_email,
            "phone": clean_phone,
            "street_address": street,
            "city": city,
            "state": state,
            "country": country,
            "updated_at": base_registration,
            "simulated_true_id": f"TRUE-{i:05d}"
        })
        record_id += 1

        # 2. Probability of Duplicate in Source 2 (CRM with typo or nickname)
        if random.random() < 0.25:
            # Introduce typo in name or alternate email
            typo_name = first_name
            if len(first_name) > 3 and random.random() < 0.4:
                # Slight typo (e.g., 'Alejandro' -> 'Alejandor')
                typo_name = first_name[:-2] + first_name[-1] + first_name[-2]
            
            crm_email = clean_email if random.random() < 0.7 else f"{first_name[0].lower()}{last_name.lower()}@{domain}"
            records.append({
                "source_record_id": f"SRC-{record_id}",
                "source_system": "SALESFORCE_CRM",
                "first_name": typo_name,
                "last_name": last_name,
                "email": crm_email,
                "phone": clean_phone if random.random() < 0.8 else None,
                "street_address": street,
                "city": city,
                "state": state,
                "country": country,
                "updated_at": base_registration + timedelta(days=random.randint(5, 60)),
                "simulated_true_id": f"TRUE-{i:05d}"
            })
            record_id += 1

        # 3. Probability of Address/City Change (SCD Type 2 test case)
        if random.random() < 0.15:
            new_city, new_state, new_country = random.choice(cities)
            new_street = fake.street_address()
            records.append({
                "source_record_id": f"SRC-{record_id}",
                "source_system": "SHOPIFY_STORE",
                "first_name": first_name,
                "last_name": last_name,
                "email": clean_email,
                "phone": clean_phone,
                "street_address": new_street,
                "city": new_city,
                "state": new_state,
                "country": new_country,
                "updated_at": base_registration + timedelta(days=random.randint(100, 300)),
                "simulated_true_id": f"TRUE-{i:05d}"
            })
            record_id += 1

    df = pd.DataFrame(records)
    return df

def generate_orders(customers_df: pd.DataFrame, products_df: pd.DataFrame, num_orders: int = 12000) -> pd.DataFrame:
    orders = []
    source_customer_ids = customers_df["source_record_id"].tolist()
    product_ids = products_df["product_id"].tolist()
    product_prices = dict(zip(products_df["product_id"], products_df["unit_price"]))
    product_costs = dict(zip(products_df["product_id"], products_df["unit_cost"]))
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 6, 30)
    delta_days = (end_date - start_date).days
    
    statuses = ["DELIVERED", "DELIVERED", "DELIVERED", "SHIPPED", "PROCESSING", "CANCELLED", "RETURNED"]
    
    for i in range(1, num_orders + 1):
        order_date = start_date + timedelta(days=random.randint(0, delta_days), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        cust_id = random.choice(source_customer_ids)
        prod_id = random.choice(product_ids)
        qty = random.choices([1, 2, 3, 4, 5], weights=[0.65, 0.20, 0.08, 0.04, 0.03])[0]
        unit_p = product_prices[prod_id]
        unit_c = product_costs[prod_id]
        
        discount = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.6, 0.15, 0.12, 0.08, 0.05])[0]
        gross_amount = round(qty * unit_p, 2)
        net_amount = round(gross_amount * (1.0 - discount), 2)
        shipping_cost = 0.0 if net_amount > 50.0 else 4.99
        status = random.choice(statuses)
        
        delivered_date = None
        if status in ["DELIVERED", "RETURNED"]:
            delivered_date = order_date + timedelta(days=random.randint(1, 5))
            
        orders.append({
            "order_id": f"ORD-{i:06d}",
            "source_customer_id": cust_id,
            "product_id": prod_id,
            "order_timestamp": order_date,
            "order_status": status,
            "quantity": qty,
            "unit_price": unit_p,
            "unit_cost": unit_c,
            "discount_rate": discount,
            "gross_amount": gross_amount,
            "net_amount": net_amount,
            "shipping_cost": shipping_cost,
            "delivered_timestamp": delivered_date
        })
        
    df = pd.DataFrame(orders)
    return df

def main():
    print("⏳ [GENERATING] Creating raw synthetic data for Bronze Layer...")
    data_dir = get_data_dir()
    
    # 1. Products
    products_df = generate_products(150)
    products_file = data_dir / "raw_products.parquet"
    products_df.to_parquet(products_file, index=False)
    print(f"  📦 Products generated: {len(products_df):,} rows -> {products_file.name}")
    
    # 2. Customers with duplicates
    customers_df = generate_customers_with_duplicates(2500)
    customers_file = data_dir / "raw_customers.parquet"
    customers_df.to_parquet(customers_file, index=False)
    print(f"  👥 Customers generated (with duplicates): {len(customers_df):,} rows -> {customers_file.name}")
    
    # 3. Orders
    orders_df = generate_orders(customers_df, products_df, 15000)
    orders_file = data_dir / "raw_orders.parquet"
    orders_df.to_parquet(orders_file, index=False)
    print(f"  🛒 Orders generated: {len(orders_df):,} rows -> {orders_file.name}")
    
    print("✅ [SUCCESS] Bronze Layer Parquet files generated successfully in data/01_raw/\n")

if __name__ == "__main__":
    main()
