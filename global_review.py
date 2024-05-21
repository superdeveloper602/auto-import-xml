import csv
from openai import OpenAI
from dotenv import load_dotenv
from io import StringIO
import os
from collections import defaultdict
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

def filter_csv_file(input_filename, delimiter='~'):
    filtered_rows = []
    
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        
        for row in reader:
            if row[1] != "":  # Assuming 'content' is the third column (index 1)
                filtered_rows.append(row)
    
    return filtered_rows

def calculate_average_points(filtered_rows):
    article_ratings = defaultdict(lambda: {'ratingInterest': 0, 'ratingClearPleasant': 0, 'ratingInformative': 0, 'count': 0})

    for row in filtered_rows:
        created_at, content, pointsEarned, articleId, userid, ratingInterest, ratingClearPleasant, ratingInformative, id, title = row
        
        ratingInterest = float(ratingInterest)
        ratingClearPleasant = float(ratingClearPleasant)
        ratingInformative = float(ratingInformative)
        
        article_ratings[articleId]['ratingInterest'] += ratingInterest
        article_ratings[articleId]['ratingClearPleasant'] += ratingClearPleasant
        article_ratings[articleId]['ratingInformative'] += ratingInformative
        article_ratings[articleId]['count'] += 1

    average_ratings = {}
    for articleId, ratings in article_ratings.items():
        count = ratings['count']
        average_ratings[articleId] = {
            'averageRatingInterest': round(ratings['ratingInterest'] / count, 2),
            'averageRatingClearPleasant': round(ratings['ratingClearPleasant'] / count, 2),
            'averageRatingInformative': round(ratings['ratingInformative'] / count, 2)
        }
    
    return average_ratings

def remove_newlines(text):
    """
    Removes newline characters ('\n') from the input text.

    Parameters:
    text (str): The input string from which newline characters are to be removed.

    Returns:
    str: The cleaned string with newline characters removed.
    """
    cleaned_text = text.replace('\n', '')
    return cleaned_text

def analyze_content_with_chatgpt(content):
    # Define the questions to ask
    print("review: " + content)
    # Prepare the messages for the API request
    messages = [
      {"role": "system", "content": "Ceci est une liste d'avis sur des articles. Pouvez-vous me lister les points positifs, les points négatifs ainsi que les points à améliorer et le sentiment (positif, négatif ou neutre) ? Affiche uniquement le résultat et non ce sur quoi vous l'avez basé.\nSous cette forme, points_positifs~points_négatifs~points d'amélioration"},
      {"role": "user", "content": content}
    ]
    load_dotenv()
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    # Call the OpenAI API
    response = client.chat.completions.create(
      messages=messages,
      model="gpt-4",
      temperature=0.7,
      max_tokens=64,
      top_p=1
    )
    # Extract the content from the response
    print("response:" + str(response.choices))
    content = response.choices[0].message.content
    print("content_response_feedback: " + response.choices[0].message.content)
    if '~' in content:
      parts = content.split('~')
    else:
      parts = content.split('\n')
    print("parts: " + str(parts))
    # Remove any leading/trailing whitespace and filter out empty parts
    parts = [part for part in parts if part]

    # Ensure we have exactly three parts (positive, negative, suggestions)
    suggestions = ""
    negative_points = ""
    positive_points = ""
    sentiment = ""
    print("lenparts: " + str(len(parts)))
    if len(parts) >= 4:
      positive_points = parts[0]
      negative_points = parts[1]
      suggestions = parts[2]
      sentiment = parts[-1]
    elif len(parts) == 7:
      positive_points = parts[4]
      negative_points = parts[5]
      suggestions = parts[6]
      sentiment = parts[7]
    elif len(parts) == 6:
      positive_points = parts[1]
      negative_points = parts[3]
      suggestions = parts[5]
      sentiment = parts[-1]
    elif len(parts) == 3:
      positive_points, negative_points, sentiment = parts
    elif len(parts) == 2:
      positive_points, sentiment = parts
    elif len(parts) == 1:
      positive_points = parts[0]
    print("sentimel: " + sentiment)
    return {
        'positive_points': positive_points,
        'negative_points': negative_points,
        'suggestions': suggestions,
        'sentiment': sentiment
    }

