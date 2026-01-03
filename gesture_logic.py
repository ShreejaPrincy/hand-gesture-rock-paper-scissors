from collections import deque, Counter

class GestureDetector:
    def __init__(self, max_frames=5):
        self.history = deque(maxlen=max_frames)

    def fingers_status(self, hand_landmarks):
        fingers = []

        # Thumb
        fingers.append(1 if hand_landmarks.landmark[4].x >
                          hand_landmarks.landmark[3].x else 0)

        # Other fingers
        tips = [8, 12, 16, 20]
        for tip in tips:
            fingers.append(
                1 if hand_landmarks.landmark[tip].y <
                     hand_landmarks.landmark[tip - 2].y else 0
            )
        return fingers

    def get_gesture(self, fingers):
        _, i, m, r, p = fingers

        if [i, m, r, p] == [0, 0, 0, 0]:
            return "Rock"
        elif [i, m, r, p] == [1, 1, 0, 0]:
            return "Scissors"
        elif [i, m, r, p] == [1, 1, 1, 1]:
            return "Paper"
        else:
            return "Unknown"

    def smooth(self, gesture):
        self.history.append(gesture)
        return Counter(self.history).most_common(1)[0][0]

    @staticmethod
    def decide_winner(user, computer):
        if user == computer:
            return "Draw"

        rules = {
            "Rock": "Scissors",
            "Paper": "Rock",
            "Scissors": "Paper"
        }

        return "YAY! You Win!" if rules[user] == computer else "Computer Wins!"
