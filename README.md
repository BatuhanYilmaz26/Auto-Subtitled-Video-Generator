## Auto-Subtitled-Video-Generator

![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![OpenAI](https://camo.githubusercontent.com/ea872adb9aba9cf6b4e976262f6d4b83b97972d0d5a7abccfde68eb2ae55325f/68747470733a2f2f696d672e736869656c64732e696f2f7374617469632f76313f7374796c653d666f722d7468652d6261646765266d6573736167653d4f70656e414926636f6c6f723d343132393931266c6f676f3d4f70656e4149266c6f676f436f6c6f723d464646464646266c6162656c3d)

#### About this project
- This project is an automatic speech recognition application that takes a YouTube video link or a video file as input to generate a video with subtitles.
- You can also upload an audio file to generate a transcript as .txt, .vtt, .srt files.
- The application performs 2 tasks:
  - Detects the language, transcribes the input video in its original language.
  - Detects the language, translates it into English and then transcribes.
- Downloaded the video of the input link using [pytube](https://github.com/pytube/pytube).
- Generated a transcription of the video using the [OpenAI Whisper](https://openai.com/blog/whisper) model.
- Saved the transcriptions as .txt, .vtt and .srt files.
- Generated a subtitled version of the input video using [ffmpeg](https://github.com/FFmpeg).
- Displayed the original video and the subtitled video side by side.
- Built a multipage web app using [Streamlit](https://streamlit.io) and hosted on [HuggingFace Spaces](https://huggingface.co/spaces).
- You can download the generated .txt, .vtt, .srt files and the subtitled video.
- You can use the app via this [link](https://huggingface.co/spaces/BatuhanYilmaz/Auto-Subtitled-Video-Generator).

![](auto-sub.gif)
