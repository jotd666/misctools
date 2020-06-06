import os,sys,re,glob
import getopt,traceback

# TODO: EIle => Elle, aIlez => allez, coloneI => colonel

# space 1999: srt_fix.py -i "Space 1999 - 1x01 - Breakaway.DVDRip.en.srt" -o .. -r 23.95/25.0 -s 8

class SrtFix:
    replace_html_re = re.compile("(&#\d+;)")
    detach_upper = re.compile("([a-z])([A-Z][a-z])")
    detach_you = re.compile("([a-z])(you)")
    attach_ly = re.compile(r"\s+(l+[ye])\b")
    ALL = re.compile(r"\bAII\b")
    replace_wrong_Is = re.compile("([a-z]+)(I+)([a-z]*)")
    replace_l_alone = re.compile(r"\bl\b")
    replace_quote_II = re.compile(r"'II\b")
    replace_II_alone = re.compile(r"\bII\b")
    replace_II_vowel = re.compile(r"([AEOU])II")
    replace_ll_alone = re.compile(r"\bll\b")
    replace_stray_italics = re.compile(r"</?i>(\s*[a-z0-9']\s*)</?i>")

    wrong_i_followers = ['a','e','i','o','u','y',u'\xe0',u'\xe2',u'\xe9',u'\xea',u'\xfb']  # questionable a: Ian

    __VERSION_NUMBER = "1.2"
    __MODULE_FILE = sys.modules[__name__].__file__
    __PROGRAM_NAME = os.path.basename(__MODULE_FILE)
    __PROGRAM_DIR = os.path.abspath(os.path.dirname(__MODULE_FILE))
    __SIMPLE_TIME = r"(\d\d?):(\d\d?):(\d\d?),(\d\d\d)"
    __SIMPLE_TIME_RE = re.compile(__SIMPLE_TIME)
    __TIME_RE = re.compile(__SIMPLE_TIME+" --> "+__SIMPLE_TIME)
    __ACCENT_STR = """&#224;&agrave
&#225;&aacute
&#226;&acirc
&#227;&atilde
&#228;&auml
&#229;&aring
&#230;&aelig
&#231;&ccedil
&#232;&egrave
&#233;&eacute
&#234;&ecirc
&#235;&euml
&#236;&igrave
&#239;&iring
&#237;&iacute
&#238;&icirc
&#239;&iuml
&#240;&eth
&#241;&ntilde
&#242;&ograve
&#243;&oacute
&#244;&ocirc
&#245;&otilde
&#246;&ouml
&#247;&divide
&#248;&oslash
&#249;&ugrave
&#250;&uacute
&#251;&ucirc
&#252;&uuml
&#253;&yacute
&#254;&thorn
&#255;&yum"""
    accent_repl = []
    z = __ACCENT_STR.replace("\r","").split("\n")
    for l in z:
        accent_repl.append(l.split(";"))

    class Time:
        def __init__(self,groups=[0,0,0,0]):
            self.time = int(groups[0])*3600 + int(groups[1])*60 + int(groups[2]) + float(groups[3])/1000.0
        def __str__(self):
            itime = int(self.time)
            rval = "%02d:%02d:%02d,%03d" % (itime // 3600,(itime // 60) % 60,
            itime % 60, int(1000 * (self.time - itime)))
            return rval
        def __cmp__(self,other):
            return self.time - other.time

    class TimeRange:
        def __init__(self):
            self.start = SrtFix.Time()
            self.end = SrtFix.Time()
        def __str__(self):
            return str(self.start)+" --> "+str(self.end)
        def add(self,t):
            self.start.time += t
            self.end.time += t
        def mul(self,t):
            self.start.time *= t
            self.end.time *= t

    def __init__(self):
        self.__logfile = ""
        # init members with default values
        self.__input_file = []
        self.__output_dir = ""
        self.__ratio = 1
        self.__shift = 0
        self.__start_reference = None
        self.__end_reference = None
        self.__time_to_start_fix = None
        self.__fix_spelling = False
        self.__french = False

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
            f = open(self.__logfile,"ab")
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

        longopts_eq = ["version","help","input=","output=","fix-spelling","French","shift=","ratio=","Start-reference=","End-reference=","Time-to-start-fix="]

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
            if option in ('-f','--'+self.__longopts[oi]):
                self.__fix_spelling = True
            oi += 1
            if option in ('-F','--'+self.__longopts[oi]):
                self.__french = True
            oi += 1
            if option in ('-s','--'+self.__longopts[oi]):
                self.__shift = eval(value.replace(",","."))  # so 26,456-34,123 works (copy from srt)
            oi += 1
            if option in ('-r','--'+self.__longopts[oi]):
                self.__ratio = eval(value)
            oi += 1
            if option in ('-S','--'+self.__longopts[oi]):
                self.__start_reference = value
            oi += 1
            if option in ('-E','--'+self.__longopts[oi]):
                self.__end_reference = value
            oi += 1
            if option in ('-T','--'+self.__longopts[oi]):
                self.__time_to_start_fix = value

        if len(self.__input_file) == 0:
            self.__error("input file not set")
        if self.__output_dir == "":
            self.__error("output dir not set")

    def __usage(self):

        sys.stderr.write("Usage: "+self.__PROGRAM_NAME+self.__opt_string+os.linesep)

    @staticmethod
    def __replacer(s):
        rval = int(s.group(1)[2:-1])
        if rval == 339:
            return "oe"
        else:
            return chr(rval)
    @staticmethod
    def __fix_i(s):
        rval = s.group(1)+s.group(2).replace("I","l")+s.group(3)
        return rval

    @staticmethod
    def fix_spelling(l,french):
        for r in SrtFix.accent_repl:
            l = l.replace(r[1],r[0])

        l = re.sub(SrtFix.replace_stray_italics,r"\1",l)

        if french:
            l = re.sub(SrtFix.replace_II_alone,"Il",l)  # french
            l = re.sub(SrtFix.replace_ll_alone,"Il",l)  # french
        else:
            l = re.sub(SrtFix.replace_quote_II,"'ll",l) # 'll instead of 'II
            l = re.sub(SrtFix.replace_l_alone,"I",l)  # "l" instead of "I"
        if l.upper() != l:
            l = re.sub(SrtFix.replace_html_re,SrtFix.__replacer,l)
            l = re.sub(SrtFix.replace_wrong_Is,SrtFix.__fix_i,l)
            if french:
                l = re.sub(SrtFix.replace_II_alone,"Il",l)  # french
                l = re.sub(SrtFix.replace_II_vowel,r"\1ll",l)  # french
                l = re.sub(SrtFix.replace_ll_alone,"Il",l)  # french
                l = l.replace("I'","l'")
            l = re.sub(r"([A-Z])I([a-z])",r"\1l\2",l)  # AIter => Alters
            while True:
                l2 = re.sub(r"(\d)\s(\d)",r"\1\2",l)  # fix spaces between digits
                fixed = l2 == l
                l = l2
                if fixed:
                    break

            l = l.replace("''",'"')
            l = l.replace(". . .",'...')
            l = re.sub(r"L([bcdfgjklmnpqrstvwxz])",r"I\1",l)  # Lvan => Ivan
            l = re.sub(r"\bl([bcdfgjkmnpqrstvwxz])",r"I\1",l)  # lt => It, exception for "ll"
            l = re.sub(SrtFix.detach_upper,r"\1 \2",l)  # theJedi => the Jedi
            # Ia => La, and so on
            for c in SrtFix.wrong_i_followers:
                pos = -1
                while True:
                    res=-1
                    for i in range(pos+1,len(l)):
                        if i>0 and ord(l[i])==ord(c) and ord(l[i-1])==ord('I'):
                            res=i
                            l = l[:res-1]+'l'+l[res:]
                            break
                    pos=res
                    if pos == -1:
                        break
            if not french:
                l = re.sub(SrtFix.detach_you,r"\1 \2",l)  # aboutyou => about you
                l = re.sub(SrtFix.attach_ly,r"\1",l) # absolute ly => absolutely
                l = re.sub(SrtFix.ALL,"All",l)
            # eL => el
