#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scripts that alter documentation/interchange formats"""
import sys
import os
import argparse

import json
import markdown
import glob
import subprocess
import tempfile
import shutil
import time
import uuid

from latexhelper.handystuff import SmartDescriptionFormatter, myprogname, mybundlename
from latexhelper.handystuff import cmd_to_string, whichem

import io

MYBUNDLE=mybundlename()
MYPROGNAME=myprogname()
MYMODULENAME, ignore= os.path.splitext(os.path.basename(__file__))
NAMEDICT={'MYMODULENAME': MYMODULENAME,
          'MYPROGNAME': MYPROGNAME,
          'MYBUNDLE':MYBUNDLE}


cmdmap=whichem(['rst2pdf'])
FULLRST2PDF=cmdmap['rst2pdf']

def json_indent():
    """Output indented json from compliant json input"""
    longdesc=u"""
BUNDLE:  {MYBUNDLE}
MODULE:  {MYMODULENAME}
PROGRAM: {MYPROGNAME}

    Overview:

        Output indented json from compliant json input.

""".format(**NAMEDICT)
    mystdin="STDIN"
    mystdout="STDOUT"
    defaultinput = mystdin
    parser = argparse.ArgumentParser(prog=MYPROGNAME, description=longdesc,
                                     formatter_class=SmartDescriptionFormatter)
    tmphelp="json input file - 'STDIN' means use stdin - (default {})".format(defaultinput)
    parser.add_argument('-i', '--input-json', dest='input_json', default=defaultinput, 
                        help=tmphelp)
    parser.add_argument('-o', '--output-json', dest='output_json', default=mystdout,
                        help="output file - 'STDOUT' means use stdout - (default 'STDOUT')")
    args = parser.parse_args()
    if args.input_json == mystdin:
        print("{}: awaiting json format input from '{}'".format(MYPROGNAME,
                                                                mystdin),
              file=sys.stderr)
        contents = json.load(sys.stdin)
    else:
        filename = os.path.expanduser(args.input_json)
        try:
            with open(filename, "r") as infp:
                contents = json.load(infp)
                print("{}: reading json format input from '{}'".format(MYPROGNAME,
                                                                       filename),
                      file=sys.stderr)
        except FileNotFoundError:
                print("{}: FileNotFoundError '{}'".format(MYPROGNAME,
                                                          filename),
                      file=sys.stderr)
                print("{}: Try: '{} -h'".format(MYPROGNAME,MYPROGNAME), file=sys.stderr)
                exit(-1)
           
    if args.output_json == mystdout:
        print("{}: emitting indented json to '{}'".format(MYPROGNAME, mystdout), file=sys.stderr)
        json.dump(contents, sys.stdout, indent=4)
    else:
        filename = os.path.expanduser(args.output_json)
        print("{}: emitting indented json to '{}'".format(MYPROGNAME, filename), file=sys.stderr)
        with open(filename, "w") as outfp:
            json.dump(contents, outfp, indent=4)
    exit(0)

