import os
from pathlib import Path
import shutil
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.silence import split_on_silence

class AudioSplitter:
    def __init__(self, output_dir="audio_output", voice="en-US-ChristopherNeural"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice = voice
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")
        
    async def list_voices(self):
        """List all available voices"""
        voices = await edge_tts.list_voices()
        for voice in voices:
            print(f"Voice Name: {voice['Name']}")
            print(f"Short Name: {voice['ShortName']}")
            print(f"Gender: {voice['Gender']}")
            print(f"Locale: {voice['Locale']}")
            print("-------------------")
        return voices
        
    async def create_sentence_audio(self, text, sentence_id):
        """Create audio file from full sentence"""
        filename = self.output_dir / f"sentence_{sentence_id}_{self.clean_filename(text)[:30]}.mp3"
        
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(filename))
        
        return filename

    def split_audio_into_words(self, audio_path, text, sentence_id):
        """Split sentence audio into individual word audio files"""
        audio = AudioSegment.from_mp3(audio_path)
        
        # Parameters for splitting (may need adjustment)
        chunks = split_on_silence(
            audio,
            min_silence_len=100,
            silence_thresh=-40,
            keep_silence=50
        )
        
        words = text.split()
        word_files = []
        
        for i, (chunk, word) in enumerate(zip(chunks, words)):
            filename = self.output_dir / f"word_{sentence_id}_{i}_{self.clean_filename(word)}.mp3"
            chunk.export(str(filename), format="mp3")
            word_files.append(filename)
            
        return word_files

    async def process_sentence(self, text, sentence_id=1):
        try:
            print(f"Processing sentence: {text}")
            
            sentence_file = await self.create_sentence_audio(text, sentence_id)
            print(f"Created sentence audio: {sentence_file}")
            
            word_files = self.split_audio_into_words(sentence_file, text, sentence_id)
            print(f"Created {len(word_files)} word audio files")
            
            return {
                'sentence_file': sentence_file,
                'word_files': word_files,
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
    splitter = AudioSplitter(output_dir="my_audio_output", voice="en-US-ChristopherNeural")
    
    # Optional: List available voices
    voices = await splitter.list_voices()
    
    sentences = [
        "some text here"
    ]
    
    try:
        results = await splitter.process_multiple_sentences(sentences)
        
        # Print results
        for result in results:
            print("\nProcessed sentence:")
            print(f"Text: {result['text']}")
            print(f"Sentence audio: {result['sentence_file']}")
            print(f"Word audio files: {result['word_files']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_my_sentences())