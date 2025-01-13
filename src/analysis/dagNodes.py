#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataset import *

import ast 
from sys import exit

############################################# General String tools #############################################
def sanitizeLine(line):
    line = line.replace("\n", "")
    line = line.replace("U", "")
    line = ' '.join(line.split())
    return line



############################################# AST tools #############################################
# https://stackoverflow.com/questions/1128234/how-can-i-obtain-the-full-ast-in-python
def depth_ast(root):
     return 1 + max(map(depth_ast, ast.iter_child_nodes(root)),
                    default = 0)




def checkEquals(node1, node2): 
    # possible types of nodes:
    # UnaryOp, BinaryOp, Name
    if (type(node1) != type(node2)):
        #print("\nInside FAILED first type check")
        return False
    
    # if module, we're at the very top of the tree - break these down to Expr.op level
    if (type(node1) == ast.Module):
        #print("debug: inside module check")
        newnode1 = node1.body[0].value
        newnode2 = node2.body[0].value
        return checkEquals(newnode1, newnode2)

    # if they are both UnaryOp...
    # operand, op
    if (type(node1) == ast.UnaryOp):
        #print("\nDebug: in unary op")
        #print("\nnode1.op: " + str(node1.op))
        #print("\nnode2.op: " + str(node2.op))
        # check that the operation is the same. If it is, then check operand.
        if (type(node1.op) == type(node2.op)):
            return (checkEquals(node1.operand, node2.operand))
        else:
            return False
        
    # binary op:
    # op, left, right
    elif (type(node1) == ast.BinOp):
        #print("\nDebug: in binary op")
        #print("\nnode1.op: " + str(node1.op))
        #print("\nnode2.op: " + str(node2.op))
        # check operation, if true then check left and right children
        if (type(node1.op) == type(node2.op)):
            return (checkEquals(node1.left, node2.left) and checkEquals(node1.right, node2.right))
        
    elif (type(node1) == ast.Name):
        #print("\nDebug: in Name op")
        # Name - attr: id
        # leaf node. check string equivalents.
        if (node1.id == node2.id):
            return True

    elif(type(node1) == ast.Constant):
        #print("\nDebug: in Constant op")
        # Constant - attr: value
        # leaf node.
        if (node1.value == node2.value):
            return True
        
    return False


############################################# DAG and OPS counting #############################################
def getTopOpNodeFromAST(tree):
    if (type(tree) == ast.Module):
        return tree.body[0].value
    else:
        print("\nERROR: getTopOpNode: module not given. type is: " + str(type(tree)))
        exit(0)

    


# just gets the DAG nodes for a expression. Expects no newlines or duplicate spaces.
# dictionary: nodes and how many times they appear
# same thing as getting OPS.
# return value: dictionary of all operations and how many times they appear.
# the len of the dict is the number of ops.
# the keys are the DAGs. 
# if not given a node dictionary, return a new one.
def dagNodeDictFromMBAString(line, inputDict = None):
    # input example: "(x + y) | x"
    # get the AST first
    # to append d2 to d1 for example: d1.update(d2)
    nodeDict = {}
    if inputDict != None:
        nodeDict = inputDict

    # dict contains all operations in the tree. So for example given x + y + z
    # we will have: x + y + z, y + z, x + y

    fulltree = ast.parse(line)
    
    gen = ast.walk(fulltree)
    for i in gen:
        if (type(i) == ast.UnaryOp
            or type(i) == ast.BinOp):
            # we are at an operation
            # if it's in the dictionary, increment the dict count

            # check value equivalence not pointer equivalence - iterate through all dict members 
            # and checkEquals

            # if dict is empty:
            if not nodeDict:
                nodeDict[i] = 1
            else:
                found = False
                for k, v in nodeDict.items():
                    if checkEquals(i, k):
                        nodeDict[k] = v + 1
                        found = True
                        break
                
                if found == False:
                    nodeDict[i] = 1
    return nodeDict




def getNumOps(tree):
    sum = 0
    for x in ast.walk(tree):
        if isinstance(x, ast.BinOp) or isinstance(x, ast.UnaryOp):
            sum = sum + 1
        
    return sum


# input:single expression; gets ops, not dags, counts duplicates
def opsFromMBAString(exprStr = ""):

    try:
        return getNumOps(ast.parse(exprStr))
    except Exception as e:
        print("OpsFromMBAString failed on expr: " + exprStr)
        print(e)
        exit(0)
        
        

# Expects string, not AST. counts via parentheses rather than AST,
# as ASTs don't preserve parentheses
def getMaxNestedLevelFromMBAStr(mbaStr):
    maxLevel = 1

    currentLevel = 1

    for c in mbaStr:
        if c == "(":
            currentLevel += 1
        if c == ")":
            if currentLevel > maxLevel:
                maxLevel = currentLevel
                currentLevel -= 1
    return maxLevel 

