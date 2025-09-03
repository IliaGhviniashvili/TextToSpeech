import os
from pathlib import Path
import shutil
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.silence import split_on_silence
import json
import subprocess
import pandas as pd
import re

class AudioSplitter:
    def __init__(self, output_dir="audio_output", voice="en-US-AvaMultilingualNeural"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice = voice
        # Map numeric dubber IDs to Edge TTS short voice names
        # Extend this mapping as needed
        self.voice_map = {
            1: "en-GB-ThomasNeural",
            2: "en-US-AvaMultilingualNeural",
        }
    
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

    def _voice_for_id(self, dubber_id):
        """Return edge-tts short voice name for a numeric dubber id, fallback to default voice."""
        return self.voice_map.get(dubber_id, self.voice)

    async def _synthesize_to_file(self, text, voice_name, out_path):
        """Synthesize given text with specified voice to an mp3 file."""
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(str(out_path))

    async def create_multivoice_sentence_audio(self, text, dubbers, sentence_id):
        """Create audio file for a sentence with multiple segments/voices based on dubbers list."""
        formatted_id = f"ENGSPG{sentence_id:06d}-0810"
        final_filename = self.output_dir / f"{formatted_id}.mp3"

        parts = text.split(" - ")
        if not isinstance(dubbers, list) or len(dubbers) != len(parts):
            # Fallback to single-voice if mapping is invalid
            print("Dubbers list invalid or length mismatch; falling back to single-voice synthesis")
            return await self.create_sentence_audio(text, sentence_id)

        print(f"Creating multi-voice audio for sentence id {sentence_id}: {len(parts)} parts")

        temp_files = []
        try:
            # Synthesize each part with its corresponding voice
            for index, (part_text, dubber_id) in enumerate(zip(parts, dubbers), start=1):
                voice_name = self._voice_for_id(dubber_id)
                tmp_path = self.output_dir / f"tmp_{formatted_id}_{index}.mp3"
                await self._synthesize_to_file(part_text, voice_name, tmp_path)
                temp_files.append(tmp_path)

            # Concatenate parts
            combined = None
            for tmp in temp_files:
                seg = AudioSegment.from_file(tmp)
                if combined is None:
                    combined = seg
                else:
                    combined = combined + seg

            if combined is None:
                raise Exception("No audio segments generated for multi-voice synthesis")

            combined.export(str(final_filename), format="mp3")
            return final_filename
        finally:
            # Cleanup temp files
            for tmp in temp_files:
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    async def process_sentence(self, text, sentence_id=1):
        try:
            # Support both plain strings and objects with keys 's' and optional 'd'
            if isinstance(text, dict):
                sentence_text = text.get('s', '')
                dubbers = text.get('d')
            else:
                sentence_text = text
                dubbers = None

            print(f"Processing sentence: {sentence_text}")

            # If there is a separator in text but no 'd' provided, treat as single-voice (old style)
            if isinstance(dubbers, list) and " - " in sentence_text:
                sentence_file = await self.create_multivoice_sentence_audio(sentence_text, dubbers, sentence_id)
            else:
                sentence_file = await self.create_sentence_audio(sentence_text, sentence_id)
            print(f"Created sentence audio: {sentence_file}")
            
            # word_files = self.split_audio_into_words(sentence_file, text, sentence_id)
            # print(f"Created {len(word_files)} word audio files")
            
            return {
                'sentence_file': sentence_file,
                # 'word_files': word_files,
                'text': sentence_text
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
    # output_path = "D:/Lingwing/dubbers/thomas" 
    output_path = Path(__file__).parent / "thomas"
    # output_path = Path(__file__).parent / "words"
    splitter = AudioSplitter(output_dir=output_path, voice="en-GB-ThomasNeural")
    
    # Optional: List available voices
    # voices = await splitter.list_voices()
    try:
        # 1) Try to load sentences from an Excel file in the content/ folder
        content_dir = Path(__file__).parent / "content"
        excel_file_name = "sentences.xlsx" 
        excel_path = content_dir / excel_file_name

        sentences = None

        if excel_path.exists():
            print(f"Loading sentences from Excel: {excel_path}")
            try:
                df = pd.read_excel(excel_path)
                # Normalize columns to lowercase and trimmed
                df.columns = [str(c).strip().lower() for c in df.columns]
                if 'sentence' in df.columns:
                    sentences_from_excel = []
                    for _, row in df.iterrows():
                        sentence_text = str(row['sentence']).strip()
                        if not sentence_text or sentence_text.lower() == 'nan':
                            continue

                        dubbers_value = row.get('dubbers', None)
                        d_list = None
                        if pd.notna(dubbers_value):
                            # Extract all integers from the cell (supports formats like "1,2", "[1, 2]", "1 2", etc.)
                            numbers = re.findall(r"\d+", str(dubbers_value))
                            if numbers:
                                d_list = [int(n) for n in numbers]

                        if d_list:
                            sentences_from_excel.append({'s': sentence_text, 'd': d_list})
                        else:
                            sentences_from_excel.append({'s': sentence_text})

                    sentences = sentences_from_excel
                else:
                    print("Excel file does not contain a 'sentence' column; falling back to sentences.json")
            except Exception as e:
                print(f"Failed to read Excel file: {e}. Falling back to sentences.json")

        # 2) Fallback to JSON if Excel not used
        if sentences is None:
            print("Loading sentences from sentences.json")
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

    