# standard imports
import os,sys,glob,re
import argparse,traceback




class ArgParser(object):
    def __init__(self, program_name, version):
        self.__parser = argparse.ArgumentParser(prog=program_name,add_help=True)
        self.__main_group = self.__parser.add_argument_group("Specific arguments")
        self.__parser.add_argument('--version', action='version', version=version)

    def add_argument(self, long_opt, desc, short_opt=None, required=False, default=None, *args, **kwargs):
        # For easy writting, user use '=' at param name end if it receive a value
        # And omit it if this parameter is just a flag
        #
        # All the standard parameters of argparse.ArgumentParser().add_argument() are also accepted :
        # eg. self.__ARG_PARSER.add_argument("max-lines", "Maximum number of lines", type=int)
        # => the max_lines parameter will automatically be converted to an integer
        #
        if long_opt.endswith('='):
            # Store linked value
            action="store"
            # Remove the '=' at end to normalize
            long_opt = long_opt[:-1]
        elif long_opt.endswith('=[]'):
            # Store in an array
            action="append"
            if default == None:
                default = []
            # Remove the '=[]' at end to normalize
            long_opt = long_opt[:-3]
        else:
            # Flag mode
            action="store_true"
            if default == None:
                default = False

        if not short_opt:
            short_opt = long_opt[0]

        self.__main_group.add_argument("-"+short_opt, "--"+long_opt, help=desc, dest=long_opt, action=action, default=default, required=required, *args, **kwargs)

    def accept_positional_arguments(self, name, desc, *args, **kwargs):
        """
            Use this method if positonal arguments are going to be used
        """
        self.__parser.add_argument(name, help=desc, nargs='*', action="store", *args, **kwargs)

    def parse(self,args=None):
        return self.__parser.parse_args(args=args)

class Grep:
    __VERSION_NUMBER = "1.0"
    try:
        __MODULE_FILE = __file__
    except:
        __MODULE_FILE = sys.executable
    __PROGRAM_NAME = os.path.basename(__MODULE_FILE)
    __PROGRAM_DIR = os.path.abspath(os.path.dirname(__MODULE_FILE))


    def __init__(self):
        self.__ARG_PARSER = ArgParser(self.__PROGRAM_NAME,self.__VERSION_NUMBER)
        self.__logfile = ""
        self.__temp_directory = None
        self.__with_traceback = True

        # define arguments here: ex self.__output_file = None
        # so completion works

        try:
            # set binary mode on output/error stream for Windows
            import msvcrt
            msvcrt.setmode (sys.stdout.fileno(), os.O_BINARY)
            msvcrt.setmode (sys.stderr.fileno(), os.O_BINARY)
        except:
            pass
    def __create_temp_directory(self):
        """
        defines self.__temp_directory
        """

        self.__temp_directory = os.path.join(os.getenv("TEMP"),self.__PROGRAM_NAME.replace(".py","")+("_%d" % os.getpid()))
        if not os.path.isdir(self.__temp_directory):
            os.mkdir(self.__temp_directory)
        return self.__temp_directory

    def __delete_temp_directory(self):
        if self.__temp_directory != None:
            [rc,output] = python_lacks.rmtree(self.__temp_directory)
            if rc == 0:
                self.__temp_directory = None
            else:
                self.__warn("Could not delete temp dir %s: %s" % (self.__temp_directory,output))

    def init_from_custom_args(self,args):
        """
        module mode, with arguments like when called in standalone
        """
        self.__parse_args(args)
        self.__purge_log()
        return self.__doit()

    def _init_from_sys_args(self):
        """ standalone mode """

        try:
            self.__do_init()
        except Exception:
            raise
        finally:
            self.__delete_temp_directory()

        return self.__found
