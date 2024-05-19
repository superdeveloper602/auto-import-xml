import csv
from openai import OpenAI
from dotenv import load_dotenv
from io import StringIO
import os
from collections import defaultdict
import re

def filter_csv_file(input_filename, delimiter='~'):
    filtered_rows = []
    
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        
        for row in reader:
            if row[2]:  # Assuming 'content' is the third column (index 2)
                filtered_rows.append(row)
    
    return filtered_rows

def calculate_average_ratings(filtered_rows):
    averages = defaultdict(list)
    
    for row in filtered_rows:
        created_at, articleId, content, pointsEarned, userid, ratingInterest, ratingClearPleasant, ratingInformative, id = row
        ratingInterest = float(ratingInterest)
        ratingClearPleasant = float(ratingClearPleasant)
        ratingInformative = float(ratingInformative)
        
        average_rating = (ratingInterest + ratingClearPleasant + ratingInformative) / 3
        averages[articleId].append(round(average_rating,))
    
    # Calculate the mean average rating per article
    average_ratings = {articleId: sum(ratings) / len(ratings) for articleId, ratings in averages.items()}
    
    return average_ratings

def analyze_content_with_chatgpt(content):
    # Define the questions to ask
    print("review: " + content)
    # Prepare the messages for the API request
    messages = [
      {"role": "system", "content": "Des avis d'utilisateurs vous seront présentés sur un article et votre travail consiste à répondre à chacune des questions suivantes. Les questions sont les suivantes :\n - Quels aspects positifs sont mentionnés ? \n - Quels aspects négatifs sont mentionnés ?\n - Quelles suggestions d'amélioration sont mentionnées ?\n - Quel est le sentiment général de l'avis ? (positif, négatif, neutre)\n. Vous fournirez des réponses uniques à chaque question. Chaque réponse ne doit inclure que son prédicat, en omettant toutes les parties inutiles telles que « points mentionnés : », et ne renvoie pas de réponses non pertinentes et n'ajoute pas de caractère de nouvelle ligne dans chacune de vos réponses. S'il n'y a rien à apporter, laissez la réponse vide. répond avec un tilde (~) ENTRE chaque question pour une analyse plus facile."},
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
    print("content: " + response.choices[0].message.content)
    parts = content.split('~')
    print("parts: " + str(parts))
    # Remove any leading/trailing whitespace and filter out empty parts
    parts = [part.strip() for part in parts if part.strip()]

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
        articleId = row[1]  # Assuming 'articleId' is the fifth column (index 1)
        content = row[2]    # Assuming 'content' is the third column (index 2)
        reviews_by_article[articleId].append(content)
    
    return reviews_by_article

def determine_overall_sentiment(sentiments):
    return sentiments["sentiment"]

def get_article_review_summary(articleId, reviews_by_article):
    if articleId not in reviews_by_article:
        return {"articleId": articleId, "total_reviews": 0, "overall_sentiment": "neutre"}
    
    reviews = reviews_by_article[articleId]
    total_reviews = len(reviews)
    print("total_reviews: ", reviews)
    print("articleId: ", articleId)
    count_positive = 0
    count_negative = 0
    for review in reviews:
        sentiments = analyze_content_with_chatgpt(review)
        result = determine_overall_sentiment(sentiments)
        if 'positif' in result.lower() or 'positive' in result.lower():
            count_positive += 1
        if 'négatif' in result.lower() or 'negative' in result.lower():
            count_negative += 1
    
    if count_positive == count_negative:
      overall_sentiment = "neutre"
    elif count_positive > count_negative:
      overall_sentiment = "positif"
    else:
      overall_sentiment = "négatif"
    
    return {
        "articleId": articleId,
        "total_reviews": total_reviews,
        "overall_sentiment": overall_sentiment
    }

def get_user_statistics(input_filename, delimiter='~'):
    total_users = set()
    unique_users = set()

    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        
        for row in reader:
            if row[5]:  # Assuming 'userid' is the sixth column (index 5)
                total_users.add(row[5])  # Add user ID to total users set
                if row[2]:  # Assuming 'content' is the third column (index 2)
                    unique_users.add(row[5])  # Add user ID to unique users set

    total_users_count = len(total_users)
    unique_users_count = len(unique_users)

    return total_users_count, unique_users_count

def export_feedback_to_csv(output_filename, filtered_rows, average_ratings):
    with open(output_filename, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile,delimiter='~')
        writer.writerow(["review", "rating", "positive_points", "negative_points", "suggestions", "sentiment"])
        print('average_ratings: ', average_ratings)
        for row in filtered_rows:
            created_at, articleId, content, pointsEarned, userid, ratingInterest, ratingClearPleasant, ratingInformative, id = row
            analysis = analyze_content_with_chatgpt(content)
            writer.writerow([
                content,
                average_ratings[articleId],
                analysis["positive_points"],
                analysis["negative_points"],
                analysis["suggestions"],
                analysis["sentiment"]
            ])

def export_article_summary_to_csv(output_filename, article_summaries, average_ratings):
    with open(output_filename, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='~')
        writer.writerow(["articleId", "averageRating", "reviewsCount", "overallSentiment"])
        print('article_summaries: ', article_summaries)
        for article_summary in article_summaries:
            articleId = article_summary["articleId"]
            writer.writerow([
                articleId,
                average_ratings.get(articleId, 0),
                article_summary["total_reviews"],
                article_summary["overall_sentiment"]
            ])

def main(input_filename, feedback_output_filename, summary_output_filename):
    # Step 1: Filter the CSV data
    filtered_rows = filter_csv_file(input_filename)
    
    # Step 2: Calculate average ratings
    average_ratings = calculate_average_ratings(filtered_rows)
    
    # Step 3: Aggregate reviews by article (return map from articleId to list of reviews)
    reviews_by_article = aggregate_reviews_by_article(filtered_rows)
    
    # Step 4: Summarize reviews for each article
    article_summaries = []
    for articleId in reviews_by_article.keys():
        summary = get_article_review_summary(articleId, reviews_by_article)
        article_summaries.append(summary)
    # Step 5: Export the feedback data to a CSV file
    export_feedback_to_csv(feedback_output_filename, filtered_rows, average_ratings)
    
    # Step 6: Export the summary data to a CSV file
    export_article_summary_to_csv(summary_output_filename, article_summaries, average_ratings)

# File names
input_filename = 'reviews.csv'
feedback_output_filename = 'feedback_details.csv'
summary_output_filename = 'article_summary.csv'

main(input_filename, feedback_output_filename, summary_output_filename)
