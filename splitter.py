import os
import sys

def main():
    filename = "Anime.txt"
    
    if not os.path.exists(filename):
        print("file " + filename + " not found")
        sys.exit(1)

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    anime_lines = []
    for line in lines:
        stripped = line.strip()
        if "Manga" in stripped:
            break
        if not stripped:
            continue
        if stripped[0] == "[":
            continue
        if stripped[0] == "#":
            continue
        anime_lines.append(line)

    batch_size = 50
    for i in range(0, len(anime_lines), batch_size):
        chunk = anime_lines[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        output_name = "anime_batch_" + str(batch_num) + ".txt"
        
        with open(output_name, "w", encoding="utf-8") as out_f:
            out_f.writelines(chunk)
            
        print("generated " + output_name + " with " + str(len(chunk)) + " titles")

    print("\nall files split successfully")

if __name__ == "__main__":
    main()