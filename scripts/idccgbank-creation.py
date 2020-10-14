#!/usr/bin/env python3

import os.path
import sys

import conllu
# pylint: disable=no-name-in-module
from ufal.udpipe import Model, Pipeline, ProcessingError
from typing import NamedTuple

cd = os.path.dirname(os.path.realpath(__file__))
udModelPath = cd + "/../models/indonesian-gsd-ud-2.5-191206.udpipe"
udInputPath = cd + "/../datasets/id_pud-ud-test-revised-1-0.conllu"
udParsedPath = cd + "/../datasets/id_pud-ud-revised-1-0.parsed.conllu"
ccgbankFormattedPath = cd + "/../datasets/idccgbank.auto"

class IDPUDParser:
    def __init__(self, udModelPath: str, udInputPath: str, udParsedPath: str):
        self.udModelPath = udModelPath
        self.udInputPath = udInputPath
        self.udParsedPath = udParsedPath

        self.errMsg = ""
        self.parsed = False

    def __str__(self):
        ret = "IDPUDParser {"
        ret += "\n  udModelPath = \"%s\"," % self.udModelPath
        ret += "\n  udInputPath = \"%s\"," % self.udInputPath
        ret += "\n  udParsedPath = \"%s\"," % self.udParsedPath
        ret += "\n  parsed = %s," % self.parsed
        ret += "\n}"
        return ret

    def proceed(self):
        fmt = "conllu"
        model = Model.load(self.udModelPath)

        if not model:
            self.errMsg = "Can't load model from '%s'\n" % self.udModelPath
            return

        if not os.path.isfile(self.udInputPath):
            self.errMsg = "Can't load file from '%s'\n" % self.udInputPath
            return

        err = ProcessingError()
        inFile = open(self.udInputPath, "r")
        pipeln = Pipeline(model, fmt, Pipeline.DEFAULT, Pipeline.DEFAULT, fmt)

        processed = pipeln.process(inFile.read(), err)
        inFile.close()

        if err.occurred():
            self.errMsg = "run_udpipe error:\n"
            self.errMsg += err.message
            return

        outFile = open(self.udParsedPath, "w")
        outFile.write(processed)
        outFile.close()

        self.parsed = True

class CONLLU:
    def __init__(self, inputPath: str):
        self.inputPath = inputPath

        self.tokenList = []
        self.tokenTree = None

        self.errMsg = None
        self.formatted = False

    def __str__(self):
        ret = "CONLLU {"
        ret += "\n  inputPath = %s" % self.inputPath
        if len(self.tokenList) == 0:
            ret += "\n  tokenList = []"
        else:
            ret += "\n  tokenList = [TokenList<%s>]" % str(len(self.tokenList))
        if self.tokenTree == None:
            ret += "\n  tokenTree = None"
        else:
            ret += "\n  tokenTree = [TokenTree<%s>]" % str(len(self.tokenTree))
        ret += "\n  errMsg = %s" % self.errMsg
        ret += "\n  formatted = %s" % self.formatted
        ret += "\n}"
        return ret

    def parse(self):
        if not os.path.isfile(self.inputPath):
            self.formatted = False
            self.errMsg = "Can't load file from '%s'\n" % self.inputPath
            return

        idPud = open(self.inputPath, "r").read()
        self.tokenList = conllu.parse(idPud)
        self.tokenTree = conllu.parse_tree(idPud)

        if len(self.tokenList) > 0 and len(self.tokenTree) > 0:
            self.formatted = True

    def removeNonProjectives(self):
        nonProjectives = []
        for i in range(len(self.tokenList)):
            isProjective = True
            sentence = self.tokenList[i]
            for j in range(len(sentence)):
                if not isProjective:
                    break

                word = sentence[j]
                head = word["head"] - 1
                if head == -1:
                    continue

                left = min(j, head) + 1
                right = max(j, head)
                while left < right and isProjective:
                    currHead = sentence[left]["head"]
                    while currHead != head + 1 and currHead != 0:
                        currHead = sentence[currHead - 1]["head"]
                    if currHead != head + 1:
                        isProjective = False
                    left += 1
            if not isProjective:
                nonProjectives.append(i)

        for i in nonProjectives:
            del self.tokenList[i]
            del self.tokenTree[i]

class CCGT(NamedTuple):
    ccgCat: str
    head: int
    dtrs: int

class CCGL(NamedTuple):
    ccgCat: str
    posTag: str
    word: str

class CCGNode:
    def __init__(self, value):
        self.value = value

        self.left = None
        self.right = None

    def __str__(self):
        val = self.value
        if type(val) == CCGT:
            return "<T %s %s %s>" % val
        elif type(val) == CCGL:
            return " ".join([
                "<L",
                "%s" % val.ccgCat,
                "%s" % val.posTag,
                "%s" % val.posTag,
                "%s" % val.word,
                "%s>" % val.ccgCat,
            ])
        return "<ill-formated CCG node>"

class CCGTree:
    def __init__(self):
        self.root = None

    def __str__(self):
        return "(%s)" % self._strTraverse(self.root)

    def _strTraverse(self, node):
        ret = "(%s" % str(node)
        if node.left != None:
            ret += " %s" % self._strTraverse(node.left)
        if node.right != None:
            ret += " %s" % self._strTraverse(node.right)
        return "%s)" % ret

class IDCCGbank:
    def __init__(self, ccgbankFormattedPath: str):
        self.ccgbankFormattedPath = ccgbankFormattedPath

        self.built = False
        self.errMsg = None

    def build_from(self, idConllu: CONLLU):
        ccgbank = []

        # WIP: ID PUD to ID CCG format conversion

        outFile = open(self.ccgbankFormattedPath, "w")
        outFile.write("\n".join(ccgbank))
        outFile.close()

        self.built = True

def run():
    args = sys.argv
    if len(args) == 1 or args[1] == "help":
        print("IDCCGbank Creation")
        print()
        print("Available commands:")
        print("  help               show this message")
        print("  parse-pud          run_udpipe parse ID PUD")
        print("  build-ccgbank      building IDCCGbank from formatted ID PUD")
        return

    if args[1] == "parse-pud":
        print("Parsing ID PUD...")

        idPudParser = IDPUDParser(udModelPath, udInputPath, udParsedPath)
        idPudParser.proceed()

        if not idPudParser.parsed:
            sys.stderr.write(idPudParser.errMsg)
            sys.exit(1)

        print("ID PUD successfully parsed.")
    elif args[1] == "build-ccgbank":
        print("Building CCGbank...")

        idConllu = CONLLU(udParsedPath)
        idConllu.parse()
        idConllu.removeNonProjectives()

        if not idConllu.formatted:
            sys.stderr.write(idConllu.errMsg)
            sys.exit(1)

        idCcgbank = IDCCGbank(ccgbankFormattedPath)
        idCcgbank.build_from(idConllu)

        if not idCcgbank.built:
            sys.stderr.write(idCcgbank.errMsg)
            sys.exit(1)

        print("IDCCGbank successfully built.")
    else:
        print("Unknown command. See \"help\" for more.")

if __name__ == "__main__":
    run()
