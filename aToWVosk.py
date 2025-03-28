import os
from pathlib import Path
import shutil
from pydub import AudioSegment
import json
from vosk import Model, KaldiRecognizer
import wave
import re
import pandas as pd

class AudioSplitter:
    def __init__(self, output_dir="audio_output", model_path="model"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.current_word_number = 1  # Add counter for word numbering
        self.mismatches = []
        self.word_data = [] 
        
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
            # data = wf.readframes(4000)
            data = wf.readframes(512)
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

    def split_audio_file(self, audio_path, original_text, ordinal_number):
        try:
            print(f"Processing audio: {audio_path}")
            
            # Get original words and their positions
            original_words = original_text.lower().strip().split()
            original_word_count = len(original_words)
            
            # Convert and get timestamps
            wav_path = self.convert_to_wav(audio_path)
            words_with_times = self.get_word_timestamps(wav_path)
            detected_word_count = len(words_with_times)
            
            # Only analyze detected text if word counts don't match
            if detected_word_count != original_word_count:
                detected_text = ' '.join(w['word'] for w in words_with_times)
                filename = Path(audio_path).name
                self.mismatches.append({
                    'filename': filename,
                    'original_text': original_text,
                    'detected_text': detected_text,
                    'original_word_count': original_word_count,
                    'detected_word_count': detected_word_count,
                    'detected_words': [w['word'] for w in words_with_times]
                })
                print(f"Warning: Word count mismatch!")
                print(f"Original words ({original_word_count}): {original_words}")
                print(f"Detected words ({detected_word_count}): {[w['word'] for w in words_with_times]}")
        
            # Load the original audio
            audio = AudioSegment.from_file(audio_path)
            word_files = []
        
            # Create a list to store all words (detected and missing)
            all_words_data = []
            
            # First, process the original words
            for i, original_word in enumerate(original_words):
                filename = f"ENGSPGX{self.current_word_number:06d}-0810"
                
                word_data = {
                    'word': original_word,
                    'fileName': filename,
                    'ordinalNumber': ordinal_number,
                    'wordIndex': i,
                    'originalWord': original_word,
                    'detected': False,
                    'isExtra': False
                }
            
                # Only create audio file if word was detected
                if i < len(words_with_times):
                    vosk_data = words_with_times[i]
                    start_time = int(vosk_data['start'] * 1000)
                    end_time = int(vosk_data['end'] * 1000)
                
                    word_audio = audio[start_time:end_time]
                    silence = AudioSegment.silent(duration=100)
                    word_audio = silence + word_audio + silence
                
                    full_filename = self.output_dir / f"{filename}.mp3"
                    word_audio.export(str(full_filename), format="mp3")
                    word_files.append(full_filename)
                
                    word_data['detected'] = True
            
                all_words_data.append(word_data)
                self.current_word_number += 1
        
            # Now process any extra detected words
            last_original_word_number = self.current_word_number - 1
            for i in range(original_word_count, detected_word_count):
                vosk_data = words_with_times[i]
                extra_word = vosk_data['word']
                
                # Create filename with _X suffix for extra words
                extra_number = i - original_word_count + 1
                filename = f"ENGSPGX{last_original_word_number}_{extra_number}-0810"
                
                word_data = {
                    'word': extra_word,
                    'fileName': filename,
                    'ordinalNumber': ordinal_number,
                    'wordIndex': i,
                    'originalWord': extra_word,
                    'detected': True,
                'isExtra': True
            }
                
                # Create audio file for extra word
                start_time = int(vosk_data['start'] * 1000)
                end_time = int(vosk_data['end'] * 1000)
                
                word_audio = audio[start_time:end_time]
                silence = AudioSegment.silent(duration=100)
                word_audio = silence + word_audio + silence
                
                full_filename = self.output_dir / f"{filename}.mp3"
                word_audio.export(str(full_filename), format="mp3")
                word_files.append(full_filename)
            
                all_words_data.append(word_data)
        
            # Add all words to the Excel data
            self.word_data.extend(all_words_data)
        
            # Clean up
            os.remove(wav_path)
        
            return {
                'word_files': word_files,
                'all_words_data': all_words_data,
                'word_count_match': detected_word_count == original_word_count,
                'text': ' '.join(w['word'] for w in words_with_times)
            }
        
        except Exception as e:
            print(f"Error processing audio file: {str(e)}")
            return None

    def save_excel(self, output_file):
        """Save word data to Excel file"""
        try:
            print(f"\nAttempting to save {len(self.word_data)} words to Excel...")
            
            filtered_word_data = []
            current_sequence = 1
            current_ordinal = None
            has_hyphen = False
            
            for entry in self.word_data:
                # Check if we're starting a new sentence
                if current_ordinal != entry['ordinalNumber']:
                    if has_hyphen:
                        # If previous sentence had a hyphen, increment sequence to maintain gap
                        current_sequence += 1
                    current_ordinal = entry['ordinalNumber']
                    has_hyphen = False
                
                if entry['word'] in ['-', '–', '—']:
                    has_hyphen = True
                    continue
                
                # Update the filename while keeping the -0810 suffix
                original_filename = entry['fileName']
                suffix = original_filename.split('-')[1]  # Get the '0810' part
                new_filename = f"ENGSPGX{current_sequence:06d}-{suffix}"
                entry['fileName'] = new_filename
                filtered_word_data.append(entry)
                current_sequence += 1
            
            df = pd.DataFrame(filtered_word_data)
            print("DataFrame created successfully")
            print("DataFrame contents:")
            print(df.head())  # Show first few rows
            
            df.to_excel(output_file, index=False)
            print(f"Excel file saved to: {output_file}")
        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Target directory exists: {Path(output_file).parent.exists()}")
            print(f"Write permissions: {os.access(str(Path(output_file).parent), os.W_OK)}")

    def save_mismatches(self, output_file):
        """Save mismatches to a JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'mismatches': self.mismatches
            }, f, indent=2, ensure_ascii=False)

def process_audio_folder():
    try:
        # Get absolute path to the model directory
        current_dir = Path(__file__).parent
        model_path = current_dir / "model"
        
        print(f"Looking for model in: {model_path.absolute()}")
        
        try:
            # Load original sentences
            with open('sentences.json', 'r', encoding='utf-8') as f:
                sentences_data = json.load(f)
                sentences = sentences_data['sentences']
            print("Successfully loaded sentences.json")
        except Exception as e:
            print(f"Error loading sentences.json: {e}")
            return

        try:
            # Initialize splitter
            splitter = AudioSplitter(
                output_dir="D:/Lingwing/dubbers/thomas/words",
                model_path=model_path
            )
        except Exception as e:
            print(f"Error initializing AudioSplitter: {e}")
            return

        # Directory containing the sentence audio files
        input_dir = Path("D:/Lingwing/dubbers/thomas")
        print(f"Looking for audio files in: {input_dir}")
        
        try:
            audio_files = list(sorted(input_dir.glob("ENGA1*.mp3")))
            print(f"Found {len(audio_files)} audio files")
        except Exception as e:
            print(f"Error finding audio files: {e}")
            return

        # Process all mp3 files in the input directory
        try:
            for i, audio_file in enumerate(audio_files):
            # for i, audio_file in enumerate(audio_files[1200:], start=1200):
                try:
                    print(f"\nProcessing: {audio_file.name}")
                    
                    # Extract ordinal number from filename
                    ordinal_match = re.search(r'ENGA1(\d+)', audio_file.name)
                    ordinal_number = int(ordinal_match.group(1)) if ordinal_match else i + 1
                    
                    # Get corresponding sentence
                    if i < len(sentences):
                        original_text = sentences[i]
                        result = splitter.split_audio_file(str(audio_file), original_text, ordinal_number)
                        
                        if result:
                            print(f"Created {len(result['word_files'])} word files")
                            if 'text' in result:
                                print(f"Original text: {original_text}")
                                print(f"Detected text: {result['text']}")
                            print(f"Current word_data length: {len(splitter.word_data)}")
                            
                            # Save Excel and mismatches every 100 files
                            if (i + 1) % 100 == 0:
                                try:
                                    # Save partial Excel
                                    excel_file = input_dir / f"word_data_partial_{i+1}.xlsx"
                                    print(f"\nSaving partial Excel file to: {excel_file}")
                                    splitter.save_excel(excel_file)
                                    print(f"Partial Excel file saved successfully")
                                    
                                    # Save partial mismatches
                                    mismatches_file = input_dir / f"text_mismatches_partial_{i+1}.json"
                                    splitter.save_mismatches(mismatches_file)
                                    print(f"Partial mismatches saved to: {mismatches_file}")
                                except Exception as e:
                                    print(f"Error saving partial files: {e}")
                    else:
                        print(f"Warning: No corresponding sentence found for {audio_file.name}")
                except Exception as e:
                    print(f"Error processing file {audio_file.name}: {e}")
                    continue
        except Exception as e:
            print(f"Error in main processing loop: {e}")

        print("\nFinished processing audio files")
        print(f"Final word_data count: {len(splitter.word_data)}")

        try:
            # Save final mismatches to JSON file
            mismatches_file = input_dir / "text_mismatches.json"
            splitter.save_mismatches(mismatches_file)
            print(f"Final mismatches saved to: {mismatches_file}")
        except Exception as e:
            print(f"Error saving final mismatches: {e}")

        try:
            # Save final word data to Excel file
            excel_file = input_dir / "word_data.xlsx"
            print(f"\nAttempting to save final Excel file to: {excel_file}")
            print(f"Total words processed: {len(splitter.word_data)}")
            splitter.save_excel(excel_file)
            print(f"Final Excel file saved successfully")
        except Exception as e:
            print(f"Error saving final Excel file: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Critical error in process_audio_folder: {e}")
        import traceback
        traceback.print_exc()

            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure you:")
        print("1. Downloaded the model from https://alphacephei.com/vosk/models")
        print("2. Extracted the complete model to a 'model' folder")
        print("3. The model folder contains all necessary files (am/, conf/, etc.)")

if __name__ == "__main__":
    process_audio_folder()