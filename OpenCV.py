import cv2
import numpy as np
import pygame
pygame.init()

# Modes either from webcam or from image (0: camera or 1: image)
MODE = 1
# Image file location
PATH = "images\\sheet.jpg"
# Image width to process (smaller makes processing easier)
IMAGE_WIDTH = 400
# Dimensions of the paper
PAPER_WIDTH = 8.5
PAPER_HEIGHT = 11
# Final viewing dimensions based on aspect ratio of original paper
VIEWING_WIDTH = 500
VIEWING_HEIGHT = round(PAPER_HEIGHT * VIEWING_WIDTH / PAPER_WIDTH)
# Webcam number (usually 0 unless you have more than one webcam connected)
WEBCAM_NUM = 0
# Initialize camera object
CAMERA = None


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


def rescale(points, width, height, viewing_width, viewing_height):
    # Shape the numpy array into something easier to work with
    points = points.reshape((4, 2))
    # Scale up each of the points to the image's original scale
    for point_num in range(4):
        points[point_num] = [round(points[point_num][0] * viewing_width / width), round(points[point_num][1] * viewing_height / height)]
    # Reshape the numpy array into a format that OpenCV can read
    points = points.reshape((4, 1, 2))
    # Function returns the scaled points
    return points


def get_sheet_corners(image, total_area):
    # Initialize empty numpy array and maximum area value
    sheet_corners = np.array([])
    max_area = 0
    final_contour = np.array([])
    # Get all the outline of the objects that OpenCV detects
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # For each contour
    for contour in contours:
        # Get the surface area
        area = cv2.contourArea(contour)
        # Check if surface area is big enough (this ignores all the tiny bits of corny shit that we don't need)
        if area > total_area // 8:
            # Get perimeter of the shape detected by OpenCV
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
    # Function returns warped image OpenCV object
    return processed


def main():
    # Get first frame from camera or image from file
    if MODE == 0:
        _, image = CAMERA.read()
    else:
        image = cv2.imread(PATH)
    # Get initial image dimensions
    initial_h, initial_w, _ = image.shape
    # Calculate width of contour line
    contour_thickness = initial_w // 100
    # Calculate the dimensions of the image to process while keeping the aspect ratio constant (smaller means less processing required)
    width = IMAGE_WIDTH
    height = round(initial_h * width / initial_w)
    # Check if the music sheet window is opened
    opened = False


    win = pygame.display.set_mode((1000, 1000))


    # Main loop
    running = True
    while running:
        # Get frame from camera or image from file
        if MODE == 0:
            _, image = CAMERA.read()

        # Resize the image to make processing it easier
        resized_image = cv2.resize(image, (width, height))

        # Preprocess the image (grayscale, blur and thresholding)
        processed_image = preprocess(resized_image)

        # Create a copy of the original image
        computer_image = image.copy()

        # Get the corners of the sheet (if it is detected)
        sheet_corners, final_contour = get_sheet_corners(processed_image, width * height)
        # If a big enough four-sided shape was detected
        if sheet_corners.size != 0:
            # Rescale the corners to fit with the initial high quality image
            rescale(sheet_corners, width, height, initial_w, initial_h)
            # Warp initial high quality image (not sized down) based on new rescaled corners
            warped_image = warp(image, sheet_corners, initial_w, initial_h)



            # Resize the warped image into the final dimensions (specified at the start)
            final_image = cv2.resize(warped_image, (VIEWING_WIDTH, VIEWING_HEIGHT))
            # Show the final processed image
            cv2.imshow("Music Sheet", final_image)
            opened = True



            # Resize contour from the small resized image scale to the initial scale
            # All the x values of each point in the contour (index 0)
            final_contour[:, :, 0] = final_contour[:, :, 0] * initial_w / width
            # All the y values of each point in the contour (index 1)
            final_contour[:, :, 1] = final_contour[:, :, 1] * initial_h / height
            # Draw the outline of the sheet on the computer image
            cv2.drawContours(computer_image, final_contour, -1, (255, 0, 0), contour_thickness)

        # Resize the computer image to the viewing width while keeping the aspect ratio of the image constant
        computer_image = cv2.resize(computer_image, (VIEWING_WIDTH, round(initial_h * VIEWING_WIDTH / initial_w)))
        # Show image
        cv2.imshow("Computer Vision", computer_image)

        # Check for 1 millisecond (to not slow the program down) if either the window is closed
        # or key 'q' is pressed or key "escape" is pressed
        key_pressed = cv2.waitKey(1)
        if cv2.getWindowProperty("Music Sheet", 0) and opened or cv2.getWindowProperty("Computer Vision", 0) \
                or key_pressed == ord('q') or key_pressed == 27:
            # Stop main loop
            running = False



        img_array = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        surf = pygame.surfarray.make_surface(img_array)
        surf = pygame.transform.rotate(surf, -90)
        surf = pygame.transform.flip(surf, True, False)
        surf = pygame.transform.smoothscale(surf, (VIEWING_WIDTH, VIEWING_HEIGHT))
        win.blit(surf, (0, 0))
        pygame.display.update()


if __name__ == "__main__":
    try:
        if MODE == 0:
            # Initialize video capture
            CAMERA = cv2.VideoCapture(WEBCAM_NUM)
            # Set camera brightness
            CAMERA.set(10, 150)

        main()

        # Close webcam
        if MODE == 0:
            CAMERA.release()
        # Close everything
        cv2.destroyAllWindows()

    except Exception as error:
        print(error)
