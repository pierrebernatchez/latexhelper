#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tool for composing math exercise documents in latex markup automatically by selecting question snippets"""
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

from handyhelper.handystuff import SmartDescriptionFormatter, myprogname, mybundlename
from handyhelper.handystuff import cmd_to_string, whichem, vdate_now

import io

def deprecated_proof_title(category, proof_number):
    """Get a replacement title string for a proof"""
    # proof_title = "copie pour vérification: {}  x{:02d}".format(args.category, args.proof)

    replacements = {
        "calculus": "Copie pour vérification: Calcul {}",
        "statistics_and_probability": "Copie pour vérification: Statistiques et probabilité {}",
        "functions": "Copie pour vérification: Fonctions {}",
        "template": "Copie pour vérification: template {}",
        "algebra_and_numbers": "Copie pour vérification: Algèbre et Nombres {}",
        "geometry_and_trigonometry": "Copie pour vérification: Géométrie et Trigonométrie {}"
    }
    qname="x{:02d}.tex".format(proof_number)
    sub = replacements[category].format(qname)
    return sub
    

def default_attributes():
    """Default values of attributes to filled in for each document"""
    alist = [("author", "Anonyme"),
             ("thanks", "Les questions de cet exercise sont tirées par l'auteur de la collection 'Math Sans Mystère'.  La collection à son tour est dérivée d'examens de l'IB de 2007, 2010, 2011, 2012, 2018"),
             ("comment", "The title field is a map from category name to category title value. It is ok to modify the title value but not the category name."), 
             ("title", {"calculus":"Éxercices de révision: Calcul",
                        "statistics_and_probability":"Éxercices de révision: Statistiques et probabilité",
                        "functions":"Éxercices de révision: Fonctions",
                        "template":"Exercise template",
                        "algebra_and_numbers":"Éxercices de révision: Algèbre et Nombres",
                        "geometry_and_trigonometry":"Éxercices de révision: Géométrie et Trigonométrie"}),
             ("alltitle", {"calculus":"Liste Complète: Calcul",
                           "statistics_and_probability":"Liste Complète: Statistiques et probabilité",
                           "functions":"Liste Complète: Fonctions",
                           "template":"Exercise template",
                           "algebra_and_numbers":"Liste Complète: Algèbre et Nombres",
                           "geometry_and_trigonometry":"Liste Complète: Géométrie et Trigonométrie"}),
             ("prooftitle", {"calculus":"Exemple pour approuver: Calcul",
                             "statistics_and_probability":"Exemple pour approuver: Statistiques et probabilité",
                             "functions":"Exemple pour approuver: Fonctions",
                             "template":"Exercise template",
                             "algebra_and_numbers":"Exemple pour approuver: Algèbre et Nombres",
                             "geometry_and_trigonometry":"Exemple pour approuver: Géométrie et Trigonométrie"}),
             ("credentials", "/home/ubuntu/s3conf_ogopogo"),
             ("publish", "s3://www.ogopogo.biz/mathsansmystere/"),
             ("fetch", "https://s3.amazonaws.com/www.ogopogo.biz/mathsansmystere/"),
             ("with_logo", False)]
    return dict(alist)
 
MYBUNDLE=mybundlename()
MYPROGNAME=myprogname()
MYMODULENAME, ignore= os.path.splitext(os.path.basename(__file__))
NAMEDICT={'MYMODULENAME': MYMODULENAME,
          'MYPROGNAME': MYPROGNAME,
          'MYBUNDLE':MYBUNDLE}

 
cmdmap=whichem(['pdflatex','s3cmd','echo'])
FULLPDFLATEX=cmdmap['pdflatex']
FULLS3CMD=cmdmap['s3cmd']
FULLECHO=cmdmap['echo']

def make_pdflatex_command(full_latexfilename, outdir=None):
    if outdir is not None:
        mycommand = [FULLPDFLATEX, '-output-directory', outdir, full_latexfilename]
    else:
        mycommand = [FULLPDFLATEX, full_latexfilename]
    return mycommand

