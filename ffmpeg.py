# TODO: audio extraction: 128kb settings audio pas pris en compte! -A 0 marche plus non plus
import os,sys,re,glob,subprocess
import getopt,traceback

class FFMpeg:

    __VERSION_NUMBER = "1.1"
    __MODULE_FILE = __file__
    __PROGRAM_NAME = os.path.basename(__MODULE_FILE)
    __PROGRAM_DIR = os.path.abspath(os.path.dirname(__MODULE_FILE))
    __AUDIO_CODEC_MP3 = "libmp3lame"
    __AUDIO_CODEC_AAC = "aac -strict -2"
    __POSSIBLE_VIDEO_TYPES = ["mp4","avi","mpg"]
    def __init__(self):
        self.__logfile = ""
        # init members with default values
        self.__input_file = []
        self.__output_dir = None
        self.__video_bitrate = 800
        self.__audio_bitrate = 192
        self.__deinterlace = False
        self.__two_pass = True
        self.__shutdown = False
        self.__audio_channel_reverse = False
        self.__renaming_pattern = None
        self.__force_aspect = None
        self.__batch_file = None
        self.__ipad = False
        self.__subtitle_file = None
        self.__audio_codec = self.__AUDIO_CODEC_MP3
        self.__video_type = "mp4"

    def init_from_sys_args(self,debug_mode = True):
        """ standalone mode """

        try:
            self.__do_init()
        except Exception:
            if debug_mode:
                # get full exception traceback
                traceback.print_exc()
            else:
                self.__message(str(sys.exc_info()[1]))

            sys.exit(1)

