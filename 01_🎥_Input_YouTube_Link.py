import whisper
from pytube import YouTube
import requests
import time
import streamlit as st
from streamlit_lottie import st_lottie
import numpy as np
import os
from typing import Iterator
from io import StringIO
from utils import write_vtt, write_srt
import ffmpeg
from languages import LANGUAGES

st.set_page_config(page_title="Auto Subtitled Video Generator", page_icon=":movie_camera:", layout="wide")

# Define a function that we can use to load lottie files from a link.
@st.cache(allow_output_mutation=True)
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

col1, col2 = st.columns([1, 3])
with col1:
    lottie = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_jh9gfdye.json")
    st_lottie(lottie)

with col2:
    st.write("""
    ## Auto Subtitled Video Generator 
    ##### Input a YouTube video link and get a video with subtitles.
    ###### ➠ If you want to transcribe the video in its original language, select the task as "Transcribe"
    ###### ➠ If you want to translate the subtitles to English, select the task as "Translate" 
    ###### I recommend starting with the base model and then experimenting with the larger models, the small and medium models often work well. """)
    

@st.cache(allow_output_mutation=True)
def populate_metadata(link):
    yt = YouTube(link)
    author = yt.author
    title = yt.title
    description = yt.description
    thumbnail = yt.thumbnail_url
    length = yt.length
    views = yt.views
    return author, title, description, thumbnail, length, views


@st.cache(allow_output_mutation=True)
def download_video(link):
    yt = YouTube(link)
    video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
    return video


