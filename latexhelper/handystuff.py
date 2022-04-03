#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (print_function, unicode_literals)
u"""
Smart descriptor for argparse
"""
import sys
import os
import argparse
import datetime
import time
import glob
import subprocess



def mybundlename():
    mybundle = os.path.basename(os.path.dirname(__file__)) 
    return mybundle # the base name of whatever directory  this file is in

MYBUNDLE=mybundlename()

def myprogname():
    """Figure out and return the our progarm's name"""
    fullname = os.path.expanduser(sys.argv[0])
    basename = os.path.basename(fullname)
    return basename
    
MYPROGNAME=myprogname()
MYMODULENAME, ignore= os.path.splitext(os.path.basename(__file__))
NAMEDICT={'MYMODULENAME': MYMODULENAME,
          'MYPROGNAME': MYPROGNAME,
          'MYBUNDLE':MYBUNDLE}

class SmartDescriptionFormatter(argparse.RawDescriptionHelpFormatter):
    def _fill_text(self, text, width, indent):
        if text.startswith('R|'):
            paragraphs = text[2:].splitlines()
            rebroken = [argparse._textwrap.wrap(tpar, width) for tpar in paragraphs]
            #print(rebroken)
            rebrokenstr = []
            for tlinearr in rebroken:
                if (len(tlinearr) == 0):
                    rebrokenstr.append("")
                else:
                    for tlinepiece in tlinearr:
                        rebrokenstr.append(tlinepiece)
            return '\n'.join(rebrokenstr) #(argparse._textwrap.wrap(text[2:], width))
        # this is the RawTextHelpFormatter._split_lines
        #return argparse.HelpFormatter._split_lines(self, text, width)
        return argparse.RawDescriptionHelpFormatter._fill_text(self, text, width, indent)

     
def cmd_to_string(acmd):
    quoted_strings=[]
    for astr in acmd:
        if '"' in astr:
            if "'" in astr:
                raise ValueError("Cannot quote with an argument that has both \" and \' in it")
            quoted_strings.append("'{}'".format(astr))
        else:
            quoted_strings.append('"{}"'.format(astr))
    mystring = " ".join(quoted_strings[:])
    return mystring

#
# A pair of functions ot aid in pipelining with subprocess calls
# pipe and pipe_wait.  I got these of the net.
#
def pipe(*args):
    '''
    Takes as parameters several dicts, each with the same
    parameters passed to popen.

    Runs the various processes in a pipeline, connecting
    the stdout of every process except the last with the
    stdin of the next process.
    '''
    if len(args) < 2:
        raise ValueError( "pipe needs at least 2 processes")
    # Set stdout=PIPE in every subprocess except the last
    # all but the last will go to input of the next
    # the last will be used to collect the result
    for i in args[:]:
        i["stdout"] = subprocess.PIPE

    # Runs all subprocesses connecting stdins and stdouts to create the
    # pipeline. Closes stdouts to avoid deadlocks.
    popens = [subprocess.Popen(**args[0])]
    for i in range(1,len(args)):
        args[i]["stdin"] = popens[i-1].stdout
        popens.append(subprocess.Popen(**args[i]))
        popens[i-1].stdout.close()

    # Returns the array of subprocesses just created
    return popens
    
def pipe_wait(popens,decode_code='utf-8'):
    '''
    Given an array of Popen objects returned by the
    pipe method, wait for all processes to terminate
    and return the output of the last one.
    Crap out if any of the processs fail
    '''
    lastoutput = popens[-1].stdout.read().decode(decode_code)
    expected = [0] * len(popens)
    results = expected[:]
    while popens:
        last = popens.pop(-1)
        results[len(popens)] = last.wait()
    assert results == expected # crap out unless all return 0
    return lastoutput

def subprocess_lines_from_stdin(args, inputlines):
    """Invoke  a subprocess that reads inputlines from standard in"""
    #
    # At this writing there is always a warning about Pseudo-terminal
    # that confuses the output user sees.  So we endeavour to
    # filter that out here too.
    #
    print("{}: {}".format(MYPROGNAME, cmd_to_string(args)), file=sys.stderr)
    
    bigchunk="".join(inputlines)
    # trying to make Communicate like our chunk by converting it to bytes
    bigbytes= bytearray(bigchunk, 'utf-8')
    ssh_process = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    outdata, errdata = ssh_process.communicate(input=bigbytes)
    errdata = errdata.decode('utf-8')
    ssh_process.wait()
    errlines = errdata.splitlines()
    # discard the Pseudo-terminal warning
    filtered = [al for al in errlines if 'Pseudo-terminal' not in al ]
    for al in filtered:
        l = al.strip()
        if len(l) > 0:
            print("{}: {}".format(MYPROGNAME,l), file=sys.stderr)
    print("{}: {} done.".format(MYPROGNAME, args[0]), file=sys.stderr)
            
