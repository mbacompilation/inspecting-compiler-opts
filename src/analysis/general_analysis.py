#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from enum import Enum
import dagNodes
from dataset import Dataset
from dataset import Entry
import dataset
import ast
import random


outputFolder = "../../mba_analysis_results"


# set up variables which map the output mba expressions to the ground truth variables
# param order: x, y, z, a, b, c, d, e, f
# if MSVC: param_1, param_2, param_3, param_4, param_5, param_6, param_7, param_8, param_9
# elif gcc or clang: param_1, param_2, param_3, param_4, param_5, param_6, param_7, param_8, param_9


def runAnalysis():
    # d. applyCalcAttrFunctionToAll(self, function, attributeName = "", overwrite=True, retValues = False):
    
    # load
    datasets = list(dataset.loadDatasetsFromFolder())

    # calc metrics
    for d in datasets:
        print("Performing calculations on: " + d.name)


        d.applyAttrFunctionToAllAcrossEntries(countOperations, attributeName="numOps", overwrite=True, retValues=False)
        d.applyAttrFunctionToAllAcrossEntries(getDepthLevelByParens, "nestedExprLevel")
        d.applyAttrFunctionToAllAcrossEntries(getNumDAGs, "numDAGs")
        d.applyAttrFunctionToAllAcrossEntries(genOpTypeDict, attributeName="opsPercentages")
        d.applyAttrFunctionToAllAcrossEntries(getPercentageTermsWhichCancel, attributeName="percentageDAGsCancel")

        # save inside loop
        dataset.saveDataset(d)
    
        
    print("Done! Saved datasets")
    return


def runDatasetStats():
    datasets = list(dataset.loadDatasetsFromFolder())

    # calc metrics
    for d in datasets:
        print("Generating dataset stats on: " + d.name)


        # signature: function, attributeName=None, overwrite=True, save=True, retValue = False
        d.calcDatasetAttr(getNumChangedInfo, attributeName = "numChangedInfo")

        calcPercentSizeDecreaseForEntriesByOps(d.entries)
        d.calcDatasetAttr(calcDatasetAveragePercentDecreaseByOps, attributeName="avgDecreaseByOps")
        d.calcDatasetAttr(calcDatasetAverageOpTypePercentage, attributeName="avgOpPercentage")

        d.calcDatasetAttr(calcAvgPercentDAGsCancel, attributeName="avgPercentDAGsCancel")

        d.calcDatasetAttr(calcAvgDagProportion, attributeName="avgUniqueProportion")
        d.calcDatasetAttr(getNumChangedInfo, attributeName="numChangedInfo")
        print("Finished for: " + d.name)

        # save inside loop
        dataset.saveDataset(d)

    print("Done! Saved datasets")
    return



def printInfo():
    datasets = list(dataset.loadDatasetsFromFolder())
    for d in datasets:
        print("Dataset: " + d.name)
        #d.printDatasetAttrsWithFunction(printNumChangedByOps)

        printAvgPercentDecreaseForOptCompilersByOps(d.attrs)

    return




# dataset-level functions:

def getNumChangedInfo(entries:[Entry]):
    infoDict = {}

    # init dictionary
    for compilername in entries[0].compiled_mba.keys():
        infoDict[compilername] = {
            "numUnchanged" : 0,
            "numReduced" : 0,
            "numLargerThanMBA" : 0,
            "numSmallerThanGT" : 0,
            "numFullySimplified" : 0,
            "numDAGsSameAsMBA" : 0,
            "numDAGsLargerThanMBA" : 0,
            "numDAGsSmallerThanGT" : 0,
            "numDagsReduced" : 0
        }

    for entry in entries:
        for compilername, exprInfo in entry.compiled_mba.items():
            attrs = exprInfo.attributes
            numOps = attrs["numOps"]
            numDAGs = attrs["numDAGs"]

            gtOps = entry.gt.attributes["numOps"]
            gtDAGs = entry.gt.attributes["numDAGs"]

            mbaOps = entry.mba.attributes["numOps"]
            mbaDAGs = entry.mba.attributes["numDAGs"]

            if numOps > mbaOps:
                infoDict[compilername]["numLargerThanMBA"] += 1
            elif numOps == mbaOps:
                infoDict[compilername]["numUnchanged"] += 1
            elif numOps < mbaOps:
                infoDict[compilername]["numReduced"] += 1


            if numOps == gtOps:
                infoDict[compilername]["numFullySimplified"] += 1
            elif numOps < gtOps:
                infoDict[compilername]["numSmallerThanGT"] += 1


            if numDAGs == mbaDAGs:
                infoDict[compilername]["numDAGsSameAsMBA"] += 1
            elif numDAGs < mbaDAGs:
                infoDict[compilername]["numDagsReduced"] += 1
            elif numDAGs > mbaDAGs:
                infoDict[compilername]["numDAGsLargerThanMBA"] += 1



            if numDAGs < gtDAGs:
                infoDict[compilername]["numDAGsSmallerThanGT"] += 1

    return infoDict



