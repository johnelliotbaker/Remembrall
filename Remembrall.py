from ebml_python.container import File
from ebml_python.tags import MATROSKA_TAGS
from ebml_python.data_elements import ElementTag, ElementSimpleTag
from ebml_python.element import ElementMaster

import datetime
import os
import fnmatch
import stat
import shutil
from os.path import exists
from os.path import basename, dirname
from glob import glob
import argparse
import pdb

ACCEPTED_YES = ['y', 'Y', 'yes', 'Yes', 'YES']
CONFIRM_MOVE = """Are you sure you want to restore filenames? (y/N) """
FILENAME_TAG_NAME = 'OriginalFilename'
FILENAME_TAG_ALREADY_EXISTS = """
This file already has a filename tag of 
{}
Do you want to tag it with
{}? (y/N) 
"""

def getCwd():
    return dirname(os.path.realpath(__file__))

def hasDup(arr):
    return len(arr) != len(set(arr))

def eternalQuestion(command):
    while command.lower() not in ['save', 'restore', 's', 'r']:
        command = input('Type (s)ave or (r)estore: ')
    if command in ['save', 's']:
        return 'save'
    elif command in ['restore', 'r']:
        return 'restore'
    return command

def recursiveWalk(rootPath, ext):
    matches = []
    for root, dirnames, filenames in os.walk(rootPath):
        for filename in fnmatch.filter(filenames, ext):
            matches.append(os.path.join(root, filename))
    return matches

