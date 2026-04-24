import cv2
import pytesseract
import numpy as np
import re

# Tell Python exactly where Tesseract lives on Ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

class CardScanner:
    def __init__(self, camera_index=0):
        """Initializes the webcam and sets the UI boundaries."""
        self.cap = cv2.VideoCapture(camera_index)
        
        # A standard Pokemon Card is 2.5 by 3.5 (1:1.4 ratio)
        # We will make our box 250 pixels wide by 350 pixels tall
        self.scan_zone = (195, 65, 250, 350) 

    def preprocess_image(self, image_roi, mode="title"):
        """Applies different vision filters depending on the zone of the card."""
        # 1. Grayscale & Resize
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 2. Gaussian Blur to smooth the foil dot-matrix print
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        
        if mode == "title":
            # TITLE MODE: For giant foil text and hollow outlines
            # Massive block size (51) to read the overall light of the word
            thresh = cv2.adaptiveThreshold(
                blur, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                51, 5 
            )
            
            # "Ink Bleed" Effect: Erode expands the BLACK pixels
            # Forces the black outline to melt inward and fill the hollow white text
            kernel = np.ones((3, 3), np.uint8)
            processed = cv2.erode(thresh, kernel, iterations=1)
            
        elif mode == "number":
            # NUMBER MODE: For the tiny, standard black print at the bottom
            # Tight block size (15) to keep small numbers crisp
            thresh = cv2.adaptiveThreshold(
                blur, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                15, 4 
            )
            
            # Morphological Closing: Just fixes tiny gaps in numbers
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
        return processed

    def run(self):
        """Starts the camera loop."""
        print("Starting camera... Press 's' to scan, or 'q' to quit.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame. Is your webcam plugged in?")
                break

            # 1. MIRROR THE FEED FOR THE UI (Makes it feel natural for the streamer)
            display_frame = cv2.flip(frame, 1)

            x, y, w, h = self.scan_zone
            
            # Draw the main full-card box
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw visual guides for the Guillotine cuts
            top_slice_y = y + int(h * 0.15)
            bottom_slice_y = y + int(h * 0.80) # Grab the bottom 20% to avoid cutting off numbers!
            cv2.line(display_frame, (x, top_slice_y), (x+w, top_slice_y), (0, 200, 200), 1)
            cv2.line(display_frame, (x, bottom_slice_y), (x+w, bottom_slice_y), (0, 200, 200), 1)

            cv2.putText(display_frame, "Align Full Card Inside Box", (x-10, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Show the video feed
            cv2.imshow("Pokemon TCG Scanner", display_frame)

            key = cv2.waitKey(1) & 0xFF
            
            # Press 'q' to quit
            if key == ord('q'):
                break
                
            # Press 's' to manually trigger a scan
            elif key == ord('s'):
                # 2. CROP THE CARD FROM THE MIRRORED FRAME
                roi = display_frame[y:y+h, x:x+w]
                
                # 3. FLIP IT IN POST (Reverse the mirror so Tesseract can read it!)
                true_card = cv2.flip(roi, 1)
                
                # 4. THE GUILLOTINE (Top 15%, Bottom 20%)
                title_slice = true_card[0:int(h * 0.15), 0:w]
                number_slice = true_card[int(h * 0.80):h, 0:w]
                
                # Apply the specific processing pipelines!
                proc_title = self.preprocess_image(title_slice, mode="title")
                proc_number = self.preprocess_image(number_slice, mode="number")
                
                # Title OCR: PSM 6 forces left-to-right reading to ignore scattered background noise
                title_config = r'-c tessedit_char_whitelist=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" -l eng --psm 6'
                
                # Number OCR: PSM 11 looks for sparse text (the sniper)
                number_config = r'-c tessedit_char_whitelist=0123456789/ -l eng --psm 11'

                # Extract raw text
                title_text = pytesseract.image_to_string(proc_title, config=title_config).strip()
                number_text = pytesseract.image_to_string(proc_number, config=number_config)
                
                print("\n--- SCAN TRIGGERED ---")
                
                # --- HP & TITLE EXTRACTION ---
                # Look for a 2 or 3 digit number (HP)
                hp_match = re.search(r'\b(\d{2,3})\b', title_text)
                extracted_hp = hp_match.group(1) if hp_match else "Unknown"
                
                # Clean up the title by stripping out the numbers
                clean_title = re.sub(r'\d+', '', title_text).strip()
                
                print(f"🧠 Title Read: {clean_title}")
                print(f"❤️ HP Read: {extracted_hp}")
                
                # --- NUMBER EXTRACTION ---
                match = re.search(r'(\d+)/(\d+)', number_text)
                if match:
                    clean_number = str(int(match.group(1))) 
                    extracted_total = match.group(2)
                    print(f"🔢 Number Read: {clean_number}/{extracted_total}")
                else:
                    print("🔢 Number Read: 🔴 FAILED (Check alignment)")
                
                # Stack the Title and Number images vertically so you can see what Tesseract saw
                combined_debug = np.vstack((proc_title, proc_number))
                cv2.imshow("Tesseract Debug (Top & Bottom)", combined_debug)

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    scanner = CardScanner(camera_index=1) 
    scanner.run()