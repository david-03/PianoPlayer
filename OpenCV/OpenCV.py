# Create pop-up window
def select_mode():
    global PAPER_WIDTH, PAPER_HEIGHT
    root = tk.Tk()
    root.title("Select Mode")
    root.iconbitmap("data\\piano.ico")
    root.resizable(width=False, height=False)

    # Check if input is valid
    # "*" because the callback from line 62 generates a number of arguments
    # "_" because we don't use the arguments in the function
    def check_valid(*_):
        # Store user input in temporary string variable
        paper_width = width_entry.get()
        paper_height = height_entry.get()
        if len(paper_width) > 4:
            # Set tkinter variable width_value to the first two characters of user input only
            width_value.set(paper_width[:4])
        if len(paper_height) > 4:
            height_value.set(paper_height[:4])
        # Check if input is a valid number, change button state accordingly
        try:
            width = float(paper_width[:4])
            height = float(paper_height[:4])
            if file_button["state"] == "disabled" and width > 0 and height > 0 and 0.5 < width / height < 2:
                enable()
            elif file_button["state"] == "normal" and (width < 0 or height < 0 or width / height >= 2 or width / height <= 0.5):
                disable()
        except ValueError:
            disable()

    # Tkinter variable with starting value of 17 and linked to check_valid function
    width_value = tk.StringVar()
    width_value.set(PAPER_WIDTH)
    # Whenever width_value is changed, it calls the function check_valid
    width_value.trace('w', check_valid)

    # Same as width_value
    height_value = tk.StringVar()
    height_value.set(PAPER_HEIGHT)
    height_value.trace("w", check_valid)

    def disable():
        for button in [file_button, camera_button]:
            button["state"] = "disabled"
            button["bg"] = "#d3d3d3"
            button["cursor"] = "X_cursor"

    def enable():
        for button in [file_button, camera_button]:
            button["state"] = "normal"
            button["bg"] = HEX_LIGHT_BLUE
            button["cursor"] = "arrow"

    # Close everything
    def end():
        root.destroy()
        root.quit()

    # What to do when button is clicked
    def click_file():
        global MODE, PATH, PAPER_WIDTH, PAPER_HEIGHT
        # Shows an "Open" dialog box and returns the path to the selected file
        PATH = askopenfilename(filetypes=[("Images", ".jpeg .jpg .jfif, .jpx, .jp2 .png .tiff .tif")])
        if PATH:
            MODE = 2
            PAPER_WIDTH = float(width_entry.get()[:4])
            PAPER_HEIGHT = float(height_entry.get()[:4])
            end()

    def click_camera():
        global MODE
        MODE = 1
        end()

    # Create a main frame inside window (to change cursor)
    main_frame = tk.LabelFrame(root, bd=0)
    main_frame.grid(row=0, pady=10)
    # Empty frame to create spacing underneath
    empty_frame = tk.LabelFrame(root, bd=0)
    empty_frame.grid(row=1, pady=25)
    # Text inside frame
    text = tk.Label(main_frame, text="Analyze image from...", font="Verdana 20 bold")
    text.grid(row=0, pady=25)
    # Button
    file_button = tk.Button(main_frame, text="Existing File", font="Verdana 24", command=click_file, bd=5,
                            bg=HEX_LIGHT_BLUE)
    file_button.grid(row=1, padx=100, pady=10)
    # Button
    camera_button = tk.Button(main_frame, text="Camera", font="Verdana 24", command=click_camera, bd=5,
                              bg=HEX_LIGHT_BLUE)
    camera_button.grid(row=2, padx=100, pady=10)

    # Create frame inside mainframe
    frame = tk.LabelFrame(main_frame, bd=0)
    frame.grid(row=3, pady=25)
    # Text inside frame
    width_text = tk.Label(frame, text="Paper width: ", font="Verdana 20")
    width_text.grid(row=0, column=0, sticky="e")
    # Input box next to text
    width_entry = tk.Entry(frame, width=5, borderwidth=10, justify="center", font="Verdana 24 bold",
                           fg=HEX_BLUE, bg=HEX_LIGHT_BLUE, textvariable=width_value)
    width_entry.grid(row=0, column=1)
    # Text under previous
    height_text = tk.Label(frame, text="Paper height: ", font="Verdana 20")
    height_text.grid(row=1, column=0, sticky="e")
    # Input box under previous
    height_entry = tk.Entry(frame, width=5, borderwidth=10, justify="center", font="Verdana 24 bold",
                            fg=HEX_BLUE, bg=HEX_LIGHT_BLUE, textvariable=height_value)
    height_entry.grid(row=1, column=1)

    # Check if root window is closed
    root.protocol("WM_DELETE_WINDOW", end)
    # Tkinter loop to keep window open
    root.mainloop()


