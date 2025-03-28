import os
from pathlib import Path
import shutil
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.silence import split_on_silence
import json
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2

class AudioSplitter:
    def __init__(self, output_dir="audio_output", voice="en-US-AvaMultilingualNeural"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice = voice
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")
        
    # async def list_voices(self):
    #     """List all available voices and save to JSON"""
    #     voices = await edge_tts.list_voices()
        
    #     # Create a more readable format for the JSON
    #     voice_data = [{
    #         'name': voice['Name'],
    #         'short_name': voice['ShortName'],
    #         'gender': voice['Gender'],
    #         'locale': voice['Locale']
    #     } for voice in voices]
        
    #     # Save to JSON file
    #     json_path = Path(__file__).parent / 'available_voices.json'
    #     with open(json_path, 'w', encoding='utf-8') as f:
    #         json.dump(voice_data, f, indent=2)
        
    #     # Also print to console
    #     for voice in voices:
    #         print(f"Voice Name: {voice['Name']}")
    #         print(f"Short Name: {voice['ShortName']}")
    #         print(f"Gender: {voice['Gender']}")
    #         print(f"Locale: {voice['Locale']}")
    #         print("-------------------")
            
    #     return voices

        
    async def create_sentence_audio(self, text, sentence_id):
        """Create audio file from full sentence"""
        formatted_id = f"ENGSPG{sentence_id:06d}-0810"
        filename = self.output_dir / f"{formatted_id}.mp3"
        
        print(f"Creating audio file for sentence: {text}")
        
        communicate = edge_tts.Communicate(text, self.voice)
        # communicate = edge_tts.Communicate(text, self.voice, rate='-10%')
        await communicate.save(str(filename))
        
        try:
            # Create ID3 tag if it doesn't exist
            audio = MP3(filename)
            if not audio.tags:
                audio.add_tags()
            
            # Set the title to the sentence text
            audio.tags.add(TIT2(encoding=3, text=text))
            audio.save()
            
            print(f"Added title metadata: {text}")
        except Exception as e:
            print(f"Warning: Could not add metadata: {str(e)}")
        
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
    # output_path = "D:/Lingwing/dubbers/helpers/thomas" 
    output_path = Path(__file__).parent / "words"
    splitter = AudioSplitter(output_dir=output_path, voice="en-GB-ThomasNeural")
    
    # Optional: List available voices
    # voices = await splitter.list_voices()
    
    sentences = [
        "do you have free time tomorrow?"
    ]
    
    try:
        results = await splitter.process_multiple_sentences(sentences)
        
        # Print results
        for result in results:
            print("\nProcessed sentence:")
            print(f"Text: {result['text']}")
            print(f"Sentence audio: {result['sentence_file']}")
            # print(f"Word audio files: {result['word_files']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_my_sentences())

    