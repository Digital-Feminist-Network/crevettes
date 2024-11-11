# crevettes

A Python utility to capture a thread and commends for a given Reddit thread. This utility came out of a research need for the [Digital Feminist Network](https://digfemnet.org/).

## Requirements

* [praw](https://github.com/praw-dev/praw)
* [python-dotenv](https://github.com/theskumar/python-dotenv)

## Usage

Local CSV
```
crevettes thread_id
```

Google Sheets and Local CSV.
```
crevettes thread_id google_sheets_folder_id path/to/json/keyfile 
```

## Example

```
crevettes 1bq51lp
```

```
crevettes 1gnex8a 1Nr1xMEN1WTxrwNfyFz4fg1fTyB3oCAcg
```

You will need a `.env` file populated with the following:

```
REDDIT_CLIENT_ID=YOUR_CLIENT_ID
REDDIT_CLIENT_SECRET=YOUR_CLIENT_SECRET
REDDIT_USER_AGENT=YOUR_USER_AGENT
```

## License

The Unlicense
