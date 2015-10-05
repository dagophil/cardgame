import os


def main():
    # Clubs, Spades, Hearts, Diamonds
    colors = {"pik": "S",
              "herz": "H",
              "karo": "D",
              "kreuz": "C"}
    numbers = {"2": "2",
               "3": "3",
               "4": "4",
               "5": "5",
               "6": "6",
               "7": "7",
               "8": "8",
               "9": "9",
               "10": "T",
               "bube": "J",
               "dame": "Q",
               "koenig": "K",
               "ass": "A"}

    folder = "resources/card_deck/"
    for filename in os.listdir(folder):
        fullname = os.path.join(folder, filename)
        if not os.path.isfile(fullname):
            continue
        if "_" not in filename:
            continue
        else:
            col, r = filename.split("_")
            num, ext = r.split(".")
            new_filename = colors[col] + numbers[num] + "." + ext
            new_fullname = os.path.join(folder, new_filename)
            os.rename(fullname, new_fullname)
            print "renamed", fullname, "=>", new_fullname


if __name__ == "__main__":
    main()
