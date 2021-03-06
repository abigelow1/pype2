#!/usr/bin/python
# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys
from pype import *
from vectorops import *
import math

def RunSet(app):
	app.console.clear()

	P = app.params.check(mergewith=app.getcommon())
	app.params.save()
	app.warn_run_start()
	app.running, app.paused = 1, 0

	flist = []
	for n in range(P['nframes']):
		s = Sprite(P['size'], P['size'], 0, 0, fb=app.fb, on=0)
		s.noise(0.50)
		s.render()
		flist.append(s)
		con(app, "%s: made frame %d/%d" % (now(), n, P['nframes']))

	t = Timer()

	times = []
	try:
		while app.running:
			for j in range(10):
				n = 0
				t.reset()
				for s in flist:
					if not app.running:
						break
					app.fb.clear()
					s.fastblit()
					app.fb.flip()
					n = n + 1
					app.idlefn()
				x = t.ms()
				if x > 0:
					x = 1000.0 * float(n) / float(x)
					con(app, "%s: %.1f fps" % (now(), x))
					times.append(x)
	except:
		error.reporterror()

	for s in flist:
		del s
	del flist

	print P['size'], mean(times), std(times)
				
	app.running, app.paused = 0, 0
	app.warn_run_stop()
	return 1


def main(app):
	app.startfn = RunSet

	app.mybutton = app.taskbutton(text=__name__, check=1)
	app.notebook = TaskNotebook(title=__name__, checkbutton=app.mybutton)
	page = app.notebook.add('Params', 'Params')

	parfile = app.taskname()
	if parfile:
		parfile = parfile + '.par'
	app.params = ParamTable(page, (
		("nframes",		"10",				is_int),
		("size",		"100",				is_int),
		), file=parfile)
	app.notebook.lift('Params')

def cleanup(app):
	app.params.save()
	app.mybutton.destroy()
	app.notebook.destroy()


if not __name__ == '__main__':
	loadwarn(__name__)
else:
	dump(sys.argv[1])
