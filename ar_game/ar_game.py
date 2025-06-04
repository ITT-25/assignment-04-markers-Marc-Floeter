import cv2, pyglet, sys, random
import cv2.aruco as aruco
import numpy as np
from PIL import Image


# EINSTELLUNGEN UND KONSTANTEN #########################################################################

# Fenster
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

MARKER_IDS = [0, 1, 2, 3]

# Spieleinstellungen
START_HEALTH = 3
MOSQUITO_SPAWNRATE = 3
BALLOON_SPAWNRATE = 5
MAX_MOSQUITOS = 5
MAX_BALLOONS = 3

# Hautfarbenerkennung (in HSV-Kodierung)
DARKER_SKINTONE = [0, 30, 60]
LIGHTER_SKINTONE = [20, 150, 255]

# Kreis um Fingerspitze anzeigen
FINGER_TRACKPOINT = True 

TARGET_RADIUS = 30

# Texturen
MOSQUITO_TEXTURE = pyglet.image.load("assets/mosquito.png")
BALLOON_TEXTURE = pyglet.image.load("assets/balloon.png")

# Sonstige
FRAMERATE = 60
TARGET_CORNERS = np.array([
    [0, 0],
    [WINDOW_WIDTH - 1, 0],
    [WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1],
    [0, WINDOW_HEIGHT - 1]
], dtype="float32")

# Texte
INSTRUCTION_TEXT = "Halte dein Spielfeld so vor die Kamera, dass alle vier Marker gut sichtbar sind! Drücke R um neu zu starten"
GAME_OVER_TEXT = "GAME OVER! Drücke R um neu zu starten"


# GLOBALE VARIABLEN ####################################################################################

# Fenster, Video und Rendering
video_id = 0
cap = cv2.VideoCapture(video_id) # Create a video capture object for the webcam
window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)
batch = pyglet.graphics.Batch() # Batch für Targets
warped_frame = None  # Entzerrtes Spielfeld

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

# Labels
INSTRUCTION_LABEL = pyglet.text.Label(
    text=INSTRUCTION_TEXT,
    font_name='Arial',
    font_size=24,
    x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 2,
    anchor_x='center', anchor_y='center',
    multiline=True,
    width=WINDOW_WIDTH,
    align='center',
    color=(0, 0, 0, 255)
)
SCORE_LABEL = pyglet.text.Label(
    text="Score: 0",
    font_name='Arial',
    font_size=24,
    x=WINDOW_WIDTH - 20, y=WINDOW_HEIGHT - 30,
    anchor_x='right', anchor_y='top',
    color=(0, 0, 0, 255)
)
HEALTH_LABEL = pyglet.text.Label(
    text=f"Health: {START_HEALTH}",
    font_name='Arial',
    font_size=24,
    x=20, y=WINDOW_HEIGHT - 30,
    anchor_x='left', anchor_y='top',
    color=(0, 0, 0, 255)
)

# Define the ArUco dictionary, parameters, and detector
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)
markers_detected = False

# Spielvariablen
score = 0
health = START_HEALTH
mosquitos = []
balloons = []
game_over = False


# TARGET-KLASSEN ########################################################################################

class Mosquito:
    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = random.randint(0, WINDOW_HEIGHT)
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-100, 100)
        self.sprite = pyglet.sprite.Sprite(MOSQUITO_TEXTURE, x=self.x, y=self.y, batch=batch)
        self.sprite.scale = 0.05

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bildschirmbegrenzung (Abprallen)
        if self.x < 0 or self.x > WINDOW_WIDTH:
            self.vx = -self.vx
        if self.y < 0 or self.y > WINDOW_HEIGHT:
            self.vy = -self.vy
        
        # Sprite-Position anpassen
        self.sprite.x = self.x
        self.sprite.y = self.y