def preprocess(image):
    # Convert image to grayscale so it's easier process for the computer
    processed = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    for _ in range(2):
        # Blur the image so that only the most important details remain
        processed = cv2.GaussianBlur(processed, (9, 9), 5)
        # Use an adaptive threshold to separate the music sheet from the background
        processed = cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 101, 1)
    # Function returns the final processed image
    return processed


# Reorder points so that each corner is in the correct position
def reorder(points):
    # Shape the numpy array into something easier to work with
    points = points.reshape((4, 2))
    # Create empty numpy array
    reordered = np.zeros((4, 1, 2), np.int32)
    # Do the sum of each point in array of points (adds x pixel value of point to y value)
    points_sum = points.sum(1)
    # Do the difference of each point in array of points (adds x pixel value of point to y value)
    points_difference = np.diff(points, axis=1)
    # The minimum corresponds to the top left corner (e.g.: 0 + 0)
    reordered[0] = points[np.argmin(points_sum)]
    # The maximum corresponds to the bottom right corner (since pixel value increases the more you go right and down)
    reordered[3] = points[np.argmax(points_sum)]
    # The biggest absolute difference (y to x) occurs in the two other points
    # When you subtract the height to the width of the upper right corner, you get the lowest possible number out of the four corners
    reordered[1] = points[np.argmin(points_difference)]
    # Idem but for the lower left corner, you get the highest possible difference
    reordered[2] = points[np.argmax(points_difference)]
    # Function returns the reordered points (up to down, left to right corners)
    return reordered


