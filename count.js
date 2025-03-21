import fs from 'fs';

const rawData = fs.readFileSync('D:/Lingwing/dubbers/thomas/text_mismatches.json');
const data = JSON.parse(rawData);

console.log(data.mismatches.length);

let totalMoreDetected = 0;
let totalLessDetected = 0;

for (const mismatch of data.mismatches) {
    if (mismatch.detected_word_count > mismatch.original_word_count) {
        totalMoreDetected++;
    } else if (mismatch.detected_word_count < mismatch.original_word_count) {
        totalLessDetected++;
    }
}

console.log(`Total more detected: ${totalMoreDetected}`);
console.log(`Total less detected: ${totalLessDetected}`);