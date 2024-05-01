import xml.etree.ElementTree as ET
import csv

def import_xml_data():
    try:
        tree = ET.parse('data.xml')
        root = tree.getroot()
        articles = process_articles(root)
        print(articles)

        # Write to CSV
        write_to_csv(articles, 'temp_data.csv')
        print('Data inserted successfully.')
    except Exception as e:
        print(f'Failed to import XML data: {e}')

def process_articles(root):
    articles = []
    article_list = root.findall('.//articlelist/article')
    for article in root.findall('.//article'):
      article_id = article.find(".//metadata[@name='ArticleId']").get('value')
    article_name = article.find(".//metadata[@name='Articlename']").get('value')
    print(f"Article ID: {article_id}, Article Name: {article_name}")
    
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
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for article in articles:
                # Assuming each article is a dict with 'title' and 'content' keys
                writer.writerow([article['title'], article['content']])
        print('The CSV file was written successfully')
    except Exception as e:
        print(f'Error writing CSV file: {e}')

import_xml_data()
