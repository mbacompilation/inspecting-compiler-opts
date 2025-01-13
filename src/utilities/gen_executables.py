#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from subprocess import call

"""
For all c files with embedded MBA in a given directory, 
create executables with the following compilers and options.

# input directory should contain all the files to be compiled.
# output directory is the intended output location.
Usage: gen_executables.py <input directory path> <output directory path> < "msvc" | "gcc" | "clang">

# generated filename format:
    inputfilename_compiler_optsetting[.exe if MSVC, .bin if Linux]

"""



# blank is no optimizations
# for each available compiler, for each of these settings, an executable will be generated
msvc_optim_settings = ["O1", ""]
gcc_optim_settings = ["-O3", ""]
clang_optim_settings = ["-O3", ""]

#
# O1
#check_output("cl " + inputFolder + f + " /Fe: " + outputo1filename + "_O1" + " /Z7 /O1", shell=True)

# O2
#check_output("cl " + inputFolder + f + " /Fe: " + outputo2filename + "_O2" + " /Z7 /O2", shell=True)

msvc_compile_string = "cl {input_filename} /{optimization} /Fe: {out_name} /Z7"
gcc_compile_string = "gcc {input_filename} {optimization} -o {out_name}"
clang_compile_string = "clang {input_filename} {optimization} -o {out_name}"


# take given compiler name from sysargs. If none given, try all compilers.
compiler_choice  = ""
compstr = ""
input_folder = ""
output_folder = ""

if (len(sys.argv)) < 3:
    print("Usage: gen_executables.py <input_folder> <output directory path> [msvc | gcc | clang]")
    exit()


    
input_folder = sys.argv[1]
output_folder = sys.argv[2]
compiler_choice = sys.argv[3]
optsettings = []
    

if compiler_choice == "msvc":
    compstr = msvc_compile_string
    optsettings = msvc_optim_settings
    
elif compiler_choice == "gcc":
    compstr = gcc_compile_string
    optsettings = gcc_optim_settings
    
elif compiler_choice == "clang":
    compstr = clang_compile_string
    optsettings = clang_optim_settings
    
else:
    print("Unrecognized compiler: " + compiler_choice + "\n")
    exit()
 



"""
# copy/pasted from gen_c:
 

if os.path.isdir(mba_filepath):
    # get all files in this dir and feed them through
    filenames = next(os.walk(mba_filepath), (None, None, []))[2] #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    for f in filenames:
        print("f is: " + f)
        mba_to_c_file(mba_filepath + "/" + f, out_c_folderpath)
""" 




if os.path.isdir(input_folder):
    filenames = next(os.walk(input_folder), (None, None, []))[2] #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    for f in filenames:
       if ".c" not in f and ".cpp" not in filenames:
           print("Invalid file: " + f + ", skipping")
           continue
       else:
        # for each optimization setting, run the compile string
        for setting in optsettings:
            # create output filename
            # file + compiler + optsetting
            outputfilename = f + " " + setting
            
            # create full output path
            outputfilepath = output_folder + "/" + outputfilename
            
            # format string with options
            # {input_filename} {optimization} -o {out_name}
            full_input_filepath = input_folder + "/" + f
            outfilename = f

            if ".c" in outfilename[-2:]:
                outfilename = outfilename[:-2]
            #outfilename = f.removesuffix(".c")
            outfilename += "_" + compiler_choice + "_" + setting.strip("-")
            
             
            command = compstr.format(input_filename = full_input_filepath, optimization = setting, out_name = output_folder + "/" + outfilename)
            
            # run the command and check for errors
            #print("f is: " + f)
            """
            subprocess.call(["ls", "-l"])
            """
            
            call(command, shell=True)
        
            
else:
    print("Error: please input name of folder which contains files to compile.")
    
    
    
    
print("Done!")
    



        


# https://docs.python.org/2/library/subprocess.html#subprocess.call
# result = subprocess.call(["ls", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


    


    