def make_publish_command(full_pdfilename, pubtarget=None, credentials=None):
    basepdfname=os.path.basename(full_pdfilename)
    if pubtarget is None:
        mycommand = [FULLECHO, basepdfname, ' Not published because no target given.']
    elif credentials is None:
        targetfile = os.path.join(pubtarget,basepdfname) 
        mycommand = [FULLS3CMD, 'put', full_pdfilename, targetfile]
    else:
        targetfile = os.path.join(pubtarget,basepdfname) 
        mycommand = [FULLS3CMD, '-c', credentials, 'put', full_pdfilename, targetfile]
    return mycommand

# pdflatex -output-directory out_docs out_docs/algebra_and_numbers_2022-03-30T20\:48.tex
def assert_directory(adir):
    if os.path.exists(adir):
        return True
    else:
        emsg = 'Directory "{}" does not exist'.format(adir)
        print("{}: fatal error: {}".format(MYPROGNAME, emsg), file=sys.stderr)
        raise ValueError("Assert failed:"+emsg)
    
def exercise_title(config, category, with_logo=False):
    """Compose the document title lines to match the config file, and the category"""
    if with_logo:
        tline="\\title{\\begin{center}\\includegraphics[scale=0.5]{ib-logo.png}\\end{center} " + config['title'][category]+ "}\n"
    else:
        tline="\\title{ " + config['title'][category]+ "}\n"
    authorline="\\author{"  + config['author'] + "\\thanks{" + config['thanks'] + "}}\n"
    return tline + authorline + "\\date{\\today}\n" + "\\maketitle\n"


def exercise_preamble(fulldirname):
    #
    # We just need to tweak the preamble to have the right graphics path for given 
    # question directory.  All the rest is a constant.
    #
    mypreamble="""\
% --------------------------------------------------------------
% This preamble was generated by ${MYPROGNAME}
% --------------------------------------------------------------
 
\\documentclass[10pt]{article}


% Basic Packages for Encoding (Input AND Output) and Langauge Support
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage[french]{babel}
\\usepackage{enumitem}

% Change Layout with a User-Friendly Interface
\\usepackage[margin=1in]{geometry} 

% Include Pictures with a User-Friendly Interface
\\usepackage{graphicx}
\\usepackage{float}

% so that we can import question snippets.
\\usepackage{import}


% Extended Math Support from the Famous 'American Mathematical Society'
\\usepackage{amsmath,amsthm,amssymb}

% Section title formatting
\\usepackage{titlesec}

\\titleformat{\\section}
            {\\normalfont\\scshape}{\\thesection}{1em}{}

\\newcommand{\\N}{\\mathbb{N}}
\\newcommand{\\Z}{\\mathbb{Z}}

\\usepackage{pgfplots}

%% this command I just copied from suggestion on the net about
%% how to automatically get page breaks to avoid the middel of questions
%% basically a shot in the dark that worked
\\newcommand\\mysection{\\vfil\\penalty-9999\\vfilneg\\section}

%Numbered Questions 
\\newcounter{question}
\\newenvironment{question} %% the * prevente myection from generating its own number
               {\\refstepcounter{question}\\par\\smallskip\\noindent\\mysection*{\\textbf{Q~\\thequestion.}}\\par \\noindent \\rmfamily}
               {\\smallskip}

"""
    mycategory = os.path.basename(fulldirname)
    gp = "\\graphicspath{ {./images/" + mycategory + "/} }\n"
    fullpreamble = mypreamble + gp
    return fullpreamble
    
    
def test():
    ad = default_attributes()
    jstring = json.dumps(ad, ensure_ascii=False, indent=4).encode('utf8')
    print(jstring.decode(), file=sys.stderr)
    return

