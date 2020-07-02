import pygame

# Initialize pygame
pygame.init()

# Get user's monitor width, create pygame window and set fullscreen
MON_W = pygame.display.Info().current_w
MON_H = pygame.display.Info().current_h
WIN = pygame.display.set_mode((MON_W, MON_H), pygame.FULLSCREEN)

# Colors used
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (32, 32, 32)
RED = (255, 0, 0)
LIGHT_BLUE = (100, 100, 255)
DARK_BLUE = (0, 0, 255)

# Other global variables
CLOSE = (50, 30)
SPACING = 20
WIDTH = (MON_W - 2 * SPACING) // 52
HEIGHT = MON_H // 4 - SPACING
FADE = 5
NOTE_FADE = 200
DELAY = 1000
OCCUPIED_CHANNELS = [0, 1, 2, 3, 4, 5, 6, 7]

# Create 8 pygame sound channels (you can only play one sound at a time in a channel)
for i in range(8):
    globals()["channel_{0}".format(i)] = pygame.mixer.Channel(i)

# ALL OF THE GLOBAL VARIABLES BELOW ARE DETERMINED BY USER INPUT OR IMAGE RECOGNITION
# Tempo in beats per minute
TEMPO = 120
# Default articulation
ARTICULATION = "legato"
# Number of beats in a bar (top number)
TIME_SIGNATURE_TOP = 3
# Note value of a beat (bottom number)
TIME_SIGNATURE_BOTTOM = 8
# Number of milliseconds for each beat
BEAT_DURATION = 60 / TEMPO * 1000


# Attribute of each note read from the music sheet
class N:
    def __init__(self, key, value, articulation=ARTICULATION, channel=None, pedal=False):
        self.key = key
        self.value = value
        self.articulation = articulation
        self.hand = 0
        self.beat_num = 0
        self.played = False
        self.pedal = pedal
        self.faded = False
        self.channel = channel

    def play(self, start_time):
        # Get current ticks
        current_time = pygame.time.get_ticks()
        # Calculate elapsed time since start of program
        elapsed = current_time - start_time
        # If the time matches the beat number for this particular note
        if self.key and elapsed >= self.beat_num * DURATION + DELAY:
            # If the pedal is not applied (which keeps the notes from stopping), fade the note out
            if not self.pedal:
                # If the note has been played and its time is passed and the articulation is staccato, fade the note out quickly
                # Or if the note is a silence that has not been played yet, fade out the channels corresponding to the note
                if self.articulation[0] != "l" and elapsed >= (self.beat_num + min_val / self.value - 1) * DURATION + DELAY \
                        or self.articulation[0] == "l" and elapsed >= (self.beat_num + min_val / self.value) * DURATION + DELAY:
                    if self.played and not self.faded:
                        if not self.channel:
                            # Quickly fade this note only
                            channel = globals()["channel_{0}".format((self.beat_num % 2) + 4 * self.hand)]
                        else:
                            channel = pygame.mixer.Channel(self.channel)
                        channel.fadeout(NOTE_FADE)
                        # Keep track of when a note has already been faded out so that the channel doesn't fade out all other notes
                        self.faded = True
                elif self.key == "s" and not self.played:
                    # Quickly fade all notes on the channels that correspond to that hand
                    for n in range(4):
                        channel = globals()["channel_{0}".format(4 * self.hand + n)]
                        channel.fadeout(NOTE_FADE)
                    # If the silence was just played, update its played value
                    if self.key == "s":
                        self.played = True
            # If the key to play is not a silence and the time is right and the note has not already been played
            if not self.played and self.key != "s":
                # Check which note object corresponds to the note being played
                for note_object in NOTES:
                    # If the key is exactly the same (e.g.: "Ab5" = "Ab5")
                    if self.key == note_object.key:
                        # Set the color to start the fade
                        if len(note_object.key_type) == 1:
                            note_object.color = LIGHT_BLUE
                        else:
                            note_object.color = DARK_BLUE
                        # Stop the for loop
                        break
                if self.channel:
                    channel = pygame.mixer.Channel(self.channel)
                    OCCUPIED_CHANNELS.remove(self.channel)
                elif not self.pedal:
                    # Calculate which channel to play the note in (each channel is responsible for half the notes)
                    channel = globals()["channel_{0}".format((self.beat_num % 2) + 4 * self.hand)]
                else:
                    channel = globals()["channel_{0}".format((self.beat_num % 4) + 4 * self.hand)]
                # Stop any sound playing on this channel
                channel.stop()
                # Play the current note
                channel.play(globals()[self.key])
                print("Playing note: " + self.key)
                # Append the note to a list so that the program doesn't play it again
                self.played = True