def md_to_html():
    """Convert a markdown document to html"""
    longdesc=u"""
BUNDLE:  {MYBUNDLE}
MODULE:  {MYMODULENAME}
PROGRAM: {MYPROGNAME}

    Overview:

        Convert a markdown document to html.

""".format(**NAMEDICT)
    mystdin="STDIN"
    mystdout="STDOUT"
    defaultinput = "README.md"
    parser = argparse.ArgumentParser(prog=MYPROGNAME, description=longdesc,
                                     formatter_class=SmartDescriptionFormatter)

    
    tmphelp="markdown input file - 'STDIN' means use stdin - (default {})".format(defaultinput)
    parser.add_argument('-i', '--input-md', dest='input_md', default=defaultinput, 
                        help=tmphelp)
    parser.add_argument('-o', '--output-html', dest='output_html', default=mystdout,
                        help="output file - 'STDOUT' means use stdout - (default 'STDOUT')")
    args = parser.parse_args()
    if args.input_md == mystdin:
        print("{}: awaiting markdown format input from '{}'".format(MYPROGNAME,
                                                                    mystdin),
              file=sys.stderr)
        contents = sys.stdin.read()
    else:
        filename = os.path.expanduser(args.input_md)
        try:
            with open(filename, "r") as infp:
                contents = infp.read()
                print("{}: reading markdown format input from '{}'".format(MYPROGNAME,
                                                                       filename),
                      file=sys.stderr)
        except FileNotFoundError:
                print("{}: FileNotFoundError '{}'".format(MYPROGNAME,
                                                          filename),
                      file=sys.stderr)
                print("{}: Try: '{} -h'".format(MYPROGNAME,MYPROGNAME), file=sys.stderr)
                exit(-1)
    myhtml = markdown.markdown(contents)   
    if args.output_html == mystdout:
        print("{}: emitting html to '{}'".format(MYPROGNAME, mystdout), file=sys.stderr)
        sys.stdout.write(myhtml)
        sys.stdout.write("\n")
    else:
        filename = os.path.expanduser(args.output_html)
        print("{}: emitting html to '{}'".format(MYPROGNAME, filename), file=sys.stderr)
        with open(filename, "w") as outfp:
            outfp.write(myhtml)
            outfp.write("\n")

def docs_rst_to_pdf():
    """    Convert .rst files in current directory and doc/ 
    subdirectory to .pdf files in the target directory."""
    longdesc=u"""
BUNDLE:  {MYBUNDLE}
MODULE:  {MYMODULENAME}
PROGRAM: {MYPROGNAME}

    Overview:

        Convert .rst files in current directory and doc/ subdirectory
        to .pdf files in the target directory.

""".format(**NAMEDICT)
    if FULLRST2PDF=='': 
        raise ValueError("rst2pdf program not installed")
    defaultdir = os.getcwd()
    default_outdir = os.path.join(defaultdir, "pdf_docs")

    parser = argparse.ArgumentParser(prog=MYPROGNAME, description=longdesc,
                                     formatter_class=SmartDescriptionFormatter)
    parser.add_argument('-s', '--source-directory',
                        dest='source_directory', default=defaultdir, 
                        help="source directory (default {})".format(defaultdir))
    parser.add_argument('-o', '--output-directory',
                        dest='output_directory', default=default_outdir,
                        help="output directory (default {})".format(default_outdir))
    args = parser.parse_args()
    maindir=os.path.expanduser(args.source_directory)
    doc_dir= os.path.join(maindir, 'doc')
    outdir = os.path.expanduser(args.output_directory)
    for adr in [maindir,doc_dir, outdir]:
        if not os.path.exists(outdir):
            print("{}: directory '{}' does not exist".format(MYPROGNAME,outdir),
                  file=sys.stderr)
            print("{}: try '{} -h'".format(MYPROGNAME,MYPROGNAME),
                  file=sys.stderr)
            exit(1)
    baselist = glob.glob(os.path.join(maindir, "*.rst"))
    doclist = glob.glob(os.path.join(doc_dir,  "*.rst"))
    bothlist = [anm for anm in baselist if anm != ''] + [anm for anm in doclist if anm != ''] 
    full_list=[]
    for anm in bothlist:
        noext, ext = os.path.splitext(anm)
        full_list.append(noext)
    out_dir = os.path.expanduser(args.output_directory)
    pairs = [ (anm + '.rst',
               os.path.join(out_dir, os.path.basename(anm)) + '.pdf') for anm in full_list] 
    if len(pairs) > 0:
        for inname, outname in pairs:
            acommand = [FULLRST2PDF, inname, '-o', outname]
            print("{}: {}".format( MYPROGNAME, cmd_to_string(acommand)), file=sys.stderr)       
            subprocess.check_call(acommand)
        exit(0)
    else:
        print("{}: No .rst files found under '{}' nor under '{}'".format(MYPROGNAME, 
                                                                         maindir,
                                                                         doc_dir),
              file=sys.stderr)
        exit(1)

        
if __name__ == '__main__':
    print("{}: This module intended for importing, not invoking it directly.".format(MYPROGNAME),
          file=sys.stderr)
    


    
