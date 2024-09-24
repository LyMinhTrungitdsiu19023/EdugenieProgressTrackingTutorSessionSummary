import os
import boto3
import logging
import pandas as pd

from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from sqlalchemy import create_engine

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())


# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SCORING_TABLE_NAME = os.getenv("SCORING_TABLE_NAME")
SUMMARY_TABLE_NAME = os.getenv("SUMMARY_TABLE_NAME")
DATABASE_URI = os.getenv("DATABASE_URI")

dynamodb_client = boto3.client('dynamodb')

# Skill of evaluation skills
skills = [
    "critical_thinking",
    "emotional_awareness",
    "creative_thinking",
    "communication",
    "problem_solving"
]

# Connection engine
engine = create_engine(DATABASE_URI)

    
def fetch_all_users():
    query = "SELECT us.user_id AS user_id, vc.id AS video_call_session_id FROM user_scenario us INNER JOIN video_call_session vc ON us.id = vc.user_scenario_id WHERE vc.deleted_at IS NULL AND us.user_id IS NOT NULL"
    return pd.read_sql_query(query, engine)
    
    
def filter_scores(query_result):
    items = query_result["Items"]
    scores = []
    for item in items:
        scores.append({key: next(iter(value.values())) for key, value in item.items() if key in skills})
    scores = pd.DataFrame(scores).astype('float').mean().round(2)
    return scores
    

def query_scores(series, today, yesterday):
    video_call_session_id = series['video_call_session_id']
    try:
        query = {
            "TableName": SCORING_TABLE_NAME,
            "KeyConditions": {
                "video_call_session_id": {
                    "AttributeValueList": [{"N": str(video_call_session_id)}],
                    "ComparisonOperator": "EQ"
                },
                "end_time": {
                    "AttributeValueList": [{"S": yesterday}, {"S": today}],
                    "ComparisonOperator": "BETWEEN"
                }
            },
            "ScanIndexForward": False
        }
        query_result = dynamodb_client.query(**query)
        scores = filter_scores(query_result)
        series = pd.concat([series, scores])
        return series
    except ClientError as e:
        logging.info("An error occurred during query on DynamoDB: {}".format(e))
        raise e
    
    
def save_records(user_score_df):
    try:
        user_score_df.to_sql(SUMMARY_TABLE_NAME, engine, if_exists="append", index=False)
        logging.info("Data inserted successfully!")
    except Exception as e:
        logging.info("Error inserting data:", e)
        
        
def main(event, context):
    # Get dates
    today = datetime.utcnow().replace(minute=0, second=0, microsecond=0).isoformat()
    yesterday = (datetime.utcnow() - timedelta(days=1)).replace(minute=0, second=0).isoformat()
    
    # Get list of users with available history messages
    user_df = fetch_all_users()
    user_score_df = user_df.apply(lambda x: query_scores(x, today, yesterday), axis=1).astype({
        "user_id": "int",
        "video_call_session_id": "int"
    })
    if len(user_score_df) > 0:
        user_score_df = user_score_df.dropna(subset=skills).groupby("user_id")[skills].agg("mean").reset_index()
        user_score_df["created_date"] = today
        user_score_df["updated_date"] = today
        save_records(user_score_df)
    else:
        logging.info("No record found")

    
if __name__ == "__main__":
    event = {""}
    main(event, None)
