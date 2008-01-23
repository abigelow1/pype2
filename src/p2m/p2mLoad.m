function r = p2mLoad(fname, plexchan)
%function r = p2mLoad(fname, plexchan)
%
%  Loads '.p2m' and '.ical' files generated by the p2m
%  tools. File suffix is used to figure out what kind of
%  file it is..
%
%  This is really just a wrapper for the built in LOAD
%  function which only recognized the '.mat' extension.
%
%  INPUT
%    fname = ascii filename
%    plexchan = OPTIONAL plexon channel to select on load (format: "005a" etc)
%      (this call p2mSelect, replacing the spike_times list with the
%       indicated channel). For TTL data, don't specify this argument, or
%       use 'TTL'.
%
%  OUTPUT
%    t = data structure generated by p2m tools:
%            p2m/p2mBatch/p2mEyecalBatch etc..
%
%Mon Feb 17 16:19:31 2003 mazer 
%
%Tue Apr 15 19:09:30 2003 mazer 
%  Modified to automatically handle .gz files.
%  Along those lines -- if the specified file doesn't
%   exist, it will automatically append a '.gz' and
%   try for that.
%
%Wed May 28 12:12:40 2003 mazer 
%  Modified to return right away if a pf datastruct
%  is passed in instead of a filename
%
%Fri Oct 27 12:38:39 2006 mazer 
%  added plexchan option

if ~ischar(fname)
  % if it's not a char, then assume it's an already loaded
  % pf structure and just return it..
  r = fname;
  if exist('plexchan', 'var')
    r = p2mSelect(r, plexchan);
  end
  return
end

% expand wildcard, if any..
flist = p2m_dir(fname);
if length(flist) > 0
  fname = flist{1};
end

if strcmp(fname((end-2):end), '.gz') == 1
  gz = 1;
  fname = fname(1:(end-3));
else
  gz = 0;
end

fname2 = p2m_fname(fname);

if ~p2mExist(fname2) & p2mExist([fname2 '.gz'])
  gz = 1;
end
  
if ~strcmp(fname2, fname)
  fname = fname2;
  fprintf('true file: %s\n', fname);
end
if gz
  fprintf('gzip: automatic\n');
end

fname0 = fname;
fname = cannonicalfname(fname);
if strcmp(fname0, fname) == 0
  % only print warning if cannonical name doesn't match the
  % name specified by user
  fprintf('loading: %s\n', fname);
end
  

if fname(end-3:end) == '.p2m'
  if gz
    gzload([fname '.gz']);
  else
    load(fname, '-mat');
  end
  fprintf('%d trials\n', length(PF.rec));
  r = PF;
elseif fname(end-4:end) == '.ical'
  if gz
    gzload([fname '.gz']);
  else
    load(fname, '-mat');
  end
  r = ical;
elseif fname(end-3:end) == '.fix'
  if gz
    gzload([fname '.gz']);
  else
    load(fname'-mat');
  end
  r = fixes;
else
  error(['unknown file type: ' fname]);
end

if exist('plexchan', 'var')
  r = p2mSelect(r, plexchan);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5

function z = gzload(fname)

t = tempname;
[s, w] = unix(sprintf('gunzip <%s >%s', fname, t));
if s
  error(sprintf('can''t find %s', fname));
end
evalin('caller', sprintf('load(''%s'', ''-mat'')', t));
delete(t);
