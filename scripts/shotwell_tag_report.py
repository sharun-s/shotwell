# basically show stats on tags
# how many tags - counts per tag
# how many marked as unidentified
# what is the connection between the TagTable and the PhotoTable
# related tags - flowering, veg
# location tags 
# photos 211 tags 71
#	overlapping tags - related tags? - clusters - neuralnets/bayesian/max ent classifiers, collab filtering	
# what happens when there are 2 or 3 plants in same pic - and all have multiple names

import sqlite3 as s
import pandas as p
import sys
import argparse
import matplotlib.pyplot as mp
import matplotlib.collections as col
import calplot
parser = argparse.ArgumentParser(description='Shotwell Tags Inspector.', epilog=' If Tag not specified generates a report on all Tags.')
parser.add_argument('-r', nargs='?', metavar='Tag', help='show related tags given a tag')
parser.add_argument('-f', nargs='?', metavar='Tag', help='show filenames given a tag')
parser.add_argument('-d', nargs='?', metavar='Tag', help='show dates given a tag')
parser.add_argument('-cal', nargs='?', metavar='Tag', help='show calendar given a tag')
parser.add_argument('-age', nargs='?', metavar='Tag', help='days since last photo taken given a tag')


#parser.add_argument('tag')
args = parser.parse_args()

#c=s.connect("/home/s/.local/share/shotwell/data/photo.db")
c=s.connect("/home/s/shotwelltestdir/data/photo.db")

ur=c.execute("select * from TagTable;")
vr=c.execute("select * from PhotoTable;")

f=ur.fetchall()
g=vr.fetchall()
#[i for i in g if i[1].find('Kalan') > -1]

tagdf=p.DataFrame(f)
tagtablecols=['id','name','photo_id_list','time_created']
tagdf.columns=tagtablecols
tagdf['photo_id_list']=tagdf['photo_id_list'].str.split(',')
tagdf=tagdf.explode('photo_id_list')
#sometimes a tag list has a trailing comma so an empty entry is added to the photo id list
#remove these empty entries
tagdf=tagdf[tagdf['photo_id_list']!='']

#old db schema
#pcols=['id' , 'filename' , 'width' , 'height' , 'filesize' , 'timestamp' , 'exposure_time' , 'orientation' , 'original_orientation' , 'import_id' , 'event_id' , 'transformations' , 'md5' , 'thumbnail_md5' , 'exif_md5' , 'time_created' , 'flags', 'rating' , 'file_format' , 'title', 'backlinks', 'time_reimported' , 'editable_id' , 'metadata_dirty', 'developer', 'develop_shotwell_id' , 'develop_camera_id' , 'develop_embedded_id' , 'comment'] 
pcols=["id", "filename","width","height","filesize","timestamp","exposure_time","orientation","original_orientation","import_id","event_id","transformations", "md5", "thumbnail_md5", "exif_md5", "time_created", "flags", "rating", "file_format", 'title', 'backlinks', 'time_reimported', 'editable_id', 'metadata_dirty', 'developer','develop_shotwell_id', 'develop_camera_id', 'develop_embedded_id', 'comment', 'has_gps', 'gps_lat', 'gps_lon']
pf=p.DataFrame(g)
pf.columns=pcols
c.close()

def getDetailsGivenTag(tagname):
	return tagdf[tagdf['name']==tagname]
#pf[pf.filename.str.contains('Kalan')]
def getFilenamesfromTagPhotoIDList(tag_photoidlist):
	# to convert id in tagtable to photoid strip away 'thumb' 
	# (for other phototype prefixes look in shotwell sourcecode src/db/PhotoTable.vala,TagTable.vala ) 
	# and convert remaining to hex
	photoids=tag_photoidlist.photo_id_list.apply(lambda x:int(x[5:], 16))
	print(*pf[pf.id.isin(photoids)].filename.values)

