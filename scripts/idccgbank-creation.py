#!/usr/bin/env python3

import os.path
import sys
# pylint: disable=no-name-in-module
from ufal.udpipe import Model, Pipeline, ProcessingError
import conllu

cd = os.path.dirname(os.path.realpath(__file__))
udModelPath = cd + "/../models/indonesian-gsd-ud-2.5-191206.udpipe"
udInputPath = cd + "/../datasets/id_pud-ud-test-revised-1-0.conllu"
udParsedPath = cd + "/../datasets/id_pud-ud-revised-1-0.parsed.conllu"

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
        ret += "\n}"
        return ret

    def parse(self):
        if not os.path.isfile(self.inputPath):
            self.errMsg = "Can't load file from '%s'\n" % self.inputPath
            return

        idPud = open(self.inputPath, "r").read()
        self.tokenList = conllu.parse(idPud)
        self.tokenTree = conllu.parse_tree(idPud)

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

def run():
    args = sys.argv
    if len(args) == 1 or args[1] == "help":
        print("IDCCGbank Creation")
        print()
        print("Available commands:")
        print("  help               show this message")
        print("  parse-pud          run_udpipe parse ID PUD")
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
    else:
        print("Unknown command. See \"help\" for more.")

if __name__ == "__main__":
    run()