def pipeline_pip_package_version(packagename):
    """Implement this: 'pip show -V packagename | egrep ^Version: | cut --delimiter=\  -f 2' with subprocess """
    # egrep="/bin/egrep"
    # cut="/usr/bin/cut"
    # pip="/home/ubuntu/animbboard_venv/bin/pip"
    process1 = dict(args=['/home/ubuntu/animbboard_venv/bin/pip', 'show',  '-V', packagename], shell=False)
    process2 = dict(args=['/bin/egrep', '^Version:'], shell=False)
    process3 = dict(args=['/usr/bin/cut', '--delimiter= ', '-f', '2'], shell=False)
    popens = pipe(process1, process2, process3)
    result = pipe_wait(popens)
    # result = result.decode('utf-8')
    cleanresult = result.strip()
    return cleanresult

def package_version(packagename):
    """tack the version number onto the end of the packagename"""
    # expect this to raise AssertionError when no package exists (along with a printed wardning
    return "-".join([packagename, pipeline_pip_package_version(packagename)])

def maybe_makedir(fullpath, octal_mode=0o775): # rwx rwx rx 
    """Make all intermediate level directories unless the leaf directory  already exists"""
    try:
        os.makedirs(fullpath, octal_mode)
    except OSError as e:
        if e.errno == 17:
            pass
        else:
            raise
    return

def hardlink_dir_files(sourcedir, destdir):
    """Make a hard link in dest to each file in source"""
    sourcelist = glob.glob(os.path.join(sourcedir, '*'))
    svdir = os.getcwd()
    os.chdir(destdir)
    for afile in sourcelist:
        alinkname = os.path.basename(afile)
        try:
            os.unlink(alinkname)
        except:
            pass
        os.link(afile, alinkname)
    os.chdir(svdir)

def hardlink_dir_frames(sourcedir, destdir, start_frame=1):
    """Make a hard link in dest to frames (frame_NNNN.png) in source (maybe renumber)"""
    sources = sorted(glob.glob(os.path.join(sourcedir, "frame_????.png")))
    n = len(sources)
    assert( n > 0) # Treat no source frames as an error
    if start_frame is None:
        # no renumbering
        dests = [os.path.basename(asrc) for asrc in sources]
        x = dests[-1]
        snext_frame = x[-8:-4]
        next_frame=int(snext_frame) + 1 
    else:
        # renumber starting from this number
        next_frame = start_frame + n
        dests = ["frame_{:04d}.png".format(anum) for anum in range(start_frame, next_frame)]
    pairs = zip(sources,dests)
    svdir = os.getcwd()
    os.chdir(destdir)
    for afile, alinkname in pairs:
        os.link(afile, alinkname)
    os.chdir(svdir)
    return next_frame

def whichem(brief_list):
    """A way to 'which' all a module's commands into a map (brief -> which(brief))"""
    mykeys = list(set(brief_list))  # unique it
    keymap = dict([(ak, '') for ak in mykeys])
    completed = subprocess.run(['/usr/bin/which']+ mykeys,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    # return code will not be 0 unless all have worked out, so we we dont check it
    output = completed.stdout
    result = output.splitlines()
    result = [aline.strip('\n') for aline in result]
    for nam, fnam in [(os.path.basename(fnam), fnam) for fnam in result]:
        keymap[nam] = fnam
    return keymap

def vdate_now(date_only=False):
    """A way to obtain a version date string that is consistent regardless of locale"""
    naive_dt = datetime.datetime.utcnow() # naive datetime set to current UTC
    if date_only:
        mystring = naive_dt.strftime("%Y-%m-%d")
    else:
        mystring = naive_dt.strftime("%Y-%m-%d")
    return mystring


if __name__ == '__main__':
    print("{}: This module is not intended to be used directly, but imported.".format(MYPROGNAME))
    exit(1)

    
