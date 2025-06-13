import cv2

def test_camera():
    # Try all available video devices
    for i in range(4):
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if cap.isOpened():
            print(f"Successfully opened video device {i}")
            ret, frame = cap.read()
            if ret:
                print(f"Successfully read frame from video device {i}")
                # Release the camera
                cap.release()
                return True
            cap.release()
    return False

if __name__ == "__main__":
    if test_camera():
        print("Camera test successful!")
    else:
        print("Failed to access any camera")