def maybe_create_config(fullname, verbose=False):
    """Load the json config file, if it does not exist, generate a default and load that"""
    if os.path.exists(fullname):
        with open(fullname, "r") as cfile:
            cfg = json.load(cfile)
        return cfg
    cfg = default_attributes()
    #
    # Pretty good trick to overcome the utf-8 encoding for json issue.
    # So we can see the json file without the stupid escaped characters.
    #
    jstring = json.dumps(cfg, ensure_ascii=False, indent=4).encode('utf8')
    with open(fullname, "w") as cout:
        print(jstring.decode(), file=cout)
    if verbose:
        print('{}: Creating json format configuration file: "{}"'.format(MYPROGNAME,fullname), file=sys.stderr)
        print('{}: You may want to edit attributes such as "author"'.format(MYPROGNAME), file=sys.stderr)
        print('{}: These are its current contents'.format(MYPROGNAME), file=sys.stderr)
        print(jstring.decode(), file=sys.stderr)
    return cfg

def curry_import_mapper(category,comment_filter=None):
    """Return a function which maps a qestion name to an import line for a specific category"""
    def unfiltered_map(qname):
        """Funcion maps question name (basename in the category's tex directory) to import line"""
        qimport_string = "\\import{./tex/" + category + "/}{" + qname + "}"
        return qimport_string
    def filtered_map(qname):
        """Funcion maps question name (basename in the category's tex directory) to import line"""
        snippetname=os.path.join("./tex", category, qname)
        with open(snippetname, "r") as snipin:
            aline = snipin.readline().strip()
            if comment_filter in aline:
                include_it = True
            else:
                include_it = False
        if include_it:
            qimport_string = "\\import{./tex/" + category + "/}{" + qname + "}"
            return qimport_string
        else:
            return ""
    if comment_filter is not None:
        return filtered_map
    else:
        return unfiltered_map

def numbs_to_questions(raw_numb_list, question_dir):
    """produce a sorted sequence of existing unique question file names from a raw list of numbers"""
    def numb_to_filename(anumb):
        anam="x{:02d}.tex".format(anumb)
        return anam
    def uniquefy(nseq):
        """Unique sorted n generator"""
        old=None
        for n in sorted(nseq):
            if old is None:
                old = n
                yield n
            if n > old:
                old = n
                yield n
    unique_questions = [ numb_to_filename(n) for n in uniquefy(raw_numb_list)]
    existing_questions = [ q for q in unique_questions if os.path.exists(os.path.join(question_dir, q))]
    return existing_questions
    

def generate_latex(latexfilename, questions, category=None, basedir=None, localconfig=None):
    """Generate the latex markup for the document and write it to the given filename"""
    fulldirname=os.path.join(basedir, category)
    any_mapper = curry_import_mapper(category,comment_filter=None)
    gdc_mapper = curry_import_mapper(category, comment_filter="GDC:YES")
    nogdc_mapper = curry_import_mapper(category, comment_filter="GDC:NO")
    xpreamble=exercise_preamble(fulldirname)
    xbegin= "\\begin{document}\n"
    xtitle = exercise_title(localconfig, category, with_logo=localconfig["with_logo"])
    xnewpage = "\\newpage\n"
    xend="\\end{document}\n"
    xgdc="\\section*{\\textbf{Calculatrice Graphique Permise}}\n"
    xnogdc="\\section*{\\textbf{Calculatrice Graphique Non Permise}}\n"
    gdc_list = [ ast for ast in  [gdc_mapper(anm) for anm in questions] if len(ast) >0 ]
    nogdc_list = [ ast for ast in  [nogdc_mapper(anm) for anm in questions] if len(ast) >0 ]
    with open(latexfilename, "w") as latexfile:
        latexfile.write(xpreamble)
        latexfile.write(xbegin)
        latexfile.write(xtitle)
        latexfile.write(xnewpage)
        if len(nogdc_list) > 0:
            latexfile.write(xnogdc)
            for animport in nogdc_list:
                latexfile.write(animport)
                latexfile.write('\n')
        if len(gdc_list) > 0:
            latexfile.write(xgdc)
            for animport in gdc_list:
                latexfile.write(animport)
                latexfile.write('\n')
        latexfile.write(xend)
    
