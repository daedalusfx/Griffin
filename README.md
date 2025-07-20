
# 🦅 Griffin: Intelligent Broker Analyzer

![Griffin preview](/screenshouts/preview.png)
![Griffin preview-desktop](/screenshouts/desktop.png)


**A powerful, data-driven desktop application for analyzing and comparing the price feed quality of financial brokers using machine learning.**  
**یک برنامه‌ی دسکتاپ قدرتمند و مبتنی بر داده برای تحلیل و مقایسه کیفیت قیمت‌گذاری کارگزاران مالی با استفاده از یادگیری ماشین.**

[Features](#-key-features) • [Methodology](#-methodology--algorithms) • [Installation](#-getting-started) • [Usage](#-usage) • [Project Structure](#-project-structure) • [Contributing](#-contributing) • [License](#-license)

---

Griffin is an open-source tool designed to bring **transparency** to the opaque world of broker price feeds. Instead of relying on marketing claims, Griffin empowers traders to make **data-driven decisions** using **statistical analysis** and **unsupervised machine learning**—objectively evaluating broker performance based on real-world data.  
**گریفین یک ابزار متن‌باز است که با هدف شفاف‌سازی در بازار غیرشفاف داده‌های قیمت‌گذاری کارگزاران ساخته شده است. به‌جای اتکا به تبلیغات، این ابزار به معامله‌گران اجازه می‌دهد تا با استفاده از تحلیل آماری و یادگیری ماشینِ بدون‌ناظر، تصمیمات آگاهانه بر اساس داده‌های واقعی بگیرند.**

---

## ✨ Key Features  
## ✨ قابلیت‌های کلیدی

- **Modern GUI**  
  Built with **PyQt6**, featuring a sleek, dark-themed interface for a professional user experience.  
  **رابط کاربری مدرن:** ساخته‌شده با PyQt6، دارای تم تیره و طراحی حرفه‌ای برای تجربه کاربری روان.

- **Data-Driven Analysis**  
  Uses **K-Means clustering** to group brokers based on statistical characteristics of their price feeds.  
  **تحلیل مبتنی بر داده:** دسته‌بندی خودکار کارگزاران بر اساس ویژگی‌های آماری با استفاده از الگوریتم خوشه‌بندی K-Means.

- **High-Performance Visualization**  
  Interactive 2D scatter plots via **PyQtGraph** allow users to zoom, pan, and explore data smoothly.  
  **بصری‌سازی سریع و تعاملی:** نمودارهای پراکندگی دو بعدی تعاملی با امکان بزرگنمایی، جابجایی و کاوش سریع داده‌ها.

- **Dynamic Data Sourcing**  
  Connects to an **InfluxDB** instance to retrieve available brokers, symbols, and timeframes on-the-fly.  
  **دریافت داده‌های پویا:** اتصال مستقیم به InfluxDB برای دریافت بروکرها، نمادها و تایم‌فریم‌های موجود به صورت لحظه‌ای.

- **Asynchronous Execution**  
  Heavy data processing runs in background threads for a **non-blocking, responsive UI**.  
  **پردازش غیرهمزمان:** اجرای پردازش‌های سنگین در پس‌زمینه برای حفظ عملکرد روان رابط کاربری.

- **Modular & Extensible**  
  Clean architecture with a clear separation between UI and backend logic—easy to maintain and extend.  
  **معماری ماژولار و قابل توسعه:** طراحی تمیز با جداسازی واضح بین منطق برنامه و رابط کاربری برای نگهداری و توسعه آسان.

---

## 🔬 Methodology & Algorithms  
## 🔬 روش‌شناسی و الگوریتم‌ها

Griffin processes raw OHLC data through the following stages:  
**گریفین داده‌های خام OHLC را طی مراحل زیر پردازش می‌کند:**

### 1. Feature Engineering  
### ۱. استخراج ویژگی‌ها

Transforms raw price data into meaningful statistics:  
**تبدیل داده‌های خام قیمتی به ویژگی‌های آماری قابل تحلیل:**

- **Gap_Median**  
  Median gap between candles (abs(open - previous close)); lower = higher liquidity.  
  **میانگین شکاف قیمتی بین کندل‌ها (اختلاف باز با بسته‌ی قبلی)؛ مقدار کمتر نشان‌دهنده نقدشوندگی بالاتر است.**

- **Spike_Median**  
  Median of `(high - low) / abs(open - close)`; lower = more stable price action.  
  **نسبت میانه نوسان به بدنه کندل؛ مقدار کمتر نشانه‌ای از رفتار قیمتی پایدارتر است.**

- **Spike_Max & Gap_Max**  
  Max observed spike/gap values; helpful in identifying brokers with outlier behaviors.  
  **بیشترین مقادیر مشاهده‌شده برای اسپایک و گپ؛ برای شناسایی رفتارهای غیرعادی کارگزاران مفید است.**

### 2. Data Preprocessing  
### ۲. پیش‌پردازش داده‌ها

- **StandardScaler** from `scikit-learn` standardizes features (mean = 0, variance = 1) for unbiased clustering.  
  **استانداردسازی ویژگی‌ها با استفاده از StandardScaler برای حذف سوگیری ناشی از مقیاس‌های متفاوت.**

### 3. Clustering with K-Means  
### ۳. خوشه‌بندی با K-Means

- **K-Means** groups brokers by statistical similarity.  
  **گروه‌بندی کارگزاران بر اساس شباهت آماری.**
- Uses the **Elbow Method** to auto-select the optimal number of clusters.  
  **استفاده از روش Elbow برای تعیین تعداد بهینه خوشه‌ها.**

### 4. Dimensionality Reduction with PCA  
### ۴. کاهش ابعاد با PCA

- **Principal Component Analysis (PCA)** reduces high-dimensional feature space to 2D.  
  **کاهش ابعاد ویژگی‌ها به فضای دوبعدی برای نمایش تصویری.**
- Enables intuitive visualization on scatter plots (X & Y = principal components).  
  **ایجاد نمودار قابل درک با استفاده از مؤلفه‌های اصلی به عنوان محورهای X و Y.**

### 5. Visualization  
### ۵. بصری‌سازی

- **PyQtGraph** plots clusters with unique colors.  
  **نمایش خوشه‌ها با رنگ‌های مجزا توسط PyQtGraph.**
- Hover-enabled tooltips show broker names for easy exploration.  
  **نمایش نام کارگزار هنگام حرکت ماوس برای کاوش آسان.**

---

## 🚀 Getting Started  
## 🚀 شروع سریع

### Prerequisites  
### پیش‌نیازها

- Python 3.8 or higher.  
  **پایتون نسخه ۳.۸ یا بالاتر**
- Access to an InfluxDB instance containing OHLC data with `broker`, `symbol`, and `period` as tags.  
  **دسترسی به پایگاه داده InfluxDB که داده‌های OHLC شامل تگ‌های `broker`، `symbol` و `period` را داشته باشد.**

### 🔧 Installation  
### 🔧 نصب

```bash
git clone https://github.com/your-username/griffin.git
cd griffin
```

Set up a virtual environment:  
**ایجاد محیط مجازی:**

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies:  
**نصب وابستگی‌ها:**

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration  
## ⚙️ پیکربندی

Create a `.env` file in the root directory and add your InfluxDB credentials:  
**یک فایل `.env` در ریشه پروژه ایجاد کرده و اطلاعات اتصال به InfluxDB را وارد کنید:**

```env
INFLUX_URL=http://127.0.0.1:8086
INFLUX_TOKEN=your-secret-token
INFLUX_ORG=your-org-name
INFLUX_BUCKET=your-bucket-name
```

The app will automatically load these settings.  
**برنامه این تنظیمات را به‌صورت خودکار بارگذاری می‌کند.**

---

## 💻 Usage  
## 💻 نحوه استفاده

To run the application:  
**برای اجرای برنامه:**

```bash
python main.py
```

### Workflow  
### گردش‌کار

1. Open the app and verify the InfluxDB connection.  
   **برنامه را اجرا کرده و اتصال به InfluxDB را بررسی کنید.**
2. Click **"Fetch Data from DB"** to populate the broker, symbol, and timeframe lists.  
   **روی دکمه "Fetch Data from DB" کلیک کنید تا لیست بروکرها، نمادها و تایم‌فریم‌ها بارگذاری شود.**
3. Choose analysis parameters and select brokers.  
   **پارامترهای تحلیل را انتخاب کرده و بروکرهای موردنظر را علامت بزنید.**
4. Click **"Start Analysis"**.  
   **روی دکمه "Start Analysis" کلیک کنید.**
5. View results in the **Cluster Plot** and **Detailed Report** tabs.  
   **نتایج را در تب‌های "Cluster Plot" و "Detailed Report" مشاهده کنید.**

---

## 📂 Project Structure  
## 📂 ساختار پروژه

```
Griffin/
├── .env                  # Environment variables  /  متغیرهای محیطی
├── main.py               # Entry point           /  فایل اصلی برنامه
├── requirements.txt      # Dependencies          /  وابستگی‌های پروژه
├── core/
│   └── analysis_engine.py    # Core logic         /  منطق تحلیل داده
├── ui/
│   └── main_window.py        # GUI components     /  اجزای رابط کاربری
└── utils/
    ├── pandas_model.py       # DataFrame model    /  مدل داده‌های جدول‌نما
    └── worker.py             # Background tasks   /  وظایف پس‌زمینه
```

---

## 🤝 Contributing  
## 🤝 مشارکت در توسعه

We welcome contributions! To contribute:  
**مشارکت شما خوش‌آمد است! برای همکاری:**

1. Fork the repository.  
   **مخزن را فورک کنید.**
2. Create a feature branch:

```bash
git checkout -b feature/AmazingFeature
```

3. Commit your changes:

```bash
git commit -m "Add AmazingFeature"
```

4. Push to your fork:

```bash
git push origin feature/AmazingFeature
```

5. Open a Pull Request.  
   **در GitHub یک Pull Request باز کنید.**

---

## 📜 License  
## 📜 مجوز

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.  
**این پروژه تحت مجوز GNU GPL نسخه ۳ منتشر شده است. برای اطلاعات بیشتر به فایل LICENSE مراجعه کنید.**
