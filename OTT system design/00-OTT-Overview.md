# OTT Overview (Easy Guide)

This guide explains OTT systems in simple terms to help you prep for interviews.

## What is OTT?
An OTT (Over-The-Top) service streams media over the internet directly to users — no cable/satellite required. Examples: Netflix, Prime Video, Disney+, YouTube.

## Key Stakeholders
- Content Providers: Upload and manage titles (movies/series).
- OTT Platform: Stores, processes, and streams content to users.
- Users: Watch content across devices (mobile, web, smart TV).

## Core User Experience
- Playback: Smooth, low-latency video start and seek.
- Search: Fast discovery across title, genre, tags.
- Recommendations: Personalized suggestions per profile.
- Personalization: Multiple profiles per account, watch history, parental controls.

## High-Level Flow
1. Provider uploads raw content.
2. OTT stores metadata and the raw file.
3. Media is processed (transcoded, encrypted, packaged).
4. Processed outputs are stored as chunks.
5. CDN serves chunks to users near their location.
6. Player adapts quality based on network (HLS/DASH).