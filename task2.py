import json
import os
import re
from data_saver import upload_to_drive
# Function to load JSON data from a file
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

# Function to sanitize file names (removes invalid characters)
def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)  
    filename = re.sub(r'[\n\r]', '', filename)  
    return filename

# Function to extract countries from brands based on the product's brand name
def get_countries_by_brand(brand_name, brands):
    brand_name = brand_name.strip().lower()  
    for brand in brands:
        if brand.get('Name', '').strip().lower() == brand_name:
            return brand.get('Countries', [])
    return []  # Return empty if brand is not found

# Function to check if a material is used in a product based on INCI
def is_material_used_in_product(material_inci, product_ingredients):
    if not material_inci or not product_ingredients:
        return False  #

    for inci in material_inci.split("\n"):
        if inci.strip().lower() in product_ingredients.lower():
            return True
    return False

# Function to generate documentation for each material
def generate_documentation(materials, brands, products, output_dir, drive_folder_id=None):
    os.makedirs(output_dir, exist_ok=True)  

    material_product_map = {material.get('Name', 'Unknown Material'): [] for material in materials}

    for product in products:
        if not product:
            continue

        product_name = product.get('Name', 'Unknown Product')
        brand_name = product.get('Brand', 'Unknown Brand')
        countries = get_countries_by_brand(brand_name, brands)
        product_ingredients = product.get('Ingredients', '')

        print(f"Processing Product: {product_name}, Brand: {brand_name}, Countries: {countries}")

        for material in materials:
            if not material:
                continue

            material_name = material.get('Name', 'Unknown Material')
            material_slug = sanitize_filename(material_name.lower().replace(' ', '_').replace('®', '').replace('.', ''))
            file_name = f"{material_slug}.doc"
            file_path = os.path.join(output_dir, file_name)

            # Get the INCI list for the material
            inci_list = material.get('INCI', '')

            # Check if the product uses the material
            if is_material_used_in_product(inci_list, product_ingredients):
                material_product_map[material_name].append(product_name)

            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"{material_name}\n\n")
                    file.write(f"Manufacturer: {material.get('Manufacturer', 'N/A')}\n\n")
                    file.write(f"Composition: {material.get('Composition', 'N/A')}\n\n")
                    file.write("INCI List:\n")
                    file.write(inci_list if inci_list else 'N/A')
                    file.write("\n\n")
                    file.write(f"Status: {material.get('Status', 'N/A')}\n\n")
                    file.write(f"Expiration Date: {material.get('Expiration', 'N/A')}\n\n")

                    file.write(f"Brand: {brand_name}\n\n")
                    file.write(f"Countries: {', '.join(countries) if countries else 'Not available'}\n\n")

                # Upload file to Google Drive
                if drive_folder_id:
                    upload_to_drive(file_path, drive_folder_id)

            except PermissionError:
                print(f"Permission denied: {file_path}. Skipping this file.")
                continue

    # Append product list to material documentation
    for material in materials:
        material_name = material.get('Name', 'Unknown Material')
        file_name = sanitize_filename(material_name.lower().replace(' ', '_').replace('®', '').replace('.', '')) + '.doc'
        file_path = os.path.join(output_dir, file_name)

        if material_product_map.get(material_name):
            try:
                with open(file_path, 'a', encoding='utf-8') as file:
                    file.write("\nProducts using this material:\n")
                    for product in material_product_map[material_name]:
                        file.write(f"- {product}\n")
                    file.write("\n---\n\n")

                # Upload updated file to Google Drive
                if drive_folder_id:
                    upload_to_drive(file_path, drive_folder_id)

            except PermissionError:
                print(f"Permission denied: {file_path}. Skipping this file.")
                continue

def main():
    products_file = 'scraped_data/products.json'
    materials_file = 'scraped_data/raw_materials.json'
    brands_file = 'scraped_data/Brands.json'
    output_dir = 'material_docs'
    drive_folder_id = "google drive folder id"  

    # Load the data
    products = load_json(products_file)
    materials = load_json(materials_file)
    brands = load_json(brands_file)

    # Debugging: Print sample data to verify JSON is loaded correctly
    print(f"Loaded {len(products)} products, {len(materials)} materials, {len(brands)} brands")

    # Generate documentation and upload to Google Drive
    generate_documentation(materials, brands, products, output_dir, drive_folder_id)
    print(f"Documentation generated in '{output_dir}' directory and uploaded to Google Drive.")

if __name__ == '__main__':
    main()

