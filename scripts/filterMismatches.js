import fs from 'fs/promises';
import path from 'path';

async function filterMismatches() {
    try {
        // Read the original mismatches file
        const data = await fs.readFile('D:/Lingwing/andrewMultilingualNeural3/text_mismatches.json', 'utf8');
        const mismatches = JSON.parse(data);

        // Function to get word count (after basic normalization)
        const getWordCount = (text) => {
            return text.toLowerCase()
                .replace(/[.,!?;:'"()-]/g, '')  // Remove punctuation
                .replace(/\s+/g, ' ')           // Normalize spaces
                .trim()
                .split(' ')
                .length;
        };

        // Filter mismatches to only include different word counts
        const realMismatches = {
            mismatches: mismatches.mismatches.filter(item => {
                const originalWordCount = getWordCount(item.original_text);
                const detectedWordCount = getWordCount(item.detected_text);
                
                // Debug output for word count differences
                if (originalWordCount !== detectedWordCount) {
                    console.log('\nWord count difference found in:', item.filename);
                    console.log('Original:', item.original_text, `(${originalWordCount} words)`);
                    console.log('Detected:', item.detected_text, `(${detectedWordCount} words)`);
                }
                
                return originalWordCount !== detectedWordCount;
            })
        };

        // Save the filtered mismatches
        await fs.writeFile(
            'D:/Lingwing/andrewMultilingualNeural3/real_text_mismatches3.json',
            JSON.stringify(realMismatches, null, 2),
            'utf8'
        );

        console.log(`\nFound ${realMismatches.mismatches.length} real mismatches`);
        console.log('Filtered mismatches saved to real_text_mismatches.json');

    } catch (error) {
        console.error('Error:', error);
    }
}

filterMismatches();