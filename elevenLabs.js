import fs from "fs/promises";
import path from "path";
import ffmpeg from "fluent-ffmpeg";

async function splitElevenLabsAudioIntoWords(audioPath, alignment) {
    try {
      const outputDir = "./elevenlabs_audio_output";
      await fs.mkdir(outputDir, { recursive: true });
  
      const { characters, character_end_times_seconds } = alignment;
      let words = [];
      let currentWord = {
        characters: [],
        startIndex: 0,
        endIndex: 0
      };
  
      // First, identify words and their indices
      for (let i = 0; i < characters.length; i++) {
        if (characters[i] === " ") {
          if (currentWord.characters.length > 0) {
            currentWord.endIndex = i - 1;
            words.push({
              word: currentWord.characters.join(""),
              startIndex: currentWord.startIndex,
              endIndex: currentWord.endIndex
            });
            currentWord = {
              characters: [],
              startIndex: i + 1,
              endIndex: 0
            };
          } else {
            currentWord.startIndex = i + 1;
          }
        } else {
          currentWord.characters.push(characters[i]);
        }
      }
  
      // Handle the last word
      if (currentWord.characters.length > 0) {
        currentWord.endIndex = characters.length - 1;
        words.push({
          word: currentWord.characters.join(""),
          startIndex: currentWord.startIndex,
          endIndex: currentWord.endIndex
        });
      }
  
      // Process each word with rounded timing
      for (let i = 0; i < words.length; i++) {
        const word = words[i];
        
        // Calculate start time
        let startTime;
        if (word.startIndex > 1) {
          const previousEndTime = character_end_times_seconds[word.startIndex - 2];
          const thisStartTime = character_end_times_seconds[word.startIndex - 1];
          startTime = (previousEndTime + thisStartTime) / 2;
        } else {
          startTime = 0;
        }
  
        // Calculate end time
        let endTime;
        if (word.endIndex < characters.length - 2) {
          const thisEndTime = character_end_times_seconds[word.endIndex];
          const nextStartTime = character_end_times_seconds[word.endIndex + 1];
          endTime = (thisEndTime + nextStartTime) / 2;
        } else {
          endTime = character_end_times_seconds[word.endIndex];
        }
  
        // Round timestamps to nearest 0.05 seconds
        startTime = Math.round(startTime * 20) / 20;
        endTime = Math.round(endTime * 20) / 20;
  
        console.log(`Processing word: "${word.word}" (${word.startIndex}-${word.endIndex}) from ${startTime} to ${endTime}`);
  
        const outputFileName = `word_${i}_${word.word.replace(/[^a-zA-Z0-9]/g, "")}.mp3`;
        const outputPath = path.join(outputDir, outputFileName);
  
        await new Promise((resolve, reject) => {
          ffmpeg(audioPath)
            .setStartTime(startTime)
            .duration(endTime - startTime)
            .output(outputPath)
            .on("end", resolve)
            .on("error", reject)
            .run();
        });
      }
  
      console.log(`Successfully split audio into ${words.length} word files`);
      return {
        outputDirectory: outputDir,
        words: words,
      };
    } catch (error) {
      console.error("Error splitting audio:", error);
      throw error;
    }
  }
