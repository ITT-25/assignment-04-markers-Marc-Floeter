import cv2, os, argparse, sys
import numpy as np

# Input args parsen, Konstanten setzen
parser = argparse.ArgumentParser(description="Perspective Image Extractor")
parser.add_argument("input", help="Pfad zum Eingabebild")
parser.add_argument("output", help="Pfad zur Ausgabedatei")
parser.add_argument("width", type=int, help="Breite des entzerrten Bildes")
parser.add_argument("height", type=int, help="Höhe des entzerrten Bildes")
args = parser.parse_args()

INPUT_IMG_PATH = args.input
OUTPUT_IMG_PATH = args.output
OUTPUT_DIR = os.path.dirname(OUTPUT_IMG_PATH)
TARGET_WIDTH = args.width
TARGET_HEIGHT = args.height
TARGET_CORNERS = np.array([
    [0, 0],
    [TARGET_WIDTH - 1, 0],
    [TARGET_WIDTH - 1, TARGET_HEIGHT - 1],
    [0, TARGET_HEIGHT - 1]
], dtype="float32")

PREVIEW_WINDOW_NAME = "Preview Window"
WARPED_WINDOW_NAME = "Warped"

ORIGINAL_IMAGE = cv2.imread(INPUT_IMG_PATH)
corners_img = ORIGINAL_IMAGE.copy()
corners = [] # oben-links, oben-rechts, unten-rechts, unten-links (Uhrzeigersinn ab oben-links)

awaiting_input = False


# Input args prüfen
if not os.path.isfile(INPUT_IMG_PATH):
    print(f"Fehler: Eingabedatei existiert nicht: {INPUT_IMG_PATH}")
    sys.exit(1)
if ORIGINAL_IMAGE is None:
    print(f"Fehler: Bild konnte nicht geladen werden (evtl. falsches Format): {INPUT_IMG_PATH}")
    sys.exit(1)
if not os.path.exists(OUTPUT_DIR):
    print(f"Warnung: Output-Verzeichnis existierte nicht und wurde neu erstellt: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR)

# Falls alles mit args ok -> Fenster erstellen
cv2.namedWindow(PREVIEW_WINDOW_NAME)


# Anfangs Originalbild anzeigen
cv2.imshow(PREVIEW_WINDOW_NAME, ORIGINAL_IMAGE)


def mouse_callback(event, x, y, flags, param):
    global corners, corners_img, awaiting_input, warped_img

    # Falls Mausklick und noch keine 4 Eckpunkte ausgewählt
    if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
        corners.append((x, y))
        corners_img = cv2.circle(corners_img, (x, y), 5, (255, 0, 0), -1) # Eckmarker setzen
        cv2.imshow(PREVIEW_WINDOW_NAME, corners_img)

        # Falls alle 4 Eckpunkte ausgewählt
        if len(corners) == 4: 
            warped_img = warp_image(ORIGINAL_IMAGE, corners)
            cv2.imshow(WARPED_WINDOW_NAME, warped_img) # Transformiertes Bild anzeigen
            awaiting_input = True # Ab jetzt auf Input bzgl. transformiertem Bild (Speichern, Verwerfen) warten


# Bild zerren
def warp_image(image, source_corners):
    source_corners = np.array(source_corners, dtype="float32")
    transformation_matrix = cv2.getPerspectiveTransform(source_corners, TARGET_CORNERS)
    warped_img = cv2.warpPerspective(image, transformation_matrix, (TARGET_WIDTH, TARGET_HEIGHT))

    return warped_img


# Transformation zurücksetzen
def reset():
    global corners, awaiting_input, corners_img

    if cv2.getWindowProperty(WARPED_WINDOW_NAME, cv2.WND_PROP_VISIBLE) == 1:
        cv2.destroyWindow(WARPED_WINDOW_NAME)
    corners = []
    corners_img = ORIGINAL_IMAGE.copy()
    cv2.imshow(PREVIEW_WINDOW_NAME, corners_img)
    awaiting_input = False


# Maus-Callback setzen
cv2.setMouseCallback(PREVIEW_WINDOW_NAME, mouse_callback)


# Key Inputs prüfen
while True:
    key = cv2.waitKey(1)
    if awaiting_input:
        if key == ord("s") or key == ord("S"): # S wenn Transformation durchgeführt -> Bild speichern und reset
            cv2.imwrite(OUTPUT_IMG_PATH, warped_img)
            print(f"Bild gespeichert unter: {OUTPUT_IMG_PATH}")
            reset()
        elif key == 27:  # ESC wenn Transformation durchgeführt -> Transformation verwerfen
            print("Verwerfe Transformation –> Zurück zur Auswahl.")
            reset()
    elif key == 27: # ESC wenn Transformation noch nicht durchgeführt -> Punkte verwerfen
        print("Verwerfe Transformationspunkte")
        reset()
    elif key == ord("q") or key == ord("Q"):  # Q im Vorschaufenster -> komplett beenden
        cv2.destroyAllWindows()
        break