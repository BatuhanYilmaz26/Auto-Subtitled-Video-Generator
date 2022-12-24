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
from zipfile import ZipFile
from io import BytesIO
import base64

st.set_page_config(page_title="Auto Subtitled Video Generator", page_icon=":movie_camera:", layout="wide")

# Define a function that we can use to load lottie files from a link.
@st.cache(allow_output_mutation=True)
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


APP_DIR = pathlib.Path(__file__).parent.absolute()

LOCAL_DIR = APP_DIR / "local_transcript"
LOCAL_DIR.mkdir(exist_ok=True)
save_dir = LOCAL_DIR / "output"
save_dir.mkdir(exist_ok=True)


col1, col2 = st.columns([1, 3])
with col1:
    lottie = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_cjnxwrkt.json")
    st_lottie(lottie)

with col2:
    st.write("""
    ## Auto Subtitled Video Generator 
    ##### ➠ Upload a video file and a transcript as .srt or .vtt file and get a video with subtitles.
    ##### ➠ Processing time will increase as the video length increases. """)


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


def split_video_audio(uploaded_file):
    with open(f"{save_dir}/input.mp4", "wb") as f:
            f.write(uploaded_file.read())
    audio = ffmpeg.input(f"{save_dir}/input.mp4")
    audio = ffmpeg.output(audio, f"{save_dir}/output.wav", acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(audio, overwrite_output=True)


def main():
    uploaded_video = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov", "mkv"])
    # get the name of the input_file
    if uploaded_video is not None:
        filename = uploaded_video.name[:-4]
    else:
        filename = None
    transcript_file = st.file_uploader("Upload Transcript File", type=["srt", "vtt"])
    if transcript_file is not None:
        transcript_name = transcript_file.name
    else:
        transcript_name = None
    if uploaded_video is not None and transcript_file is not None:
        if transcript_name[-3:] == "vtt":
            with open("uploaded_transcript.vtt", "wb") as f:
                f.writelines(transcript_file)
                f.close()
            with open(os.path.join(os.getcwd(), "uploaded_transcript.vtt"), "rb") as f:
                vtt_file = f.read()
            if st.button("Generate Video with Subtitles"):
                with st.spinner("Generating Subtitled Video"):
                    split_video_audio(uploaded_video)
                    video_file = ffmpeg.input(f"{save_dir}/input.mp4")
                    audio_file = ffmpeg.input(f"{save_dir}/output.wav")
                    ffmpeg.concat(video_file.filter("subtitles", "uploaded_transcript.vtt"), audio_file, v=1, a=1).output("video_sub.mp4").run(quiet=True, overwrite_output=True)
                    video_with_subs = open("video_sub.mp4", "rb")
                col3, col4 = st.columns(2)
                with col3:
                    st.video(uploaded_video)
                with col4:
                    st.video(video_with_subs)
                zipObj = ZipFile("subtitled_video.zip", "w")
                zipObj.write("video_sub.mp4")
                zipObj.close()
                ZipfileDotZip = "subtitled_video.zip"
                with open(ZipfileDotZip, "rb") as f:
                    datazip = f.read()
                    b64 = base64.b64encode(datazip).decode()
                    href = f"<a href=\"data:file/zip;base64,{b64}\" download='{ZipfileDotZip}'>\
            Download Subtitled Video\
        </a>"
                st.markdown(href, unsafe_allow_html=True)

        elif transcript_name[-3:] == "srt":
            with open("uploaded_transcript.srt", "wb") as f:
                f.writelines(transcript_file)
                f.close()
            with open(os.path.join(os.getcwd(), "uploaded_transcript.srt"), "rb") as f:
                srt_file = f.read()
            if st.button("Generate Video with Subtitles"):
                with st.spinner("Generating Subtitled Video"):
                    split_video_audio(uploaded_video)
                    video_file = ffmpeg.input(f"{save_dir}/input.mp4")
                    audio_file = ffmpeg.input(f"{save_dir}/output.wav")
                    ffmpeg.concat(video_file.filter("subtitles",  "uploaded_transcript.srt"), audio_file, v=1, a=1).output("video_sub.mp4").run(quiet=True, overwrite_output=True)
                    video_with_subs = open("video_sub.mp4", "rb")
                col3, col4 = st.columns(2)
                with col3:
                    st.video(uploaded_video)
                with col4:
                    st.video(video_with_subs)
                zipObj = ZipFile("subtitled_video.zip", "w")
                zipObj.write("video_sub.mp4")
                zipObj.close()
                ZipfileDotZip = "subtitled_video.zip"
                with open(ZipfileDotZip, "rb") as f:
                    datazip = f.read()
                    b64 = base64.b64encode(datazip).decode()
                    href = f"<a href=\"data:file/zip;base64,{b64}\" download='{ZipfileDotZip}'>\
            Download Subtitled Video\
        </a>"
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please upload a .srt or .vtt file")
    else:
        st.info("Please upload a video file and a transcript file")


if __name__ == "__main__":
    main()
        