class Balloon:
    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = -TARGET_RADIUS
        self.vy = random.uniform(10, 100)
        self.sprite = pyglet.sprite.Sprite(BALLOON_TEXTURE, x=self.x, y=self.y, batch=batch)
        self.sprite.scale = 0.2

    def update(self, dt):
        self.y += self.vy * dt
        self.sprite.y = self.y

        if self.y > WINDOW_HEIGHT + TARGET_RADIUS:
            balloons.remove(self)


# SPIELLOGIK ###########################################################################################

@window.event
def on_draw():
    global warped_frame, score, health, markers_detected, game_over

    window.clear()
    ret, frame = cap.read()
    if not ret:
        return

    frame_to_draw = frame
    markers_detected = False

    if not game_over:

        # MARKER ERKENNEN ##############################################################################
        
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers in the frame
        corners, ids, rejectedImgPoints = detector.detectMarkers(gray)

        # Check if 4 markers are detected
        if ids is not None and len(ids) == 4:

            id_list = ids.flatten() # 2D zu 1D array 
            corners_dict = {id_list[i]: corners[i] for i in range(len(id_list))} # Jeder Marker-ID ihre Eckpunkte zuordnen

            try:
                # SPIELFELD AUSRICHTEN #################################################################
                
                points = []
                for i in MARKER_IDS:

                    # Mittelpunkt aller Marker berechnen
                    all_points = np.concatenate([corners_dict[i][0] for i in MARKER_IDS], axis=0)
                    center = np.mean(all_points, axis=0)

                    # für jeden Marker den innersten Punkt wählen
                    for i in MARKER_IDS:
                        marker_corners = corners_dict[i][0]  # 4 Punkte
                        distances = []
                        for point in marker_corners:
                            distance = np.linalg.norm(point - center)  # Abstand zum Mittelpunkt
                            distances.append(distance)

                        # Index des kleinsten Abstands zur Mitte finden
                        min_index = np.argmin(distances)
                        inner_point = marker_corners[min_index]
                        points.append(inner_point)
                
                points = np.array(points, dtype="float32")

                # Sortiere die Punkte für Input der warp-Funktion: ol, or, ur, ul
                s = points.sum(axis=1) # Oben links hat kleinste Summe, unten rechts die größte
                diff = np.diff(points, axis=1) # Oben rechts hat kleinsten Unterschied, unten links den größten

                rect = np.zeros((4, 2), dtype="float32")
                rect[0] = points[np.argmin(s)]       # oben links
                rect[1] = points[np.argmin(diff)]    # oben rechts
                rect[2] = points[np.argmax(s)]       # unten rechts
                rect[3] = points[np.argmax(diff)]    # unten links

                # Frame anhand der Marker auf verzerren
                warped = warp_image(frame, rect)
                markers_detected = True

                # Zu zeichnenden Frame auf warped setzen (statt Originalbild)
                frame_to_draw = warped


                # FINGERERKENNUNG ######################################################################
                
                # Frame kopieren für Fingererkennungsberechnungen
                warped_frame = warped.copy()

                # HSV-Farbmodell (Um Hautfarben zu erkennen)
                hsv_frame = cv2.cvtColor(warped_frame, cv2.COLOR_BGR2HSV)

                # Hautfarbenspektrum festlegen
                lower_skin = np.array(DARKER_SKINTONE, dtype=np.uint8)
                upper_skin = np.array(LIGHTER_SKINTONE, dtype=np.uint8)

                # Hautfarbenmaske erstellen
                skincolor_mask = cv2.inRange(hsv_frame, lower_skin, upper_skin)

                # Konturen der Hand finden
                contours, hierarchy = cv2.findContours(skincolor_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                # Höchstgelegenen Punkt der Handkontur finden (min von y) und als Fingerspitze setzen
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea) # größte erkannte Kontur nehmen
                    y_values = largest_contour[:, :, 1] # y-Werte aus der Kontur

                    # Punkt mit dem kleinsten y-Wert (höchster Punkt im Bild)
                    min_y_index = y_values.argmin()
                    top_point = largest_contour[min_y_index][0]

                    finger_pos_cv2 = tuple(top_point) # In ein Tuple (Koordianten) umwandeln
                    finger_pos_pyglet = (finger_pos_cv2[0], WINDOW_HEIGHT - finger_pos_cv2[1]) # Koordinaten von cv2 zu pyglet system umrechnen
                
                else:
                    finger_pos_pyglet = None
                

                # KOLLISIONSCHECK FINGER -> TARGET #####################################################
                if finger_pos_pyglet is not None:

                    if FINGER_TRACKPOINT:
                        cv2.circle(warped, finger_pos_cv2, TARGET_RADIUS, (0, 255, 0), -1)
                    
                    # Kollisionscheck Mücken
                    for mosquito in mosquitos:
                        distance = np.linalg.norm(np.array(finger_pos_pyglet) - np.array([mosquito.x, mosquito.y]))
                        
                        if distance < TARGET_RADIUS:
                            mosquito.sprite.delete()
                            mosquitos.remove(mosquito)
                            score += 1
                            update_labels()

                    # Kollisionscheck Ballons
                    for balloon in balloons:
                        distance = np.linalg.norm(np.array(finger_pos_pyglet) - np.array([balloon.x, balloon.y]))
                        
                        if distance < TARGET_RADIUS:
                            balloon.sprite.delete()
                            balloons.remove(balloon)
                            health -= 1
                            update_labels()

                            if health <= 0: # Gameover, wenn keine Leben mehr
                                game_over = True
                                INSTRUCTION_LABEL.text = GAME_OVER_TEXT

            except KeyError:
                pass

    # Zu zeichnenden Frame (mit oder ohne Zerrung) in Pyglet umwandeln und zeichnen
    img = cv2glet(frame_to_draw, 'BGR')
    img.blit(0, 0, 0)
    
    if markers_detected: # Ingame
        batch.draw() # Targets zeichnen
    else: # Start/Pause/GameOver
        INSTRUCTION_LABEL.draw()
    
    # Score und Leben Labels immer zeichnen
    SCORE_LABEL.draw()
    HEALTH_LABEL.draw()


