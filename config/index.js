export default {
  gcs: {
    serviceAccountKey: {},
    gcs_bucket: process.env.GCS_BUCKET,
    projectId: process.env.PROJECT_ID,
    structure: {
      audios: "audios",
      screenshots: "screenshots",
      other: "other",
    },
    url: process.env.GCS_URL,
  },
  speechToText: {
    languageCode: "en-US", // or your preferred language
    enableWordTimeOffsets: true,
  },
};
