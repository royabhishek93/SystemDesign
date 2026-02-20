# Media Processing Pipeline (Async)

Goal: Convert raw media into streamable variants for many devices at scale, decoupled from upload path.

## Stages & Outputs
- Ingest validation: container/codec check, duration, audio tracks, subtitles.
- Compression/Transcoding: generate bitrate ladder (e.g., 240p–4K) using H.264/HEVC/AV1.
- Audio processing: stereo/5.1/Atmos, loudness normalization.
- Encryption/DRM packaging: prepare CMAF segments + manifests (HLS/DASH) with DRM keys.
- Thumbnails & previews: image sprites, trailer cuts.
- QC/Rule checking: profanity, copyright, regional rules; reject on violations.

## Talk Tracks (Interview)
Below are short, plain-English lines you can say in an interview for each processing step.

- Ingest validation — what it is: Quick checks to ensure the uploaded file is a valid, supported video (container, codecs, duration, audio, subtitles).  
	Example: If the file is corrupted or missing audio, we flag it instead of spending hours transcoding.  
	Talk track: “We validate uploads first to avoid wasting compute on bad files.”

- Compression / Transcoding — what it is: Create multiple versions (resolutions/bitrates) from the original so the player can pick the best quality for the network/device.  
	Example: Produce 480p@1Mbps, 720p@3Mbps, 1080p@6Mbps from one source.  
	Talk track: “We transcode to a bitrate ladder so playback adapts smoothly and saves bandwidth.”

- Audio processing — what it is: Prepare and normalize audio tracks (stereo/5.1/Atmos) and match loudness across titles.  
	Example: Downmix 5.1 to stereo for phones and ensure volume levels are consistent.  
	Talk track: “We normalize and format audio so it sounds correct on every device.”

- Encryption / DRM packaging — what it is: Split the video into encrypted chunks and create manifests so licensed players can request keys and play securely.  
	Example: Each 6s segment is encrypted; the player fetches a license to decrypt it.  
	Talk track: “We package and encrypt segments and use DRM to protect paid content.”

- Thumbnails & previews — what it is: Generate poster images, sprite sheets, and short preview clips for the UI.  
	Example: Show a 128×72 thumbnail grid on hover or an auto-play 5s preview.  
	Talk track: “We make thumbnails and previews to help users browse quickly.”

- QC / Rule checking — what it is: Automated checks for policy and quality issues (profanity, copyright, loudness, missing metadata); fail or flag for review.  
	Example: If unlicensed music is detected, the title is blocked and sent to legal review.  
	Talk track: “We run automated QC to catch legal and quality problems before publishing.”

## Orchestration — simple story

- Step 1 — hand a ticket: When upload finishes we write a tiny ticket (job) to a queue with the file location and ID. It’s like giving a factory a work order — fast and non-blocking.  
	Talk track: “We hand a small work ticket to the pipeline so uploads finish immediately and processing happens in the background.”

- Step 2 — production manager (DAG): A workflow engine (the production manager) reads the ticket and runs the steps in order, while sending independent tasks (thumbnails, subtitles) to different machines at the same time.  
	Talk track: “The DAG sequences work and parallelizes independent tasks so we finish faster.”

- Step 3 — workers (machines): Worker machines do the heavy jobs (transcode, encode, package). We add more machines when the queue grows and remove them when it shrinks.  
	Talk track: “Workers are the factory machines — we scale them up for busy periods and scale down when idle.”

- Step 4 — put finished goods on the shelf: Finished files (segments, manifests) go to object storage in versioned folders. Versioning keeps old and new builds separate.  
	Talk track: “We write outputs to versioned paths so rollbacks and cache updates are safe.”

- Step 5 — update the catalog: After validation we update the metadata catalog so the player knows which versions and regions are available.  
	Talk track: “We update the catalog last so users only see fully-processed content.”

## Why asynchronous? — simple story

- Imagine the creator drops a crate at the factory door and goes for coffee; the factory works on it. The web server doesn’t hang waiting for hours. That’s async: upload returns fast, heavy work runs later.  
	Talk track: “Async keeps the user waiting time short and lets the backend scale independently.”

## Failures, retries & safety — simple story

- Try again: If a machine fails, try the task a few times with delays. If it still fails, put it on a special shelf (DLQ) for humans to inspect.  
	Talk track: “We retry transient errors and escalate persistent ones to humans.”

- Safe re-runs: Always write to a versioned folder or temp area, then mark it ready only when checks pass — so rerunning won’t break published files.  
	Talk track: “We use versioned outputs so re-runs are safe.”

- Publish what’s ready: If a low-res version finishes first, make it available so users can start watching while HD is still being made.  
	Talk track: “We publish available renditions progressively to reduce wait time.”

## Performance tuning — simple story

- Keyframes: Put anchor frames at segment boundaries so the player can jump and switch quality cleanly.  
	Talk track: “We align keyframes with segments for smooth seeking and switching.”

- Parallel work & special chips: Run multiple transcodes at once and use GPUs/hardware encoders for heavy codecs to finish faster.  
	Talk track: “We parallelize and use hardware encoders where it makes sense.”

- Low latency: For live or instant previews, make smaller chunks so viewers see updates in seconds.  
	Talk track: “For low-latency use cases we use small chunks and CMAF chunking.”

## Observability — simple story

- Watch the line: Track queue length, how long each step takes, and how many succeed or fail. Correlate a user’s upload to the final playback trace.  
	Talk track: “We instrument queues and per-stage timing to find slow or costly steps.”

- Classify errors: Tag errors (codec, storage, DRM) so alerts go to the right team.  
	Talk track: “We classify errors so engineers can act fast.”

## Security & compliance — simple story

- Keys locked in a safe: Keep DRM keys in a separate, audited service; packaging never stores the keys with content.  
	Talk track: “We isolate key management and audit access to prevent leaks.”

- Rules & watermarks: Apply regional edits and watermarks to deter leaks; block content that fails legal checks.  
	Talk track: “We enforce regional rules and watermark content to reduce legal risk.”

## Tooling — simple list

- FFmpeg for custom processing, cloud transcoders for scale, and shaka-packager/Bento4 for packaging and encryption.  
	Talk track: “We use FFmpeg for flexibility and managed transcoders for operational scale.”