def convert(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


loaded_model = whisper.load_model("base")
current_size = "None"


@st.cache(allow_output_mutation=True)
def change_model(current_size, size):
    if current_size != size:
        loaded_model = whisper.load_model(size)
        return loaded_model
    else:
        raise Exception("Model size is the same as the current size.")


@st.cache(allow_output_mutation=True)
def inference(link, loaded_model, task):
    yt = YouTube(link)
    path = yt.streams.filter(only_audio=True)[0].download(filename="audio.mp3")
    if task == "Transcribe":
        options = dict(task="transcribe", best_of=5)
        results = loaded_model.transcribe(path, **options)
        vtt = getSubs(results["segments"], "vtt", 80)
        srt = getSubs(results["segments"], "srt", 80)
        lang = results["language"]
        return results["text"], vtt, srt, lang
    elif task == "Translate":
        options = dict(task="translate", best_of=5)
        results = loaded_model.transcribe(path, **options)
        vtt = getSubs(results["segments"], "vtt", 80)
        srt = getSubs(results["segments"], "srt", 80)
        lang = results["language"]
        return results["text"], vtt, srt, lang
    else:
        raise ValueError("Task not supported")


@st.cache(allow_output_mutation=True)
def getSubs(segments: Iterator[dict], format: str, maxLineWidth: int) -> str:
    segmentStream = StringIO()

    if format == 'vtt':
        write_vtt(segments, file=segmentStream, maxLineWidth=maxLineWidth)
    elif format == 'srt':
        write_srt(segments, file=segmentStream, maxLineWidth=maxLineWidth)
    else:
        raise Exception("Unknown format " + format)

    segmentStream.seek(0)
    return segmentStream.read()


def get_language_code(language):
    if language in LANGUAGES.keys():
        detected_language = LANGUAGES[language]
        return detected_language
    else:
        raise ValueError("Language not supported")


def generate_subtitled_video(video, audio, transcript):
    video_file = ffmpeg.input(video)
    audio_file = ffmpeg.input(audio)
    ffmpeg.concat(video_file.filter("subtitles", transcript), audio_file, v=1, a=1).output("final.mp4").run(quiet=True, overwrite_output=True)
    video_with_subs = open("final.mp4", "rb")
    return video_with_subs        
    

def main():
    size = st.selectbox("Select Model Size (The larger the model, the more accurate the transcription will be, but it will take longer)", ["tiny", "base", "small", "medium", "large"], index=1)
    loaded_model = change_model(current_size, size)
    st.write(f"Model is {'multilingual' if loaded_model.is_multilingual else 'English-only'} "
        f"and has {sum(np.prod(p.shape) for p in loaded_model.parameters()):,} parameters.")
    link = st.text_input("YouTube Link (The longer the video, the longer the processing time)")
    task = st.selectbox("Select Task", ["Transcribe", "Translate"], index=0)
    if task == "Transcribe":
        if st.button("Transcribe"):
            author, title, description, thumbnail, length, views = populate_metadata(link)
            results = inference(link, loaded_model, task)
            video = download_video(link)
            lang = results[3]
            detected_language = get_language_code(lang)
                
            col3, col4 = st.columns(2)
            col5, col6, col7, col8 = st.columns(4)
            col9, col10 = st.columns(2)
            with col3:
                st.video(video)
                
            # Write the results to a .txt file and download it.
            with open("transcript.txt", "w+", encoding='utf8') as f:
                f.writelines(results[0])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.txt"), "rb") as f:
                datatxt = f.read()
                
            with open("transcript.vtt", "w+",encoding='utf8') as f:
                f.writelines(results[1])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.vtt"), "rb") as f:
                datavtt = f.read()
                
            with open("transcript.srt", "w+",encoding='utf8') as f:
                f.writelines(results[2])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.srt"), "rb") as f:
                datasrt = f.read()

            with col5:
                st.download_button(label="Download Transcript (.txt)",
                                data=datatxt,
                                file_name="transcript.txt")
            with col6:   
                st.download_button(label="Download Transcript (.vtt)",
                                    data=datavtt,
                                    file_name="transcript.vtt")
            with col7:
                st.download_button(label="Download Transcript (.srt)",
                                    data=datasrt,
                                    file_name="transcript.srt")
            with col9:
                st.success("You can download the transcript in .srt format, edit it (if you need to) and upload it to YouTube to create subtitles for your video.")
            with col10:
                st.info("Streamlit refreshes after the download button is clicked. The data is cached so you can download the transcript again without having to transcribe the video again.")
            
            with col4:
                with st.spinner("Generating Subtitled Video"):
                    video_with_subs = generate_subtitled_video(video, "audio.mp3", "transcript.srt")
                st.video(video_with_subs)
                st.balloons()
            with col8:
                st.download_button(label="Download Subtitled Video",
                                    data=video_with_subs,
                                    file_name=f"{title} with subtitles.mp4")
    elif task == "Translate":
        if st.button("Translate to English"):
            author, title, description, thumbnail, length, views = populate_metadata(link)
            results = inference(link, loaded_model, task)
            video = download_video(link)
            lang = results[3]
            detected_language = get_language_code(lang)
                
            col3, col4 = st.columns(2)
            col5, col6, col7, col8 = st.columns(4)
            col9, col10 = st.columns(2)
            with col3:
                st.video(video)
                
            # Write the results to a .txt file and download it.
            with open("transcript.txt", "w+", encoding='utf8') as f:
                f.writelines(results[0])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.txt"), "rb") as f:
                datatxt = f.read()
                
            with open("transcript.vtt", "w+",encoding='utf8') as f:
                f.writelines(results[1])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.vtt"), "rb") as f:
                datavtt = f.read()
                
            with open("transcript.srt", "w+",encoding='utf8') as f:
                f.writelines(results[2])
                f.close()
            with open(os.path.join(os.getcwd(), "transcript.srt"), "rb") as f:
                datasrt = f.read()
            with col5:
                st.download_button(label="Download Transcript (.txt)",
                                data=datatxt,
                                file_name="transcript.txt")
            with col6:   
                st.download_button(label="Download Transcript (.vtt)",
                                    data=datavtt,
                                    file_name="transcript.vtt")
            with col7:
                st.download_button(label="Download Transcript (.srt)",
                                    data=datasrt,
                                    file_name="transcript.srt")
            with col9:
                st.success("You can download the transcript in .srt format, edit it (if you need to) and upload it to YouTube to create subtitles for your video.")
            with col10:
                st.info("Streamlit refreshes after the download button is clicked. The data is cached so you can download the transcript again without having to transcribe the video again.")
            
            with col4:
                with st.spinner("Generating Subtitled Video"):
                    video_with_subs = generate_subtitled_video(video, "audio.mp3", "transcript.srt")
                st.video(video_with_subs)
                st.balloons()
            with col8:
                st.download_button(label="Download Subtitled Video",
                                    data=video_with_subs,
                                    file_name=f"{title} with subtitles.mp4")
    else:
        st.error("Please select a task.")


if __name__ == "__main__":
    main()
    st.markdown("###### Made with :heart: by [@BatuhanYılmaz](https://twitter.com/batuhan3326) [![this is an image link](https://i.imgur.com/thJhzOO.png)](https://www.buymeacoffee.com/batuhanylmz)")