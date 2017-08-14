#!/bin/bash

#ssh-keygen -t rsa #luego enter enter enter
#cd $HOME/.ssh/
#ssh-copy-id -i id_rsa.pub jsoler@10.55.0.202

#-------------------------

#input
DATASETPATH="/home/joan/Escritorio/twitchbot/twitchbot3.0/dataset/"

#output (donde pone el texto filtrado, tambien lo envia a ieppa pero por sicurezidad mejor guardarlos en local tb)
OUTPUTPATH="/home/joan/Escritorio/twitchbot/twitchbot3.0/filtered_dataset/"

#-------------------------

PROCNUMBER=`cat /proc/cpuinfo | awk '/^processor/{print $3}' | tail -1`

cd $DATASETPATH
#remove white spaces
#rename "s/\s+//g" *

NF=`ls | wc`
COUNTER=0

#generate file to process (filter per game)
games="League\ of \Leg|Star\ Cr|Dota|Warcraft|Heartstone|Counter"
ls | grep -E -i "$games" > gamelist.tmp

cat gamelist.tmp | while read f; do
	echo "----------------------------------------------"	
	echo $f
	f=$( echo "$f" | rev | cut -d"/" -f1 | rev )

	twokenizeOutput="$f".out
	numberOfLines=`wc -l < $f`
	linesSplit=$(($numberOfLines / $PROCNUMBER))

	#let COUNTER=COUNTER+1
	#echo "$COUNTER of $NF - $f"
	echo "The file contains $numberOfLines, splitting $PROCNUMBER files of $numberofLines lines"
	
	split -l $linesSplit "$f" "$f".split.
	echo "Launching $PROCNUMBER instances of twokenize."
	for i in *.split.*; do
		python ../twokenize.py "$i" `echo "$i" | sed -e's/.split.//gI'`.out &
	done
	wait

	echo "Merging all files"
	cat *.out > "$twokenizeOutput"
	#CheckFile $twokenizeOutput

	echo "Substituting URLs with URL Token and removing useless spaces"
	sed 's!http[s]\?://\S*!URL!g' "$twokenizeOutput" \
	| perl -ne 's/(?<=(?<!\pL)\pL) (?=\pL(?!\pL))//g; print;' > "$f".tmp

	echo "Removing lines with less than 4 tokens"
	awk '{if(NF>4 && $0!=prev) {print $0; prev=$0;}}' "$f".tmp > $OUTPUTPATH"$f".out

	echo "Cleaning up"
	rm "$f".tmp
	rm gamelist.tmp
	rm *.out 
	rm *.split.*

	#echo "Sending to ieppa"
	#scp $OUTPUTPATH$f.out jsoler@10.55.0.202:/mnt/vmdata/ieppa/twitch/jan16/
 

done
