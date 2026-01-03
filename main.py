import cv2
import mediapipe as mp
import random
import time
import winsound
from gesture_logic import GestureDetector

# ---------------- CONFIG ----------------
STABLE_FRAMES = 5
COUNTDOWN_TIME = 3
FREEZE_TIME = 1.5
WIN_SCORE = 2  # Best of 3

# ---------------- GAME STATES ----------------
WAITING = "WAITING"
COUNTDOWN = "COUNTDOWN"
RESULT = "RESULT"
MATCH_OVER = "MATCH_OVER"

game_state = WAITING

# ---------------- SCORES ----------------
user_score = 0
computer_score = 0

# ---------------- VARIABLES ----------------
detector = GestureDetector(STABLE_FRAMES)
countdown_start = 0
last_user_gesture = None

user_move = "Waiting..."
computer_move = None
game_result = ""

# ---------------- ICONS ----------------
icons = {
    "Rock": cv2.imread("rock.png", cv2.IMREAD_UNCHANGED),
    "Paper": cv2.imread("paper.png", cv2.IMREAD_UNCHANGED),
    "Scissors": cv2.imread("scissors.png", cv2.IMREAD_UNCHANGED),
}

def overlay_png(bg, overlay, x, y, scale=0.15):
    if overlay is None:
        return
    h, w = overlay.shape[:2]
    overlay = cv2.resize(overlay, (int(w * scale), int(h * scale)))
    b, g, r, a = cv2.split(overlay)
    overlay_rgb = cv2.merge((b, g, r))
    mask = cv2.merge((a, a, a))
    roi = bg[y:y + overlay_rgb.shape[0], x:x + overlay_rgb.shape[1]]
    bg_part = cv2.bitwise_and(roi, cv2.bitwise_not(mask))
    fg_part = cv2.bitwise_and(overlay_rgb, mask)
    bg[y:y + overlay_rgb.shape[0], x:x + overlay_rgb.shape[1]] = cv2.add(bg_part, fg_part)

# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # UI background bar (WHITE)
    cv2.rectangle(frame, (0, 0), (w, 260), (255, 255, 255), -1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    instruction = ""
    current_time = time.time()
    smooth_gesture = "Unknown"

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            fingers = detector.fingers_status(hand_landmarks)
            gesture = detector.get_gesture(fingers)
            smooth_gesture = detector.smooth(gesture)

    # ---------------- WAITING ----------------
    if game_state == WAITING:
        instruction = "Show your gesture"
        if smooth_gesture != "Unknown":
            countdown_start = current_time
            game_state = COUNTDOWN
            winsound.Beep(600, 150)

    # ---------------- COUNTDOWN ----------------
    elif game_state == COUNTDOWN:
        remaining = COUNTDOWN_TIME - int(current_time - countdown_start)
        if remaining > 0:
            instruction = f"Hold... {remaining}"
        else:
            if smooth_gesture != "Unknown":
                user_move = smooth_gesture
                computer_move = random.choice(["Rock", "Paper", "Scissors"])
                game_result = detector.decide_winner(user_move, computer_move)

                if game_result == "YAY! You Win!":
                    user_score += 1
                    winsound.Beep(900, 200)
                    winsound.Beep(1100, 200)
                elif game_result == "Computer Wins!":
                    computer_score += 1
                    winsound.Beep(400, 300)
                else:
                    winsound.Beep(650, 150)

                last_user_gesture = user_move
                game_state = RESULT

    # ---------------- RESULT ----------------
    elif game_state == RESULT:
        instruction = "Change gesture for next round"
        if user_score == WIN_SCORE or computer_score == WIN_SCORE:
            game_state = MATCH_OVER
            match_end_time = current_time
        elif smooth_gesture != last_user_gesture and smooth_gesture != "Unknown":
            detector.history.clear()
            game_state = WAITING

    # ---------------- MATCH OVER ----------------
    elif game_state == MATCH_OVER:
        instruction = "MATCH OVER"
        winner_text = "YOU WON THE MATCH" if user_score == WIN_SCORE else "COMPUTER WON"
        cv2.putText(frame, winner_text, (80, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
        if current_time - match_end_time > 3:
            user_score = computer_score = 0
            user_move = "Waiting..."
            computer_move = None
            game_result = ""
            detector.history.clear()
            game_state = WAITING

    # ---------------- UI TEXT (FIXED SCORE COLOR) ----------------
    cv2.putText(frame, f"YOU: {user_score}   COMPUTER: {computer_score}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)  # ✅ BLACK

    cv2.putText(frame, f"Your Move: {user_move}", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 150, 0), 2)

    cv2.putText(frame, f"Computer: {computer_move if computer_move else '---'}",
                (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (150, 0, 0), 2)

    cv2.putText(frame, f"Result: {game_result}", (20, 170),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 0), 2)

    cv2.putText(frame, instruction, (20, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 200), 2)

    if user_move in icons:
        overlay_png(frame, icons[user_move], 420, 80)
    if computer_move in icons:
        overlay_png(frame, icons[computer_move], 420, 130)

    cv2.imshow("Rock Paper Scissors - CV", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
