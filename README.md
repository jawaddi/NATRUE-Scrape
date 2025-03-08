# NATRUE-Scrape

## Overview
NATRUE-Scrape is a Python-based web scraper designed to extract details about products, brands, and raw materials. The project consists of three scripts, each responsible for scraping specific data. You can either run them individually or execute all at once using `main.py`.

- **products.py for scraping products**
- **brand.py for scraping brands**
- **raw_materials.py for scraping raw materials**

## Requirements
Before running the scraper, ensure you have the following:
- **Google Sheets API enabled**
- **Google Cloud credentials set up**
- **Service account JSON file downloaded and added to the project**
- **Google Sheet created, with its name configured in the code**

## Installation & Setup

### 1. Set Up Virtual Environment
```sh
python -m venv venv
source venv/bin/activate  # For macOS/Linux
venv\Scripts\activate      # For Windows
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Run the Scraper
To run all scripts at once:
```sh
python main.py
```
To run individual scripts:
```sh
python script_name.py
```

**Note:** Don't forget to uncomment the function in the individual scripts if you want to run them alone.

