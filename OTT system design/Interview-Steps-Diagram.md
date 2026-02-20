# Interview Steps Diagram

This PlantUML sequence diagram shows the end-to-end flow from upload to playback.

Paste the contents of [Interview-Steps-Diagram.puml](OTT%20system%20design/Interview-Steps-Diagram.puml) into a PlantUML renderer (e.g., the public server/editor) to generate a URL and PNG. Once rendered, we can store the URL in a new file (e.g., \"Class Diagam Url 2\") and save the snapshot as \"image-2.png\" to match this workspace’s conventions.

## Diagram Source
```plantuml
@startuml
left to right direction
skinparam shadowing false
skinparam arrowThickness 1
skinparam defaultFontName Helvetica

actor "Content Provider" as CP
participant "OTT API" as API
database "Metadata DB" as DB
queue "Message Queue" as MQ
node "Workers\n(Transcode/Encrypt/Package)" as WK
cloud "Object Storage\n(Origin)" as S3
cloud "CDN" as CDN
actor "User/Player" as USER

CP -> API: Request upload
API -> DB: Upsert metadata (title, tags, release date)
API -> S3: Create presigned multipart URL
API --> CP: Return presigned URL + uploadId

CP -> S3: Multipart upload (parallel parts, retries)
CP -> API: Finalize upload
API -> S3: Validate object (etag/checksum)
API -> MQ: Enqueue processing job

MQ -> WK: Pull job
WK -> S3: Read raw object
WK -> S3: Write renditions (segments/manifests)
WK -> DB: Update availability per rendition

USER -> CDN: Request manifest (HLS/DASH)
CDN -> S3: Fetch origin (cache miss)
CDN --> USER: Serve cached segments/manifests
USER -> CDN: Adaptive segment requests (seek, bitrate switches)
@enduml
```