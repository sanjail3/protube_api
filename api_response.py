from fastapi import FastAPI, Request, Response
from youtube_transcript_api import YouTubeTranscriptApi
import openai

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()




@app.post("/summary")
async def generate_summary(request: Request):
    data = await request.json()
    youtube_link = data['youtube_link']
    youtube_link = str(youtube_link)

    # Define the maximum number of tokens for OpenAI completion
    max_tokens = 4000

    def generate_segment_summary(transcript):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": transcript + "this is one of the chapter in video create chapter title and summarise in key points answer should be Chapter title and summary"}
            ]
        )
        summary = completion.choices[0].message.content
        return summary

    def generate_full_summary(transcript):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": transcript + " the above is the different chapter summary of youtube video transcript from this give me only major keytake away don't give other answer your answer should be Keypoints: and answer don't mention any chapter here you give only main keypoints"}
            ]
        )
        summary = completion.choices[0].message.content
        return summary

    def get_link(url):
        pattern = r"(?<=v=)[\w-]+"
        match = re.search(pattern, url)
        if match:
            video_id = match.group()
            return video_id
        else:
            return "Invalid YouTube URL."

    video_id = get_link(youtube_link)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'], preserve_formatting=True)
    transcript_text = " ".join([t['text'] for t in transcript])
    chapter_length = 300

    # Create an empty list to store the chapters
    chapters = []

    # Loop through each segment of the transcript
    for i, segment in enumerate(transcript):
        # Determine the start time of the current segment
        start_time = segment["start"]

        # Determine the chapter number for the current segment
        chapter_number = math.floor(start_time / chapter_length) + 1

        # If this is the first segment in a new chapter, create a new chapter dictionary
        if len(chapters) < chapter_number:
            chapter = {"number": chapter_number, "segments": []}
            chapters.append(chapter)
        else:
            chapter = chapters[chapter_number - 1]

        # Add the current segment to the current chapter
        chapter["segments"].append(segment)

    # Generate chapter summaries
    chapter_summary = []
    for chapter in chapters:
        txt = f"Chapter {chapter['number']}: "
        for segment in chapter["segments"]:
            txt += segment['text']
        chap_sum = generate_segment_summary(txt)
        chapter_summary.append(chap_sum)

    full_chap = " ".join([i for i in chapter_summary])
    summary = generate_full_summary(full_chap)

    # Create JSON response
    response = {
        "chapter_summary": chapter_summary,
        "overall_summary": summary
    }

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
