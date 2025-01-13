#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from dataset import Dataset, Entry, ExprInfo, saveDataset
from sys import exit


"""
Note: this script does not take command line arguments. 
Edit the three variables below to adjust where to load MBA files.

"""


prepped_mba_folder = "../../dataset/prepped_mba_files/"
compiled_mba_folder = "../../dataset/post_compilation_mba/"
dataset_folder = "../../dataset/mba_full_dataset/"



asm_to_vars = {
    "param_1" : "x",
    "param_2" : "y",
    "param_3" : "z",
    "param_4" : "a",
    "param_5" : "b",
    "param_6" : "c",
    "param_7" : "d",
    "param_8" : "e",
    "param_9" : "f",
    
    # gcc and clang use these instead of param_4-6
    "in_ECX" : "a",
    "in_R8D" : "b",
    "in_R9D" : "c",
    
    }



def swapNames(line):
    
    """
    Transform all instances of param_*, in_r8, and in_r9 to their corresponding
    variable names in the post compilation output.
    
    # set up variables which map the output mba expressions to the ground truth variables
    # param order: x, y, z, a, b, c, d, e, f
    # if MSVC: param_1, param_2, param_3, param_4, param_5, param_6, param_7, param_8, param_9
    # elif gcc or clang: param_1, param_2, param_3, in_ECX, in_R8D, in_R9D, param_7, param_8, param_9
    
    """
    newline = line
    
    for item in asm_to_vars.items():
        newline = newline.replace(item[0], item[1])
        
    return newline
    



def createBaseDatasets():
    skipped_files = []
    datasetsByName = {}
    
    if os.path.isdir(prepped_mba_folder) == False:
       print("Could not open folder with base MBA info. Aborting. Folder path: " + compiled_mba_folder)
       exit()
    
    filenames = next(os.walk(prepped_mba_folder), (None, None, []))[2] #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    for f in filenames:
        
        dname = f.replace(".txt", "")
        if "gcc" in dname or "clang" in dname or "msvc" in dname or "lifted" in dname:
            print("Warning: it looks like you might be trying to load post compilation MBA into base MBA dataset.")
            print("Please check your folder path for prepped_mba_folder in init_mba_datasets.py")
            print("filename: " + f)
            
            
        entries = []
        
        try: 
            handle = open(prepped_mba_folder + "/" + f, 'r')
            
            for line in handle.readlines():
                # format: "2;(x | y);(x + (~ (x | (x ^ (~ y)))))"
                if "#" in line:
                    continue
                
                try:
                    line = swapNames(line)
                    line = line.replace("U", "")
                    entryNo, gtStr, mbaStr = line.split(";")
                    entryNo = entryNo.rstrip()
                    gtStr = gtStr.rstrip()
                    mbaStr = mbaStr.rstrip()
                    newEntry = Entry(num=int(entryNo), gt = ExprInfo(expr=gtStr), obf = ExprInfo(expr=mbaStr))
                    entries.append(newEntry)
                    
                except:
                    print("\nError trying to read line: " + line)
                    handle.close()
                    exit(0)
                    
        
        except:
            print("Could not open or read file: " + f)
            print("Skipping")
            skipped_files.append(f)
            
        datasetSaveLocation = dataset_folder + "/" + dname + ".json"
        datasetsByName[dname] = Dataset(name=dname, entries=entries, saveFilePath=datasetSaveLocation) #self, name="Unnamed Dataset", entries:list[Entry] = [], attrs = {})
        handle.close()
    
    
    print("Finished loading base MBA info for " + str(len(datasetsByName.items())) + " files. Skipped files: ")
    for s in skipped_files:
        print("\t" + s)

    return datasetsByName



def populateCompdInfo(datasetsToPopulate = []):
    if len(datasetsToPopulate) == 0:
        print("Was given 0 base datasets to populate compiled info. Exiting")
        exit(0)
        
    if os.path.isdir(compiled_mba_folder) == False:
        print("Could not open folder with base MBA info. Aborting. Folder path: " + compiled_mba_folder)
        exit(0)
        
        
    filenames = next(os.walk(compiled_mba_folder), (None, None, []))[2] #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    for f in filenames:
        # example filename: L1add_clang_O3_lifted_mba.txt
        # unoptimized: L1add_clang__lifted_mba.txt
        
        try:
            ds, compiler, option = f.split("_")[0:3]
            # Messed up the MSVC filename generation so have to catch this case
            if ".exe" in option:
                option = option.strip(".exe")
            
            if option == "":
                option = "default"
                
            
        except Exception as e:
            print("Invalid filename format for file: " + f + "; skipping")
            print(e)
            continue
        
        
   
        # compdmba dict key/name info
        
        if not ds in datasetsToPopulate:
            print("No corresponding dataset for file: " + f)
            print("skipping")
            continue
        
        curDataset = datasetsToPopulate[ds]
        print("loading dataset, with file: " + curDataset.name +", " + f)
        
        handle = open(compiled_mba_folder + "/" + f, 'r')
        
        try:
            for line in handle.readlines():
                line = swapNames(line)
                line = line.replace("U", "")
                #line format: "7;param_1 + param_2"
                entryno, expression = line.split(";")
                newComp = {compiler + "_" + option : ExprInfo(expr=expression.rstrip())}
                curDataset.addCompedInfoForEntry(entryno, newComp)
                
                
        except:
            print("\nError trying to read or place line: " + line)
            handle.close()
            exit(0)
        
        
    
    
           
        
        handle.close()
    
    return
    


datasetsByName = createBaseDatasets()
populateCompdInfo(datasetsByName)

for ds in datasetsByName.values():
    print("Saving dataset: " + ds.name)
    saveDataset(ds)
    
    
print("Finished saving all datasets")


    
