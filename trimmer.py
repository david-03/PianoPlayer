from scipy.io import wavfile

THRESHOLD = 500
keys = ["A", "B", "C", "D", "E", "F", "G", "Ab", "Bb", "Cb", "Db", "Eb", "Fb", "Gb"]
total_trimmed = 0


def trim_note(key_name):
    start_crop = 0
    end_crop = 0
    fs, data = wavfile.read('wav\\Piano.ff.{0}.wav'.format(key_name))
    for ind, line in enumerate(data):
        if abs(line[0]) >= THRESHOLD or abs(line[1]) >= THRESHOLD:
            start_crop = ind
            break
    length = len(data) - 1
    for i in range(length):
        ind = length - i
        if abs(data[ind][0]) >= THRESHOLD or abs(data[ind][1]) >= THRESHOLD:
            end_crop = ind
            break
    wavfile.write("data\\{0}.wav".format(key_name), fs, data[start_crop:end_crop])


def main():
    global total_trimmed
    for key in keys:
        for num in range(0, 9):
            note_name = "{0}{1}".format(key, num)
            try:
                trim_note(note_name)
                print("Trimmed: " + note_name)
                total_trimmed += 1
            except WindowsError:
                print("Note not found: " + note_name)


if __name__ == "__main__":
    try:
        main()
        print("Total number of notes trimmed: " + str(total_trimmed))
    except Exception as error:
        print(error)
