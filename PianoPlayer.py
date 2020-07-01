import pygame

# Initialize pygame
pygame.init()

# Tempo in beats per minute
TEMPO = 120
# Notes to play in first two channels (index 0 and 1), corresponds to right hand
NOTES_0 = ["E5", "Eb5",
           "E5", "Eb5", "E5", "B4", "D5", "C5",
           "A4", 0, 0, "C4", "E4", "A4",
           "B4", 0, 0, "E4", "Ab4", "B4",
           "C5", 0, 0, "E4", "E5", "Eb5",
           "E5", "Eb5", "E5", "B4", "D5", "C5",
           "A4", 0, 0, "C4", "E4", "A4",
           "B4", 0, 0, "E4", "C5", "B4",
           "A4", 0, 0, 0, 0, 0]
# Notes to play in channels 3 and 4 (index 2 and 3), corresponds to left hand
NOTES_1 = [0, 0,
           0, 0, 0, 0, 0, 0,
           "A2", "E3", "A3", 0, 0, 0,
           "E2", "E3", "Ab3", 0, 0, 0,
           "A2", "E3", "A3", 0, 0, 0,
           0, 0, 0, 0, 0, 0,
           "A2", "E3", "A3", 0, 0, 0,
           "E2", "E3", "Ab3", 0, 0, 0,
           "A2", "E3", "A3", 0, 0, 0]
# Calculate duration of each note in milliseconds (to change later because right now all the notes are of equal length)
DURATION = round(0.5 * 60 / TEMPO * 1000)
# Load the notes for the two hands
for i in range(2):
    for note in globals()["NOTES_{0}".format(i)]:
        if note:
            globals()[note] = pygame.mixer.Sound("data\\{0}.wav".format(note))

# Create 8 pygame sound channels (you can only play one sound at a time in a channel)
for i in range(8):
    globals()["channel_{0}".format(i)] = pygame.mixer.Channel(i)

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
DARK_BLUE = (0, 0, 200)

# Other global variables
CLOSE = (50, 30)
SPACING = 20
WIDTH = (MON_W - 2 * SPACING) // 52
HEIGHT = MON_H // 4 - SPACING
FADE = 5
DELAY = 1000


# Each note has attributes (to keep track of fades and to see which note is currently playing, etc)
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


def play_notes(start_time, played_notes, notes_list_num):
    # Get current ticks
    current_time = pygame.time.get_ticks()
    # Play the notes for the current hand (e.g.: notes_list_num = 0 corresponds to NOTES_0 - right hand)
    for ind, key_sound in enumerate(globals()["NOTES_{0}".format(notes_list_num)]):
        # If the key to play is not 0 (None) and the time is right and the note has not already been played
        if key_sound and current_time - start_time >= ind * DURATION + DELAY and ind not in played_notes:
            # Check which note object corresponds to the note being played
            for note_object in NOTES:
                # If the key is exactly the same (e.g.: "Ab5" = "Ab5")
                if key_sound == note_object.key:
                    # Set the color to start the fade
                    if len(note_object.key_type) == 1:
                        note_object.color = LIGHT_BLUE
                    else:
                        note_object.color = DARK_BLUE
                    # Stop the for loop
                    break
            # Calculate which channel to play the note in (each channel is responsible for half the notes)
            channel_num = globals()["channel_{0}".format((ind % 2) + 2 * notes_list_num)]
            # Stop any sound playing on this channel
            channel_num.stop()
            # Play the current note
            channel_num.play(globals()[key_sound])
            print("Playing note: " + key_sound)
            # Append the note to a list so that the program doesn't play it again
            played_notes.append(ind)
    # Update the played notes list
    return played_notes


def main():
    # Keep track of time
    initial_time = pygame.time.get_ticks()
    # Keep track of frames per second
    clock = pygame.time.Clock()
    # Initialize local variables
    closed = False
    played_0 = []
    played_1 = []

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
        played_0 = play_notes(initial_time, played_0, 0)
        played_1 = play_notes(initial_time, played_1, 1)

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