class Chord:
    def __init__(self, notes, value, articulation=ARTICULATION, pedal=False):
        self.beat_num = 0
        self.pedal = pedal
        self.key = []
        self.channel = 0
        self.value = value
        for n, key in enumerate(notes):
            while self.channel in OCCUPIED_CHANNELS:
                self.channel += 1
            self.key.append(N(key, value, articulation, channel=self.channel, pedal=self.pedal))
            OCCUPIED_CHANNELS.append(self.channel)
        pygame.mixer.set_num_channels(self.channel + 1)

    def play(self, start_time):
        for key in self.key:
            key.beat_num = self.beat_num
            key.play(start_time)


# Notes to play in channels 1 and 2 in regular legato and staccato (index 0 and 1), corresponds to right hand
# Notes play also in channels 1 to 4 (index 0 to 3) when the pedal is pressed. That way, each note can play longer before fading out
# The notes lists are lists of bars, which are themselves lists of notes. That way, we can keep track of when the pedal is pressed
NOTES_0 = [[N("E5", 16), N("Eb5", 16)],
           [N("E5", 16), N("Eb5", 16), N("E5", 16), N("B4", 16), N("D5", 16), N("C5", 16)],
           [N("A4", 8), N("s", 16), N("C4", 16), N("E4", 16), N("A4", 16)],
           [N("B4", 8), N("s", 16), N("E4", 16), N("Ab4", 16), N("B4", 16)],
           [N("C5", 8), N("s", 16), N("E4", 16), N("E5", 16), N("Eb5", 16)],
           [N("E5", 16), N("Eb5", 16), N("E5", 16), N("B4", 16), N("D5", 16), N("C5", 16)],
           [N("A4", 8), N("s", 16), N("C4", 16), N("E4", 16), N("A4", 16)],
           [N("B4", 8), N("s", 16), N("E4", 16), N("C5", 16), N("B4", 16)],
           [N("A4", 4)]]
# Notes to play in channels 5 and 6 in regular legato and staccato (index 4 and 5), corresponds to left hand
# Notes play also in channels 5 to 8 (index 4 to 7) when the pedal is pressed. That way, each note can play longer before fading out
NOTES_1 = [[N("s", 8)],
           [N("s", TIME_SIGNATURE_BOTTOM / TIME_SIGNATURE_TOP)],
           [N("A2", 16), N("E3", 16), N("A3", 16), N("s", 16), N("s", 8)],
           [N("E2", 16), N("E3", 16), N("Ab3", 16), N("s", 16), N("s", 8)],
           [N("A2", 16), N("E3", 16), N("A3", 16), N("s", 16), N("s", 8)],
           [N("s", TIME_SIGNATURE_BOTTOM / TIME_SIGNATURE_TOP)],
           [N("A2", 16), N("E3", 16), N("A3", 16), N("s", 16), N("s", 8)],
           [N("E2", 16), N("E3", 16), N("Ab3", 16), N("s", 16), N("s", 8)],
           [N("A2", 16), N("E3", 16), N("A3", 16), N("s", 16)]]
# Bars during which the pedal is applied (keeps the notes playing)
PEDAL_BARS = [2, 3, 4, 6, 7, 8]

# Initialize minimum value variable
min_val = 0
# For both the hands
for i in range(2):
    # Get one bar at a time
    for ind, bar in enumerate(globals()["NOTES_{0}".format(i)]):
        # Get each note in that bar
        for note_obj in bar:
            # Set the hand value (useful for determining the channel to play on)
            note_obj.hand = i
            # Update minimum value
            if note_obj.value > min_val:
                min_val = note_obj.value
            # Update pedal variable for that note
            if ind in PEDAL_BARS:
                note_obj.pedal = True
# Calculate duration in milliseconds of the shortest note in the piece
DURATION = round(TIME_SIGNATURE_BOTTOM / min_val * BEAT_DURATION)

# For both of the hands
for i in range(2):
    # Reset the beat count for each hand
    beat = 0
    # Take each bar at a time
    for bar in globals()["NOTES_{0}".format(i)]:
        # Take each note
        for note_obj in bar:
            # Set the start time of that note as the current beat number
            note_obj.beat_num = beat
            # Add a beat
            beat += 1
            # If the value of the current note is not the minimum value, add beats according to note length
            if note_obj.value != min_val:
                for _ in range(round(min_val / note_obj.value - 1)):
                    beat += 1
            # Load the notes for the two hands
            if note_obj.key and note_obj.key != "s":
                if type(note_obj.key) != list:
                    globals()[note_obj.key] = pygame.mixer.Sound("data\\{0}.wav".format(note_obj.key))
                else:
                    for note in note_obj.key:
                        globals()[note.key] = pygame.mixer.Sound("data\\{0}.wav".format(note.key))