def printNumChangedByDAGs(attrDict:dict):
    try:
        info = attrDict["numChangedInfo"]
    except KeyError:
        print("Error: key: numChangedInfo does not exist in dataset attributes")
        return

    """
    infoDict[compilername] = {
           "numUnchanged": 40,
                "numReduced": 926,
                "numLargerThanMBA": 42,
                "numSmallerThanGT": 0,
                "numFullySimplified": 1,
                "numDAGsSameAsMBA": 83,
                "numDAGsLargerThanMBA": 94,
                "numDAGsSmallerThanGT": 0,
                "numDagsReduced": 831
        }
    """

    # gcc, gcc O3, Clang, Clang O3, MSVC, MSVC O1

    # Loki AND D30 (1000)&    200  800 &  369  631 &  370 / 630 & 0 / 933  &  625 / 375  & s - s\\
    # DagsSameAsMBA / DAGsReduced

    infoStr = ""
    for compilername in ["gcc_default", "gcc_O3", "clang_default", "clang_O3", "msvc_default", "msvc_O1"]:
        stats = info[compilername]
        numFullySimplified = stats["numFullySimplified"]
        # Don't double-count the reductions
        numReduced = stats["numReduced"] - numFullySimplified

        infoStr += str(numFullySimplified) + " -- " + str(numReduced) + " & "


    print(infoStr)
    return


def printNumChangedByOps(attrDict:dict):
    try:
        info = attrDict["numChangedInfo"]
    except KeyError:
        print("Error: key: numChangedInfo does not exist in dataset attributes")
        return

    """
    infoDict[compilername] = {
           "numUnchanged": 40,
                "numReduced": 926,
                "numLargerThanMBA": 42,
                "numSmallerThanGT": 0,
                "numFullySimplified": 1,
                "numDAGsSameAsMBA": 83,
                "numDAGsLargerThanMBA": 94,
                "numDAGsSmallerThanGT": 0,
                "numDagsReduced": 831
        }
    """

    # gcc, gcc O3, Clang, Clang O3, MSVC, MSVC O1

    # Loki AND D30 (1000)&    200  800 &  369  631 &  370 / 630 & 0 / 933  &  625 / 375  & s - s\\
    # DagsSameAsMBA / DAGsReduced

    infoStr = ""
    for compilername in ["gcc_default", "gcc_O3", "clang_default", "clang_O3", "msvc_default", "msvc_O1"]:
        stats = info[compilername]
        infoStr += str(stats["numFullySimplified"]) + " -- " + str(stats["numReduced"]) + " & "


    print(infoStr)
    return


def printAvgPercentDecreaseForOptCompilersByOps(attrDict:dict):
    print("Compiler order: gcc_O3, clang_O3, msvc_O1")

    decreaseDict = attrDict["avgDecreaseByOps"]

    infoStr = ""
    for key in ["gcc_O3_avgPercentDecreaseByOps",
                "clang_O3_avgPercentDecreaseByOps",
                "msvc_O1_avgPercentDecreaseByOps"]:

        avgDecrease = decreaseDict[key]
        infoStr += str(round(avgDecrease, 3)) + "\%" + " & "

    print(infoStr)
    return

#### expression-level functions:
# usage: # applyAttrFunctionForCompedExpressions(self, function, attributeName, overwrite = True, yieldValues = False):
# signature for function ref: (expr:str)
# signature for applyToCompd: gtStr = self.gt.expr, mbaStr = self.mba.expr, exprStr = compdExpr[1].expr)

def countOperations(exprStr:str):
    num = None
    num = dagNodes.opsFromMBAString(exprStr)
    return num

