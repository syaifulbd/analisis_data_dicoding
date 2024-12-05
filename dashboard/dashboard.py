import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Memuat data
@st.cache_data
def load_data():
    products = pd.read_csv('https://drive.google.com/uc?id=1OguwsMaRrvAGlZXzy-0xyn5Lrv50CzsD')
    product_translation = pd.read_csv('https://drive.google.com/uc?id=1oIh6OvYFS4Q09ode1gk6GvUyQjabdwFI')
    reviews = pd.read_csv('https://drive.google.com/uc?id=1MGHu8STjZIcGHPcQeccMvcJi8ESm-sjL')
    orders = pd.read_csv('https://drive.google.com/uc?id=1zvDxQY5qrta2eJIebO572AsUGZepk8nw')
    order_items = pd.read_csv('https://drive.google.com/uc?id=1OGB12emxEPR9X1pMoUNxKXo5VH56ro3C')
    customers = pd.read_csv('https://drive.google.com/uc?id=1R_B2hI-W1SO_Rry2Nxub9rBl8U246lJC')

    # Gabung product dengan kategori
    products = products.merge(product_translation, on='product_category_name', how='left')

    # Filter order hanya yang berhasil terkirim
    orders = orders[orders['order_status'] == 'delivered']

    # Gabung semua dataset
    order_details = (order_items
                     .merge(products, on='product_id', how='left')
                     .merge(orders, on='order_id', how='left')
                     .merge(reviews, on='order_id', how='left')
                     .merge(customers, on='customer_id', how='left'))

    # Data cleansing
    order_details.drop(columns=['seller_id', 'shipping_limit_date', 'product_name_lenght', 
                                'product_description_lenght', 'product_photos_qty', 
                                'product_weight_g', 'product_length_cm', 'product_height_cm', 
                                'product_width_cm', 'review_creation_date', 'review_answer_timestamp', 
                                'customer_zip_code_prefix', 'review_comment_title', 'review_comment_message'], inplace=True)
    order_details.dropna(subset=['customer_id', 'review_id'], inplace=True)
    order_details['product_category_name'] = order_details['product_category_name'].fillna('Unknown')
    order_details['product_category_name_english'] = order_details['product_category_name_english'].fillna('Unknown')
    order_details['order_delivered_customer_date'] = order_details['order_delivered_customer_date'].fillna(order_details['order_estimated_delivery_date'])
    order_details['order_delivered_carrier_date'] = order_details['order_delivered_carrier_date'].fillna(order_details['order_estimated_delivery_date'])
    order_details['order_approved_at'] = order_details['order_approved_at'].fillna(order_details['order_purchase_timestamp'])

    # Tambahkan kolom waktu pengiriman
    order_details['delivery_time'] = (pd.to_datetime(order_details['order_delivered_customer_date']) - 
                                      pd.to_datetime(order_details['order_purchase_timestamp'])).dt.days
    return order_details

# Load data
order_details = load_data()

# Dashboard
st.title("Dashboard Analisis Penjualan dan Pengiriman")

# Sidebar
st.sidebar.title("Navigasi")
menu = st.sidebar.selectbox("Pilih Analisis:", ["Volume Penjualan", "Waktu Pengiriman dan Ulasan", "Visualisasi Tambahan"])

if menu == "Volume Penjualan":
    st.header("Volume Penjualan per Kategori dan Lokasi")
    sales_by_category = order_details.groupby('product_category_name_english')['order_item_id'].count().sort_values(ascending=False)
    sales_by_location = order_details.groupby('customer_city')['order_item_id'].count().sort_values(ascending=False)

    # Pilih jumlah kategori/lokasi untuk ditampilkan
    top_n = st.sidebar.slider("Jumlah kategori/lokasi yang ingin ditampilkan:", 5, 20, 10)

    # Kategori
    st.subheader(f"Top {top_n} Kategori Produk dengan Penjualan Tertinggi")
    top_categories = sales_by_category.head(top_n).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_categories, x='product_category_name_english', y='order_item_id', ax=ax)
    plt.xticks(rotation=90)
    st.pyplot(fig)

    st.subheader(f"Bottom {top_n} Kategori Produk dengan Penjualan Terendah")
    bottom_categories = sales_by_category.tail(top_n).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=bottom_categories, x='product_category_name_english', y='order_item_id', ax=ax)
    plt.xticks(rotation=90)
    st.pyplot(fig)

    # Lokasi
    st.subheader(f"Top {top_n} Lokasi Pelanggan dengan Penjualan Tertinggi")
    top_locations = sales_by_location.head(top_n).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_locations, x='customer_city', y='order_item_id', ax=ax)
    plt.xticks(rotation=90)
    st.pyplot(fig)

    st.subheader(f"Bottom {top_n} Lokasi Pelanggan dengan Penjualan Terendah")
    bottom_locations = sales_by_location.tail(top_n).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=bottom_locations, x='customer_city', y='order_item_id', ax=ax)
    plt.ylim(0,10)
    plt.xticks(rotation=90)
    st.pyplot(fig)

elif menu == "Waktu Pengiriman dan Ulasan":
    st.header("Analisis Waktu Pengiriman dan Ulasan Pengguna")
    delivery_by_reviews = order_details.groupby('review_score')['delivery_time'].mean().reset_index()

    # Waktu pengiriman vs review score
    st.subheader("Waktu Pengiriman vs Review Score")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.regplot(data=delivery_by_reviews, x='review_score', y='delivery_time', ax=ax)
    plt.title("Delivery Time vs Review Score")
    plt.xlabel("Review Score")
    plt.ylabel("Delivery Time (days)")
    st.pyplot(fig)

elif menu == "Visualisasi Tambahan":
    st.header("Visualisasi Tambahan")

    # Distribusi Skor Ulasan
    st.subheader("Distribusi Skor Ulasan")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(data=order_details, x='review_score', ax=ax)
    plt.title("Distribusi Skor Ulasan")
    plt.xlabel("Review Score")
    plt.ylabel("Jumlah")
    st.pyplot(fig)

    # Rata-rata Waktu Pengiriman per Kategori
    st.subheader("Rata-rata Waktu Pengiriman per Kategori Produk")
    avg_delivery_time_by_category = order_details.groupby('product_category_name_english')['delivery_time'].mean().sort_values().reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=avg_delivery_time_by_category.head(10), x='product_category_name_english', y='delivery_time', ax=ax)
    plt.xticks(rotation=90)
    plt.title("Top 10 Kategori Produk dengan Waktu Pengiriman Tercepat")
    st.pyplot(fig)
