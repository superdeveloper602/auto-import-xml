import xml.etree.ElementTree as ET
import csv
import os

def import_xml_data(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        articles = process_articles(root)
        write_to_csv(articles, 'temp_data.csv')
        return True
    except Exception as e:
        print(f'Failed to import XML data from {xml_file}: {e}')
        return False

def process_articles(root):
    articles = []
    article_list = root.findall('.//articlelist/article')
    for article in root.findall('.//article'):
      article_id = article.find(".//metadata[@name='ArticleId']").get('value')
    article_name = article.find(".//metadata[@name='Articlename']").get('value')
    
    content = ""
    for box in article.findall('.//box'):
        content_elements = box.findall('.//paragraph')
        for p in content_elements:
            text = ''.join(p.itertext())
            content += text
    articles.append({'title': article_name, 'content': content})

    return articles

def extract_content(box):
    contents = []
    for paragraph in box.findall('.//paragraph'):
        paragraph_text = ' '.join(char.text for char in paragraph.findall('character'))
        contents.append(paragraph_text)
    return ' '.join(contents)

def write_to_csv(articles, file_path):
    # Check if the file exists to determine if we need to write headers
    file_exists = os.path.isfile(file_path)
    
    try:
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            fieldnames = ['title', 'content']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()  # Write header only if the file did not exist

            for article in articles:
                writer.writerow({'title': article['title'], 'content': article['content']})        
    except Exception as e:
        print(f'Error writing CSV file: {e}')


if not os.path.exists(data_folder):
    os.makedirs(data_folder)
    print(f"Created folder: {data_folder}")

# List and process files in the data folder
for file_name in os.listdir(data_folder):
    if file_name.endswith('.xml'):
        file_path = os.path.join(data_folder, file_name)
        print(f'Processing file: {file_path}')
        success = import_xml_data(file_path)
        if success:
            success_count += 1
        else:
            failure_count += 1
            
print(f'Processing complete. Success: {success_count}, Failures: {failure_count}')