# Frame anhand der Marker zerren
def warp_image(image, source_corners):
    source_corners = np.array(source_corners, dtype="float32")
    transformation_matrix = cv2.getPerspectiveTransform(source_corners, TARGET_CORNERS)
    warped_img = cv2.warpPerspective(image, transformation_matrix, (WINDOW_WIDTH, WINDOW_HEIGHT))

    return warped_img


def update_labels():
    SCORE_LABEL.text = f"Score: {score}"
    HEALTH_LABEL.text = f"Health: {health}"


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


# Key-Input für Restart und Schließen
@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.Q:
        cap.release()
        window.close()
    if not markers_detected:
        if symbol == pyglet.window.key.R:
            restart()


def restart():
    global mosquitos, balloons, score, health, game_over

    mosquitos.clear()
    balloons.clear()
    score = 0
    health = START_HEALTH
    game_over = False
    update_labels()
    INSTRUCTION_LABEL.text = INSTRUCTION_TEXT


# Targets bewegen und spawnen (Auslöser = Clocks unten)
def update_targets(dt):
    if markers_detected:
        for target in mosquitos:
            target.update(dt)
        for target in balloons:
            target.update(dt)


def spawn_mosquito(dt):
    global mosquitos
    if markers_detected:
        if len(mosquitos) < MAX_MOSQUITOS:
            mosquitos.append(Mosquito())


def spawn_balloon(dt):
    global balloons
    if markers_detected:
        if len(balloons) < MAX_BALLOONS:
            balloons.append(Balloon())
    

# Scheduling für Targetbewegung und -spawning
pyglet.clock.schedule_interval(update_targets, 1/FRAMERATE)
pyglet.clock.schedule_interval(spawn_mosquito, MOSQUITO_SPAWNRATE)
pyglet.clock.schedule_interval(spawn_balloon, BALLOON_SPAWNRATE)


pyglet.app.run()