# uncomment if module mode is required
##    def init(self,my_arg_1):
##        """ module mode """
##        # set the object parameters using passed arguments
##        self.__output_file = my_arg_1
##        self.__doit()

    def __do_init(self):
        self.__opts = None
        self.__args = None
        #count_usage.count_usage(self.__PROGRAM_NAME,1)
        self.__parse_args()
        self.__doit()

    def __purge_log(self):
        if self.__logfile != "":
            try:
                os.remove(self.__logfile)
            except:
                pass

    def __message(self,msg):
        msg = self.__PROGRAM_NAME+(": %s" % msg)+os.linesep
        sys.stderr.write(msg)
        if self.__logfile != "":
            f = open(self.__logfile,"a")
            f.write(msg)
            f.close()

    def __error(self,msg):
        raise Exception("Error: "+msg)

    def __warn(self,msg):
        self.__message("Warning: "+msg)

    def __parse_args(self):
         # Command definition
         # Prepare short & long args from list to avoid duplicate info

        self.__opt_string = ""

        longopts_eq = ["version","help","input=","output-directory=","Video-bitrate=",
        "Audio-bitrate=","deinterlace","audio-channel-reverse",
        "1-pass","Force-aspect=","Rename-pattern=","Shutdown","Ipad","subtitle-file=","batch-file=","Type-video="]

        self.__shortopts = []
        self.__longopts = []
        sostr = ""

        for o in longopts_eq:
            i = o[0]

            has_args = o.endswith("=")

            if has_args:
                i += ":"
                o = o[:-1]

            sostr += i
            self.__opt_string += " -"+o[0]+"|--"+o
            if has_args:
                self.__opt_string +=" <>"


            self.__shortopts.append(i)
            self.__longopts.append(o)  # without "equal"

        self.__opts, self.__args = getopt.getopt(sys.argv[1:], sostr,longopts_eq)


        # Command options
        for option, value in self.__opts:
            oi = 0
            if option in ('-v','--'+self.__longopts[oi]):
                print(self.__PROGRAM_NAME + " v" + self.__VERSION_NUMBER)
                sys.exit(0)
            oi += 1
            if option in ('-h','--'+self.__longopts[oi]):
                self.__usage()
                sys.exit(0)
            oi += 1
            if option in ('-i','--'+self.__longopts[oi]):
                self.__input_file.extend(glob.glob(value))
            oi += 1
            if option in ('-o','--'+self.__longopts[oi]):
                self.__output_dir = value
            oi += 1
            if option in ('-V','--'+self.__longopts[oi]):
                self.__video_bitrate = int(value)
            oi += 1
            if option in ('-A','--'+self.__longopts[oi]):
                self.__audio_bitrate = int(value)
            oi += 1
            if option in ('-d','--'+self.__longopts[oi]):
                self.__deinterlace = True
            oi += 1
            if option in ('-a','--'+self.__longopts[oi]):
                self.__audio_channel_reverse = True
            oi += 1
            if option in ('-1','--'+self.__longopts[oi]):
                self.__two_pass = False
            oi += 1
            if option in ('-F','--'+self.__longopts[oi]):
                self.__force_aspect = value
            oi += 1
            if option in ('-R','--'+self.__longopts[oi]):
                self.__renaming_pattern = value
            oi += 1
            if option in ('-S','--'+self.__longopts[oi]):
                self.__shutdown = True
            oi += 1
            if option in ('-I','--'+self.__longopts[oi]):
                self.__ipad = True
            oi += 1
            if option in ('-s','--'+self.__longopts[oi]):
                self.__subtitle_file = value
            oi += 1
            if option in ('-b','--'+self.__longopts[oi]):
                self.__batch_file = value
            oi += 1
            if option in ('-T','--'+self.__longopts[oi]):
                self.__video_type = value

        if len(self.__input_file) == 0:
            self.__error("input file not set")


    def __usage(self):

        sys.stderr.write("Usage: "+self.__PROGRAM_NAME+self.__opt_string+"-- <ffmpeg args>"+os.linesep)


    @staticmethod
    def __setpriority(pid=None,priority=1):
        """ Set The Priority of a Windows Process.  Priority is a value between 0-5 where
            2 is normal priority.  Default sets the priority of the current
            python process but can take any valid process ID. """

        import win32api,win32process,win32con

        priorityclasses = [win32process.IDLE_PRIORITY_CLASS,
                           win32process.BELOW_NORMAL_PRIORITY_CLASS,
                           win32process.NORMAL_PRIORITY_CLASS,
                           win32process.ABOVE_NORMAL_PRIORITY_CLASS,
                           win32process.HIGH_PRIORITY_CLASS,
                           win32process.REALTIME_PRIORITY_CLASS]
        if pid == None:
            pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, priorityclasses[priority])

    def __title(self,m):
        os.system("title "+m)

    def __execute(self,cmd,output_file,ffmpeg_args=True):
        if ffmpeg_args:
            cmd += " "+" ".join(self.__args) # add args for ffmpeg
        cmd += ' "'+output_file+'"'
        self.__message("Running %s" % cmd)
        if self.__batch_file:
            rc = 0
            f = open(self.__batch_file,"a")
            f.write(cmd+"\n")
            f.close()
        else:
            p = subprocess.Popen(cmd,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            self.__setpriority(p.pid)  # below normal
            while True:
                o = p.stdout.readline()
                if len(o)==0 and p.poll() != None: break
                sys.stdout.write(o.decode())
                sys.stdout.flush()
            rc = p.wait()
        return rc

    def __get_indexes(self,input_file):
        av_re = re.compile(r"\s*Stream\s#\d+[\(\w\)]*:(\d+)[^\d].*(Audio|Video)")
        audio = []
        video = []
        cmd = 'ffmpeg.exe -i "'+input_file+'"'

        f = os.popen(cmd+" 2>&1")
        for l in f:
            g = av_re.match(l)
            if g!=None:
                t = g.group(2)
                if t == "Audio":
                    audio.append(int(g.group(1)))
                else:
                    video.append(int(g.group(1)))

        f.close()
        if self.__audio_channel_reverse:
            audio.reverse()
        return [audio,video]

    def __doit(self):
        if self.__video_type not in self.__POSSIBLE_VIDEO_TYPES:
            self.__error("Unsupported video type %s, use %s" % self.__video_type, ",".join(self.__POSSIBLE_VIDEO_TYPES))

        if self.__batch_file and os.path.exists(self.__batch_file):
            os.remove(self.__batch_file)

        if self.__output_dir != None and not os.path.isdir(self.__output_dir):
            self.__error("output directory %s does not exist" % self.__output_dir)

        if self.__ipad:
            self.__audio_codec = self.__AUDIO_CODEC_AAC
            # TODO: rescale for 640x480

        deinterlace_option = ""
        if self.__deinterlace:
            deinterlace_option = "-filter:v yadif "  # the best deinterlace filter around
        nb_threads = 2  # 0: infinite

# multipass encode
#ffmpeg -i video.avi -an -vcodec libx264 -vpre fast_firstpass -b 2000k -bt 2000k -vf "crop=1440:1080:240:0,scale=640:480" -pass 1 -threads 0 /dev/null
#ffmpeg -i video.avi -ab 320k -acodec libfaac -vcodec libx264 -vpre normal -b 2000k -bt 2000k -vf "crop=1440:1080:240:0,scale=640:480" -pass 2 -threads 0 video.mp4

# audio: bivx
#ffmpeg -y -i "VTS_01_1.VOB"  -map 0:12 -vn -c:a libmp3lame -b:a 192k "english.mp3"
#ffmpeg -y -i "VTS_01_1.VOB"  -map 0:13 -vn -c:a libmp3lame -b:a 192k "french.mp3"
#ffmpeg -y -i noaudio.mp4 -i french.mp3 -i english.mp3 -map 0:0 -map 1 -map 2 -codec copy Cars_2.mp4
#ffmpeg -y -i noaudio.mp4 -i Executive Decision (1996)_audio_1.mp3 -map 0:0 -map 1 -codec copy execd.mp4
#ffmpeg -i INPUT -map 0:1 -c:v libx264 -c:a copy OUTPUT
#ffmpeg -i "Rock n Rolla (2008).mkv"   -c:a copy -c:v copy  "Rock n Rolla (2008).mp4"
#ipad: ffmpeg -i "Camille Redouble (2012).mp4" -c:a aac -strict experimental  -c:v copy cr.mp4
#FFMPEG -i mytestmovie.mkv -vn -an -codec:s:0:10 srt sub.srt
#mkvextract.exe tracks "c:\My_MKV_Video_File.mkv" 3:My_MKV_Video_File.srt
#incrust subtitiles: ffmpeg -i video.avi -vf subtitles=subtitle.srt out.avi
#swap audio: ffmpeg -y -i "La chvre (1981).mp4"  -vcodec copy -map 0:0 -map 0:2  -map 0:1  -c:a:0  copy  -c:a:1  copy   "La chvreswp (1981).mp4"
        video_options = ""
        if self.__video_bitrate == 0:
            # audio extraction mode only
            video_options = " -vn "
            output_ext = ".mp3"
            self.__two_pass = False
        else:
            if self.__video_type == "mp4":
                video_options = ' -vcodec libx264 -pix_fmt yuv420p'
            elif self.__video_type == ".avi":
                video_options = ' -vcodec libxvid'
            else:
                pass
            video_options += ' -b:v '+str(self.__video_bitrate)+'k '

            output_ext = "."+self.__video_type

        # set codec to mp3lame to avoid trouble (libvo_aaenc does not work all the time)
        if self.__audio_bitrate == 0:
            audio_options = " -an "
        else:
        #ffmpeg -i input.mkv \
    #-map 0:0 -map 0:1 -map 0:1 -map 0:3 \
    #-c:v copy \
    #-c:a:0 libmp3lame -b:a:0 128k \
    #-c:a:1 libfaac -b:a:1 96k \
    #-c:s copy \
    #output.mkv
    #
    # -aspect:1 '16:9'
            audio_options = ""


        everything_ok = True

        if self.__renaming_pattern != None:
            ra = self.__renaming_pattern.split(":")
            if len(ra) != 2:
                self.__error("Renaming pattern must be search_for:replace_by: ex VTS_0:my_movie")
            search_for = ra[0]
            replace_by = ra[1]

        for input_file in self.__input_file:
            output_dir = self.__output_dir
            if output_dir == None:
                output_dir = os.path.dirname(input_file)

            input_file_noext = os.path.basename(input_file[0:input_file.rfind(".")])
            subtitles_options = ""
            subtitle_file = self.__subtitle_file
            if self.__ipad and subtitle_file == None:
                #try to find .srt file to hardcode it
                subtitle_file = input_file_noext+".srt"

            if subtitle_file != None and os.path.exists(subtitle_file):
                if self.__ipad:
                    self.__message("Ipad mode: automatically using %s srt file for %s" % (subtitle_file,input_file_noext))
                subtitles_options = ' -vf subtitles="%s" ' % subtitle_file

            if self.__renaming_pattern != None:
                input_file_noext = input_file_noext.replace(search_for,replace_by)
            [aindexes,vindexes] = self.__get_indexes(input_file)
            if len(aindexes)==0:
                self.__warn("No audio channels for file %s" % input_file)

            if self.__video_bitrate == 0:
                # no video: just extract audio
                audio_options = ' -vn -c:a %s -b:a %dk ' % (self.__audio_codec,self.__audio_bitrate)
                for audio_channel in aindexes:
                    output_file = os.path.join(output_dir,input_file_noext+"_audio_"+str(audio_channel)+output_ext)
                    if output_file==input_file:
                        self.__error("Input file is the same as output file")
                    cmd = 'ffmpeg.exe -y -i "'+input_file+('" -map 0:%d ' % audio_channel)+audio_options
                    rc = self.__execute(cmd,output_file)
            else:
                audio_options = "-map 0:%d" % vindexes[0]
                for audio_channel in aindexes:
                    # compose audio options with all streams
                    audio_options += ' -map 0:%d ' % (audio_channel)
                for audio_index,audio_channel in enumerate(aindexes):
                    # compose audio options with all streams
                    audio_options += ' -c:a:%d %s -b:a:%d %dk ' % (audio_index,self.__audio_codec,audio_index,self.__audio_bitrate)
                # encode video

                output_file = os.path.join(output_dir,input_file_noext+output_ext)
                if output_file==input_file:
                    self.__error("Input file is the same as output file")
                base_cmd = 'ffmpeg -y -i "'+input_file+'" '+deinterlace_option
                if self.__force_aspect != None:
                    base_cmd += " -aspect:%d '%s'" % (vindexes[0],self.__force_aspect)

                #audio_map_cmd = ""
                #for audio_channel in aindexes:
                #    audio_map_cmd += ' -map 0:%d ' % audio_channel

                if self.__two_pass:
                    temp_output = os.path.join(output_dir,"__temp__"+input_file_noext.replace(" ","_")+output_ext)
                    cmd = base_cmd + ' -an '+video_options+' -pass 1 -threads 2'+subtitles_options
                    self.__title("Encoding %s (pass 1)" % input_file_noext)
                    rc = self.__execute(cmd,temp_output)
                    if rc == 0:
                        self.__execute("cmd /c del",temp_output,ffmpeg_args=False)
                        cmd = base_cmd
                        cmd += video_options + audio_options+' -pass 2 -threads 2'
                        self.__title("Encoding %s (pass 2)" % input_file_noext)
                    else:
                        everything_ok = False
                else:
                    self.__title("Encoding %s (single pass)" % input_file_noext)
                    # single pass
                    cmd = base_cmd
                    cmd += video_options + audio_options

                cmd += subtitles_options

                rc = self.__execute(cmd,output_file)
                if rc != 0:
                    everything_ok = False
                if self.__two_pass:
                    self.__execute("cmd /c del","ffmpeg2pass*",ffmpeg_args=False)

        if self.__shutdown:
            if everything_ok:
                # all operations OK: shutdown computer if requested (and if enough rights)
                cmd = "shutdown /s /f /t"
                rc = self.__execute(cmd,"0",ffmpeg_args=False)
                if rc!=0:
                    self.__message("Shutdown failed")
            else:
                self.__message("Shutdown cancelled because there were some errors")

if __name__ == '__main__':
    """
        Description :
            Main application body
    """


    o = FFMpeg()
    o.init_from_sys_args(debug_mode = True)
    #o.init("output_file")
