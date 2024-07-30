import pandas as pd
import time
from langchain_community.llms import Ollama

# Assuming LLAMA_PROMPT is defined in CONFIG
from CONFIG import LLAMA_PROMPT

def group_comments(data_path, data_stop):
    """
    Analyzes the comments data from a CSV file.
    
    Parameters:
    - data_path: str, path to the CSV file containing the data.
    - data_stop: str, the cutoff date (inclusive) for filtering the data in 'YYYY-MM-DD' format.
    
    The CSV file must contain the following columns:
    - "user": str, user ID
    - "comment": str, the comment text
    - "created_utc": date, the date of the comment in 'YYYY-MM-DD' format
    - "score": int, the score of the comment
    
    Returns:
    - A DataFrame with the comments grouped by user.
    """
    start= time.time()
    try:
        # Reading the dataframe from the CSV file
        data = pd.read_csv(data_path)
    except Exception as e:
        print("Invalid datapath:", e)
        return None

    # Convert 'created_utc' to datetime and extract only the date
    try:
        data['created_utc'] = pd.to_datetime(data['created_utc']).dt.date
    except Exception as e:
        print("Error converting 'created_utc' to date:", e)
        return None

    # Convert 'data_stop' to date
    try:
        data_stop = pd.to_datetime(data_stop).date()
    except Exception as e:
        print("Invalid data_stop format:", e)
        return None

    # Filter based on data_stop
    try:
        filtered_data = data[data['created_utc'] <= data_stop]
    except Exception as e:
        print("Error filtering data:", e)
        return None

    # Group by user and make a list of comments for each user
    try:
        grouped_data = filtered_data.groupby("user").agg({"comment": list}).reset_index()
    except Exception as e:
        print("Error grouping data:", e)
        return None

    return grouped_data

def sentiment_analysis(data_path, data_stop):
    """
    Analyzes the comments data from a CSV file.
    
    Parameters:
    - data_path: str, path to the CSV file containing the data.
    - data_stop: str, the cutoff date (inclusive) for filtering the data in 'YYYY-MM-DD' format.
    
    The CSV file must contain the following columns:
    - "user": str, user ID
    - "comment": str, the comment text
    - "created_utc": date, the date of the comment in 'YYYY-MM-DD' format
    - "score": int, the score of the comment
    
    Returns:
    - A DataFrame with the sentiment analysis labels.
    """
    start = time.time()
    print("\nInitializing sentiment analysis...\n")
    
    model = Ollama(model="llama3")
    eval = {}

    print(f"Grouping comments from data file: {data_path}\n")
    grouped_data = group_comments(data_path, data_stop)
    
    if grouped_data is None:
        print("Error: Grouping comments failed. Please check the data and try again.\n")
        return None

    print("Comments grouped successfully!\n")
    
    comments_dict = {user: comments for user, comments in zip(grouped_data["user"], grouped_data["comment"])}
    user_list = list(comments_dict.keys())

    print(f"Total users to analyze: {len(user_list)}\n")
    print("="*50)

    for i, user in enumerate(user_list, start=1):
        print(f"\nStarting sentiment analysis for user: {user} ({i}/{len(user_list)})\n")
        print("="*50)

        eval[user] = []
        comments = comments_dict[user]

        for j, comment in enumerate(comments, start=1):
            print(f"Analyzing comment {j} of {len(comments)} for user {user}:\n")
            print(f"<comment>{comment}</comment>\n")
            
            messages = " ".join([
                "<s>[INST]  <<SYS>>",
                LLAMA_PROMPT,
                "<<SYS>>",
                "{{ <comment>",
                comment,
                "</comment> }} [INST]"
            ])

            attempt = 0
            max_attempts = 5
            delay = 5  # Delay in seconds

            while attempt < max_attempts:
                try:
                    response = model.invoke(
                        messages,
                        stop=["<|eot_id|>"],
                        temperature=0
                    )
                    eval[user].append(response)
                    print(f"Analysis results for comment {j}: {response}\n")
                    break # Exit the loop if the call is successful
                except Exception as e:
                    print(f"Error processing comment {j} for user {user} (Attempt {attempt + 1}/{max_attempts}): {e}\n")
                    attempt += 1
                    if attempt < max_attempts:
                        print(f"Retrying in {delay} seconds...\n")
                        time.sleep(delay)
                    else:
                        print(f"Error processing comment: {comment}")
                        eval[user].append("<error>")

        print(f"Finished analysis for user: {user}\n")
        print("="*50)

    print("Sentiment analysis complete for all users!\n")
    print("Converting evaluation results to DataFrame...\n")
    eval_df = pd.DataFrame.from_dict(eval, orient='index').transpose()
    
    output_path = f"data/sentiment_analysis_results_{data_stop}.csv"
    eval_df.to_csv(output_path, index=False)
    end = time.time()

    print(f"TIME FOR COMPLETION = {end - start}s")
    


# Example usage:
data_path = "data/filtered_comments.csv"
data_stop = "2024-05-29"
sentiment_analysis(data_path, data_stop)
