import csv
import os
import re
import time
from datetime import datetime

import gspread
import praw
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Load Reddit API environment variables.
load_dotenv()

# Initialize Reddit API using environment variables.
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)


# Google Sheets setup.
def setup_google_sheets(sheet_name, folder_id, keyfile_path):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)
    client = gspread.authorize(creds)

    # Create a new Google Sheet in the given folder.
    folder = client.create(sheet_name, folder_id=folder_id)
    sheet = folder.get_worksheet(0)
    return sheet


# Fetch a given Reddit thread by thread id.
def fetch_reddit_thread(thread_id, comment_limit=None):
    submission = reddit.submission(id=thread_id)
    submission.comments.replace_more(limit=None)

    all_comments = []

    for comment in submission.comments.list():
        all_comments.append(comment)
        # Only break if a comment_limit is set and the limit is reached.
        if comment_limit and len(all_comments) >= comment_limit:
            break
        # Delay between API calls to prevent hitting rate limits
        time.sleep(0.5)

    return submission, all_comments


# Clean titles for csv filenames.
def clean_thread_title(title):
    title = title.lower()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"\s+", "-", title)
    return title


def resize_sheet_if_needed(sheet, total_rows):
    """Resize the Google Sheet if the required number of rows exceeds current limit."""
    current_row_count = sheet.row_count
    if total_rows > current_row_count:
        new_row_count = max(total_rows, current_row_count * 2)
        sheet.resize(rows=new_row_count)
        print(f"Resized sheet to {new_row_count} rows")


def find_last_row(sheet):
    """Find the last non-empty row in the sheet."""
    str_values = sheet.col_values(1)
    return len(str_values) if str_values else 0


def write_to_csv_and_sheets(submission, comments, thread_id, sheet=None):
    clean_title = clean_thread_title(submission.title)
    csv_filename = f"reddit-{thread_id}--{clean_title}.csv"

    # Define the header row.
    header_row = [
        "timestamp",
        "thread_id",
        "thread_title",
        "thread_submitter",
        "thread_body",
        "thread_timestamp",
        "thread_vote_count",
        "comment_id",
        "comment_username",
        "comment_body",
        "comment_reply_to_id",
        "comment_vote_count",
    ]

    # Open the CSV file and write the headers.
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header_row)

        # Prepare data for batch update including the header, and start with header row.
        batch_data = [header_row]

        # Write the submission (thread) metadata to CSV and batch data.
        thread_row = [
            datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
            submission.id,
            submission.title,
            (submission.author.name if submission.author else "Deleted"),
            submission.selftext,
            datetime.fromtimestamp(submission.created_utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            submission.score,
            "",
            "",
            "",
            "",
        ]
        writer.writerow(thread_row)
        batch_data.append(thread_row)

        # Write the comments data to CSV and batch data.
        for comment in comments:
            comment_row = [
                datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
                submission.id,
                "",
                "",
                "",
                "",
                "",
                comment.id,
                (comment.author.name if comment.author else "Deleted"),
                comment.body,
                (
                    comment.parent_id.split("_")[1]
                    if comment.parent_id != submission.id
                    else ""
                ),
                comment.score,
            ]
            writer.writerow(comment_row)
            batch_data.append(comment_row)

        # Write to Google Sheets if the sheet is not None.
        if sheet:
            try:
                # Reduce chunk size to prevent hitting limits
                CHUNK_SIZE = 50
                for i in range(0, len(batch_data), CHUNK_SIZE):
                    chunk = batch_data[i : i + CHUNK_SIZE]

                    last_row = find_last_row(sheet)
                    required_rows = last_row + len(chunk)
                    resize_sheet_if_needed(sheet, required_rows)

                    requests = [
                        {
                            "range": f"A{last_row + 1}:L{last_row + len(chunk)}",
                            "values": chunk,
                        }
                    ]
                    body = {"valueInputOption": "USER_ENTERED", "data": requests}

                    sheet.spreadsheet.values_batch_update(body)
                    time.sleep(1)

            except Exception as e:
                print(f"Error during batch update: {e}")

    print(f"CSV saved as {csv_filename}")


if __name__ == "__main__":
    sheet_name = "Reddit Thread Data"
    folder_id = "YOUR_FOLDER_ID"
    sheet = setup_google_sheets(sheet_name, folder_id)
    thread_id = "YOUR_THREAD_ID"
    submission, comments = fetch_reddit_thread(thread_id, comment_limit=None)

    write_to_csv_and_sheets(submission, comments, thread_id, sheet)
