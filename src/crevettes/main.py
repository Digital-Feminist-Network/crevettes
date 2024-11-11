import sys

from crevettes import harvester


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: crevettes thread_id folder_id [keyfile_path]")
        sys.exit(1)

    # Get thread ID and folder ID from command-line arguments.
    thread_id = sys.argv[1]
    folder_id = sys.argv[2]

    # Check if the optional JSON key file path is provided.
    keyfile_path = sys.argv[3] if len(sys.argv) == 4 else None

    # Fetch thread and comments.
    submission, comments = harvester.fetch_reddit_thread(thread_id)

    # Generate a clean title for both CSV and Google Sheets.
    clean_title = harvester.clean_thread_title(submission.title)
    gsheets_title = f"reddit-{thread_id}--{clean_title}"

    # Initialize Google Sheet only if JSON key file path is provided.
    sheet = None
    if keyfile_path:
        sheet = harvester.setup_google_sheets(gsheets_title, folder_id, keyfile_path)

    # Write thread metadata to both CSV and Google Sheets if the sheet is set.
    harvester.write_to_csv_and_sheets(submission, comments, thread_id, sheet)


if __name__ == "__main__":
    main()