##            for c in SrtFix.wrong_i_followers:
##                pos = -1
##                while True:
##                    res=-1
##                    for i in xrange(pos,len(l)-1):
##                        if ord(l[i+1])==ord(c) and ord(l[i])==ord('I'):
##                            res=i
##                            l = l[:res-1]+'l'+l[res:]
##                            break
##                    pos=res
##                    if pos == -1:
##                        break
        return l

    def __process_file(self,input_file,output_file):
        fr = open(input_file,"r")
        frbuf = fr.read().split("\n")
        fr.close()
        ol=[]
        bom = False
        # detect wierd encoding
        if frbuf[0].startswith("\xef\xbb\xbf\x31"):
            bom = True
            self.__message("%s: found BOM header, removing it" % input_file)
            frbuf = frbuf[1:]

        if self.__start_reference != None:
            first_subtitle = None

            # first pass: get start & ends subtitles
            for l in frbuf:
                m = self.__TIME_RE.match(l)
                if m != None:
                    # start a new subtitle
                    s = self.Time(m.groups())
                    if first_subtitle == None:
                        first_subtitle = s.time
                    else:
                        last_subtitle = s.time
            # compute ratio & shift
            # first_subtitle * ratio + shift = start_reference
            # last_subtitle * ratio + shift = end_reference
            self.__ratio = (self.__end_reference - self.__start_reference) / (last_subtitle - first_subtitle)
            # shift = start_reference - first_subtitle * ratio
            self.__shift = self.__start_reference - first_subtitle * self.__ratio

        self.__message("File %s: Fix text: %s, French: %s, shift: %f, ratio: %f" % (input_file,str(self.__fix_spelling),str(self.__french),self.__shift,self.__ratio))

        tr = self.TimeRange()
        # second pass: adjust
        for l in frbuf:
            if bom:
                # replace c3 code by code+0x40 (unicode => ANSI)
                l2 = ""
                fixn=False
                for c in l:
                    if ord(c)==0xc3:
                        fixn=True
                    else:
                        if fixn:
                            l2 += chr(ord(c)+0x40)
                            fixn=False
                        else:
                            l2 += c
                l = l2
                # replace ce code by code-0x50 (unicode => ANSI)
                l2 = ""
                fixn=False
                for c in l:
                    if ord(c)==0xce:
                        fixn=True
                    else:
                        if fixn:
                            l2 += chr(ord(c)-0x50)
                            fixn=False
                        else:
                            l2 += c
                l = l2

            m = self.__TIME_RE.match(l)
            if m != None:
                g = m.groups()
                tr = self.TimeRange()
                tr.start = self.Time(g)
                tr.end = self.Time(g[4:])

            if self.__time_to_start_fix < tr.start.time:
                if self.__fix_spelling:
                    l = self.fix_spelling(l,self.__french)

                if m != None:
                    if self.__shift != 0 or self.__ratio != 1:
                        tr.mul(self.__ratio)
                        tr.add(self.__shift)
                    l = str(tr)
            ol.append(l)

        fw = open(output_file,"w")
        for l in ol:
            fw.write(l+"\n")
        fw.close()

    def __doit(self):
        # main processing here
        if self.__start_reference != None:
            # parse
            sg = self.__SIMPLE_TIME_RE.match(self.__start_reference)
            if sg == None:
                self.__error("Wrong syntax for start reference (hh:mm:ss,ccc)")
            if self.__end_reference == None:
                self.__error("start reference specified but no end reference specified")
            eg = self.__SIMPLE_TIME_RE.match(self.__end_reference)
            if eg == None:
                self.__error("Wrong syntax for end reference (hh:mm:ss,ccc)")
            self.__start_reference = self.Time(sg.groups()).time
            self.__end_reference = self.Time(eg.groups()).time

        if self.__time_to_start_fix == None:
            self.__time_to_start_fix = 0
        else:
            sg = self.__SIMPLE_TIME_RE.match(self.__time_to_start_fix)
            if sg == None:
                self.__error("Wrong syntax for time-to-start-fix (hh:mm:ss,ccc)")
            self.__time_to_start_fix = self.Time(sg.groups()).time

        for input_file in self.__input_file:
            output_file = os.path.join(self.__output_dir,os.path.basename(input_file))
            self.__process_file(input_file,output_file)

if __name__ == '__main__':
    """
        Description :
            Main application body
    """


    o = SrtFix()
    o.init_from_sys_args(debug_mode = True)
    #o.init("output_file")
