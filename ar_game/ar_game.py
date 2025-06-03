import cv2
import cv2.aruco as aruco
import numpy as np
import pyglet
from PIL import Image
import sys


WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
MARKER_IDS = [0, 1, 2, 3]
TARGET_POS = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
TARGET_RADIUS = 30
TARGET_COLOR = (255, 0, 0)

TARGET_CORNERS = np.array([
    [0, 0],
    [WINDOW_WIDTH - 1, 0],
    [WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1],
    [0, WINDOW_HEIGHT - 1]
], dtype="float32")

video_id = 0
cap = cv2.VideoCapture(video_id) # Create a video capture object for the webcam
window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

warped_frame = None  # Entzerrtes Spielfeld

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

# Define the ArUco dictionary, parameters, and detector
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)

# converts OpenCV image to PIL image and then to pyglet texture https://gist.github.com/nkymut/1cb40ea6ae4de0cf9ded7332f1ca0d55
def cv2glet(img,fmt):
    '''Assumes image is in BGR color space. Returns a pyimg object'''
    if fmt == 'GRAY':
      rows, cols = img.shape
      channels = 1
    else:
      rows, cols, channels = img.shape

    raw_img = Image.fromarray(img).tobytes()

    top_to_bottom_flag = -1
    bytes_per_row = channels*cols
    pyimg = pyglet.image.ImageData(width=cols, 
                                   height=rows, 
                                   fmt=fmt, 
                                   data=raw_img, 
                                   pitch=top_to_bottom_flag*bytes_per_row)
    return pyimg


def warp_image(image, source_corners):
    source_corners = np.array(source_corners, dtype="float32")
    transformation_matrix = cv2.getPerspectiveTransform(source_corners, TARGET_CORNERS)
    warped_img = cv2.warpPerspective(image, transformation_matrix, (WINDOW_WIDTH, WINDOW_HEIGHT))

    return warped_img


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.Q:
        cap.release()
        window.close()


@window.event
def on_draw():
    global warped_frame

    window.clear()
    ret, frame = cap.read()
    if not ret:
        return

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers in the frame
    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)

    # Check if 4 markers are detected
    if ids is not None and len(ids) == 4:

        id_list = ids.flatten()
        corners_dict = {id_list[i]: corners[i] for i in range(len(id_list))}

        try:
            pts = []
            for i in MARKER_IDS:
                # Mittelpunkt aller Marker berechnen
                all_points = np.concatenate([corners_dict[i][0] for i in MARKER_IDS], axis=0)
                center = np.mean(all_points, axis=0)

                # für jeden Marker den innersten Punkt wählen
                for i in MARKER_IDS:
                    marker_corners = corners_dict[i][0]  # 4 Punkte
                    # Punkt mit minimalem Abstand zum Mittelpunkt
                    inner_pt = min(marker_corners, key=lambda pt: np.linalg.norm(pt - center))
                    pts.append(inner_pt)
            
            pts = np.array(pts, dtype="float32")

            # Sortiere die Punkte: tl, tr, br, bl
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)

            rect = np.zeros((4, 2), dtype="float32")
            rect[0] = pts[np.argmin(s)]       # top-left
            rect[2] = pts[np.argmax(s)]       # bottom-right
            rect[1] = pts[np.argmin(diff)]    # top-right
            rect[3] = pts[np.argmax(diff)]    # bottom-left

            warped = warp_image(frame, rect)
            warped_frame = warped.copy()

            cv2.circle(warped, TARGET_POS, TARGET_RADIUS, TARGET_COLOR, -1)
            
            img = cv2glet(warped, 'BGR')
            img.blit(0, 0, 0)
            return
        
        except KeyError:
            # Falls Marker fehlen, Originalbild anzeigen
            pass

    # Wenn nicht alle Marker erkannt wurden, Originalbild anzeigen
    img = cv2glet(frame, 'BGR')
    img.blit(0, 0, 0)

pyglet.app.run()