import { SpeechClient } from '@google-cloud/speech';
import config from '../config/index.js';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ffmpeg from 'fluent-ffmpeg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const speech = new SpeechClient({
  credentials: config.gcs.serviceAccountKey
});

async function splitAudioIntoWords(audioPath, words) {
  try {
    // Create output directory
    const outputDir = './google_audio_output5';
    await fs.mkdir(outputDir, { recursive: true });

    // Process each word
    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      const startTime = parseFloat(word.startTime);
      const duration = parseFloat(word.endTime) - startTime;
      
      // Add 100ms padding before and after
      const paddedStart = Math.max(0, startTime - 0.1);
      const paddedDuration = duration + 0.2;

      const outputFileName = `word_${i}_${word.word.replace(/[^a-zA-Z0-9]/g, '')}.mp3`;
      const outputPath = path.join(outputDir, outputFileName);

      // Create a promise to handle the FFmpeg operation
      await new Promise((resolve, reject) => {
        ffmpeg(audioPath)
          .setStartTime(paddedStart)
          .duration(paddedDuration)
          .output(outputPath)
          .on('end', resolve)
          .on('error', reject)
          .run();
      });
    }

    console.log(`Successfully split audio into ${words.length} word files`);
    return outputDir;
  } catch (error) {
    console.error('Error splitting audio:', error);
    throw error;
  }
}

async function processAudio(audioFilePath) {
  try {
    const file = await fs.readFile(audioFilePath);
    const audioBytes = file.toString('base64');

    const request = {
      audio: { content: audioBytes },
      config: {
        encoding: 'MP3',
        sampleRateHertz: 44100,
        languageCode: config.speechToText.languageCode,
        enableWordTimeOffsets: true,
        enableWordConfidence: true,  // Add this to get more details
        model: 'video',  // Try using the video model which might give more precise timestamps
      },
    };

    const [response] = await speech.recognize(request);
    
    // Log the raw response to see what Google is sending
    console.log('Raw response from Google:', 
      JSON.stringify(response.results[0].alternatives[0].words[0], null, 2)
    );
    
    if (!response.results || response.results.length === 0) {
      throw new Error('No transcription results found');
    }

    const words = response.results[0].alternatives[0].words.map(wordInfo => {
      // Convert to numbers and handle undefined values
      const startSeconds = Number(wordInfo.startTime?.seconds || 0);
      const startNanos = Number(wordInfo.startTime?.nanos || 0);
      const endSeconds = Number(wordInfo.endTime?.seconds || 0);
      const endNanos = Number(wordInfo.endTime?.nanos || 0);
      
      // Calculate precise timings
      const startTime = startSeconds + (startNanos / 1000000000);
      const endTime = endSeconds + (endNanos / 1000000000);

      return {
        word: wordInfo.word,
        startTime: startTime.toFixed(3),
        endTime: endTime.toFixed(3),
        // Add raw values for debugging
        rawStart: wordInfo.startTime,
        rawEnd: wordInfo.endTime
      };
    });

    // Then split the audio
    const outputDir = await splitAudioIntoWords(audioFilePath, words);

    return {
      transcript: response.results[0].alternatives[0].transcript,
      words: words,
      outputDirectory: outputDir
    };
  } catch (error) {
    console.error('Error processing audio:', error);
    throw error;
  }
}

// Test the function
try {
  const results = await processAudio('./children.mp3');
  console.log(JSON.stringify(results, null, 2));
} catch (error) {
  console.error('Failed to process:', error);
}