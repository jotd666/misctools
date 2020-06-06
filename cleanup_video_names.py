import os,glob,sys,re

input_files = []
for exts in ["mp4","srt","avi","mkv"]:
    input_files.extend(glob.glob("*."+exts))

def repl_function(g):
    return g.group(1).replace("."," ")+" (%s)" % (g.group(2)+g.group(3)) + '.'+g.group(4)

if input_files == []:
    print("No matching videos in %s" % os.getcwd())
for video_in in input_files:
    # 19|20 avoids 1080 as a date!!!
    video_out = re.sub(r"(.*)\.(19|20)(\d\d)..*\.([^.][^.][^.])",repl_function,video_in)
    if video_out != video_in:
        print(video_in,"===>",video_out)
        os.rename(video_in,video_out)