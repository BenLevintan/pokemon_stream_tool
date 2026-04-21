import cv2

def get_working_camera():

    # Try index 1 - external camera
    print("Attempting to connect to external cam...")
    cap = cv2.VideoCapture(1)

    # Check if we managed connection with camera 1
    if cap.isOpened():
        ret, test_frame = cap.read()
        if ret:
            print("Using external cam.")
            return cap
        

    # In case camera index 1 has failed -> fallback to index 0
    cap.release()

    print("Fail to connect to an external cam, trying to use webcam/next video imput...")
    cap = cv2.VideoCapture(0)    

    if cap.isOpened():
        ret, test_frame = cap.read()
        if ret:
            print("Using index 0 cam.")
            return cap
        

    # If both failed
    cap.release()
    print("Error: Could not find any working cameras.")
    return None