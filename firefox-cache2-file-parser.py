import argparse
import os
import struct
import datetime
import hashlib
import csv
from xlsxwriter import Workbook

argParser = argparse.ArgumentParser(description='Parse Firefox cache2 files in a directory or individually.')
argParser.add_argument('-f', '--file', help='single cache2 file to parse')
argParser.add_argument('-d', '--directory', default=os.path.join(os.environ['USERPROFILE'], 'AppData\Local\Mozilla\Firefox\Profiles'), help='directory with cache2 files to parse')
argParser.add_argument('-o', '--output', default='Firefox_Cache2.xlsx', help='CSV or XLSX output file')
argParser.add_argument('-r', '--recursive', action='store_true', default=True, help='Scan input folder recursively (including subfolders)')
argParser.add_argument('-v', '--verbose', action='store_true', default=False, help='Print cache while parsing')
args = argParser.parse_args()

chunkSize = 256 * 1024

script_dir = os.path.dirname(__file__)

def ParseCacheFile (parseFile):
    if verbose:
        print "parsing file: {0}".format(parseFile.name)
    fileSize = os.path.getsize(parseFile.name)
    parseFile.seek(-4, os.SEEK_END)
    metaStart = struct.unpack('>I', parseFile.read(4))[0]
    numHashChunks = metaStart / chunkSize
    if metaStart % chunkSize :
        numHashChunks += 1
    parseFile.seek(metaStart + 4 + numHashChunks * 2, os.SEEK_SET)
    version = struct.unpack('>I', parseFile.read(4))[0]
    #if version > 1 :
        # TODO quit with error
    fetchCount = struct.unpack('>I', parseFile.read(4))[0]
    lastFetchInt = struct.unpack('>I', parseFile.read(4))[0]
    lastModInt = struct.unpack('>I', parseFile.read(4))[0]
    frecency = struct.unpack('>I', parseFile.read(4))[0]
    expireInt = struct.unpack('>I', parseFile.read(4))[0]
    keySize = struct.unpack('>I', parseFile.read(4))[0]
    flags = struct.unpack('>I', parseFile.read(4))[0] if version >= 2 else 0
    key = parseFile.read(keySize)
    key_hash = hashlib.sha1(key).hexdigest().upper()

    if doXlsx:
        vals1 = [fetchCount, format(datetime.datetime.fromtimestamp(lastFetchInt)), format(datetime.datetime.fromtimestamp(lastModInt)), format(hex(frecency)), format(datetime.datetime.fromtimestamp(expireInt)), keySize, flags, key, key_hash]
        vals2 = [fetchCount, lastFetchInt, lastModInt, hex(frecency), expireInt, keySize, flags, key, key_hash]
        for col in range(len(vals1)):
            worksheet1.write(row, col, vals1[col])
            worksheet2.write(row, col, vals2[col])

    elif doCsv :
        csvWriter.writerow((fetchCount,
                            datetime.datetime.fromtimestamp(lastFetchInt),
                            datetime.datetime.fromtimestamp(lastModInt),
                            hex(frecency),
                            datetime.datetime.fromtimestamp(expireInt),
                            flags,
                            key,
                            key_hash))

    if verbose:
        print "version: {0}".format(version)
        print "fetchCount: {0}".format(fetchCount)
        print "lastFetch: {0}".format(datetime.datetime.fromtimestamp(lastFetchInt))
        print "lastMod: {0}".format(datetime.datetime.fromtimestamp(lastModInt))
        print "frecency: {0}".format(hex(frecency))
        print "expire: {0}".format(datetime.datetime.fromtimestamp(expireInt))
        print "keySize: {0}".format(keySize)
        print "flags: {0}".format(flags)
        print "key: {0}".format(key)
        print "key sha1: {0}\n".format(key_hash)

if args.verbose:
    verbose = True
else:
    verbose = False
if args.directory or args.file :
    if args.output :
        ext = os.path.splitext(args.output)[-1]
        if ext == '.csv':
            doCsv, doXlsx, saved = True, False, False
        elif ext == '.xlsx':
            doCsv, doXlsx, saved = False, True, False
        else:
            verbose, doCsv, doXlsx, saved = True, False, False, False
        if doXlsx:
            workbook = Workbook(args.output)
            bold = workbook.add_format({'bold': True})
            worksheet1 = workbook.add_worksheet('Firefox Cache2 Time')
            worksheet1.freeze_panes(1, 0)
            worksheet2 = workbook.add_worksheet('Firefox Cache2 Timestamps')
            worksheet2.freeze_panes(1, 0)
            columnNames = ['Fetch Count', 'Last Fetch', 'Last Modified', 'Frecency', 'Expiration', 'Key size', 'Flags', 'URL', 'Key Hash']
            columnWidth = [10, 20, 20, 15, 20, 10, 5, 40, 30]
            columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            for i in range(len(columnNames)):
                worksheet1.write(0, i, columnNames[i], bold)
                worksheet1.set_column(columns[i] + ':' + columns[i], columnWidth[i])
                worksheet2.write(0, i, columnNames[i], bold)
                worksheet2.set_column(columns[i] + ':' + columns[i], columnWidth[i])

        if doCsv:
            csvFile = open(args.output, 'w')
            csvWriter = csv.writer(csvFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            csvWriter.writerow(('Fetch Count', 'Last Fetch', 'Last Modified', 'Frecency', 'Expiration', 'Flags', 'URL', 'Key Hash'))
    row = 1
    if args.recursive:
        for root, dirs, files in os.walk(args.directory):
            for filename in files:
                if len(os.path.splitext(filename)[-1]):
                    continue
                file = open(os.path.join(root, filename), 'r')
                try:
                    ParseCacheFile(file)
                    row += 1
                except:
                    print('Could not parse file ' + filename)
    else:
        procPath = args.directory
        fileList = os.listdir(procPath)
        for filePath in fileList :
            if os.path.isdir(os.path.join(procPath, filePath)):
                continue
            file = open(os.path.join(procPath, filePath), 'r')
            try:
                ParseCacheFile(file)
                row += 1
            except:
                print('Could not parse file ' + filePath)

    if doXlsx:
        try:
            workbook.close()
            print('Data written to XLSX file ' + args.output)
            saved = True
        except:
            print('Could not save XLSX file ' + args.output)

    elif doCsv :
        try:
            csvFile.close()
            print('Data written to CSV file ' + args.output)
            savd = True
        except:
            print('Could not save CSV file ' + args.output)

    if saved:
        os.startfile(args.output)
else :
    argParser.print_help()
