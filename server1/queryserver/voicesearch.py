import speech_recognition as sr

r = sr.Recognizer()

def choose_mic(mic_name):
	# print("Available devices")
	chosen = ()
	for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
		# print(microphone_name)
		if microphone_name == mic_name:
			chosen = i,mic_name
	print("Choosing", chosen[1])
	return chosen[0]

def listen(device_id, sample_rate, chunk_size):
	with sr.Microphone(device_index=device_id, sample_rate=sample_rate,
	                   chunk_size=chunk_size) as source:
		r.adjust_for_ambient_noise(source)
		print("Say Something")
		audio = r.listen(source)

		try:
			text = r.recognize_google(audio)
			print("you said '", text, "'", sep="")
			return text

		except sr.UnknownValueError:
			print("Google Speech Recognition could not understand audio")
			return None

		except sr.RequestError as e:
			print("Could not request results from GoogleSpeechRecognitionservice;{0}".format(e))
			return None

def doVoiceSearch():
	mic_name = "Microphone (USB Audio Device)"
	sample_rate = 48000
	chunk_size = 2048

	device_id = choose_mic(mic_name)
	term = listen(device_id, sample_rate, chunk_size)
	return term

if __name__ == '__main__':
	doVoiceSearch()