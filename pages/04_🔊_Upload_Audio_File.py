import whisper
import streamlit as st
from streamlit_lottie import st_lottie
from utils import write_vtt, write_srt
import ffmpeg
import requests
from typing import Iterator
from io import StringIO
import numpy as np
import pathlib
import os
import torch
from zipfile import ZipFile
from io import BytesIO
import base64
import re

st.set_page_config(page_title="Auto Transcriber", page_icon="🔊", layout="wide")

torch.cuda.is_available()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
loaded_model = whisper.load_model("small", device=DEVICE)

# Define a function that we can use to load lottie files from a link.
@st.cache(allow_output_mutation=True)
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


APP_DIR = pathlib.Path(__file__).parent.absolute()

LOCAL_DIR = APP_DIR / "local_audio"
LOCAL_DIR.mkdir(exist_ok=True)
save_dir = LOCAL_DIR / "output"
save_dir.mkdir(exist_ok=True)


col1, col2 = st.columns([1, 3])
with col1:
    lottie = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_1xbk4d2v.json")
    st_lottie(lottie)

with col2:
    st.write("""
    ## Auto Transcriber
    ##### Input an audio file and get a transcript.
    ###### ➠ If you want to transcribe the audio in its original language, select the task as "Transcribe"
    ###### ➠ If you want to translate the transcription to English, select the task as "Translate" """)


def inferecence(loaded_model, uploaded_file, task):
    with open(f"{save_dir}/input.mp3", "wb") as f:
            f.write(uploaded_file.read())
    audio = ffmpeg.input(f"{save_dir}/input.mp3")
    audio = ffmpeg.output(audio, f"{save_dir}/output.wav", acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(audio, overwrite_output=True)
    if task == "Transcribe":
        options = dict(task="transcribe", best_of=5)
        results = loaded_model.transcribe(f"{save_dir}/output.wav", **options)
        vtt = getSubs(results["segments"], "vtt", 80)
        srt = getSubs(results["segments"], "srt", 80)
        lang = results["language"]
        return results["text"], vtt, srt, lang
    elif task == "Translate":
        options = dict(task="translate", best_of=5)
        results = loaded_model.transcribe(f"{save_dir}/output.wav", **options)
        vtt = getSubs(results["segments"], "vtt", 80)
        srt = getSubs(results["segments"], "srt", 80)
        lang = results["language"]
        return results["text"], vtt, srt, lang
    else:
        raise ValueError("Task not supported")


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


def main():
    input_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a"])
    if input_file is not None:
        filename = input_file.name[:-4]
    else:
        filename = None
    task = st.selectbox("Select Task", ["Transcribe", "Translate"], index=0)
    if task == "Transcribe":
        if st.button("Transcribe"):
            with st.spinner("Transcribing the audio..."):
                results = inferecence(loaded_model, input_file, task)
            col3, col4 = st.columns(2)
            
            with col3:
                st.audio(input_file)
                
            # Split result["text"]  on !,? and . , but save the punctuation
            sentences = re.split("([!?.])", results[0])
            # Join the punctuation back to the sentences
            sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
            text = "\n\n".join(sentences)
            with open("transcript.txt", "w+", encoding='utf8') as f:
                f.writelines(text)
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
            
            zipObj = ZipFile("transcripts.zip", "w")
            zipObj.write("transcript.txt")
            zipObj.write("transcript.vtt")
            zipObj.write("transcript.srt")
            zipObj.close()
            ZipfileDotZip = "transcripts.zip"
            with open(ZipfileDotZip, "rb") as f:
                datazip = f.read()
                b64 = base64.b64encode(datazip).decode()
                href = f"<a href=\"data:file/zip;base64,{b64}\" download='{ZipfileDotZip}'>\
        Download Transcripts\
    </a>"
            st.markdown(href, unsafe_allow_html=True)

    elif task == "Translate":
        if st.button("Translate to English"):
            with st.spinner("Translating to English..."):
                results = inferecence(loaded_model, input_file, task)
            col3, col4 = st.columns(2)

            with col3:
                st.audio(input_file)
                
            # Split result["text"]  on !,? and . , but save the punctuation
            sentences = re.split("([!?.])", results[0])
            # Join the punctuation back to the sentences
            sentences = ["".join(i) for i in zip(sentences[0::2], sentences[1::2])]
            text = "\n\n".join(sentences)
            with open("transcript.txt", "w+", encoding='utf8') as f:
                f.writelines(text)
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
                
            zipObj = ZipFile("transcripts.zip", "w")
            zipObj.write("transcript.txt")
            zipObj.write("transcript.vtt")
            zipObj.write("transcript.srt")
            zipObj.close()
            ZipfileDotZip = "transcripts.zip"
            with open(ZipfileDotZip, "rb") as f:
                datazip = f.read()
                b64 = base64.b64encode(datazip).decode()
                href = f"<a href=\"data:file/zip;base64,{b64}\" download='{ZipfileDotZip}'>\
        Download Transcripts\
    </a>"
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("Please select a task.")


if __name__ == "__main__":
    main()