class Remembrall(object):
    def __init__(self, src, bRecursive=False):
        self.src = os.path.abspath(src)
        self.bRecursive = bRecursive
        self.aFilepath = []

    def validateMove(self, aJob):
        print('Validating files...')
        aSrcPath = [x[0] for x in aJob]
        aDstPath = [x[1] for x in aJob]
        if hasDup(aSrcPath):
            return False, 'Source path has duplicates'
        if hasDup(aDstPath):
            return False, 'Destination path has duplicates'
        return True, ''

    def getFileList(self, path, bRecursive=False):
        if path is None:
            raise Exception("Invalid path")
        if bRecursive is False:
            self.aFilepath = glob(os.path.join(path, '*.mkv'))
        else:
            self.aFilepath = recursiveWalk(path, '*.mkv')

    def getSegment(self, ebmlFile):
        segment = next(ebmlFile.children_named('Segment'))
        return segment

    def removeSegUid(self, segment):
        try:
            info = next(segment.children_named('Info'))
            segmentUid = next(info.children_named('SegmentUID'))
            info.remove_children_named('SegmentUID')
        except Exception as e:
            if str(e) != '':
                print(e)

    def removeFilenameTag(self, segment):
        tagGroups = next(segment.children_named('Tags'))
        for tagGroup in tagGroups:
            for t in tagGroup:
                if type(t) is ElementSimpleTag:
                    if t.tag_name == FILENAME_TAG_NAME:
                        tagGroup.remove_child(t)

    def getOrigTag(self, segment):
        aOrigTag = []
        try:
            tagGroups = next(segment.children_named('Tags'))
            for tagGroup in tagGroups:
                for t in tagGroup:
                    if type(t) is ElementSimpleTag:
                        aOrigTag.append((t.tag_name, t.string_val))
        except Exception as e:
            pass
        return aOrigTag

    def getOrigFilename(self, aOrigTag):
        for origTag in aOrigTag:
            if origTag[0] == FILENAME_TAG_NAME:
                oName = origTag[1]
                return oName
        raise Exception("Original name could not be found.")

    def append2TagGroups(self, filepath, aOrigTag):
        filename = basename(filepath)
        tagGroups = ElementMaster.new('Tags')
        tagGroup = ElementTag.new_with_value(50, 'None', tagGroups)
        bAddFilename = True
        for origTag in aOrigTag:
            tagName = origTag[0]
            tagVal = origTag[1]
            if tagName == FILENAME_TAG_NAME:
                if tagVal not in [filename, '']:
                    choice = input(FILENAME_TAG_ALREADY_EXISTS.format(
                        tagVal, filename))
                    if choice in ACCEPTED_YES:
                        ElementSimpleTag.new_with_value(
                            FILENAME_TAG_NAME,
                            filename,
                            tagGroup)
                    else:
                        ElementSimpleTag.new_with_value(
                            tagName, tagVal, tagGroup)
                    bAddFilename = False
            else:
                ElementSimpleTag.new_with_value(
                    tagName, tagVal, tagGroup)
        if bAddFilename:
            ElementSimpleTag.new_with_value(
                FILENAME_TAG_NAME, filename, tagGroup)
        return tagGroups

    def writeErrorLog(self, dError):
        aFilename = dError['aFilename']
        now = datetime.datetime.now()
        res = []
        res.append('')
        res.append('===================================================')
        res.append(str(now))
        res.append('Mode: {}'.format(dError['mode']))
        res.append('---------------------------------------------------')
        res.append('Following files could not be processed.')
        res.append('Your original source files likely had problems.')
        res.append('Use tools like mkvtoolnix-gui to inspect and fix.')
        res.append('Also try mkvmerge badfile.mkv -o newfile.mkv')
        res.append('---------------------------------------------------')
        for errorFile in aFilename:
            res.append(errorFile)
        res.append('---------------------------------------------------')
        strn = '\n'.join(res)
        print(strn)
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(strn)

    def engrave(self):
        self.getFileList(self.src, self.bRecursive)
        aFilepath = self.aFilepath
        aErrorFile = []
        for filepath in aFilepath:
            print('{}'.format(filepath))
            src = filepath
            try:
                ebmlFile = File(src, summary=True)
                segment = self.getSegment(ebmlFile)
                self.removeSegUid(segment)
                aOrigTag = self.getOrigTag(segment)
                tagGroups = self.append2TagGroups(
                        filepath, aOrigTag)
                segment.remove_children_named('Tags')
                segment.add_child(tagGroups, 0)
                segment.normalize()
                access = os.stat(src)
                os.chmod(src, access.st_mode | stat.S_IWRITE)
                with open(src, 'rb+') as f:
                    ebmlFile.save_changes(f)
            except Exception as e:
                print(e)
                aErrorFile.append(filepath)
            if 'ebmlFile' in locals(): ebmlFile.close()
        if len(aErrorFile) > 0:
            print('There were errors.')
            print('Please examine the log.txt file.')
            dError = {}
            dError['mode'] = 'save'
            dError['aFilename'] = aErrorFile
            self.writeErrorLog(dError)
        else:
            print('Saved all without error.')

    def restore(self):
        self.getFileList(self.src, self.bRecursive)
        aFilepath = self.aFilepath
        aErrorFile = []
        choice = input(CONFIRM_MOVE)
        if choice in ACCEPTED_YES:
            aJob = []
            for filepath in aFilepath:
                print('Verifying {}'.format(filepath))
                srcPath = filepath
                try:
                    srcFilename = basename(srcPath)
                    srcDir = dirname(srcPath)
                    ebmlFile = File(srcPath)
                    segment = self.getSegment(ebmlFile)
                    aOrigTag = self.getOrigTag(segment)
                    origName = self.getOrigFilename(aOrigTag)
                    dstPath = os.path.join(srcDir, origName)
                    if srcPath != dstPath:
                        aJob.append((srcPath, dstPath))
                except Exception as e:
                    print(e)
                    aErrorFile.append(filepath)
                if 'ebmlFile' in locals(): ebmlFile.close()
            if len(aErrorFile) > 0:
                print('There were errors.')
                print('Please examine the log.txt file.')
                dError = {}
                dError['mode'] = 'restore'
                dError['aFilename'] = aErrorFile
                self.writeErrorLog(dError)
            bValid, error = self.validateMove(aJob)
            if bValid:
                print('Processing restore...')
                for job in aJob:
                    srcPath = job[0]
                    dstPath = job[1]
                    print('{}\n   ^^^ {}'.format(srcPath, dstPath))
                    shutil.move(srcPath, dstPath)
        else:
            print('Exiting without making changes.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Save and restore original mkv names.')
    parser.add_argument('directory', type=str,
            help='MKV Directory')
    parser.add_argument('-c', '--command', type=str,
            help='(s)ave or (r)estore')
    parser.add_argument('-R', '--recursive',
            action='store_true',
            help='Process inner directories recursively')
    args = parser.parse_args()
    rootPath = args.directory
    bRecursive = args.recursive
    if not os.path.isdir(rootPath):
        raise Exception("Invalid directory")
    rem = Remembrall(rootPath, bRecursive)
    command = args.command if args.command is not None else ''
    command = eternalQuestion(command)
    if command == 'save':
        rem.engrave()
    elif command == 'restore':
        rem.restore()
