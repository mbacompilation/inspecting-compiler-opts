#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from sys import exit
import os
import signal

"""
classes:

Dataset_entry:
.ground:expr_info ( the unobfuscated MBA )
.mba_obf:expr_info ( the obfuscated MBA from the original dataset, uncompiled)
.compiled_mba:dict[str(name): expr_info] ( info about compiled MBA, per compiler and optimization setting
.entry_no:int 


expr_info:
.expr:str
.attributes:dict{str:<varying>} ex: ["term depth" : 5] or ["largest term" : "x * y + 3"]
attributes val can also be a dictionary 

"""


timeoutLength = 12000 # seconds
defaultFolder = "../../dataset/paper_dataset/"

class ExprInfo:
    
    def __init__(self, inputDict={}, expr="", attributes=None):
        # If there's a dictionary given, assuming we're reading from JSON and 
        # need to parse it; otherwise, use the given attributes and expr directly.
        
        #init these anyways
        self.expr:str = expr
        self.attributes:dict = {}
        
        if inputDict != {}:
            self.expr = inputDict["expr"]
            self.attributes = inputDict["attributes"]
        else:
            self.expr = expr
            if attributes is None:
                self.attributes = {}
            else:
                self.attributes = attributes
            
    
    
    def makeSampleData(self):
        self.expr = "x + y"
        self.attributes["ops"] = 1
        self.attributes["depth"] = 1
        
    def makeSampleData2(self):
        self.expr = "x + y | z"
        self.attributes["ops"] = 2
        self.attributes["depth"] = 2
        
    def __str__(self):
        retStr = "ExprInfo: "
        retStr += self.expr
        for key, val in self.attributes.items():
            retStr += ("\nAttribute: " + "'" + str(key) + "': " + str(val))
            
        return retStr
    
    def removeAttr(self, name):
        try:
            del self.attributes[name]
        except KeyError:
            return


        
        
    def addAttr(self, newAttrName, newAttrVal, overwrite = True):
        if newAttrName in self.attributes and overwrite == False:
            print("Error: overwriting attribute named: " + newAttrName + "; aborting")
            exit(0)
            
        self.attributes[newAttrName] = newAttrVal
    

