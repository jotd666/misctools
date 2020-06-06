import os,sys
import getopt,traceback
import fnmatch
#import count_usage

import re


class Multiren:
    """ Tool: Multiren

 Usage: multiple rename of files/directories of the current directory
 according to a pattern."""

    __VERSION_NUMBER = "2.0"
    __MODULE_FILE = __file__
    __PROGRAM_NAME = os.path.basename(__MODULE_FILE)
    __PROGRAM_DIR = os.path.abspath(os.path.dirname(__MODULE_FILE))

    def __init__(self):
        self.__logfile = ""
        # init members with default values
        self.__list_to_replace = []
        self.__list_for_replacement = []
        self.__case_insensitive = False
        self.__regex = False
        self.__word_only = False
        self.__CCMODE=False
        self.__CCOPT=""
        self.__inside = False
        self.__no_checkout = True
        self.__file_types = []
        self.__directory = "."


    def __create_temp_directory():
        """
        defines self.__temp_directory
        """

        self.__temp_directory = os.path.join(os.getenv("TEMP"),self.__PROGRAM_NAME.replace(".py","")+("_%d" % os.getpid()))
        if not os.path.exists():
            os.mkdir(self.__temp_directory)

    def __delete_temp_directory():
        os.system("rmdir /Q /S "+self.__temp_directory)

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
            # log exception by e-mail

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

    def __doit(self):
        # create regex list

        self.__sub_list = []
        if len(self.__list_for_replacement) > 1:
            self.__error("You can specify only one pattern to change")

        if len(self.__list_for_replacement) != len(self.__list_to_replace):
            self.__error("search and replace lists do not have the same size")

        i = 0
        max = len(self.__list_for_replacement)
        while i < max:

            if self.__regex:
                pattern = self.__list_to_replace[i]
            else:
                pattern = re.escape(self.__list_to_replace[i])

            if self.__word_only:
                pattern = r"\b"+pattern+r"\b"

            if self.__case_insensitive:
                self.__search_re = re.compile(pattern,re.IGNORECASE)
            else:
                self.__search_re = re.compile(pattern)

            self.__sub_list.append([self.__search_re, self.__list_for_replacement[i]])
            i += 1

        for f in os.listdir(self.__directory):
            filepath = os.path.join(self.__directory,f)
            doit = len(self.__file_types)==0
            if not doit:
                for p in self.__file_types:
                    if fnmatch.fnmatch(f,p):
                        doit = True
                        break
            if doit:
                self.__process_file(filepath)


##    def __purge_log(self):
##        if self.__logfile != "":
##            try:
##                os.remove(self.__logfile)
##            except:
##                pass
##
##    def __message(self,msg):
##        msg = self.__PROGRAM_NAME+(": %s" % msg)+os.linesep
##        sys.stderr.write(msg)
##        if self.__logfile != "":
##            f = open(self.__logfile,"ab")
##            f.write(msg)
##            f.close()
##
##    def __error(self,msg):
##        raise Exception("Error: "+msg)
##
##    def __warn(self,msg):
##        self.__message("Warning: "+msg)

    def __parse_args(self):
         # Command definition
         # Prepare short & long args from list to avoid duplicate info

        self.__opt_string = ""

        longopts_eq = [
        ["version","shows version"],
        ["help","shows this help"],
        ["unreserved-fallback",""],
        ["message-log=",""],
        ["directory=","directories input"],
        ["1=","String/regex to replace"],
        ["2=","Replacement string"],
        ["extension-pattern=","Only files with this extension must be process ex: *.txt to modify only .txt files"],
        ["Case-insensitive","Ignore case"],
        ["word-only","Replace word only"],
        ["Regex","Enable regex mode"],
        ["inside","performs pattern replacement inside the renamed file too"],
        ]


        self.__shortopts = []
        self.__longopts = []
        self.__opthelp = ""
        longopts_eq2=[]

        sostr = ""

        for oc in longopts_eq:
            o = oc[0]
            i = o[0]
            longopts_eq2.append(o)

            has_args = o.endswith("=")

            if has_args:
                i += ":"
                o = o[:-1]

            sostr += i
            self.__opt_string += " -"+o[0]+"|--"+o
            if has_args:
                self.__opt_string +=" <>"

            oh = "-"+i[0]+" / --"+o+" : "+oc[1]+os.linesep
            self.__opthelp += oh
            self.__shortopts.append(i)
            self.__longopts.append(o)  # without "equal"

        self.__opts, self.__args = getopt.getopt(sys.argv[1:], sostr,longopts_eq2)


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
            if option in ('-u','--'+self.__longopts[oi]):
                self.__unreserved_fallback = True
            oi += 1
            if option in ('-m','--'+self.__longopts[oi]):
                self._log = value
            oi += 1
            if option in ('-d','--'+self.__longopts[oi]):
                self.__directory = value
            oi += 1
            if option in ('-1','--'+self.__longopts[oi]):
                self.__list_to_replace.append(value)
            oi += 1
            if option in ('-2','--'+self.__longopts[oi]):
                self.__list_for_replacement.append(value)
            oi += 1
            if option in ('-e','--'+self.__longopts[oi]):
                self.__file_types.append(value)
            oi += 1
            if option in ('-C','--'+self.__longopts[oi]):
                self.__case_insensitive = True
            oi += 1
            if option in ('-R','--'+self.__longopts[oi]):
                self.__regex = True
            oi += 1
            if option in ('-w','--'+self.__longopts[oi]):
                self.__word_only = True
            oi += 1
            if option in ('-i','--'+self.__longopts[oi]):
                self.__inside = True
            oi += 1


    def __usage(self):

        sys.stderr.write("Usage: "+self.__PROGRAM_NAME+self.__opt_string+os.linesep)
        sys.stderr.write(self.__opthelp)
        sys.stderr.write("-e and -i options can be specified multiple times"+os.linesep)


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


    def __process_file(self,filepath):
        """
        returns True if everything OK
        returns False if there was a clearcase error (not blocking, hence the lack of exception)
        """
        modified = False
        filename = os.path.basename(filepath)
        for si in self.__sub_list:
            lr = si[0].sub(si[1],filename)
            if filename != lr:
                modified = True
                new_path = os.path.join(os.path.dirname(filepath),lr)

        do_it = modified

        if modified:
            try:
                    os.rename(filepath,new_path)
            except Exception as e:
                do_it = False
                self.__warn(filepath+" -> "+new_path+": "+str(e))

            if do_it:
                msg = "Renamed file "+filename + " to "+lr+" in "+os.path.dirname(filepath)
                self.__message(msg)

            if do_it and self.__inside and os.path.isfile(new_path):
                # we are about to overwrite the file
                import multifr
                mfr = multifr.Multifr()

                mfr.init(filepath=new_path,search_for=self.__list_to_replace,replace_by=self.__list_for_replacement,
                checkout = not self.__no_checkout,case_insensitive=self.__case_insensitive,word_only=self.__word_only,regex=self.__regex)




if __name__ == '__main__':
    """
        Description :
            Main application body
    """


    o = Multiren()
    o.init_from_sys_args(debug_mode = True)
    #o.init("output_file")