def genOpTypeDict(exprStr:str):
    opsDict = {
        "arithmetic" : 0.0,
        "mul" : 0.0,
        "bitwise" : 0.0
    }

    opsPercentage = {
        "arithmetic" : 0.0,
        "mul" : 0.0,
        "bitwise" : 0.0
    }


    opsDict["arithmetic"] = exprStr.count("+") + exprStr.count("-")
    opsDict["mul"] = exprStr.count("*")
    opsDict["bitwise"] = exprStr.count("^") + \
                            exprStr.count(">>") + exprStr.count("<<") + \
                            exprStr.count("&") + exprStr.count("|") + \
                            exprStr.count("~")

    totalOps = dagNodes.opsFromMBAString(exprStr)

    if opsDict["arithmetic"] > 0:
        opsPercentage["arithmetic"] = opsDict["arithmetic"] / totalOps * 100
    if opsDict["mul"] > 0:
        opsPercentage["mul"] = opsDict["mul"] / totalOps * 100
    if opsDict["bitwise"] > 0:
        opsPercentage["bitwise"] = opsDict["bitwise"] / totalOps * 100

    return opsPercentage


def checkTermCancels(exprStr:str):
    countTermEq = True
    countTermZero = True

    for i in range(0, 100):
        x = (random.randint(0, 1000))
        y = (random.randint(0, 1000))
        z = (random.randint(0, 1000))
        a = (random.randint(0, 1000))
        b = (random.randint(0, 1000))
        c = (random.randint(0, 1000))
        d = (random.randint(0, 1000))
        e = (random.randint(0, 1000))
        f = (random.randint(0, 1000))

        countTermEq = True
        countTermZero = True

        res = eval(exprStr)

        if res not in [x, y, z, a, b, c, d, e, f]:
            countTermEq = False

        if res != 0:
           countTermZero = False

    return countTermEq or countTermZero

def getPercentageTermsWhichCancel(exprStr:str):
    # gets the percentage of DAG nodes, not total operations/size
    # a term cancels if it equals 0 or an input
    # for example, from qsynth: (~c & c)

    dagDict = dagNodes.dagNodeDictFromMBAString(exprStr)

    numDags = len(dagDict)
    numTermsCancel = 0
    percentage = 0.0

    for key in dagDict:
        keyStr = ast.unparse(key)
        numTermsCancel += checkTermCancels(keyStr)

    if numTermsCancel >= 0 and numDags > 0:
        percentage = numTermsCancel / numDags * 100

    return percentage



def checkEqualityByOutputs(exprStr:str, gtStr:str):
    for i in range(0, 100):
        x = (random.randint(0, 1000))
        y = (random.randint(0, 1000))
        z = (random.randint(0, 1000))
        a = (random.randint(0, 1000))
        b = (random.randint(0, 1000))
        c = (random.randint(0, 1000))
        d = (random.randint(0, 1000))
        e = (random.randint(0, 1000))
        f = (random.randint(0, 1000))

        if eval(exprStr) != eval(gtStr):
            return False
    return True

def getCombinedAvgOpTypes(attrDict:dict):
    # Average together the averages from the op types for each compiler,
    # generating one average per dataset

    percentageDict = attrDict["avgOpPercentage"]
    infoDict = {}
    arithStatName = "_avgArithPercentage"
    mulStatName = "_avgMulPercent"
    booleanStatName = "_avgBitwisePercent"

    arithPercentSum = 0.0
    mulPercentSum = 0.0
    bitwisePercentSum = 0.0



    for name in ["gcc_O3", "clang_O3", "msvc_O1"]:
        arithPercentSum += percentageDict[name + arithStatName]
        mulPercentSum += percentageDict[name + mulStatName]
        bitwisePercentSum += percentageDict[name + booleanStatName]


    infoDict["overall_avg_arith"] = arithPercentSum / 3
    infoDict["overall_avg_mul"] = mulPercentSum / 3
    infoDict["overall_bitwise"] = bitwisePercentSum / 3


    # setting dictionary directly - nothing to return here
    attrDict["condensed_compiled_op_types"] = infoDict
    return

def getNumDAGs(exprStr:str):
    num = len(dagNodes.dagNodeDictFromMBAString(exprStr).keys())
    return num

def getDepthLevelByParens(exprStr:str):
    result = dagNodes.getMaxNestedLevelFromMBAStr(exprStr)
    return result


def calcPercentSizeDecreaseForEntriesByOps(entries:[Entry]):
    # Calculate percent decrease, for those entries which are smaller after
    # compilation.

    # For each entry:
    for entry in entries:
        # Set the mbaOps
        mbaOps = entry.mba.attributes["numOps"]
        compiledExprs = entry.compiled_mba
        # For each compiled expression:
        for compilerName, compdExprInfo in compiledExprs.items():
            # get the compd ops
            compdOps = compdExprInfo.attributes["numOps"]
            percentDecrease = (mbaOps - compdOps) / abs(mbaOps) * 100
            # Store the percentDecrease in expr attrs
            compdExprInfo.attributes["percentDecreaseByOps"] = percentDecrease
    return