class Entry:
    def __init__(self, inputDict=None, num=0, gt=None, obf=None, compiled_mba=None):
        if inputDict == None:
            self.num:int = num
            self.gt:ExprInfo = gt
            self.mba:ExprInfo = obf
            if compiled_mba is None:
                self.compiled_mba:{} = {} # dict: "compiler name":ExprInfo
                # example: {"gcc__O3": ExprInfo("x + y")}
            else:
                self.compiled_mba = compiled_mba
            
        else:
            self.num= int(inputDict["num"])
            self.gt = ExprInfo(inputDict["gt"])
            self.mba = ExprInfo(inputDict["mba"])
            
            self.compiled_mba = {}
            
            for compname, exprinfo in inputDict["compiled_mba"].items():
                self.compiled_mba[compname] = ExprInfo(inputDict=exprinfo)
                        
    
    def setGT(self, gtIn):
        self.gt = gtIn
        self.num = 1
        
    def addCompedMBAInfo(self, infoIn:dict):
        if not isinstance(infoIn, dict):
            print("Error: Incorrect type for adding compiled MBA info to existing entry; type: " + type(infoIn).__name__)
            exit(1)
        
        self.compiled_mba.update(infoIn)
        
        
        
    # takes a reference to a function expecting (expr:str).  
    def applyCalcAttrFunctionToAll(self, function, attributeName = "", overwrite=True, retValues = False):
        vals = [self.num]
        
        # gt
        result = None
        try:
            with timeout(timeoutLength):
                result = function(exprStr = self.gt.expr)
        except TimeoutError:
            result = "timeout"
        if attributeName != "":
            self.gt.addAttr(attributeName, result, overwrite)
        
        
        if retValues:
            vals.append(["gt", result])
            
        # mba
        result = None
        try:
            with timeout(timeoutLength):
                result = function(exprStr = self.mba.expr)
        except TimeoutError:
            result = "timeout"
        if attributeName != "":
            self.mba.addAttr(attributeName, result, overwrite)
        
        if retValues:
            vals.append(["mba", result])
        
       
        # compd expressions
        
        for compdExpr in self.compiled_mba.items():
            result = None
            try:
                with timeout(timeoutLength):
                    result = function(exprStr = compdExpr[1].expr)
            except TimeoutError:
                result = "timeout"
            
            
            if attributeName != "":
                compdExpr[1].addAttr(attributeName, result, overwrite)
                
            if retValues:
                vals.append([compdExpr[0], result])
                 
        return vals
                
        
        
    
    
    # takes a reference to a function expecting (gtExpr:str, mbaExpr:str, and compiledExpr:str)
    def applyAttrFunctionForCompedExpressions(self, function, attributeName = "", overwrite = True, retValues = False):
        vals = [self.num]
        
        for compdExpr in self.compiled_mba.items():
            result = None
            try:
                with timeout(timeoutLength):
                    result = function(gtStr = self.gt.expr, mbaStr = self.mba.expr, compdStr = compdExpr[1].expr)
            except TimeoutError:
                result = "timeout"
            
            if attributeName != "":
                compdExpr[1].addAttr(attributeName, result, overwrite)
                
            if retValues:
                vals.append([compdExpr[0], result])

        return vals
        
        
        
    def makeSampleData(self):
        self.num = 2
        sampleExpr = ExprInfo()
        sampleExpr.makeSampleData()
        self.gt = sampleExpr
        
        sampleExpr2 = ExprInfo()
        sampleExpr2.makeSampleData()
        self.mba = sampleExpr2
        
        self.compiled_mba["comp_O1"] = sampleExpr2
        
        
    def __str__(self):
        
        retStr = "\nEntry: " + str(self.num) + \
            "\nGT Expr Str: " + self.gt.expr + \
                "\nMBA Expr Str: " + self.mba.expr
                
        for compname, info in self.compiled_mba.items():
            retStr += "\n" + compname + ": \n" + str(info)
                
                
        return retStr
    
    def removeAttr(self, name):
        self.gt.removeAttr(name)
        self.mba.removeAttr(name)
        
        for info in self.compiled_mba.values():
            info.removeAttr(name)
        
        
        
        
        
class Dataset:
    
    def __init__(self, name="Unnamed Dataset", entries:list[Entry] = None, attrs = None, saveFilePath=None):
        self.name:str = name
        self.entries = []
        self.attrs = {}
        self.saveFilePath = ""

        if attrs is not None:
            self.attrs = attrs
        
        if not saveFilePath is None:
            self.saveFilePath = saveFilePath
        
        if len(entries) > 0 and isinstance(entries[0], Entry):
            self.entries = entries
        else:
            for e in entries:
                self.entries.append(Entry(inputDict=e))        
                
        return
    
    def getName(self):
        return self.name
    
    
    def addEntry(self, new_item:Entry):
        self.entries.add(new_item)
        return
    
    def getEntryWithNum(self, entryNo):
        # This should correspond to index-1, warn if not and then search
        entryNo = int(entryNo)
        expectedIndex = entryNo - 1
        
        curEntry = self.entries[expectedIndex]
        
        if curEntry.num == entryNo:
            return curEntry
        
        
        print("Warning: stored entries for dataset " + self.name + " might be out of order.")

        
        for entry in self.entries:
            if entry.num == entryNo:
                return entry
            
            
        # at this point, no entry found.
        print("Error: cannot find request entry: " + str(entryNo) + " in dataset: " + self.name)
        exit(0)
        
        
    def applyAttrFunctionToAllAcrossEntries(self, function, attributeName, overwrite=True, retValues = False):
        vals = []
        
        for e in self.entries:
            res = e.applyCalcAttrFunctionToAll(function, attributeName, overwrite=overwrite, retValues = retValues)
            
            if retValues:
                vals.append(res) 
                
        return vals
                
                
    def applyAttrFunctionToCompdAcrossEntries(self, function, attributeName, overwrite=True, retValues = False):
        vals = []
        for e in self.entries:
            res = e.applyAttrFunctionForCompedExpressions(function, attributeName, overwrite, retValues)
            
            if retValues:
                vals.append(res)
                
        return vals
    
    
    def calcDatasetAttr(self, function, attributeName=None, overwrite=True, save=True, retValue = False):
        res = function(self.entries)
        
        if (save):
            if attributeName is None:
                print("Error: cannot save dataset attribute with no name given")
                exit(0)
                
            if attributeName in self.attrs and overwrite == False:
                print("Error saving attribute to dataset: " + attributeName + "exists,")
                print("but overwrite setting is false")
                exit(0)

            self.attrs[attributeName] = res
        if retValue:
            return res
        
        
        return
    
    
    def printDatasetAttrsWithFunction(self, function):
        function(self.attrs)
        
        return
    
    
        
    
    def addCompedInfoForEntry(self, entryNo, compedInfo):
        entryNo = int(entryNo)
        e = self.getEntryWithNum(entryNo)
        e.addCompedMBAInfo(compedInfo)
        
        return

    def printAttrNames(self):
        for a in self.attrs.keys():
            print("\n'" + a + "'")


    def printAttrWithName(self, name):
        if name in self.attrs:
            print(self.attrs[name])
        else:
            print("Error: '" + name + "' does not exist in dataset attributes")
            print("\t dataset name: " + self.name)
        
    def printAllEntries(self):
        for e in self.entries:
            print(e.__str__())
            print("\n")
        
        
    def __str__(self):
        retStr = "Dataset name: " + self.name + "\nNumber of entries: " + str(len(self.entries))
        for a, val in self.attrs.items():
            print("Attribute: " + "'" + a + "': " + val)
        retStr += "\n"
        return retStr

    def getAverageAttr(self, name):
        
        pass
    
    def removeAttributeForAllEntries(self, name):
        for e in self.entries:
            e.removeAttr(name)


    def addDatasetAttr(self, attrName = None, item = None):
        if attrName is None:
            print("Error: cannot save dataset attribute with no name given")
            exit(0)

        if item is None:
            print("Error: cannot save dataset attribute with no item given")
            exit(0)

        self.attrs[attrName] = item

            
  