from datetime import datetime
import re
def getDatesfromTagPhotoIDList(tag_photoidlist, printdates=True):
	# to convert id in tagtable to photoid strip away 'thumb' 
	# (for other phototype prefixes look in shotwell sourcecode src/db/PhotoTable.vala,TagTable.vala ) 
	# and convert remaining to hex
	photoids=tag_photoidlist.photo_id_list.apply(lambda x:int(x[5:], 16))
	#print(*pf[pf.id.isin(photoids)].filename.values)
	names=pf[pf.id.isin(photoids)].filename.values
	names=[i.split('/')[-1][0:-4] for i in names]
	#print(*names);print('')

	#edit names editing with with (0) (1) etc
	names=[re.sub('\(\d\)','',i) for i in names]
	#print(*names);print('')
	#edit names editing with with (0) (1) etc
	names=[re.sub(r'IMG-(\d+?)-WA\d+',r'\1_000000',i) for i in names]
	#print(*names);print('')
	names=[re.sub(r'IMG_(\d+?)_(\d+?)_\d+',r'\1_\2',i) for i in names]
	#print(*names);print('')
	#edit names editing with with (0) (1) etc
	names=[re.sub(r'signal-(\d\d\d\d)-(\d\d)-(\d\d)-(\d\d\d\d\d\d)',r'\1\2\3_\4',i) for i in names]
	#print(*names);print('')
	names=[re.sub(r'WP_(\d+?)_(\d\d)_(\d\d)_(\d\d)_Pro',r'\1_\2\3\4',i) for i in names]
	#print(*names);print('')
	names=[re.sub(r'WP_(\d+?)_\d+',r'\1_000000',i) for i in names]

	names=[re.sub(r'([A-Z,a-z,-]+_)+(\d+)_(\d+)',r'\2_\3',i) for i in names]
	#print(*names)
	dates=sorted([datetime.strptime(i,'%Y%m%d_%H%M%S') for i in names])
	if printdates:
		print(*[i.strftime("%Y %d %b %H:%M") for i in dates],sep='\n') 
	datesdf=p.DataFrame(dates)
	return datesdf

def getRelatedTags(tag_photoidlist):
	print(tagdf[tagdf.photo_id_list.isin( tag_photoidlist.photo_id_list)].name.value_counts().to_string())

if args.r:
	l=getDetailsGivenTag(args.r)	
	getRelatedTags(l)
elif args.f :
	l=getDetailsGivenTag(args.f)
	getFilenamesfromTagPhotoIDList(l)
