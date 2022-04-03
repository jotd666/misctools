
import os,sys
import getopt,traceback
import re,glob
#import count_usage

import python_lacks
import file_walker


clearcase_available = False
try:
    import clearcase
    clearcase_available = True
except:
    pass


class Multifr(file_walker.FileWalker):
    __VERSION_NUMBER = "1.5"
    __MODULE_FILE = __file__
    __PROGRAM_NAME = os.path.basename(__MODULE_FILE)
    __PROGRAM_DIR = os.path.abspath(os.path.dirname(__MODULE_FILE))

    def __init__(self):
        file_walker.FileWalker.__init__(self)
        self.program_name = self.__PROGRAM_NAME
        self.program_dir = self.__PROGRAM_DIR
        self.__logfile = ""
        # init members with default values
        self.__checkout = False
        self.__preview = False
        self.__list_to_replace = []
        self.__list_for_replacement = []
        self.__case_insensitive = False
        self.__regex = False
        self.__word_only = False

    def __create_temp_directory():
        """
        defines self.__temp_directory
        """

        self.__temp_directory = os.path.join(os.getenv("TEMP"),self.__PROGRAM_NAME.replace(".py","")+("_%d" % os.getpid()))
        python_lacks.create_directory(self.__temp_directory)

    def __delete_temp_directory():
        python_lacks.rmtree(self.__temp_directory)

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
    def init(self,filepath,search_for,replace_by,checkout=False,
    case_insensitive=False,word_only=False,regex=False):
        """ module mode """
        # set the object parameters using passed arguments
        self.__checkout = checkout
        if isinstance(search_for,list):
            self.__list_to_replace = search_for
        else:
            self.__list_to_replace = [search_for]

        if isinstance(replace_by,list):
            self.__list_for_replacement = replace_by
        else:
            self.__list_for_replacement = [replace_by]

        self.__case_insensitive = case_insensitive
        self.__regex = regex
        self.__word_only = word_only
        self._file_list.append(filepath)
        self._doit()

    def __do_init(self):
        self.__opts = None
        self.__args = None
        #count_usage.count_usage(self.__PROGRAM_NAME,1)
        self.__parse_args()
        self._doit()


    def __parse_args(self):
         # Command definition
         # Prepare short & long args from list to avoid duplicate info

        self.__opt_string = ""

        longopts_eq = [["version","shows version"],["help","shows this help"],
        ["preview","shows what is going to be modified, but changes nothing"]]
        if clearcase_available:
            longopts_eq += [["checkout","tries to checkout file if read-only"]]

        longopts_eq += [["message-log=",""],
        ["directory=","directories input"],
        ["list-of-files=","filelist (1 file per line)"],
        ["file=","file/file pattern (ex: *.txt)"],
        ["include-dir-pattern=","ex: if set to 'code', only considers files with "+os.sep+"code"+os.sep+" in path"],
        ["exclude-dir-pattern=","ex: if set to 'code', avoid files with "+os.sep+"code"+os.sep+" in path"],
        ["1=","String/regex to replace"],
        ["2=","Replacement string"],
        ["Filter-pattern=","pattern of files to process (default \"*\")"],
        ["Case-insensitive","Ignore case"],
        ["word-only","Replace word only"],
        ["Regex","Enable regex mode"],
        ]

        self.__shortopts = []
        self.__longopts = []
        self.__opthelp = ""
        longopts_eq2=[]

        sostr = ""

        for oc in longopts_eq:
            o = oc[0]
            i = o[0]
            longopts_eq2.append('--'+o)

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
            if option in ('-v',self.__longopts[oi]):
                print(self.__PROGRAM_NAME + " v" + self.__VERSION_NUMBER)
                sys.exit(0)
            oi += 1
            if option in ('-h',self.__longopts[oi]):
                self.__usage()
                sys.exit(0)
            oi += 1
            if option in ('-p',self.__longopts[oi]):
                self.__preview = True
            if clearcase_available:
                oi += 1
                if option in ('-c',self.__longopts[oi]):
                    self.__checkout = True
            oi += 1
            if option in ('-m','--'+self.__longopts[oi]):
                self._log = value
            oi += 1
            if option in ('-d',self.__longopts[oi]):
                self._directory_list.append(value)
            oi += 1
            if option in ('-l',self.__longopts[oi]):
                self._filelist_list.append(value)
            oi += 1
            if option in ('-f',self.__longopts[oi]):
                self._file_list.extend(glob.glob(value))
            oi += 1
            if option in ('-i',self.__longopts[oi]):
                self._include_dir_pattern.append(value.lower())
            oi += 1
            if option in ('-e',self.__longopts[oi]):
                self._exclude_dir_pattern.append(value.lower())
            oi += 1
            if option in ('-1',self.__longopts[oi]):
                self.__list_to_replace.append(value)
            oi += 1
            if option in ('-2',self.__longopts[oi]):
                self.__list_for_replacement.append(value)
            oi += 1
            if option in ('-F',self.__longopts[oi]):
                self._file_types.append(value)
            oi += 1
            if option in ('-C',self.__longopts[oi]):
                self.__case_insensitive = True
            oi += 1
            if option in ('-R',self.__longopts[oi]):
                self.__regex = True
            oi += 1
            if option in ('-w',self.__longopts[oi]):
                self.__word_only = True

        if len(self._file_types) == 0:
            # all file types accepted
            self._file_types.append('*')

        if len(self.__list_for_replacement) != len(self.__list_to_replace):
            self._error("number of searched patterns must match number of replacement patterns")

    def __usage(self):

        sys.stderr.write("Usage: "+self.__PROGRAM_NAME+self.__opt_string+os.linesep)
        sys.stderr.write(self.__opthelp)
        sys.stderr.write("-d,-l,-f,-e,-i,-1,-2 and -F options can be specified multiple times"+os.linesep)

    def _private_init(self,nb_files):
        # create regex list

        self.__sub_list = []

        for i in range(0,len(self.__list_for_replacement)):
            pattern = self.__list_to_replace[i]

            if self.__regex:
                pass
            else:
                pattern = re.escape(pattern)

            if self.__word_only:
                pattern = r"\b"+pattern+r"\b"

            if self.__case_insensitive:
                self.__search_re = re.compile(pattern,re.IGNORECASE)
            else:
                self.__search_re = re.compile(pattern)


            self.__sub_list.append([self.__search_re, self.__list_for_replacement[i]])


    def _process_file(self,filepath):
        """
        returns True if everything OK
        returns False if there was a clearcase error (not blocking, hence the lack of exception)
        """
        try:
            f = open(filepath,"r")
            lines = []
            for l in f:
                lines.append(l)
            f.close()
            modified = False

            # replace pattern on all lines

            for i in range(0,len(lines)):
                l = lines[i]
                for si in self.__sub_list:
                    lr = si[0].sub(si[1],l)
                    if l != lr:
                        modified = True
                        lines[i] = l = lr

            do_it = modified
            clearcase_bug = False

            if modified:

                # write the file
                if self.__checkout and not self.__preview:
                    # attempt to checkout the file if it is a clearcase file
                    try:
                        s = os.stat(filepath)
                        # get access rights
                        is_writable = (s[0] & 0o222) != 0

                        if clearcase_available and not is_writable:
                            if clearcase.is_clearcase_file(filepath):
                                clearcase.checkout(filepath)

                    except Exception:
                        self._warn("Cannot checkout file %s: skipping" % filepath)
                        do_it = False
                        clearcase_bug = True
                if do_it:
                    # we are about to overwrite the file
                    # first, remove multiple "with" directives that may have appeared

                    f = None
                    if not self.__preview:
                        try:
                            f = open(filepath,"w")
                        except:
                            self._warn(("Cannot create file %s: %s. If the file is in a snapshot view,"+
                            "try to update the view with the 'hijack overwrite' option") % (filepath,str(sys.exc_info()[1])))
                            # f = None => kind of preview mode: avoids the writing of the file
                            do_it = False
                            ###clearcase_bug = True

                    for l in lines:
                        if f != None:
                            f.write(l)
                    if f!= None:
                        f.close()

                    msg = "Refactored file "+filepath#+extra_msg

    ##        if not do_it:
    ##            msg = "file "+filepath+" unchanged"

                if self.__preview:
                    msg = "Preview: "+msg
                if do_it:
                    self._message(msg)
        except Exception as e:
            self._warn("Cannot process {}: {}".format(filepath,e))
            return False

        return not clearcase_bug


if __name__ == '__main__':
    """
        Description :
            Main application body
    """


    o = Multifr()
    o.init_from_sys_args(debug_mode = True)
    #o.init("output_file")
