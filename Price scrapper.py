import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import re
EXCHANGE_RATE_API_KEY = "c5da0eb5a2673182d46ccce5"
BASE_API_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/"
def clean_price(price_str):
    """Extract numeric value from price string"""

    cleaned = re.sub(r'[^\d.]', '', price_str)
    return float(cleaned)

def get_currency_rates(base_currency):
    """Get live currency conversion rates from exchangerate-api.com"""
    try:
        response = requests.get(f"{BASE_API_URL}{base_currency}")
        response.raise_for_status()
        data = response.json()
        
        if data['result'] == 'success':
            return data['conversion_rates']
        else:
            print(f"API Error: {data.get('error-type', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching currency rates: {e}")
        return None

def scrape_books_to_scrape():
    """Scrape product data from books.toscrape.com with proper encoding handling"""
    base_url = "https://books.toscrape.com/"
    products = []
    
    try:
        print("Connecting to books.toscrape.com...")
        response = requests.get(base_url)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        product_containers = soup.find_all('article', class_='product_pod')
        
        for container in product_containers[:10]:
            try:
                title = container.h3.a['title']
                price_element = container.find('p', class_='price_color')
                price_str = price_element.text.strip()
                
                price = clean_price(price_str)
                
                products.append({
                    'name': title,
                    'price_original': price,
                    'currency_original': 'GBP' 
                })
                
            except (AttributeError, ValueError, TypeError) as e:
                print(f"Skipping product due to error: {str(e)}")
                continue
                
    except requests.exceptions.RequestException as e:
        print(f"Failed to scrape website: {str(e)}")
        return None
        
    return products if products else None

def convert_prices(products, target_currency):
    """Convert product prices to target currency using live rates"""
    if not products:
        return products
    
    base_currency = products[0]['currency_original']
    
    rates = get_currency_rates(base_currency)
    if not rates:
        print("Using default conversion rates as fallback")
        rates = {
            'USD': 1.27,
            'KES': 160.50,
            'EUR': 1.17,
            'GBP': 1.0
        }
    
    if target_currency not in rates:
        print(f"Target currency {target_currency} not available in conversion rates")
        return products
    
    conversion_rate = rates[target_currency]
    
    for product in products:
        product['price_converted'] = product['price_original'] * conversion_rate
        product['currency_target'] = target_currency
    
    return products

def save_to_csv(products, filename='product_prices.csv'):
    """Save product data to CSV file"""
    df = pd.DataFrame(products)
    df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    columns = ['timestamp', 'name', 'price_original', 'currency_original', 
               'price_converted', 'currency_target']
    df = df[columns]
    
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def display_table(products):
    """Display product data in a nice table format"""
    if not products:
        print("No products to display")
        return
    
    df = pd.DataFrame(products)
    print("\nProduct Prices:")
    print(df[['name', 'price_original', 'currency_original', 
              'price_converted', 'currency_target']].to_string(index=False))

def plot_prices(products):
    """Plot a simple bar chart comparing original and converted prices"""
    if not products or 'price_converted' not in products[0]:
        print("No conversion data available for plotting")
        return
    
    df = pd.DataFrame(products)
    
    df['short_name'] = df['name'].apply(lambda x: x[:15] + '...' if len(x) > 15 else x)
    
    plt.figure(figsize=(12, 6))

    plt.bar(df['short_name'], df['price_original'], width=0.4, 
            label=f"Original ({products[0]['currency_original']})")

    plt.bar(df['short_name'], df['price_converted'], width=0.4, 
            label=f"Converted ({products[0]['currency_target']})", alpha=0.7)
    
    plt.title('Product Price Comparison')
    plt.ylabel('Price')
    plt.xlabel('Product Name')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    print("=== Price Scraper & Currency Converter ===")
    
    products = scrape_books_to_scrape()
    
    if not products:
        print("Failed to get product data. Exiting.")
        return

    while True:
        target_currency = input("Enter target currency (3-letter code like USD, KES, EUR): ").strip().upper()
        if len(target_currency) == 3 and target_currency.isalpha():
            break
        print("Invalid input. Please enter a 3-letter currency code.")
    
    converted_products = convert_prices(products, target_currency)
    if not converted_products:
        print("Failed to convert prices. Showing original prices.")
        converted_products = products
        

    display_table(converted_products)
    save_to_csv(converted_products)
    plot_prices(converted_products)
    
    print("\nDone!")

if __name__ == "__main__":
    main()