import cv2
import pytesseract
import numpy as np

try:
    # For when imported as a module (e.g., from a main script)
    from .camera_utils import get_working_camera
except ImportError:
    # For when run as a standalone script for testing
    from camera_utils import get_working_camera

# Tell Python exactly where Tesseract lives on Ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


class CardScanner:
    def __init__(self):
        """Initializes the scanner by finding a working camera.
        It uses the utility function which prioritizes camera 1 (external) over 0 (internal).
        """
        self.cap = get_working_camera()
        self.scan_zone = (200, 300, 240, 100) 

    def preprocess_image(self, image_roi):
        """Advanced Image Preprocessing for uneven room lighting."""
        # 1. Convert to Grayscale
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        
        # 2. Resize to make text larger for Tesseract
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 3. Adaptive Thresholding (The Magic Fix)
        # This calculates lighting dynamically for different parts of the card
        # It forces the background to be white and the text to be black, no matter the shadow.
        thresh = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        return thresh


    def run(self):
        if not self.cap or not self.cap.isOpened():
            # get_working_camera() already prints a detailed error message.
            print("Aborting scanner.")
            return

        print("Starting camera... Press 's' to scan, or 'q' to quit.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # REMOVED: cv2.flip(frame, 1) 
            # We must not mirror the frame, otherwise the text becomes backwards!

            x, y, w, h = self.scan_zone
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Hold Set Code Here", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Pokemon TCG Scanner", frame)

            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
                
            elif key == ord('s'):
                roi = frame[y:y+h, x:x+w]
                processed_roi = self.preprocess_image(roi)
                
                # Whitelist config
                custom_config = r'-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/ -l eng --psm 6'

                text = pytesseract.image_to_string(processed_roi, config=custom_config)
                
                print("\n--- SCAN TRIGGERED ---")
                print(f"Raw OCR Output: {text.strip()}")
                
                cv2.imshow("What Tesseract Sees", processed_roi)

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    scanner = CardScanner()
    scanner.run()