def gen_exercise():
    """Let the user supply a list of questions, generate a latex marked
up document to print those questions, then generate a pdf document
from the latex document."""
    longdesc=u"""
BUNDLE:  {MYBUNDLE}
MODULE:  {MYMODULENAME}
PROGRAM: {MYPROGNAME}

    Overview:

        Compose a latex exercise document by combining a predetermined
        preamble with user specific markup for title and author and
        with user selected exercise questions and compile a pdf document
        from that.

    Examples:

       {MYPROGNAME} -c calculus -a
  
           Emits a pdf document named 'calculus.pdf' that contains all
           the questions in the calculus category.
 
       {MYPROGNAME} -c algebra_and_numbers -q 1 3 9 11 
    
           Emits a pdf document named algebra_and_numbers_UUID.pdf that
           contains collection questions 1,3,9,11 (as Q1, Q2, Q3, Q4)

       {MYPROGNAME} -c geometry_and_trigonometry -p 13

            Emits a single question exercise pdf document named
            "geometry_and_trigonometry_x13_UUID.pdf for
            proof reading single question snippets.

       Where UUID is a Universally Unique Identifier String 36 characters long.
 
""".format(**NAMEDICT)
    date_stamp = vdate_now()
    uuid_stamp = str(uuid.uuid4())
    configfilename="~/.{}.cfg".format(MYBUNDLE)
    fullconfigfile= os.path.expanduser(configfilename)
    localconfig = maybe_create_config(fullconfigfile,verbose=True)    
    if FULLPDFLATEX=='':
        emsg = "pdflatex program is not installed."       
        print("{}: fatal error: {}".format(MYPROGNAME, emsg), file=sys.stderr)
        raise ValueError("Fatal error:"+emsg)
    doc_formats=["pdf", "latex" ]
    defaultdir = os.getcwd()
    default_basedir=os.path.join(defaultdir, 'tex')
    default_images=os.path.join(defaultdir, 'images')
    default_outdir = os.path.join(defaultdir, "out_docs")
    assert_directory(default_basedir)
    assert_directory(default_images)
    assert_directory(default_outdir)
    dirnames=sorted([aname for aname in os.listdir(default_basedir) if os.path.isdir(os.path.join(default_basedir,aname))])
    dirnames_with_titles = [an for an in dirnames if an in localconfig['title']]
    # for an in dirnames_with_titles:
    #    print("{}: title for {}: {}".format(MYPROGNAME, an, localconfig['title'][an]), file=sys.stderr)
    if len(dirnames_with_titles) < 1:
        emsg = '"{}" has no question subdirectories for configured categories.'.format(default_basedir)       
        print("{}: fatal error: {}".format(MYPROGNAME, emsg), file=sys.stderr)
        raise ValueError("Fatal error:"+emsg)
    else:
        catagories=[acat for acat in dirnames_with_titles if acat != 'template']
        if 'template' in dirnames_with_titles:
            template='template'
        else:
            template=None
        default_category = catagories[0]
    
    parser = argparse.ArgumentParser(prog=MYPROGNAME, description=longdesc,
                                     formatter_class=SmartDescriptionFormatter)
    default_author = localconfig['author']
    parser.add_argument('-A', '--author', dest='author', default=default_author,
                        help="Author of the exercise (default '{}')".format(default_author))
    parser.add_argument('-T', '--title', dest='title',
                        help="Override the default title (per category)")
    parser.add_argument('-c',
                        dest='category', choices = catagories, default=default_category,
                        help="math category (default {})".format(default_category))
    mxgroup = parser.add_mutually_exclusive_group(required=True)
    mxgroup.add_argument('-a', '--all-questions',
                         dest='all_questions', action='store_true', default=False,
                         help="generate a document with all the available questions from the category")
    mxgroup.add_argument('-p', '--proof', dest="proof", type=int,
                         help="generate a single proof document for the given question number")
    mxgroup.add_argument('-q', '--question-numbers', dest='question_numbers', 
                         nargs='+', type=int,
                         help="generate a document with this list of question numbers from the category")
    parser.add_argument('-o', '--output-directory', dest="output_directory", default=default_outdir,
                        help="Directory where documents will be emitted (default {})".format(default_outdir))
    parser.add_argument('-f', '--filename', dest="filename", 
                        help="Use this instead of category name in output filename")
    parser.add_argument('-t', '--type-of-document', dest="type_of_document",
                        choices=doc_formats, default=doc_formats[0],
                        help="Type to output - either latex or both latex and pdf - (default {})".format(doc_formats[0]))
    args = parser.parse_args()
    localconfig['author'] = args.author
    # override exercise title depending on circumstance
    if args.all_questions:
        localconfig['title'][args.category]=localconfig['alltitle'][args.category]
        
    if args.proof is not None:
        localconfig['title'][args.category]=localconfig['prooftitle'][args.category]
        
    if args.title is not None:
        localconfig['title'][args.category]=args.title
        
    output_directory=os.path.expanduser(args.output_directory)
    ###was here
    if args.filename is None:
        targetprefix = args.category
    else:
        targetprefix = args.filename

    if args.all_questions :
        targetname = targetprefix
    else:
        targetname = "{}_{}".format(targetprefix, uuid_stamp) 
    
    if args.question_numbers is not None:
        qdirname=os.path.join(default_basedir, args.category)
        qs = numbs_to_questions(args.question_numbers, qdirname)
        fulltarget = os.path.join(output_directory, "{}.tex".format(targetname))
        generate_latex(fulltarget, qs,
                       category=args.category, basedir=default_basedir, localconfig=localconfig)
        
    if args.proof is not None:
        #sub_title = proof_title(args.category, args.proof)
        # localconfig['title'][args.category]=sub_title
        targetname="{}_x{:02d}_{}".format(args.category, args.proof,uuid_stamp)        
        qdirname=os.path.join(default_basedir, args.category)
        qs = numbs_to_questions([args.proof], qdirname)
        fulltarget = os.path.join(output_directory, "{}.tex".format(targetname))
        generate_latex(fulltarget, qs,
                       category=args.category, basedir=default_basedir, localconfig=localconfig)
        
    if args.all_questions:
        qdirname=os.path.join(default_basedir, args.category)
        fnames = [os.path.basename(fn) for fn in sorted(glob.glob(os.path.join(qdirname, "*.tex")))]
        fulltarget = os.path.join(output_directory, "{}.tex".format(targetname))
        if len(fnames) < 1:
            print('{}: no questions in directory "{}"'.format(MYPROGNAME, qdirname), file=sys.stderr)
        else:
            generate_latex(fulltarget, fnames,
                           category=args.category, basedir=default_basedir, localconfig=localconfig)
            
    if args.type_of_document == 'pdf' or args.proof is not None:
        acmd = make_pdflatex_command(fulltarget, outdir=output_directory)
        acstring = cmd_to_string(acmd)
        print("{}: invoking: {}".format(MYPROGNAME, acstring), file=sys.stderr)
        subprocess.check_call(acmd)
        pdftarget = os.path.join(output_directory, "{}.pdf".format(targetname))
        print("{}: emitted: {}".format(MYPROGNAME,fulltarget), file=sys.stderr)
        print("{}: emitted: {}".format(MYPROGNAME,pdftarget), file=sys.stderr)
        pubtarget = localconfig['publish']
        credentials = localconfig['credentials']
        acmd = make_publish_command(pdftarget, pubtarget=pubtarget, credentials=credentials)  
        acstring = cmd_to_string(acmd)
        if pubtarget is not None:
            # dont need to emit the echo command emitted when pubtarget is none
            print("{}: invoking: {}".format(MYPROGNAME, acstring), file=sys.stderr)
        subprocess.check_call(acmd)
        if pubtarget is not None:
            fetchurl = os.path.join(localconfig['fetch'], os.path.basename(pdftarget))
            print("{}: URL: {}".format(MYPROGNAME,fetchurl), file=sys.stderr)
        

if __name__ == '__main__':
    print("{}: This module intended for importing, not invoking it directly.".format(MYPROGNAME),
          file=sys.stderr)
    


    