elif args.d :
	l=getDetailsGivenTag(args.d)
	ddf=getDatesfromTagPhotoIDList(l)
	fig = mp.figure(facecolor="#001f3f")
	fig.suptitle("PhotoCount per Day - "+args.d, color="#00efde", fontsize=16)
	ax1 = fig.add_subplot(111, frameon=False)
	#ax1.set_title('Days', color="#00d0ff")
	#ax1.get_xaxis().set_visible(False)	
	ax1.set_facecolor("#002f4f")
	ax1.set_alpha(0.1)
	ax1.tick_params(axis='y', colors='#ffc107', length=0, which='both')
	ax1.tick_params(axis='x', colors='#ffc107', length=0, which='both')
	#ax1.yaxis.label.set_color('#ffc107')
	ax1.spines['bottom'].set_color('#001f3f')#'#ccc107')
	ax1.spines['top'].set_color('#001f3f') 
	ax1.spines['right'].set_color('#001f3f')
	ax1.spines['left'].set_color('#001f3f')
	ddf.columns=['d']
	ddf['Count']=0
	# to plot no bars on days no photo was taken a Count col with 0 created
	cnts=ddf.groupby(p.Grouper(key='d',freq='D')).count()
	positives=cnts[cnts.Count !=0].index
	whatevr=cnts.plot(kind='bar', ax=ax1, color="#002f4f", 
		#color="#ffc107", 
		legend=False, width=3)
	ymax=whatevr.get_yticks()[-1]
	onlypositives=[]
	for xtic in whatevr.get_xticklabels():
		pdate=xtic.get_text().split()[0]
		if p.Timestamp(pdate) in positives:
			if pdate[8:][0] == '0':
				onlypositives.append(pdate[9:])
			else:	
				onlypositives.append(pdate[8:])
		else:
			onlypositives.append('')
	whatevr.set_xticklabels(onlypositives, rotation=0, fontsize=8)
	whatevr.xaxis.set_label_text('')
	fc=["orange", "#ffee55", "#ffee33",
	"#ffcc33","#ffcc00","#ffcc22",
	"#ffcc44","#ffaa33","#ffaa00",
	"#ff8800", "#ff8822", "#ee8822"]
	month_name=['Jan','Feb','Mar','Apr','May','Jun','July','Aug','Sep','Oct','Nov','Dec']
	for month_ in cnts.index.month.unique():
		#print(month_, (month_name[month_-1])
		collection = col.BrokenBarHCollection.span_where(range(0,len(cnts)),
			ymin=0, ymax=ymax, 
			where=cnts.index.month==month_, 
			facecolor=fc[month_-1], alpha=0.8)
		bbox=collection.get_paths()[0].get_extents()
		ax1.text(x=bbox.x0 + (bbox.x1-bbox.x0)/2, y=(bbox.y1-bbox.y0)/2, s=month_name[month_-1], 
			color='#002f4f',fontsize=12)
		ax1.add_collection(collection)
	mp.show()
elif args.cal:
	l=getDetailsGivenTag(args.cal)
	ddf=getDatesfromTagPhotoIDList(l)
	ddf.columns=['d']
	ddf['Count']=0
	# to plot no bars on days no photo was taken a Count col with 0 created
	cnts=ddf.groupby(p.Grouper(key='d',freq='D')).count()
	events=p.Series(cnts.Count, index=cnts.index)
	calplot.calplot(events, edgecolor=None, cmap='YlGn',colorbar=True, suptitle=args.cal+'- photos per day',linewidth=1)
	mp.show()

elif args.age:
	if args.age == 'all':
		print('Days since last photo')
		lall=[]
		for tagname, tagcnt in tagdf.groupby(['name']).count()['photo_id_list'].sort_values().iteritems():#.to_string())
			#print(tagname,end=' ')	
			l=getDetailsGivenTag(tagname)
			ddf=getDatesfromTagPhotoIDList(l, False)
			lastdate=ddf[0].iloc[-1]
			#print('-',(datetime.today()-lastdate).days)
			lall.append((tagname,(datetime.today()-lastdate).days))
		from pprint import pprint
		pprint(sorted(lall, key=lambda x:x[1]))
	else:
		print('days since last photo given tag '+ args.age,end=' ')	
		l=getDetailsGivenTag(args.age)
		ddf=getDatesfromTagPhotoIDList(l, False)
		lastdate=ddf[0].iloc[-1]
		print('-',(datetime.today()-lastdate).days)
else:
	print('Photo count',len(g))
	print('Tag count',len(f))
	for tagname, tagcnt in tagdf.groupby(['name']).count()['photo_id_list'].sort_values().iteritems():#.to_string())
		print(tagname, tagcnt)
		# dump all calendars
		# if tagcnt>40:
		# 	l=getDetailsGivenTag(tagname)
		# 	ddf=getDatesfromTagPhotoIDList(l)
		# 	ddf.columns=['d']
		# 	ddf['Count']=0
		# 	cnts=ddf.groupby(p.Grouper(key='d',freq='D')).count()
		# 	events=p.Series(cnts.Count, index=cnts.index)
		# 	fig,a=calplot.calplot(events, tight_layout=True, edgecolor=None, cmap='YlGn',colorbar=False, suptitle=tagname+'- photos per day',linewidth=1)
		# 	fig.savefig(tagname+"_cal.png",format='png')
