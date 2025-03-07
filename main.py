from brand import brand_scraping
from products import products_scraping
from raw_materials import raw_materials_scraping

def main():
    products_scraping()
    brand_scraping()
    raw_materials_scraping()


if __name__ == "__main__":
    main()