def aggregate_reviews_by_article(filtered_rows):
    reviews_by_article = defaultdict(list)
    
    for row in filtered_rows:
        articleId = row[3]  # Assuming 'articleId' is the fifth column (index 1)
        content = row[1]    # Assuming 'content' is the third column (index 2)
        title = row[9]    # Assuming 'title' is the ninth column (index )
        reviews_by_article[articleId].append([content, title])
    
    return reviews_by_article

def remove_special_characters_except_colon(text):
    """
    Removes special characters and newline characters from the input text except for the colon (:) character.
    
    Parameters:
    text (str): The input string from which special characters and newlines are to be removed.
    
    Returns:
    str: The cleaned string with special characters and newlines removed except for the colon.
    """
    # Define the regex pattern to match any character that is not a letter, digit, whitespace (excluding newlines), or colon
    pattern = r'[^a-zA-Z0-9\s:]|\n|\r'
    
    # Use re.sub() to replace matched characters with an empty string
    cleaned_text = re.sub(pattern, '', text)
    
    return cleaned_text

def determine_overall_sentiment(sentiments):
    return sentiments["sentiment"]

def split_by_positive_and_negative_points(text):
    """
    Splits the input text by the delimiters 'Positive points:' and 'Negative points:' 
    and returns the parts before the colons for both positive and negative points.

    Parameters:
    text (str): The input string to be split.

    Returns:
    tuple: A tuple containing the parts of the string before the colons for positive and negative points.
    """
    # Split the text by the delimiters
    parts_negative = text.split('Negative points:')
    parts_positive = parts_negative[0].split('Positive points:')
    
    print("parts_positive: " + str(parts_positive))
    print("parts_negative: " + str(parts_negative))
    
    if len(parts_positive) > 1:
        positive_part = parts_positive[1].strip()
    else:
        positive_part = ''
        
    if len(parts_negative) > 1:
        negative_part = parts_negative[1].strip()
    else:
        negative_part = ''

    return positive_part, negative_part

