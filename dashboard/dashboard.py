import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import datetime as dt
import urllib

df_all = pd.read_csv('./dashboard/all_data.csv')
df_geolocation = pd.read_csv('./data/geolocation_dataset.csv')

# change type str/obj -> datetime
datetime_columns = ["order_approved_at"]
for column in datetime_columns:
    df_all[column] = pd.to_datetime(df_all[column])

def pertanyaan_satu(df):
    product_id_counts = df_all.groupby('product_category_name_english')['product_id'].count().reset_index()
    sorted_product = product_id_counts.sort_values(by='product_id', ascending=False)
    return sorted_product

def pertanyaan_dua(df):
    rating_service = df['review_score'].value_counts().sort_values(ascending=False)
    max_score = rating_service.idxmax()
    df_cust=df['review_score']
    return (rating_service,max_score,df_cust)

def pertanyaan_tiga(df):
    df_bulanan = df_all.resample(rule='M', on='order_approved_at').agg({
    "order_id": "nunique",
    })
    df_bulanan.index = df_bulanan.index.strftime('%Y-%B')
    df_bulanan = df_bulanan.reset_index()
    df_bulanan.rename(columns={
        "order_id": "order_count",
    }, inplace=True)
    return df_bulanan

def pertanyaan_empat(df):
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df_rfm = df_all.groupby(by="customer_id", as_index=False).agg({
    "order_purchase_timestamp": "max",  # Mengambil tanggal order terakhir
    "order_id": "count",                # Menghitung jumlah order (frekuensi)
    "price": "sum"                      # Menghitung total revenue (monetary)
    })
    df_rfm.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    df_rfm["max_order_timestamp"] = df_rfm["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    # Asumsi sekarang adalah 1 hari setelah order terakhir alias '2018-10-18'
    df_rfm["recency"] = df_rfm["max_order_timestamp"].apply(lambda x: (recent_date - x).days) + 1
    df_rfm.drop("max_order_timestamp", axis=1, inplace=True)
    df_rfm = df_rfm[['customer_id', 'recency', 'frequency', 'monetary']]
    return df_rfm

def pertanyaan_lima(df1, df2):
    geolocation_new = df1.groupby(['geolocation_zip_code_prefix'])['geolocation_state'].nunique().reset_index(name='count')
    #geolocation_new[geolocation_new['count']>= 2].shape
    max_state = df1.groupby(['geolocation_zip_code_prefix','geolocation_state']).size().reset_index(name='count').drop_duplicates(subset = 'geolocation_zip_code_prefix').drop('count',axis=1)
    geolocation_map = df1.groupby(['geolocation_zip_code_prefix','geolocation_city','geolocation_state'])[['geolocation_lat','geolocation_lng']].median().reset_index()
    geolocation_map = geolocation_map.merge(max_state,on=['geolocation_zip_code_prefix','geolocation_state'],how='inner')
    customers_geolocation_map = df2.merge(geolocation_map,left_on='customer_zip_code_prefix',right_on='geolocation_zip_code_prefix',how='inner')
    return customers_geolocation_map

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/7/77/Streamlit-logo-primary-colormark-darktext.png")
    url = "https://drive.google.com/file/d/1MsAjPM7oKtVfJL_wRp1qmCajtSG1mdcK/view?usp=sharing"
    link_text = "Klik link untuk mengunduh dataset"
    st.write('Proyek Analisis Data: E-Commerce Public Dataset')
    st.write(f"[{link_text}]({url})")
    st.write('Copyright (C) 2024 by Meakhel Gunawan')

# Memanggil Fungsi
pertanyaanSatu = pertanyaan_satu(df_all)
rating_service,max_score,df_rating_service = pertanyaan_dua(df_all)
df_performa = pertanyaan_tiga(df_all)
rfm = pertanyaan_empat(df_all)
customers_geolocation_map = pertanyaan_lima(df_geolocation, df_all)

# HEADER
st.header('Proyek Analisis Data: E-Commerce Public Dataset :sparkles:')

# PERTANYAAN PERTAMA
st.subheader("Produk apa saja yang memiliki jumlah pembelian terbesar dan terkecil?")
col1, col2 = st.columns(2)
with col1:
    produk_terbanyak = pertanyaanSatu['product_id'].max()
    st.markdown(f"Jumlah Produk terbanyak: **{produk_terbanyak}**")

with col2:
    produk_tersedikit = pertanyaanSatu['product_id'].min()
    st.markdown(f"Jumlah Produk tersedikit: **{produk_tersedikit}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))
colors_positive = ["#40E65F", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
colors_negative = ["#D63341", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="product_id", y="product_category_name_english", 
            data=pertanyaanSatu.head(5), palette=colors_positive, ax=ax[0])
ax[0].set_xlabel('Frekuensi')
ax[0].set_ylabel('Nama Produk')
ax[0].set_xlabel(None)
ax[0].set_title("Produk dengan jumlah pembelian terbesar", loc="center", fontsize=18)
ax[0].tick_params(axis ='y', labelsize=15)

sns.barplot(x="product_id", y="product_category_name_english", 
            data=pertanyaanSatu.sort_values(by="product_id", ascending=True).head(5), palette=colors_negative, ax=ax[1])
ax[1].set_xlabel('Frekuensi')
ax[1].set_ylabel('Nama Produk')
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Produk dengan jumlah pembelian terkecil", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

plt.suptitle("Produk yang memiliki jumlah pembelian terbesar dan terkecil", fontsize=20)
st.pyplot(fig)
st.write('Produk dengan jumlah pembelian terbesar yaitu **bed_bath_table**. Sebaliknya produk dengan jumlah pembelian terkecil yaitu **security_and_services**.')


# PERTANYAAN KEDUA
st.subheader('Bagaimana tingkat kepuasan pembeli terhadap layanan E-Commerce kami?')
col1, col2 = st.columns(2)
with col1:
    jumlah_rating_5 = rating_service[5.0]
    st.markdown(f"Jumlah rating bintang 5: **{jumlah_rating_5}**")

with col2:
    st.markdown(f"Rata-rata rating: **{df_rating_service.mean():.2f}**")

sns.set(style="darkgrid")
plt.figure(figsize=(10, 5))
sns.barplot(x=rating_service.index, 
            y=rating_service.values, 
            order=rating_service.index,
            palette=["#40E65F" if score == max_score else "#D3D3D3" for score in rating_service.index]
            )

plt.title("Tingkat kepuasan pembeli dari rating", fontsize=15)
plt.xlabel("Rating")
plt.ylabel("Customer")
plt.xticks(fontsize=12)
st.pyplot(plt)
st.write('**Rating 5 adalah rating tertinggi** dengan perolehan lebih dari 60000 customer, yang kemudian disusul oleh **rating 4** dan **rating 1**.')


# PERTANYAAN KETIGA
st.subheader('Bagaimana performa order transaksi di platform E-Commerce setiap bulan?')
col1, col2 = st.columns(2)
with col1:
    order_terbanyak = df_performa['order_count'].max()
    tahun_bulan_terbanyak = df_performa[df_performa['order_count'] == df_performa['order_count'].max()]['order_approved_at'].values[0]
    st.markdown(f"Order terbanyak ada pada {tahun_bulan_terbanyak} : **{order_terbanyak}**")

with col2:
    order_tersedikit = df_performa['order_count'].min()
    tahun_bulan_tersedikit = df_performa[df_performa['order_count'] == df_performa['order_count'].min()]['order_approved_at'].values[0]
    st.markdown(f"Order tersedikit ada pada {tahun_bulan_tersedikit} : **{order_tersedikit}**")


plt.figure(figsize=(10, 6))
plt.plot(df_performa['order_approved_at'], df_performa['order_count'], marker='o', color='b')

plt.title('Performa Order untuk setiap bulan', fontsize=16)
plt.xlabel('Bulan', fontsize=12)
plt.ylabel('Jumlah Order', fontsize=12)
plt.xticks(rotation=90)
plt.grid(True)
plt.tight_layout()
st.pyplot(plt)
st.write('Performa order tertinggi adalah pada saat **November 2017**. Selain itu, ada peningkatan performa order mulai dari **Desember 2016** hingga **November 2017**. Kemudian mengalami stagnansi pada **Januari 2018** hingga **May 2018**.')


# PERTANYAAN EMPAT
st.subheader("Bagaimana perilaku pembelian pelanggan dengan menggunakan RFM Analysis?")
colors = ["#40E65F", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"])
with tab1:
    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="recency", 
        x="customer_id", 
        data=rfm.sort_values(by="recency", ascending=True).head(5), 
        palette=colors
        )
    plt.title("Recency (Hari)", loc="center", fontsize=18)
    plt.ylabel('')
    plt.xlabel("Customer")
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)
    st.write('Untuk Recency, customer yang terakhir kali berbelanja adalah **1 hari yang lalu** diikuti oleh **2 hari yang lalu**, tetapi ada perbedaan cukup jauh setelahnya yaitu **15 hari yang lalu** dan seterusnya.')

with tab2:
    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="frequency", 
        x="customer_id", 
        data=rfm.sort_values(by="frequency", ascending=False).head(5), 
        palette=colors,
        
        )
    plt.ylabel('')
    plt.xlabel("Customer")
    plt.title("Frequency", loc="center", fontsize=18)
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)
    st.write('Untuk Frekuensi, customer dengan pembelian produk terbanyak adalah **63 produk**, lalu terjadi gap cukup jauh ke **30an produk** dan seterusnya.')

