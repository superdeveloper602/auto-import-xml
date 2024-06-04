import xml.etree.ElementTree as ET
import csv
import os
import re
import datetime
import string

excludedTextPhrases = ['la météo', 'le top 10', 'à voir']
multiplePartsTitle = ['1000 vies']

def split_mixed_case(s):
    result = []
    current_word = ""
    counter = 0

    if len(s) <= 3:
        return s

    for char in s:
        if char.isupper() or char in string.punctuation or char.isdigit():
            if counter < 3 and current_word:
                return s
            result.append(current_word)
            current_word = ""
            counter = 0

        current_word += char
        counter += 1

    if counter >= 3:
        result.append(current_word)

    if len(result) > 1:
        return " ".join(result)
    elif len(result) == 1:
        return result[0]
    else:
        return s

def is_valid_french_date(date_str):
    # French months in order
    months_fr = ["janvier", "février", "mars", "avril", "mai", "juin",
                 "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

    # Split the date string into components
    parts = date_str.strip().split()
    if len(parts) != 3:
        return False

    day, month, year = parts

    # Check if the month is valid
    if month.lower() not in months_fr:
        return False

    # Check if day and year are integers and within a valid range
    try:
        day = int(day)
        year = int(year)
        if not (1 <= day <= 31):
            return False
        if not (1000 <= year <= 9999):
            return False
    except ValueError:
        return False

    # Additional checks for date validity could include leap year calculations, etc.
    # For now, this basic check will do
    return True

def import_xml_data(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        articles = process_articles(root)
        write_to_csv(articles, 'temp_data.csv')
        return True
    except Exception as e:
        print(f'Failed to import XML data from {xml_file}: {e}, {e.__traceback__.tb_lineno}')
        return False

def get_metadata_value(root, name):
    for elem in root.findall(f'.//metadata[@name="{name}"]'):
        return elem.get('value')

def process_articles(root):
    try:
        articles = []
        # Iterate over each article found in the root
        for article in root.findall('.//article'):
            article_id = article.find(".//metadata[@name='ArticleId']").get('value')
            
            # Initialize variables to store the article name and content
            article_name = ""
            content = ""
            
            # Gather all header and paragraph elements within the current article
            headers = article.findall('.//h1') + article.findall('.//h2') + article.findall('.//h3') + article.findall('.//h4') + article.findall('.//h5')
            
            paragraphs = article.findall('.//paragraph')

            section_value = get_metadata_value(root, 'Section')
            print(f'Section value: {section_value}')

            publication_value = get_metadata_value(root, 'Publication')
            print(f'Publication value: {publication_value}')
                
            issue_date = root.find(".//metadata[@name='Issuedate']").get('value')
            print(issue_date)
            sports_content = ""
            subheader = ""
            isJournaliste = False

            # Process each header and paragraph
            for header in article.findall('.//h1'):
                text = ''.join(header.itertext()).strip()
                article_name += text + " "
            for i, p in enumerate(paragraphs):
                text = ''.join(p.itertext()).strip()
                style = p.get('style')
                if style == "600_Sports%3a670_!_INT_enc_x23":
                    sports_content += text + " "
                elif style == "400_Actu_Eco%3a420_!_TIT_edito_x04":
                    subheader = text
                elif style == "200_Texte_de_base%3a211_!_SIG_couleur_x07":
                    if i == 1 and text.startswith("Journaliste"):
                        isJournaliste = True
                        continue
                content += text + " "

            if article_name.lower() in excludedTextPhrases:
                continue
            if article_name in multiplePartsTitle:
                ### add the rest of logic
                if i >= 1:
                    article_name += " " + subheader
            
            if article_name.startswith("En bref") or article_name.startswith("En bref..."):
                print("article_name"+ article_name)
                article_name = ""
                for header in headers:
                    text = ''.join(header.itertext()).strip()
                    article_name += text + " "
                articles.append({'title': article_name, 'content': content, 'issue_date': issue_date, 'section': section_value, 'author': publication_value})
                continue

            # Only append the article if the name has more than one word
            if len(article_name.split()) > 1:
                # Check if the first word has an internal uppercase letter
                temp = article_name
                split = article_name.split()
                if len(split) >= 1:
                    split[0] = split_mixed_case(split[0])
                    tempFirst = ' '.join(split)
                    temp = tempFirst.strip()
                if article_name.startswith('Page') or article_name.startswith('Le top 10'):
                    continue
                articles.append({'title': temp, 'content': content, 'issue_date': issue_date, 'section': section_value, 'author': publication_value})
        return articles
    except Exception as e:
        print(f'Error processing articles: {e} ,{e.__traceback__.tb_lineno}')


def extract_content(box):
    contents = []
    for paragraph in box.findall('.//paragraph'):
        paragraph_text = ' '.join(char.text for char in paragraph.findall('character'))
        contents.append(paragraph_text)
    return ' '.join(contents)

def write_to_csv(articles, file_path):
    # Determine if the file exists to decide if we need to write headers and to avoid duplicates
    file_exists = os.path.isfile(file_path)

    existing_articles = set()
    # If file exists, load existing data to check for duplicates
    if file_exists:
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                # Adjust the reader to use the custom delimiter
                reader = csv.DictReader(file, delimiter='~')
                existing_articles = {frozenset(row.items()) for row in reader}
        except Exception as e:
            print(f'Error reading existing CSV file: {e}, {e.__traceback__.tb_lineno}')
            return

    try:
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            fieldnames = ['title', 'content', 'issue_date', 'section', 'author']
            # Adjust the writer to use the custom delimiter
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='~')
            
            if not file_exists:
                writer.writeheader()  # Write header only if the file did not exist

            for article in articles:
                
                article_entry = {'title': article['title'], 'content': article['content'], 'issue_date': article['issue_date'], 'section': article['section'], 'author': article['author']}
                # Convert article entry to a frozen set of items for comparison
                article_frozen = frozenset(article_entry.items())

                # Check if the article is already in the existing articles set
                if article_frozen not in existing_articles:
                    writer.writerow(article_entry)
                    existing_articles.add(article_frozen)  # Add this new entry to the set to avoid future duplicates
    except Exception as e:
        print(f'Error writing to CSV file: {e}, {e.__traceback__.tb_lineno}')

data_folder = './data'
success_count = 0
failure_count = 0

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