import os
 
nwords = 0
nsents = 0
avgSentLength = 0
avgWordLength = 0
i=0
#vocab = []

for fname in os.listdir("./dataset/"):
	print i
	sents = open("./dataset/"+fname,"r").read().split("\n")

	for sent in sents:
		words = sent.split()
		avgSentLength+=len(words)
		nsents+=1
		#vocab.extend(words)

		for word in words:
			avgWordLength+=len(word)
			nwords+=1
	i+=1
	#if i==1500:
	#	break


print "total number of words " + str(nwords)
print "avg sent length " + str(avgSentLength / float(nsents))
print "avg word length " + str(avgWordLength / float(nwords))
#print "vocabulary " + str(len(set(vocab)))