def calcAvgPercentDAGsCancel(entries:[Entry]):
    # calculates in DAG nodes
    infoDict = {}

    gtPercentCancelsSum = 0
    mbaPercentCancelsSum = 0

    for e in entries:
        gtPercentCancelsSum += e.gt.attributes["percentageDAGsCancel"]
        mbaPercentCancelsSum += e.mba.attributes["percentageDAGsCancel"]

    infoDict["mba_percentCancels"] = mbaPercentCancelsSum / len(entries)
    infoDict["gt_percentCancels"] = gtPercentCancelsSum / len(entries)

    for compilerName in entries[0].compiled_mba.keys():
        percentCancelsSum = 0

        for entry in entries:
            percentCancelsSum += entry.compiled_mba[compilerName].attributes["percentageDAGsCancel"]

        infoDict[compilerName + "percentageDAGsCancel"] = percentCancelsSum / len(entries)

    return infoDict


def calcAvgDagProportion(entries:[Entry]):
    infoDict = {}
    mbaRatioSum = 0

    for e in entries:
        # mba ops, dags
        mbaOps = e.mba.attributes["numOps"]
        mbaDAGs = e.mba.attributes["numDAGs"]
        ratio = mbaDAGs/mbaOps * 100.0

        mbaRatioSum += ratio

    avgRatio = mbaRatioSum / len(entries)
    infoDict["mba_avgProportionUnique"] = avgRatio


    for compilerName in entries[0].compiled_mba.keys():
        ratioSum = 0

        for entry in entries:
            numDAGs = entry.compiled_mba[compilerName].attributes["numDAGs"]
            numOps = entry.compiled_mba[compilerName].attributes["numOps"]
            if numOps > 0:
                ratio = numDAGs/numOps * 100.0
            else:
                ratio = 1

            ratioSum += ratio
        infoDict[compilerName + "_avgProportionUnique"] = ratioSum / len(entries)
    return infoDict



def calcDatasetAveragePercentDecreaseByOps(entries:[Entry]):
    infoDict = {}

    for compilerName in entries[0].compiled_mba.keys():
        percentDecreaseSum = 0
        for entry in entries:
            ops = entry.compiled_mba[compilerName].attributes["numOps"]
            mbaOps = entry.mba.attributes["numOps"]
            gtOps = entry.gt.attributes["numOps"]
            # Don't include those which are equal or larger, and don't include
            # Those which are fully reduced (separate table in the paper)
            if ops < mbaOps and ops != gtOps:
                percentDecreaseSum += entry.compiled_mba[compilerName].attributes["percentDecreaseByOps"]

        avePercentDecrease = percentDecreaseSum / len(entries)
        infoDict[compilerName + "_avgPercentDecreaseByOps"] = avePercentDecrease

    return infoDict


def calcDatasetAverageOpTypePercentage(entries:[Entry]):
    infoDict = {}

    mbaPercentArithSum = 0
    mbaPercentMulSum = 0
    mbaPercentBitwiseSum = 0

    gtPercentArithSum = 0
    gtPercentMulSum = 0
    gtPercentBitwiseSum = 0

    for e in entries:
        mbaPercentArithSum += e.mba.attributes["opsPercentages"]["arithmetic"]
        mbaPercentMulSum += e.mba.attributes["opsPercentages"]["mul"]
        mbaPercentBitwiseSum += e.mba.attributes["opsPercentages"]["bitwise"]

        gtPercentArithSum += e.gt.attributes["opsPercentages"]["arithmetic"]
        gtPercentMulSum += e.gt.attributes["opsPercentages"]["mul"]
        gtPercentBitwiseSum += e.gt.attributes["opsPercentages"]["bitwise"]


    avgArithPercent = mbaPercentArithSum / len(entries)
    avgMulPercent = mbaPercentMulSum / len(entries)
    avgBitwisePercent = mbaPercentBitwiseSum / len(entries)

    infoDict["mba_avgArithPercentage"] = avgArithPercent
    infoDict["mba_avgMulPercent"] = avgMulPercent
    infoDict["mba_avgBitwisePercent"] = avgBitwisePercent

    infoDict["gt_avgArithPercentage"] = gtPercentArithSum / len(entries)
    infoDict["gt_avgMulPercent"] = gtPercentMulSum / len(entries)
    infoDict["gt_avgBitwisePercent"] = gtPercentBitwiseSum / len(entries)


    for compilerName in entries[0].compiled_mba.keys():
        percentArithSum = 0
        percentMulSum = 0
        percentBitwiseSum = 0

        for entry in entries:
            percentArithSum += entry.compiled_mba[compilerName].attributes["opsPercentages"]["arithmetic"]
            percentMulSum += entry.compiled_mba[compilerName].attributes["opsPercentages"]["mul"]
            percentBitwiseSum += entry.compiled_mba[compilerName].attributes["opsPercentages"]["bitwise"]

        avgArithPercent = percentArithSum / len(entries)
        avgMulPercent = percentMulSum / len(entries)
        avgBitwisePercent = percentBitwiseSum / len(entries)

        infoDict[compilerName + "_avgArithPercentage"] = avgArithPercent
        infoDict[compilerName + "_avgMulPercent"] = avgMulPercent
        infoDict[compilerName + "_avgBitwisePercent"] = avgBitwisePercent

    return infoDict


