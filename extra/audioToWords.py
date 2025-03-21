import os
from pathlib import Path
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence

class AudioSplitter:
    def __init__(self, output_dir="audio_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")

    def split_audio_file(self, audio_path, text, output_prefix="word"):
        """Split an existing audio file into words"""
        try:
            print(f"Processing audio: {audio_path}")
            
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Parameters for splitting (may need adjustment)
            chunks = split_on_silence(
                audio,
                min_silence_len=10,    # minimum length of silence (ms)
                silence_thresh=-40,     # silence threshold (dB)
                keep_silence=50,        # keep this much silence around the chunk
                seek_step=1            # step size for seeking silence
            )
            
            # Get words from text
            words = text.split()
            
            if len(chunks) != len(words):
                print(f"Warning: Number of audio chunks ({len(chunks)}) doesn't match number of words ({len(words)})")
            
            # Create output files
            word_files = []
            
            # Save the original file
            original_filename = self.output_dir / f"original_{self.clean_filename(text)[:30]}.mp3"
            audio.export(str(original_filename), format="mp3")
            word_files.append(original_filename)
            
            # Save individual word chunks
            for i, (chunk, word) in enumerate(zip(chunks, words)):
                filename = self.output_dir / f"{output_prefix}_{i}_{self.clean_filename(word)}.mp3"
                chunk.export(str(filename), format="mp3")
                word_files.append(filename)
            
            return {
                'original_file': original_filename,
                'word_files': word_files[1:],  # Exclude original file
                'text': text
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
    splitter = AudioSplitter(output_dir="split_audio_output")
    
    # Path to your audio file
    audio_path = "we-travelled.mp3"  # Replace with your audio file path
    
    # The text that matches the audio
    text = "We travelled around the world last year"  # Replace with your text
    
    try:
        result = splitter.split_audio_file(audio_path, text)
        
        if result:
            print("\nProcessed audio:")
            print(f"Original file: {result['original_file']}")
            print(f"Word files: {result['word_files']}")
            print(f"Text: {result['text']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    process_audio()