#!/usr/bin/env python3

import os.path
import sys
# pylint: disable=no-name-in-module
from ufal.udpipe import Model, Pipeline, ProcessingError

class IDPUDParser:
    def __init__(self, udModelPath: str, udInputPath: str, udOutputPath: str):
        self.udModelPath = udModelPath
        self.udInputPath = udInputPath
        self.udOutputPath = udOutputPath

        self.errMsg = ""
        self.parsed = False

    def __str__(self):
        ret = "IDPUDParser {"
        ret += "\n  udModelPath = \"%s\"," % self.udModelPath
        ret += "\n  udInputPath = \"%s\"," % self.udInputPath
        ret += "\n  udOutputPath = \"%s\"," % self.udOutputPath
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

        outFile = open(self.udOutputPath, "w")
        outFile.write(processed)
        outFile.close()

        self.parsed = True

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

        cd = os.path.dirname(os.path.realpath(__file__))
        udModelPath = cd + "/../models/indonesian-gsd-ud-2.5-191206.udpipe"
        udInputPath = cd + "/../datasets/id_pud-ud-test-revised-1-0.conllu"
        udOutputPath = cd + "/../datasets/id_pud-ud-revised-1-0.parsed.conllu"

        idPudParser = IDPUDParser(udModelPath, udInputPath, udOutputPath)
        idPudParser.proceed()

        if not idPudParser.parsed:
            sys.stderr.write(idPudParser.errMsg)
            sys.exit(1)

        print("ID PUD successfully parsed.")
    else:
        print("Unknown command. See \"help\" for more.")

if __name__ == "__main__":
    run()
