#!/usr/bin/env python3
'''
	Script para comparar os logs com o gold
'''
import os
import re

rootDir = '/home/lucas/Documents/carol-fi/logs-part1/sa'
outputLog = 'compareLog.log'

outs = [] # lista com diretórios que tem um arquivo output com sdc

for dirName, subdirList, fileList in os.walk(rootDir):
	if re.search("sdcs", dirName):
		for file in fileList:
			if file == 'outputsa':
				outs.append(dirName +'/outputsa')

	
sdcCounter = 1		
gold = 500796
for out in outs:
	print("#SDC " + str(sdcCounter) + ' => ' + out)
	sdcOut = open(out)
	pos = 1
	for line in sdcOut:
		r = int(line)
		if(r != gold):
			print("#ERR r:"+str(r)+" e:"+str(gold))
	sdcCounter+=1