def get_article_review_summary(articleId, reviews_by_article):
    if articleId not in reviews_by_article:
        return {"articleId": articleId, "total_reviews": 0, "overall_sentiment": "neutre"}
    
    reviews = reviews_by_article[articleId]
    print("total_reviews_1: ", reviews)
    print("articleId: ", articleId)
    articleTitle = reviews[0][1]
    reviews = [review[0] for review in reviews]
    total_reviews = len(reviews)
    count_positive = 0
    count_negative = 0
    positive_points = []
    negative_points = []
    suggestions = []
    # for review in reviews:
    #     reviews.append(review[0])
    #     # sentiments = analyze_content_with_chatgpt(review[0])
    #     # result = determine_overall_sentiment(sentiments)
    #     # positive_points.append(sentiments['positive_points'])
    #     # negative_points.append(sentiments['negative_points'])
    #     # print("suggestions: " + sentiments['suggestions'])
    #     # suggestions.append(sentiments['suggestions'])
    #     # if 'positif' in result.lower() or 'positive' in result.lower():
    #     #     count_positive += 1
    #     # if 'négatif' in result.lower() or 'negative' in result.lower():
    #     #     count_negative += 1

    # # if count_positive == count_negative:
    # #   overall_sentiment = "neutre"
    # # elif count_positive > count_negative:
    # #   overall_sentiment = "positif"
    # # else:
    # #   overall_sentiment = "négatif"
    
    # # positive_string = '; '.join(positive_points)
    # # negative_string = '; '.join(negative_points)

    load_dotenv()
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv('OPENAI_API_KEY'),
    )

    reviews_string = '\n'.join(reviews)
    print("reviews_string: " + reviews_string)
    # Call the OpenAI API
    response = client.chat.completions.create(
      messages=[
        {"role": "system", "content": "Ceci est une liste d'avis sur des articles. Pouvez-vous me lister les points positifs, les points négatifs ainsi que les points à améliorer et le sentiment (positif, négatif ou neutre) ? Affiche uniquement le résultat et non ce sur quoi vous l'avez basé.\nSous cette forme, points_positifs~points_négatifs~points d'amélioration"},
        {"role": "user", "content": reviews_string}
      ],
      model="gpt-4",
      temperature=0.7,
      max_tokens=64,
      top_p=1
    )
    
    # Extract the content from the response
    print("response:" + str(response.choices))
    content = response.choices[0].message.content
    print("content_response_feedback: " + response.choices[0].message.content)
    count = content.count('~')
    if count >= 3:
      parts = content.split('~')
    else:
      content.replace('~', '')
      parts = content.split('\n')
    print("parts: " + str(parts))
    # Remove any leading/trailing whitespace and filter out empty parts
    parts = [part for part in parts if part]

    # Ensure we have exactly three parts (positive, negative, suggestions)
    suggestions = ""
    negative_points = ""
    positive_points = ""
    sentiment = ""
    print("lenparts: " + str(len(parts)))
    if len(parts) >= 4:
      positive_points = parts[0]
      negative_points = parts[1]
      suggestions = parts[2]
      sentiment = parts[-1]
    elif len(parts) == 7:
      positive_points = parts[4]
      negative_points = parts[5]
      suggestions = parts[6]
      sentiment = parts[7]
    elif len(parts) == 6:
      positive_points = parts[1]
      negative_points = parts[3]
      suggestions = parts[5]
      sentiment = parts[-1]
    elif len(parts) == 3:
      positive_points, negative_points, sentiment = parts
    elif len(parts) == 2:
      positive_points, sentiment = parts
    elif len(parts) == 1:
      positive_points = parts[0]
    print("sentimel: " + sentiment)
    # return {
    #     'positive_points': positive_points,
    #     'negative_points': negative_points,
    #     'suggestions': suggestions,
    #     'sentiment': sentiment
    # }
    return {
        "articleTitle": articleTitle,  # Assuming the first review is the article title
        "postive_points": remove_newlines(positive_points.replace('"', '').replace("'", '')),
        "negative_points": remove_newlines(negative_points.replace('"', '').replace("'", '')),
        "suggestions": remove_newlines(suggestions.replace('"', '').replace("'", '')),
        "articleId": articleId,
        "total_reviews": total_reviews,
        "overall_sentiment": sentiment
    }

def get_user_statistics(input_filename, delimiter='~'):
    total_users = set()
    unique_users = set()

    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        
        for row in reader:
            if row[4]:  # Assuming 'userid' is the sixth column (index 5)
                total_users.add(row[4])  # Add user ID to total users set
                if row[1]:  # Assuming 'content' is the third column (index 2)
                    unique_users.add(row[4])  # Add user ID to unique users set

    total_users_count = len(total_users)
    unique_users_count = len(unique_users)

    return total_users_count, unique_users_count

def export_article_summary_to_csv(filtered_rows, output_filename, article_summaries):
    with open(output_filename, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=';')
        writer.writerow(["Titre Article","ID Article","Moyenne note interet","Moyenne note clarte/Plaisir","Moyenne note informative","Points positifs","Points negatifs","Point d'amelioration","Nombre de review","Sentiment Global"])
        average_ratings = calculate_average_points(filtered_rows)
        print('average_ratings: ', average_ratings)
        print('article_summaries: ', article_summaries)
        for article_summary in article_summaries:
            writer.writerow([
                article_summary["articleTitle"],
                article_summary["articleId"],
                average_ratings[article_summary["articleId"]]['averageRatingInterest'],
                average_ratings[article_summary["articleId"]]['averageRatingClearPleasant'],
                average_ratings[article_summary["articleId"]]['averageRatingInformative'],
                article_summary["postive_points"],
                article_summary["negative_points"],
                article_summary["suggestions"],
                article_summary["total_reviews"],
                article_summary["overall_sentiment"]
            ])
        
        # Adding two newlines before the user statistics section
        outfile.write('\n\n')
        
        # Writing user statistics
        writer.writerow(["Utilisateur totaux enregistrÃ©", "Utilisateur unique", "", "", "", "", "", "", ""])
        total_users_count, unique_users_count = get_user_statistics("reviews.csv")
        writer.writerow([
            total_users_count,
            unique_users_count,
            "", "", "", "", "", "", ""
        ])