# uncomment if module mode is required
##    def init(self,output_file):
##        """ module mode """
##        # set the object parameters using passed arguments
##        self.__output_file = output_file
##        self.__purge_log()
##        self.__doit()

    def __do_init(self):
        #count_usage.count_usage(self.__PROGRAM_NAME,1)
        self.__parse_args()
        self.__purge_log()
        self.__doit()

    def __purge_log(self):
        if self.__logfile != "":
            try:
                os.remove(self.__logfile)
            except:
                pass

    def __message(self,msg,with_prefix=True):
        if with_prefix:
            msg = self.__PROGRAM_NAME+(": %s" % msg)+os.linesep
        else:
            msg += os.linesep
        try:
            sys.stderr.write(msg)
            sys.stderr.flush()
        except:
            # ssh tunneling bug workaround
            pass
        if self.__logfile != "":
            f = open(self.__logfile,"ab")
            f.write(msg)
            f.close()

    def __error(self,msg,user_error=True,with_traceback=False):
        """
        set user_error to False to trigger error report by e-mail
        """

        self.__with_traceback = with_traceback
        raise Exception("*** Error: "+msg+" ***")

    def __warn(self,msg):
        self.__message("*** Warning: "+msg+" ***")


    def __parse_args(self,args=None):
        # Define authorized args
        self.__define_args()

        # Parse passed args
        opts = self.__ARG_PARSER.parse(args=args)
        for key, value in opts.__dict__.items():
            var_name = key.replace("-", "_").lower()
            setattr(self, "_%s__%s" % (self.__class__.__name__, var_name), value)


    def __define_args(self):
        # Note :
        # Each long opt will correspond to a variable which can be exploited in the "doit" phase
        # All '-' will be converted to '_' and every upper chars will be lowered
        # Standard argparse parameters can also be used (eg. type=int for automatic convertion)
        # Exemple :
        #   My-Super-Opt --> self.__my_super_opt
        self.__ARG_PARSER.accept_positional_arguments("filenames", "Pattern [Files]")
        self.__ARG_PARSER.add_argument("word-regexp", "force PATTERN to match only whole words", short_opt="w")
        self.__ARG_PARSER.add_argument("ignore-case", "ignore case distinctions", short_opt="i")
        self.__ARG_PARSER.add_argument("invert-match", "select non-matching lines", short_opt="v")
        self.__ARG_PARSER.add_argument("files-with-matches", "only print FILE names containing matches", short_opt="l")
        self.__ARG_PARSER.add_argument("line-number", "line number with output lines", short_opt="n")
        self.__ARG_PARSER.add_argument("clearcase-versions", "scan all clearcase versions of the current branch")

    def __process_file(self,filepath):
        f = open(filepath,"r")
        lineno = 0
        for l in f:
            lineno += 1
            l = l.rstrip("\n")
            if ((re.search(self.__pattern,l)==None) == self.__invert_match):
                self.__found = True
                if self.__files_with_matches:
                    self.__output_stream.write(filepath+"\n")
                    break
                else:
                    if len(self.__input_files)>1:
                        self.__output_stream.write(filepath+":")
                    if self.__line_number:
                        self.__output_stream.write("%d:" % lineno)

                    self.__output_stream.write(l+"\n")
        f.close()

    def __doit(self):
        if len(self.__filenames)==0:
            self.__error("No pattern specified")
        elif len(self.__filenames)==1:
            self.__input_files = ["-"]
        else:
            self.__input_files = []
            for f in self.__filenames[1:]:
                if self.__clearcase_versions:
                    input_files= glob.glob(f)
                    import clearcase_ucm as clearcase
                    [rc,output] = clearcase.cleartool("lsvtree",["-s"]+input_files,exception_on_error=True)
                    for l in output.split("\n"):
                        l = l.strip()
                        sl = l.split("@@")
                        if len(sl)==2:
                            v = os.path.basename(sl[1]) # get version final name
                            if (v.isdigit() and int(v)!=0) or v=="CHECKEDOUT":
                                self.__input_files.append(l)
                else:
                    self.__input_files.extend(glob.glob(f))

        flags = 0
        pattern = self.__filenames[0]
        if self.__ignore_case:
            flags |= re.IGNORECASE
        if self.__word_regexp:
            pattern = r"\b"+pattern+r"\b"

        self.__found = False
        self.__pattern = re.compile(pattern,flags)
        self.__output_stream = sys.stdout
        for f in self.__input_files:
            self.__process_file(f)

        return self.__found

if __name__ == '__main__':
    """
        Description :
            Main application body
    """


    o = Grep()
    found = o._init_from_sys_args()
    if not found:
        sys.exit(1)