# general: utility functions
def saveDatasetToFile(filepath, ds):
    if isinstance(ds, Dataset) == False:
        print("saveDatasetToFile: was given instance of: " + ds.type().__name__)
        print("Not saving")
        return
        
        
    try:
        with open(filepath, 'w') as f:
            outdict = json.dumps(ds, default=lambda o: o.__dict__, indent=4)
            f.write(outdict)
            
        f.close()
    except Exception as e:
        print("Could not save dataset: " + ds.getName())
        print("\n")
        print(e)
        return
        
    
def loadDatasetFromFile(filepath):
    try:
        with open(filepath, 'r') as openfile:
            #json_object = json.load(openfile)
            decoded_dataset = Dataset(**json.load(openfile))
            
    except Exception as e:
        print("Could not read dataset from file: " + filepath)
        print("\n")
        print(e)
        return None
    
    return decoded_dataset

def loadDatasetWithNameFromDefaultLocation( name):
    if ".json" not in name:
        name = name + ".json"

    return loadDatasetFromFile(defaultFolder + "/" + name)


def loadDatasetsFromFolder(folderpath=defaultFolder):
    if os.path.isdir(folderpath) == False:
       print("Could not open folder with datasets, or path is not a folder. Aborting. Folder path: " + folderpath)
       exit()
    
    filenames = next(os.walk(folderpath), (None, None, []))[2] #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
    for f in filenames:
        if ".json" in f:
            try:
                ds = loadDatasetFromFile(folderpath + "/" + f)
                yield ds
                
            except Exception as e:
                "Could not load from file: " + f + ". Skipping"
                print("Exception:")
                print(e)
                
    
    

def saveDataset(ds):
    if isinstance(ds, Dataset) == False:
        print("saveDatasetToFile: was given instance of: " + ds.type().__name__)
        print("Not saving")
        return
        
        
    if ds.saveFilePath == "":
        print("No filepath saved for dataset: " + ds.getName() + ". Cannot save.")
        return
    
    try:
        with open(ds.saveFilePath, 'w') as f:
            outdict = json.dumps(ds, default=lambda o: o.__dict__, indent=4)
            f.write(outdict)
            
        f.close()
        
    except Exception as e:
        print("Could not save dataset: " + ds.getName())
        print("\n")
        print(e)
        return


# https://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish
class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
    