def send_email_with_attachment(subject, body, to_email, csv_file_name, from_email, mailtrap_user, mailtrap_password):
    # Check if the file exists
    # if not os.path.isfile(csv_file_name):
    #     print(f"The file {csv_file_name} does not exist.")
    #     return

    # # Create a multipart message
    # msg = MIMEMultipart()
    # msg['From'] = from_email
    # msg['To'] = to_email
    # msg['Subject'] = subject

    # # Add body to email
    # msg.attach(MIMEText(body, 'plain'))

    # # Open the file to be sent
    # with open(csv_file_name, "rb") as attachment:
    #     part = MIMEBase('application', 'octet-stream')
    #     part.set_payload(attachment.read())

    # # Encode file in ASCII characters to send by email    
    # encoders.encode_base64(part)

    # # Add header as key/value pair to attachment part
    # part.add_header(
    #     "Content-Disposition",
    #     f"attachment; filename= {os.path.basename(csv_file_name)}",
    # )

    # # Attach the file
    # msg.attach(part)

    sender = "Private Person <mailtrap@demomailtrap.com>"
    receiver = "A Test User <quangkhai28999@gmail.com>"

    message = f"""\
    Subject: Hi Mailtrap
    To: {receiver}
    From: {sender}

    This is a test e-mail message."""

    with smtplib.SMTP("live.smtp.mailtrap.io", 587) as server:
      server.starttls()
      server.login(mailtrap_user, mailtrap_password)
      server.sendmail(sender, receiver, message)

    print(f"Email sent to {to_email}")

def main(input_filename, feedback_output_filename, summary_output_filename):
    # # Step 1: Filter the CSV data
    filtered_rows = filter_csv_file(input_filename)
    
    # Step 3: Aggregate reviews by article (return map from articleId to list of reviews)
    reviews_by_article = aggregate_reviews_by_article(filtered_rows)

    # Step 4: Summarize reviews for each article
    article_summaries = []
    for articleId in reviews_by_article.keys():
        summary = get_article_review_summary(articleId, reviews_by_article)
        article_summaries.append(summary)
    
    # Step 6: Export the summary data to a CSV file
    export_article_summary_to_csv(filtered_rows, summary_output_filename, article_summaries)
    
# File names
input_filename = 'reviews.csv'
feedback_output_filename = 'feedback_details.csv'
summary_output_filename = 'article_summary.csv'

subject = "Global Review"
body = "This is global review"
csv_file_name = "./article_summary.csv"

to_email = os.getenv('TO_EMAIL')
from_email = os.getenv('FROM_EMAIL')
mailtrap_user = os.getenv('MAILTRAP_USER')
mailtrap_password = os.getenv('MAILTRAP_PASSWORD')
mailtrap_server = os.getenv('MAILTRAP_SERVER')
mail_port = os.getenv('MAIL_PORT')

# main(input_filename, feedback_output_filename, summary_output_filename)
#send_email_with_attachment(subject, body, to_email, csv_file_name, from_email, mailtrap_user, mailtrap_password)

sender = f"Global Review <{from_email}>"
receiver = f"<{to_email}>"

# Create a multipart message
msg = MIMEMultipart()
msg['From'] = sender
msg['To'] = receiver
msg['Subject'] = subject

# Add body to email
msg.attach(MIMEText(body, 'plain'))

# Open the file to be sent
with open(csv_file_name, "rb") as attachment:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())

# Encode file in ASCII characters to send by email    
encoders.encode_base64(part)

# Add header as key/value pair to attachment part
part.add_header(
    "Content-Disposition",
    f"attachment; filename= {os.path.basename(csv_file_name)}",
)

# Attach the file
msg.attach(part)


with smtplib.SMTP(mailtrap_server, mail_port) as server:
    server.starttls()
    server.login(mailtrap_user, mailtrap_password)
    server.sendmail(sender, receiver, msg.as_string())