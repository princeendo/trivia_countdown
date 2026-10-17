# Social Media Post

## Suggested Facebook Text

I made a small tool for church and community events: give it a background video and a spreadsheet of trivia questions, and it creates a ready-to-play MP4 with timed questions and answer reveals.

The current preview runs locally on Apple Silicon Macs. Here's a quick demo and the project:

https://github.com/princeendo/trivia_countdown

## Post Assets

- `trivia-countdown-demo.mp4`: 14.5-second H.264/AAC demo for the Facebook upload
- `demo-thumbnail.png`: answer-reveal frame for the video's custom thumbnail
- `app-screenshot.png`: packaged-app interface with example paths and a loaded preview
- `countdown-excerpt.mp4`: short source excerpt used to create the demo
- `geodepths-countdown-source.mp4`: original source countdown video (kept locally, not committed because of its size)

Upload the MP4 as native Facebook video, select `demo-thumbnail.png` as its thumbnail, and attach `app-screenshot.png` as the supporting image if the post format permits both.

## Recreate The Demo

Create the excerpt from the original source:

```sh
ffmpeg -y -ss 194 \
  -i dist/social-media-post/geodepths-countdown-source.mp4 \
  -t 14.5 \
  -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -af "afade=t=in:st=0:d=0.4,afade=t=out:st=13.7:d=0.8" \
  -movflags +faststart \
  dist/social-media-post/countdown-excerpt.mp4
```

Render two sample questions over the excerpt:

```sh
uv run python make_trivia_countdown.py \
  dist/social-media-post/countdown-excerpt.mp4 \
  sample_objects/sample_of_5_trivia_questions.csv \
  --output dist/social-media-post/trivia-countdown-demo.mp4 \
  --duration 4 \
  --answer-duration 2 \
  --answer-flash-duration 1.5 \
  --answer-flash-interval 0.2 \
  --start-delay 0.5 \
  --end-early 0.5 \
  --fade-in-time 0.3 \
  --fade-out-time 0.3 \
  --mid-question-fade 0.3
```

## Media Rights

The countdown is marked "Motion Worship" in the video. Its use for this social post and repository example has been confirmed by the project owner.