const response = {
  alignment: {
    characters: [
      "A",
      " ",
      "d",
      "e",
      "m",
      "o",
      "c",
      "r",
      "a",
      "c",
      "y",
      " ",
      "i",
      "s",
      " ",
      "a",
      " ",
      "s",
      "y",
      "s",
      "t",
      "e",
      "m",
      " ",
      "o",
      "f",
      " ",
      "g",
      "o",
      "v",
      "e",
      "r",
      "n",
      "m",
      "e",
      "n",
      "t",
      " ",
      "w",
      "h",
      "e",
      "r",
      "e",
      " ",
      "c",
      "i",
      "t",
      "i",
      "z",
      "e",
      "n",
      "s",
      " ",
      "v",
      "o",
      "t",
      "e",
      " ",
      "t",
      "o",
      " ",
      "e",
      "l",
      "e",
      "c",
      "t",
      " ",
      "r",
      "e",
      "p",
      "r",
      "e",
      "s",
      "e",
      "n",
      "t",
      "a",
      "t",
      "i",
      "v",
      "e",
      "s",
      " ",
      "w",
      "h",
      "o",
      " ",
      "w",
      "i",
      "l",
      "l",
      " ",
      "m",
      "a",
      "k",
      "e",
      " ",
      "d",
      "e",
      "c",
      "i",
      "s",
      "i",
      "o",
      "n",
      "s",
      " ",
      "a",
      "n",
      "d",
      " ",
      "c",
      "r",
      "e",
      "a",
      "t",
      "e",
      " ",
      "l",
      "a",
      "w",
      "s",
      " ",
      "o",
      "n",
      " ",
      "t",
      "h",
      "e",
      "i",
      "r",
      " ",
      "b",
      "e",
      "h",
      "a",
      "l",
      "f",
    ],
    character_start_times_seconds: [
      0, 0.093, 0.151, 0.186, 0.244, 0.302, 0.383, 0.453, 0.499, 0.557, 0.639,
      0.755, 0.824, 0.894, 0.929, 0.975, 0.998, 1.057, 1.115, 1.184, 1.242,
      1.289, 1.347, 1.393, 1.44, 1.463, 1.486, 1.567, 1.602, 1.672, 1.707,
      1.741, 1.765, 1.823, 1.858, 1.892, 1.927, 2.009, 2.159, 2.218, 2.276,
      2.31, 2.345, 2.368, 2.415, 2.473, 2.543, 2.601, 2.659, 2.717, 2.786,
      2.844, 2.902, 2.972, 3.019, 3.135, 3.181, 3.228, 3.262, 3.297, 3.32,
      3.402, 3.46, 3.518, 3.576, 3.634, 3.68, 3.762, 3.796, 3.866, 3.924, 3.982,
      4.029, 4.063, 4.133, 4.18, 4.238, 4.307, 4.365, 4.423, 4.458, 4.505,
      4.563, 4.737, 4.807, 4.841, 4.876, 4.899, 4.934, 4.969, 5.004, 5.039,
      5.074, 5.108, 5.155, 5.201, 5.236, 5.283, 5.329, 5.399, 5.48, 5.55, 5.596,
      5.642, 5.689, 5.759, 5.828, 5.886, 5.933, 5.968, 6.002, 6.06, 6.107,
      6.153, 6.211, 6.269, 6.327, 6.374, 6.42, 6.467, 6.56, 6.629, 6.676, 6.722,
      6.757, 6.792, 6.838, 6.861, 6.885, 6.92, 6.966, 6.989, 7.036, 7.07, 7.14,
      7.221, 7.338, 7.396,
    ],
    character_end_times_seconds: [
      0.093, 0.151, 0.186, 0.244, 0.302, 0.383, 0.453, 0.499, 0.557, 0.639,
      0.755, 0.824, 0.894, 0.929, 0.975, 0.998, 1.057, 1.115, 1.184, 1.242,
      1.289, 1.347, 1.393, 1.44, 1.463, 1.486, 1.567, 1.602, 1.672, 1.707,
      1.741, 1.765, 1.823, 1.858, 1.892, 1.927, 2.009, 2.159, 2.218, 2.276,
      2.31, 2.345, 2.368, 2.415, 2.473, 2.543, 2.601, 2.659, 2.717, 2.786,
      2.844, 2.902, 2.972, 3.019, 3.135, 3.181, 3.228, 3.262, 3.297, 3.32,
      3.402, 3.46, 3.518, 3.576, 3.634, 3.68, 3.762, 3.796, 3.866, 3.924, 3.982,
      4.029, 4.063, 4.133, 4.18, 4.238, 4.307, 4.365, 4.423, 4.458, 4.505,
      4.563, 4.737, 4.807, 4.841, 4.876, 4.899, 4.934, 4.969, 5.004, 5.039,
      5.074, 5.108, 5.155, 5.201, 5.236, 5.283, 5.329, 5.399, 5.48, 5.55, 5.596,
      5.642, 5.689, 5.759, 5.828, 5.886, 5.933, 5.968, 6.002, 6.06, 6.107,
      6.153, 6.211, 6.269, 6.327, 6.374, 6.42, 6.467, 6.56, 6.629, 6.676, 6.722,
      6.757, 6.792, 6.838, 6.861, 6.885, 6.92, 6.966, 6.989, 7.036, 7.07, 7.14,
      7.221, 7.338, 7.396, 7.802,
    ],
  },
  normalized_alignment: {
    characters: [
      " ",
      "A",
      " ",
      "d",
      "e",
      "m",
      "o",
      "c",
      "r",
      "a",
      "c",
      "y",
      " ",
      "i",
      "s",
      " ",
      "a",
      " ",
      "s",
      "y",
      "s",
      "t",
      "e",
      "m",
      " ",
      "o",
      "f",
      " ",
      "g",
      "o",
      "v",
      "e",
      "r",
      "n",
      "m",
      "e",
      "n",
      "t",
      " ",
      "w",
      "h",
      "e",
      "r",
      "e",
      " ",
      "c",
      "i",
      "t",
      "i",
      "z",
      "e",
      "n",
      "s",
      " ",
      "v",
      "o",
      "t",
      "e",
      " ",
      "t",
      "o",
      " ",
      "e",
      "l",
      "e",
      "c",
      "t",
      " ",
      "r",
      "e",
      "p",
      "r",
      "e",
      "s",
      "e",
      "n",
      "t",
      "a",
      "t",
      "i",
      "v",
      "e",
      "s",
      " ",
      "w",
      "h",
      "o",
      " ",
      "w",
      "i",
      "l",
      "l",
      " ",
      "m",
      "a",
      "k",
      "e",
      " ",
      "d",
      "e",
      "c",
      "i",
      "s",
      "i",
      "o",
      "n",
      "s",
      " ",
      "a",
      "n",
      "d",
      " ",
      "c",
      "r",
      "e",
      "a",
      "t",
      "e",
      " ",
      "l",
      "a",
      "w",
      "s",
      " ",
      "o",
      "n",
      " ",
      "t",
      "h",
      "e",
      "i",
      "r",
      " ",
      "b",
      "e",
      "h",
      "a",
      "l",
      "f",
      " ",
    ],
    character_start_times_seconds: [
      0, 0.035, 0.093, 0.151, 0.186, 0.244, 0.302, 0.383, 0.453, 0.499, 0.557,
      0.639, 0.755, 0.824, 0.894, 0.929, 0.975, 0.998, 1.057, 1.115, 1.184,
      1.242, 1.289, 1.347, 1.393, 1.44, 1.463, 1.486, 1.567, 1.602, 1.672,
      1.707, 1.741, 1.765, 1.823, 1.858, 1.892, 1.927, 2.009, 2.159, 2.218,
      2.276, 2.31, 2.345, 2.368, 2.415, 2.473, 2.543, 2.601, 2.659, 2.717,
      2.786, 2.844, 2.902, 2.972, 3.019, 3.135, 3.181, 3.228, 3.262, 3.297,
      3.32, 3.402, 3.46, 3.518, 3.576, 3.634, 3.68, 3.762, 3.796, 3.866, 3.924,
      3.982, 4.029, 4.063, 4.133, 4.18, 4.238, 4.307, 4.365, 4.423, 4.458,
      4.505, 4.563, 4.737, 4.807, 4.841, 4.876, 4.899, 4.934, 4.969, 5.004,
      5.039, 5.074, 5.108, 5.155, 5.201, 5.236, 5.283, 5.329, 5.399, 5.48, 5.55,
      5.596, 5.642, 5.689, 5.759, 5.828, 5.886, 5.933, 5.968, 6.002, 6.06,
      6.107, 6.153, 6.211, 6.269, 6.327, 6.374, 6.42, 6.467, 6.56, 6.629, 6.676,
      6.722, 6.757, 6.792, 6.838, 6.861, 6.885, 6.92, 6.966, 6.989, 7.036, 7.07,
      7.14, 7.221, 7.338, 7.396, 7.454,
    ],
    character_end_times_seconds: [
      0.035, 0.093, 0.151, 0.186, 0.244, 0.302, 0.383, 0.453, 0.499, 0.557,
      0.639, 0.755, 0.824, 0.894, 0.929, 0.975, 0.998, 1.057, 1.115, 1.184,
      1.242, 1.289, 1.347, 1.393, 1.44, 1.463, 1.486, 1.567, 1.602, 1.672,
      1.707, 1.741, 1.765, 1.823, 1.858, 1.892, 1.927, 2.009, 2.159, 2.218,
      2.276, 2.31, 2.345, 2.368, 2.415, 2.473, 2.543, 2.601, 2.659, 2.717,
      2.786, 2.844, 2.902, 2.972, 3.019, 3.135, 3.181, 3.228, 3.262, 3.297,
      3.32, 3.402, 3.46, 3.518, 3.576, 3.634, 3.68, 3.762, 3.796, 3.866, 3.924,
      3.982, 4.029, 4.063, 4.133, 4.18, 4.238, 4.307, 4.365, 4.423, 4.458,
      4.505, 4.563, 4.737, 4.807, 4.841, 4.876, 4.899, 4.934, 4.969, 5.004,
      5.039, 5.074, 5.108, 5.155, 5.201, 5.236, 5.283, 5.329, 5.399, 5.48, 5.55,
      5.596, 5.642, 5.689, 5.759, 5.828, 5.886, 5.933, 5.968, 6.002, 6.06,
      6.107, 6.153, 6.211, 6.269, 6.327, 6.374, 6.42, 6.467, 6.56, 6.629, 6.676,
      6.722, 6.757, 6.792, 6.838, 6.861, 6.885, 6.92, 6.966, 6.989, 7.036, 7.07,
      7.14, 7.221, 7.338, 7.396, 7.454, 7.802,
    ],
  },
};

// Example usage:
const result = await splitElevenLabsAudioIntoWords(
  "./democracy.mp3",
  response.alignment
);