# Each drawn note has attributes (to keep track of fades and to see which note is currently playing, etc)
class Note:
    def __init__(self, key, key_type, initial_color, number):
        # Full key name (e.g.: "Ab5")
        self.key = key
        # Note name (e.g.: "Ab")
        self.key_type = key_type
        # Keep track of initial color in order to compare to current color
        self.initial_color = initial_color
        # Keep track of fade
        self.color = initial_color
        # Note number used for key spacing while drawing the key
        self.number = number

    def draw_note(self):
        # Initialize local variable
        fade1 = 0
        fade2 = 0
        # If the key is a natural key, not a sharp or a flat
        if len(self.key_type) == 1:
            # Fade to white
            fade1 = FADE
            # Create note rectangle
            rect = pygame.Rect(SPACING + (self.number - 1) * WIDTH, 3 * MON_H // 4, WIDTH, HEIGHT)
            # Draw note rectangle
            pygame.draw.rect(WIN, self.color, rect)
            # Draw black outline
            pygame.draw.rect(WIN, BLACK, rect, width=2)
        # If the key is a sharp or a flat
        else:
            # Fade to black
            fade2 = FADE
            # Create note rectangle
            rect = pygame.Rect(SPACING + int((self.number - 1) * WIDTH), 3 * MON_H // 4, 2 * WIDTH // 3, 2 * HEIGHT // 3)
            # Draw note rectangle
            pygame.draw.rect(WIN, self.color, rect)
        # Apply fade if necessary
        if self.color != self.initial_color:
            self.color = (self.color[0] + fade1, self.color[1] + fade1, self.color[2] - fade2)


# Create a list of all the 88 keys as note objects
NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NOTES = []
base_num = 0
for i, note in enumerate(NOTE_NAMES):
    # Set color and add 1 to key number if the note is a natural
    if len(note) == 1:
        base_num += 1
        color = WHITE
    else:
        color = BLACK
    # Get octave 0 for "A", "Ab" and "B" notes only (just like a real piano)
    if 9 <= i <= 11:
        # "A" is note number 1. When the for loop gets to "A", it will have passed 6 natural notes (including itself),
        # which will set base_num as 6. Idem for "B", which is number 2 and when it gets there, base_num will be 7.
        note_num = base_num - 5
        # Add two thirds to the note number for non-natural notes
        # (the starting x position of a flat or sharp note is two thirds into the previous note)
        if len(note) == 2:
            note_num += 2 / 3
        # Format the note name (e.g.: "Ab5")
        note_name = "{0}{1}".format(note, 0)
        # Create note object and append it to the global list
        NOTES.append(Note(note_name, note, color, note_num))
    # Get octaves 1 to 7
    for j in range(1, 8):
        if len(note) == 1:
            # Calculate the number based on octave and base number
            note_num = 2 + base_num + 7 * (j - 1)
        else:
            # Add two thirds to the number of the natural note that comes right before this one
            note_num = 2 + base_num + 7 * (j - 1) + 2 / 3
        # Format note name and append to list of note objects
        note_name = "{0}{1}".format(note, j)
        NOTES.append(Note(note_name, note, color, note_num))
    # Get octave 8 for "C" only
    if i == 0:
        # Format note name, set note number as 52 and append to list of note objects
        note_name = "{0}{1}".format(note, 8)
        NOTES.append(Note(note_name, note, color, 52))


# Top right X button to close program
def close_button(button_color):
    # Create rectangle
    close_rect = pygame.rect.Rect((MON_W - CLOSE[0], 0), (CLOSE[0], CLOSE[1]))
    # Draw rectangle based on color
    pygame.draw.rect(WIN, button_color, close_rect)
    # Draw white X
    pygame.draw.line(WIN, WHITE, (MON_W - 30, 10), (MON_W - 20, 20))
    pygame.draw.line(WIN, WHITE, (MON_W - 30, 20), (MON_W - 20, 10))


def main():
    # Keep track of time
    initial_time = pygame.time.get_ticks()
    # Keep track of frames per second
    clock = pygame.time.Clock()
    # Initialize local variables
    closed = False

    # Main loop
    run = True
    while run:
        # 60 frames per second
        clock.tick(60)
        # Cover the previous frame with black
        WIN.fill(BLACK)
        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Play the notes if it is time and update played notes list
        for n in range(2):
            for single_bar in globals()["NOTES_{0}".format(n)]:
                for note_object in single_bar:
                    note_object.play(initial_time)

        # Draw all white notes first (otherwise half of the black notes would be covered)
        for note_object in NOTES:
            if len(note_object.key_type) == 1:
                note_object.draw_note()
        # Draw all the black notes over the white notes
        for note_object in NOTES:
            if len(note_object.key_type) == 2:
                note_object.draw_note()

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                # If user presses escape
                if event.key == pygame.K_ESCAPE:
                    run = False
            elif event.type == pygame.MOUSEBUTTONUP:
                # If mouse is on close button
                if closed:
                    run = False

        # Change button color if mouse hovers over it
        if mouse_x >= MON_W - CLOSE[0] and mouse_y <= CLOSE[1]:
            close_button(RED)
            closed = True
        else:
            close_button(GRAY)
            closed = False

        # Update display
        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(error)
    pygame.quit()
