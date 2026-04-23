import cv2
import pytesseract
import numpy as np
import re

# Tell Python exactly where Tesseract lives on Ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

class CardScanner:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        
        # A standard Pokemon Card is 2.5 by 3.5 (1:1.4 ratio)
        # We will make our box 250 pixels wide by 350 pixels tall
        self.scan_zone = (195, 65, 250, 350) 

    def preprocess_image(self, image_roi):
        """Advanced Image Preprocessing for uneven room lighting."""
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        return thresh

    def run(self):
        print("Starting camera... Press 's' to scan, or 'q' to quit.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # 1. MIRROR THE FEED FOR THE UI (Makes it feel natural)
            display_frame = cv2.flip(frame, 1)

            x, y, w, h = self.scan_zone
            
            # Draw the main full-card box
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw visual guides inside the box so the streamer knows where the text goes
            top_slice_y = y + int(h * 0.15)
            bottom_slice_y = y + int(h * 0.85)
            cv2.line(display_frame, (x, top_slice_y), (x+w, top_slice_y), (0, 200, 200), 1)
            cv2.line(display_frame, (x, bottom_slice_y), (x+w, bottom_slice_y), (0, 200, 200), 1)

            cv2.putText(display_frame, "Align Full Card Inside Box", (x-10, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Pokemon TCG Scanner", display_frame)

            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
                
            elif key == ord('s'):
                # 2. CROP THE CARD FROM THE MIRRORED FRAME
                roi = display_frame[y:y+h, x:x+w]
                
                # 3. FLIP IT IN POST (Reverse the mirror so Tesseract can read it!)
                true_card = cv2.flip(roi, 1)
                
                # 4. THE GUILLOTINE (Chop the top and bottom, throw away the middle art)
                title_slice = true_card[0:int(h * 0.15), 0:w]
                number_slice = true_card[int(h * 0.85):h, 0:w]
                
                # Preprocess both slices to kill glare
                proc_title = self.preprocess_image(title_slice)
                proc_number = self.preprocess_image(number_slice)
                
                # Title OCR: Only allow letters and spaces
                title_config = r'-c tessedit_char_whitelist=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\'" -l eng --psm 7'
                # Number OCR: The Sniper (Numbers and Slashes only)
                number_config = r'-c tessedit_char_whitelist=0123456789/ -l eng --psm 11'

                title_text = pytesseract.image_to_string(proc_title, config=title_config).strip()
                number_text = pytesseract.image_to_string(proc_number, config=number_config)
                
                print("\n--- SCAN TRIGGERED ---")
                print(f"Title OCR Read: {title_text}")
                
                match = re.search(r'(\d+)/(\d+)', number_text)
                if match:
                    clean_number = str(int(match.group(1))) 
                    extracted_total = match.group(2)
                    print(f"Number OCR Read: {clean_number}/{extracted_total}")
                else:
                    print("Number OCR Read: 🔴 FAILED")
                
                # Stack the Title and Number images vertically so you can see what Tesseract saw
                combined_debug = np.vstack((proc_title, proc_number))
                cv2.imshow("Tesseract Debug (Top & Bottom)", combined_debug)

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    scanner = CardScanner(camera_index=1)
    scanner.run()