with tab3:
    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="monetary", 
        x="customer_id", 
        data=rfm.sort_values(by="monetary", ascending=False).head(5), 
        palette=colors,
        )
    plt.ylabel('')
    plt.xlabel("Customer")
    plt.title("Monetary", loc="center", fontsize=18)
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)
    st.write('Untuk Monetary, customer dengan pengeluaran terbesar adalah **13440** diikuti oleh **11000an**, **10000an**, dan seterusnya.')


#PERTANYAAN LIMA
st.subheader("Dimana saja customer terbanyak berdasarkan letak geografisnya?")
def plot_brazil_map(data):
    brazil = mpimg.imread(urllib.request.urlopen('https://www.mapsland.com/maps/south-america/brazil/map-of-brazil-with-cities-small.jpg'),'jpg')
    fig, ax = plt.subplots(figsize=(10, 10))
    data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", alpha=0.3, s=0.3, c='maroon', ax=ax)
    plt.axis('off')
    plt.imshow(brazil, extent=[-73.98283055, -32.189, -34.4789, 9.6], aspect='auto')
    st.pyplot(fig)
plot_brazil_map(customers_geolocation_map.drop_duplicates(subset='customer_unique_id'))
st.write('Peta diambil dari https://www.mapsland.com/')
st.write('Customer dengan pembelian terbanyak terletak pada daerah selatan negara Brazil seperti Provinsi **Sao Paulo, Rio de Janiero, Parana, Santa Cararina, Rio Gra Do Sul, dan lain sebagainya** dilihat dari **banyaknya titik-titik merah yang sangat rapat** di provinsi-provinsi tersebut. Uniknya, titik-titik yang rapat ini sebgaian besar terlihat pada **Ibu Kota dari provinsi tersebut**.')