def rescale(points, width, height, final_width, final_height):
    # Shape the numpy array into something easier to work with
    points = points.reshape((4, 2))
    # Scale up each of the points to the image's original scale
    for point_num in range(4):
        points[point_num] = [int(points[point_num][0]) * final_width // width, int(points[point_num][1]) * final_height // height]
    # Reshape the numpy array into a format that OpenCVfolder can read
    points = points.reshape((4, 1, 2))
    # Function returns the scaled points
    return points


def get_sheet_corners(image, total_area):
    # Initialize empty numpy array and maximum area value
    sheet_corners = np.array([])
    max_area = 0
    final_contour = np.array([])
    # Get all the outline of the objects that OpenCVfolder detects
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # For each contour
    for contour in contours:
        # Get the surface area
        area = cv2.contourArea(contour)
        # Check if surface area is big enough (this ignores all the tiny bits of corny shit that we don't need)
        if area > total_area // 8:
            # Get perimeter of the shape detected by OpenCVfolder
            perimeter = cv2.arcLength(contour, True)
            # Allow difference of 10% from predicted perimeter (perimeter of a perfect polygon
            # that closely matches the shape detected in the image)
            approximation = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            # Calculate the number of sides
            num_sides = len(approximation)
            # Only retain the biggest 4 sided shape
            if area > max_area and num_sides == 4:
                sheet_corners = approximation
                max_area = area
                final_contour = contour
    # Function returns either an empty array or the four corners of a quadrilateral polygon detected in the image
    return sheet_corners, final_contour


def warp(image, sheet_corners, width, height):
    # Get the correct order for all four corners
    sheet_corners = reorder(sheet_corners)
    # Convert all four numbers into numpy float format
    points1 = np.float32(sheet_corners)
    # Set the final position of each corner (the corners of the window)
    points2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    # Calculates by how much to warp each of the four sides
    matrix = cv2.getPerspectiveTransform(points1, points2)
    # Warp the image based on the perspective matrix
    processed = cv2.warpPerspective(image, matrix, (width, height))
    # Function returns warped image OpenCVfolder object
    return processed


def create_pygame_image(image, width, height, rotation=0):
    # Convert the colors to from BGR (OpenCVfolder format) to RGB (pygame format) and make the pygame image from the array
    pygame_image = pygame.surfarray.make_surface(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    # Rotate 90 degrees anticlockwise and flip the image on its x axis
    pygame_image = pygame.transform.flip(pygame.transform.rotate(pygame_image, 90 * (rotation % 4 - 1)), True, False)
    # Scale the image down with a little bit of anti-aliasing
    pygame_image = pygame.transform.smoothscale(pygame_image, (width, height))
    # Function returns pygame surface object
    return pygame_image


def display_text(window, font, text, color, width, height, height_ratio):
    # Render text and calculate position
    text_object = font.render(text, True, color)
    text_x = round(width + SPACING / 2 - text_object.get_width() / 2)
    text_y = round(height_ratio * height - text_object.get_height() / 2)
    window.blit(text_object, (text_x, text_y))
    return text_object, text_x, text_y


def main():
    # Get first frame from camera or image from file
    if MODE == 1:
        _, image = CAMERA.read()
    else:
        image = cv2.imread(r"{0}".format(PATH))

    # Get initial image dimensions
    initial_h, initial_w, _ = image.shape
    # Calculate the dimensions of the image to process while keeping the aspect ratio constant (smaller means less processing required)
    width = IMAGE_WIDTH
    height = round(initial_h * width / initial_w)
    # Calculate camera height based on camera aspect ratio
    CAMERA_HEIGHT = round(initial_h * CAMERA_WIDTH / initial_w)

    # Regulate max frames per second (actual FPS is probably way lower)
    clock = pygame.time.Clock()

    # Initialize local variables that keep track of the user's actions
    click = None
    hovering = False
    captured = False
    corner_changed = False
    image_created = False
    capturing = True
    analysing = False
    # Initialize other local variables
    warped_image = None
    final_image = None
    computer_pygame_image = None
    computer_image = np.zeros([1, 1, 3], dtype=np.uint32)
    sheet_corners = np.empty(0)
    corners_copy = np.empty(0)
    not_black = 0
    rotation = 0

    # Create pygame window
    window = pygame.display.set_mode((CAMERA_WIDTH + SPACING, CAMERA_HEIGHT))
    pygame.display.set_icon(pygame.image.load("data\\piano.png"))
    pygame.display.set_caption("Optical Music Recognition")

    # Main loop
    running = True
    while running:
        # Cover everything in gray and limit FPS to 60
        window.fill(GRAY)
        clock.tick(60)

        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # If the image has not been captured yet
        if capturing and not captured:
            # Get frame from camera
            if MODE == 1:
                _, image = CAMERA.read()

            # Resize the image to make processing it easier
            resized_image = cv2.resize(image, (width, height), cv2.INTER_AREA)

            # Check if it's just a black screen
            _, check_black = cv2.threshold(cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY), 50, 255, cv2.THRESH_BINARY)
            not_black = np.count_nonzero(check_black)
            # Create a copy of the original image
            computer_image = image.copy()
            # Analyze image only if it's not an entire black screen
            if not_black:
                # Preprocess the image (grayscale, blur and thresholding)
                processed_image = preprocess(resized_image)
                # Get the corners of the sheet (if it is detected)
                sheet_corners, final_contour = get_sheet_corners(processed_image, width * height)

                # Analyze image only once for a still image from a file
                if MODE == 2:
                    captured = True

                # If a big enough four-sided shape was detected
                if sheet_corners.size != 0 and final_contour.size != 0:
                    # Rescale the corners to fit with the camera display dimensions
                    rescale(sheet_corners, width, height, CAMERA_WIDTH, CAMERA_HEIGHT)
                    # Resize contour from the small resized image scale to the initial scale
                    # All the x values of each point in the contour (index 0)
                    final_contour[:, :, 0] = final_contour[:, :, 0] * initial_w / width
                    # All the y values of each point in the contour (index 1)
                    final_contour[:, :, 1] = final_contour[:, :, 1] * initial_h / height

                if final_contour.size != 0 and computer_image.size != 0 and len(sheet_corners) == 4:
                    # Draw the outline of the sheet on the computer image
                    cv2.drawContours(computer_image, final_contour, -1, BLUE_BGR, round(LINE_WIDTH * initial_w / CAMERA_WIDTH))

                # Create pygame image object from numpy array of computer image with contours drawn
                computer_pygame_image = create_pygame_image(computer_image, CAMERA_WIDTH, CAMERA_HEIGHT)
                image_created = True
                corners_copy = sheet_corners.copy()

        if not_black:
            if capturing:
                # Display pygame image
                window.blit(computer_pygame_image, (0, 0))

                # If the user moved the corners manually
                if captured and corner_changed:
                    # If a new pygame image object has not yet been created, create a new one from the original image (no contours)
                    if not image_created:
                        computer_pygame_image = create_pygame_image(image, CAMERA_WIDTH, CAMERA_HEIGHT)
                        image_created = True
                    pygame.draw.polygon(window, BLUE, corners_copy.reshape(4, 2), width=LINE_WIDTH)

                # If there are corners detected
                if corners_copy.size != 0:
                    for i in range(4):
                        # Take each corner individually
                        corner = corners_copy.reshape(4, 2)[i]
                        # Check if user is clicking on the corner, click number from 1 to 4, value of 0 means no click
                        if click == i + 1:
                            # Update the corner's position to match the user's mouse
                            if mouse_x <= CAMERA_WIDTH:
                                corners_copy.reshape(4, 2)[i][0] = mouse_x
                            corners_copy.reshape(4, 2)[i][1] = mouse_y
                        # Draw green circle where the corner is
                        pygame.draw.circle(window, GREEN, corner, LINE_WIDTH * 3)

            elif analysing:
                # Create warped image
                if not image_created:
                    if not rotation:
                        # Scale the corners from their previous position (camera scale) to their initial scale (full resolution)
                        rescale(corners_copy, CAMERA_WIDTH, CAMERA_HEIGHT, initial_w, initial_h)
                        # Warp initial high quality image (not sized down) based on new rescaled corners
                        warped_image = warp(image, corners_copy, initial_w, initial_h)
                    # Create pygame image based on viewing scale
                    final_image = create_pygame_image(warped_image, VIEWING_WIDTH, VIEWING_HEIGHT, rotation=rotation)
                    # Only create the image once
                    image_created = True
                    pygame.display.set_mode((VIEWING_WIDTH + SPACING, VIEWING_HEIGHT))
                    window.fill(GRAY)
                # Display image
                window.blit(final_image, (0, 0))

            if len(corners_copy) == 4:
                # If mouse is on the text, change the color
                if hovering:
                    color = GREEN
                else:
                    color = BLUE
                # Displayed text changes if user captured the image
                text = ''
                text_w = CAMERA_WIDTH
                text_h = CAMERA_HEIGHT
                if not captured:
                    text = "CAPTURE"
                elif captured:
                    if capturing:
                        text = "CROP"
                    else:
                        text = "ROTATE"
                        text_w = VIEWING_WIDTH
                        text_h = VIEWING_HEIGHT
                    if MODE == 1 or analysing:
                        # Render reset text
                        display_text(window, FONT_32, "Press  ' r '  to  reset", RED, text_w, text_h, 3 / 4)

                # Render option text
                text_object, text_x, text_y = display_text(window, FONT_64, text, color, text_w, text_h, 1 / 2)
                # Check if mouse is on the text
                if text_object.get_rect(topleft=(text_x, text_y)).collidepoint(mouse_x, mouse_y):
                    hovering = True
                else:
                    hovering = False
            else:
                # Render no image text
                display_text(window, FONT_64, "No Image Detected", RED, CAMERA_WIDTH, CAMERA_HEIGHT, 1 / 2)

        else:
            # Render no image text
            display_text(window, FONT_64, "No Image Detected", RED, CAMERA_WIDTH, CAMERA_HEIGHT, 1 / 2)
            # Draw black screen where camera screen should be
            black_screen = pygame.Rect((0, 0), (CAMERA_WIDTH, CAMERA_HEIGHT))
            pygame.draw.rect(window, BLACK, black_screen)

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not_black:
                # If there are corners and the user is not clicking on anything
                if capturing and corners_copy.size != 0 and not click and captured:
                    for i in range(4):
                        # Take each corner individually
                        corner = corners_copy.reshape(4, 2)[i]
                        radius = LINE_WIDTH * 3
                        # Get the bounding rectangle of each corner's green circle and check for collision with the mouse
                        square = pygame.rect.Rect((corner[0] - radius, corner[1] - radius), (2 * radius, 2 * radius))
                        if square.collidepoint(mouse_x, mouse_y):
                            # Register click as corner number (1 to 4, value of 0 means no click)
                            click = i + 1
                            # Tell next loop that a corner is being changed and tell it to create a new version of
                            # the pygame image object
                            corner_changed = True
                            image_created = False
                            # Skip the rest of the corners
                            break
            elif event.type == pygame.MOUSEBUTTONUP and not_black:
                # If user's mouse is on the text
                if hovering:
                    # Either capture the image or crop and warp it
                    if not captured:
                        captured = True
                    elif capturing:
                        # Go to next step (cropping and warping)
                        capturing = False
                        analysing = True
                        # Tell program to create a new image
                        image_created = False
                    else:
                        # Means that user clicked on rotate, tell program to create new image based on new rotation
                        image_created = False
                        rotation += 1
                # Otherwise, set click back to 0 (user is no longer clicking on anything)
                else:
                    click = 0
            elif event.type == pygame.KEYUP:
                # Escape or 'q' to quit
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r and not_black:
                    # Bring user back to viewing camera and capturing image
                    if captured and capturing and MODE == 1:
                        captured = False
                        # Reset corners
                        corner_changed = False
                        corners_copy = sheet_corners.copy()
                    # Bring user back to cropping step
                    elif analysing:
                        analysing = False
                        capturing = True
                        # Reset corners
                        corner_changed = False
                        corners_copy = sheet_corners.copy()
                        # Draw image that has all the contours drawn
                        computer_pygame_image = create_pygame_image(computer_image, CAMERA_WIDTH, CAMERA_HEIGHT)
                        # Reset display dimensions to fit with camera dimensions
                        pygame.display.set_mode((CAMERA_WIDTH + SPACING, CAMERA_HEIGHT))
                        # Reset number of rotations
                        rotation = 0

        # Update display
        pygame.display.flip()


if __name__ == "__main__":
    import cv2
    import numpy as np
    import pygame
    import tkinter as tk
    from tkinter.filedialog import askopenfilename

    # Initialize global variables
    # # # # # # #
    # # # # # # # # # # # # # # # # # # # # #
    # Modes either from webcam or from image (0:None, 1:camera, 2:image)
    MODE = 0
    # Image file location
    PATH = ""
    # Dimensions of the paper
    PAPER_WIDTH = 8.5
    PAPER_HEIGHT = 11
    # Final viewing dimensions based on aspect ratio of original paper
    VIEWING_WIDTH = 700
    # Camera viewing dimensions
    CAMERA_WIDTH = 600
    # Outline width
    LINE_WIDTH = CAMERA_WIDTH // 120
    # Webcam number (usually 0 unless you have more than one webcam connected)
    WEBCAM_NUM = 0
    # # # # # # # # # # # # # # # # # # # # #
    # # # # # # #

    # Set camera resolution to a very high number so that it automatically picks the next highest available
    RESOLUTION = (2000, 2000)
    # Width of image to process (original image downscaled) (smaller makes processing easier)
    IMAGE_WIDTH = 400
    # Initialize camera object
    CAMERA = None

    # Initialize pygame
    pygame.init()

    SPACING = 500
    BLACK = (0, 0, 0)
    GRAY = (75, 75, 75)
    RED = BLUE_BGR = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    HEX_BLUE = "#0000ff"
    HEX_LIGHT_BLUE = "#bff0ff"

    FONT_32 = pygame.font.Font("data\\agency-fb.ttf", 32)
    FONT_64 = pygame.font.Font("data\\agency-fb.ttf", 64)

    try:
        # Tkinter window to select some of the variables (mode and paper dimensions)
        select_mode()
        # Check if user actually selected anything
        if MODE == 1 or (MODE == 2 and PATH):
            # Final viewing dimensions based on aspect ratio of original paper
            VIEWING_HEIGHT = round(PAPER_HEIGHT * VIEWING_WIDTH / PAPER_WIDTH)
            if MODE == 1:
                # Initialize video capture
                CAMERA = cv2.VideoCapture(WEBCAM_NUM)
                # Set camera brightness and camera resolution
                CAMERA.set(10, 150)
                CAMERA.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
                CAMERA.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])

            main()

            # Close webcam
            if MODE == 1:
                CAMERA.release()

        pygame.quit()

    except Exception as error:
        print(error)
