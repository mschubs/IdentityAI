import cv2

# Replace with your actual livestream URL (HLS stream)
stream_url = "https://your_stream_url_here.m3u8"
cap = cv2.VideoCapture(stream_url)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Livestream", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()