# Pokémon Stream Tool 🔴🎥

A real-time, automated stream overlay built specifically for Pokémon card unboxing streams on platforms like Twitch and YouTube. Think of it as **"Shazam for Pokémon Cards."**

When a streamer pulls a card and holds it up to the webcam, this software instantly reads the card, cross-references a local database, fetches its current financial market value via the Pokémon TCG API, and triggers a flashy on-screen graphic in OBS.

## 🏗️ System Architecture
To keep the application fast and lightweight, the architecture is split into a separated backend and frontend:
* **The Vision (Python/OpenCV/Tesseract):** Captures webcam feed and extracts card set numbers via OCR.
* **The Brains (Pandas/TCG API):** Cross-references OCR data with a local, compiled dataset for zero-latency matching, then pings the live API for up-to-date pricing.
* **The Nerves (WebSockets):** A local Python server broadcasts the matched card data instantly.
* **The Face (HTML/CSS/JS):** A transparent web widget loaded into OBS Studio as a Browser Source to display the animated card art and prices.

## 🗺️ Development Roadmap
- [ ] **Phase 1: The Database Layer (Current)**
  - Clone raw JSON data from the Pokémon TCG repo.
  - Build Python scripts to compile and update a lightweight, local Pandas CSV database.
- [ ] **Phase 2: The Vision System**
  - Implement OpenCV for live camera capture.
  - Add image preprocessing (grayscale, contrast) to handle holographic glare.
  - Integrate PyTesseract to extract the set code and card number.
- [ ] **Phase 3: The Matchmaker**
  - Connect the OCR output to the Pandas database for instant ID validation.
  - Fetch real-time market prices using the official Pokémon TCG API.
- [ ] **Phase 4: The Stream Overlay**
  - Build the local WebSocket server.
  - Create the frontend HTML/CSS/JS UI widget.
  - Test live integration inside OBS Studio.

## 🚀 Local Setup (For Developers)

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/BenLevintan/pokemon_stream_tool.git](https://github.com/BenLevintan/pokemon_stream_tool.git)
   cd pokemon_stream_tool