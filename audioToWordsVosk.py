import os
from pathlib import Path
import shutil
from pydub import AudioSegment
import json
from vosk import Model, KaldiRecognizer
import wave

class AudioSplitter:
    def __init__(self, output_dir="audio_output", model_path="model"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # More detailed model path checking
        model_path = Path(model_path)
        if not model_path.exists():
            raise Exception(f"Model path does not exist: {model_path}")
        
        # Check for essential model files
        required_files = ['am/final.mdl', 'conf/mfcc.conf']
        missing_files = []
        for file in required_files:
            if not (model_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            raise Exception(f"Missing model files: {missing_files}. Please ensure you downloaded and extracted the complete model.")
        
        print(f"Loading model from: {model_path.absolute()}")
        try:
            self.model = Model(str(model_path.absolute()))
            print("Model loaded successfully")
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")

    def convert_to_wav(self, audio_path):
        """Convert audio to WAV format with required parameters"""
        audio = AudioSegment.from_file(audio_path)
        wav_path = str(self.output_dir / "temp.wav")
        audio.export(wav_path, format="wav", parameters=["-ar", "16000", "-ac", "1"])
        return wav_path

    def get_word_timestamps(self, wav_path):
        """Get word timestamps using Vosk"""
        wf = wave.open(wav_path, "rb")
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        words_with_times = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if 'result' in result:
                    words_with_times.extend(result['result'])

        # Get final result
        result = json.loads(rec.FinalResult())
        if 'result' in result:
            words_with_times.extend(result['result'])

        return words_with_times

    def split_audio_file(self, audio_path, text=None):
        """Split audio file into words using speech recognition"""
        try:
            print(f"Processing audio: {audio_path}")
            
            # Convert audio to WAV format
            wav_path = self.convert_to_wav(audio_path)
            
            # Get word timestamps
            words_with_times = self.get_word_timestamps(wav_path)
            
            # Load the original audio
            audio = AudioSegment.from_file(audio_path)
            
            # Create output files
            word_files = []
            
            # Save the original file
            original_filename = self.output_dir / f"original_audio.mp3"
            audio.export(str(original_filename), format="mp3")
            word_files.append(original_filename)
            
            # Split and save individual words
            for i, word_data in enumerate(words_with_times):
                start_time = int(word_data['start'] * 1000)  # Convert to milliseconds
                end_time = int(word_data['end'] * 1000)
                word = word_data['word']
                
                # Extract word segment
                word_audio = audio[start_time:end_time]
                
                # Add small silence padding
                silence = AudioSegment.silent(duration=50)
                word_audio = silence + word_audio + silence
                
                # Save word audio
                filename = self.output_dir / f"word_{i}_{self.clean_filename(word)}.mp3"
                word_audio.export(str(filename), format="mp3")
                word_files.append(filename)
            
            # Clean up temporary WAV file
            os.remove(wav_path)
            
            return {
                'original_file': original_filename,
                'word_files': word_files[1:],  # Exclude original file
                'text': text or ' '.join(w['word'] for w in words_with_times)
            }
            
        except Exception as e:
            print(f"Error processing audio file: {str(e)}")
            return None

    def cleanup(self):
        """Clean up the output directory"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

# Example usage
def process_audio():
    try:
        # Get absolute path to the model directory
        current_dir = Path(__file__).parent
        model_path = current_dir / "model"
        
        print(f"Looking for model in: {model_path.absolute()}")
        
        splitter = AudioSplitter(
            output_dir="split_audio_output",
            model_path=model_path
        )
        
        # Path to your audio file
        audio_path = current_dir / "we-travelled.mp3"
        
        if not audio_path.exists():
            raise Exception(f"Audio file not found: {audio_path}")
            
        result = splitter.split_audio_file(str(audio_path))
        
        if result:
            print("\nProcessed audio:")
            print(f"Original file: {result['original_file']}")
            print(f"Word files: {result['word_files']}")
            print(f"Detected text: {result['text']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure you:")
        print("1. Downloaded the model from https://alphacephei.com/vosk/models")
        print("2. Extracted the complete model to a 'model' folder")
        print("3. The model folder contains all necessary files (am/, conf/, etc.)")

if __name__ == "__main__":
    process_audio()