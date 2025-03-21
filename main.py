import os
from pathlib import Path
import shutil
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.silence import split_on_silence
import json
import subprocess

class AudioSplitter:
    def __init__(self, output_dir="audio_output", voice="en-US-AvaMultilingualNeural"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice = voice
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")

    async def create_sentence_audio(self, text, sentence_id):
        """Create audio file from full sentence"""
        formatted_id = f"ENGSPG{sentence_id:06d}-0810"
        filename = self.output_dir / f"{formatted_id}.mp3"
        
        print(f"Creating audio file for sentence: {text}")
        
        communicate = edge_tts.Communicate(text, self.voice)
        # communicate = edge_tts.Communicate(text, self.voice, rate='-10%')
        await communicate.save(str(filename))
        
        return filename

    async def process_sentence(self, text, sentence_id=1):
        try:
            print(f"Processing sentence: {text}")
            
            sentence_file = await self.create_sentence_audio(text, sentence_id)
            print(f"Created sentence audio: {sentence_file}")
            
            # word_files = self.split_audio_into_words(sentence_file, text, sentence_id)
            # print(f"Created {len(word_files)} word audio files")
            
            return {
                'sentence_file': sentence_file,
                # 'word_files': word_files,
                'text': text
            }
        except Exception as e:
            print(f"Error processing sentence: {str(e)}")
            return None

    async def process_multiple_sentences(self, sentences):
        """Process multiple sentences"""
        results = []
        for i, sentence in enumerate(sentences, 1):
            result = await self.process_sentence(sentence, i)
            if result:
                results.append(result)
        return results

    def cleanup(self):
        """Clean up the output directory"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

# Example usage
async def process_my_sentences():
    output_path = "D:/Lingwing/dubbers/thomas" 
    # output_path = Path(__file__).parent / "words"
    splitter = AudioSplitter(output_dir=output_path, voice="en-GB-ThomasNeural")
    
    # Optional: List available voices
    # voices = await splitter.list_voices()
    try:
        with open('sentences.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            sentences = data['sentences']
            
        results = await splitter.process_multiple_sentences(sentences)
        
        # Print results
        for result in results:
            print("\nProcessed sentence:")
            print(f"Text: {result['text']}")
            print(f"Sentence audio: {result['sentence_file']}")
            # print(f"Word audio files: {result['word_files']}")
             # Run aToWVosk.py after processing is complete

            #  this will autoamtically run the script to split the audio into words
        # print("\nRunning aToWVosk.py...")
        try:
            subprocess.run([
                "C:/Users/Lingwing/AppData/Local/Programs/Python/Python313/python.exe",
                "aToWVosk.py"
            ], check=True)
            print("aToWVosk.py completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error running aToWVosk.py: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_my_sentences())

    