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
import time

class AudioSplitter:
    def __init__(self, output_dir="audio_output", voice="ka-GE-EkaNeura"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = voice
        # Map numeric dubber IDs to Edge TTS short voice names
        # Extend this mapping as needed
        self.voice_map = {
            101: "ka-GE-GiorgiNeural",
            102: "ka-GE-EkaNeural",
        }
    
    def clean_filename(self, text):
        """Create a safe filename from text"""
        return "".join(x for x in text if x.isalnum() or x in "._- ")

    async def create_sentence_audio(self, text, sentence_id, voice_override=None):
        """Create audio file from full sentence"""
        formatted_id = f"MED8{sentence_id:06d}"
        filename = self.output_dir / f"{formatted_id}.mp3"
        
        print(f"Creating audio file for sentence: {text}")
        
        voice_to_use = voice_override if voice_override else self.voice
        communicate = edge_tts.Communicate(text, voice_to_use)
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
        formatted_id = f"MED8{sentence_id:06d}"
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

            # Choose synthesis path based on provided dubbers and text segmentation
            if isinstance(dubbers, list) and len(dubbers) > 0:
                if " - " in sentence_text:
                    parts = sentence_text.split(" - ")
                    if len(dubbers) == len(parts):
                        sentence_file = await self.create_multivoice_sentence_audio(sentence_text, dubbers, sentence_id)
                    else:
                        print(f"Dubber/part count mismatch (dubbers={len(dubbers)}, parts={len(parts)}); using first dubber id {dubbers[0]}")
                        voice_name = self._voice_for_id(dubbers[0])
                        sentence_file = await self.create_sentence_audio(sentence_text, sentence_id, voice_override=voice_name)
                else:
                    # No segmentation in text; honor the first dubber id
                    voice_name = self._voice_for_id(dubbers[0])
                    print(f"No parts separator in text; using first dubber id {dubbers[0]} -> {voice_name}")
                    sentence_file = await self.create_sentence_audio(sentence_text, sentence_id, voice_override=voice_name)
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
    output_path = str(Path.home() / "Downloads" / "medicine"/ "audios"/ "georgian")
    # output_path = Path(__file__).parent / "words"
    splitter = AudioSplitter(output_dir=output_path, voice="ka-GE-EkaNeural")
    
    # Optional: List available voices
    # voices = await splitter.list_voices()
    try:
        # 1) Try to load sentences from an Excel file in a content/ folder
        # Resolve content directory from common locations
        possible_content_dirs = [
            Path(__file__).resolve().parent / "content",
            Path.cwd() / "content",
        ]

        content_dir = None
        for candidate in possible_content_dirs:
            if candidate.exists():
                content_dir = candidate
                break
        if content_dir is None:
            # Fall back to first candidate even if it doesn't exist; subsequent checks handle existence
            content_dir = possible_content_dirs[0]

        excel_file_name = "sentences.xlsx"
        excel_path = content_dir / excel_file_name
        print(f"Resolved content directory: {content_dir}")
        print(f"Excel expected at: {excel_path} (exists={excel_path.exists()})")

        sentences = None

        if excel_path.exists():
            print(f"Loading sentences from Excel: {excel_path}")
            df = None
            # Retry loop in case the file is temporarily locked (e.g., by OneDrive/Excel)
            for attempt in range(5):
                try:
                    df = pd.read_excel(excel_path, engine="openpyxl")
                    break
                except PermissionError as e:
                    wait_seconds = 0.5 * (2 ** attempt)
                    print(f"Permission denied reading Excel (attempt {attempt+1}/5). If the file is open, please close it. Retrying in {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds)
                except Exception as e:
                    # Other read errors should surface to outer handler
                    raise

            if df is None:
                # Last resort: attempt to read from a temporary copy
                try:
                    tmp_copy = content_dir / f"._read_{excel_file_name}"
                    print(f"Attempting temp-copy read: {tmp_copy}")
                    shutil.copy2(excel_path, tmp_copy)
                    df = pd.read_excel(tmp_copy, engine="openpyxl")
                    try:
                        os.remove(tmp_copy)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Failed to read Excel file after retries: {e}. Falling back to sentences.json")
                    df = None

            try:
                if df is not None:
                # Normalize columns to lowercase and trimmed
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    print(f"Excel columns detected: {df.columns.tolist()}")
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
            json_candidates = [
                content_dir / 'sentences.json',
                Path.cwd() / 'sentences.json',
                Path(__file__).resolve().parent / 'sentences.json',
            ]
            json_path = next((p for p in json_candidates if p.exists()), json_candidates[0])
            print(f"Loading sentences from JSON: {json_path} (exists={json_path.exists()})")
            with open(json_path, 'r', encoding='utf-8') as file:
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
                "C:/Python313/python.exe",
                "aToWVosk.py"
            ], check=True)
            print("aToWVosk.py completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error running aToWVosk.py: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_my_sentences())

    