# ended up not adding to paper - did not finish fully exploring
def getDAGOccurencesAcrossDataset(dataset:Dataset):
    mbaMasterDict = {}
    gtMasterDict = {}

    #gtMasterExprDict = {}
    #mbaMasterExprDict = {}

    for entry in dataset.entries:
        gtExprDict = dagNodes.dagNodeDictFromMBAString(entry.gt.expr)
        mbaExprDict = dagNodes.dagNodeDictFromMBAString(entry.mba.expr)

        ######
        """
        for key, value in gtExprDict.items():
            EStr = ast.unparsed(key)
            gtExprDict.update({EStr: value})

        for key, value in mbaExprDict.items():
            EStr = ast.unparsed(key)
            mbaExprDict.update({EStr: value})
        """
        ##########

        # exclude expressions smaller than 5 characters, eg "~x" or "y | x"
        for key in gtExprDict:
            keyStr = ast.unparse(key)
            if (len(keyStr) < 5):
                continue

            foundKey = False
            for keyMaster in gtMasterDict:
                #if dagNodes.checkEquals(key, keyMaster):
                if keyStr == keyMaster:
                    gtMasterDict[keyMaster] += 1
                    foundKey = True
            if not foundKey:
                gtMasterDict[keyStr] = 1

        for key in mbaExprDict:
            keyStr = ast.unparse(key)
            if (len(keyStr) < 5):
                continue
            foundKey = False
            for keyMaster in mbaMasterDict:
                #if dagNodes.checkEquals(key, keyMaster):
                if keyStr == keyMaster:
                    mbaMasterDict[keyMaster] += 1
                    foundKey = True

            if not foundKey:
                mbaMasterDict[keyStr] = 1


    try:
        print("\nDebug: master GT dictionary: largest number of occurrences:")

        print(str(max(gtMasterDict, key=lambda k: gtMasterDict[k])))
        print("\nDebug: size of master dictionary: " + str(len(gtMasterDict)))
    except Exception as e:
        print("Got exception: " + str(e))

    try:

        print("\nDebug: largest term, and its occurrences:")
        largestKey = max(list(mbaMasterDict.keys()), key=len)
        print("Term: " + largestKey + "; occurrences: " + str(mbaMasterDict[largestKey]))

        print("\nDebug: master MBA dictionary: largest number of occurrences:")
        maxKey = (max(mbaMasterDict, key=mbaMasterDict.get))
        print("Key: " + maxKey + "; occurrences: " + str(mbaMasterDict[maxKey]))

        print("\nDebug: size of master dictionary: " + str(len(mbaMasterDict)))
    except Exception as e:
        print("Got exception: " + str(e))


    dataset.addDatasetAttr("mbaMasterDict", mbaMasterDict)

def getSharedSubtermsForCompdExpr(gtStr="", mbaStr = "", exprStr=""):
    if gtStr == "" or mbaStr == "" or exprStr == "":
        print("error in getShared: was given empty parameter")
        exit(0)
    
    return



##### dataset level functions
# input: [Entry]
def sampleDatasetStat():
    datasets = list(dataset.loadDatasetsFromFolder())

    # calc metrics
    for d in datasets:
        if d.name != "LD1" and d.name != "LD30":
            continue
        print("Generating dataset stats on: " + d.name)

        # Have run:

        # to run:
        # signature: function, attributeName=None, overwrite=True, save=True, retValue = False
        d.calcDatasetAttr(getNumChangedInfo, attributeName = "numChangedInfo")



        print("Finished for: " + d.name)

        # save inside loop
        dataset.saveDataset(d)

    print("Done! Saved datasets")
    return


    return

runAnalysis()
runDatasetStats()

