import os
import azure.cognitiveservices.speech as speechsdk
import openai
import tkinter as tk
from tkinter import scrolledtext, messagebox
from elevenlabs import play
from elevenlabs.client import ElevenLabs

client = ElevenLabs(
    api_key="?",  # Defaults to ELEVEN_API_KEY
)

# OpenAI API 키 설정
openai.api_key = "?"

# 콘솔 출력 인코딩 설정 (Windows 전용)
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)

# Azure 음성 인식 함수
def recognize_from_microphone():
    speech_key = os.getenv('SPEECH_KEY')
    speech_region = os.getenv('SPEECH_REGION')
    
    if not speech_key or not speech_region:
        raise ValueError("Please set the SPEECH_KEY and SPEECH_REGION environment variables.")
    
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "ko-KR"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        recognized_text = speech_recognition_result.text
        print("Recognized: {}".format(recognized_text))
        return recognized_text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        return None
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return None

# GUI 프로그램 클래스
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT Voice Assistant")

        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, state='disabled')
        self.chat_area.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        self.entry_field = tk.Entry(root, width=50)
        self.entry_field.grid(column=0, row=1, padx=10, pady=10)
        self.entry_field.bind("<Return>", self.get_response)

        self.send_button = tk.Button(root, text="Send", command=self.get_response)
        self.send_button.grid(column=1, row=1, padx=10, pady=10)

        self.voice_button = tk.Button(root, text="Voice Input", command=self.start_voice_input)
        self.voice_button.grid(column=0, row=2, padx=10, pady=10, columnspan=2)

        # 스페이스 바 누르거나 "한별아"라고 말할 때 음성 인식 시작
        self.root.bind("<space>", lambda event: self.start_voice_input())
        self.root.bind("<KeyPress>", self.check_keyword)

    def get_response(self, event=None):
        user_input = self.entry_field.get().strip()
        if not user_input:
            messagebox.showwarning("Warning", "Please enter a message.")
            return

        self.entry_field.delete(0, tk.END)
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"사용자: {user_input}\n")
        self.chat_area.config(state='disabled')

    def start_voice_input(self):
        user_input = recognize_from_microphone()
        if not user_input or user_input.strip() == "":
            messagebox.showwarning("Warning", "음성을 인식할 수 없습니다.")
            return

        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"사용자: {user_input}\n")
        self.chat_area.config(state='disabled')

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            assistant_response = response.choices[0].message['content']
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, f"챗봇: {assistant_response}\n")
            self.chat_area.config(state='disabled')

            # 음성 생성 및 재생
            audio = client.generate(text=assistant_response, voice="6d6OUupJXhfhRKu2ljiH", model="eleven_multilingual_v2")
            play(audio)

        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def check_keyword(self, event):
        if event.keysym == "Hangul_Hanja" or event.keysym == "space":
            self.start_voice_input()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
