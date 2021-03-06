function pf = p2m(pypefile, oldpf)
%function pf = p2m(pypefile)
%
%  Convert and load a raw pype datafile into a matlab data
%  structure.  This requires the program pype_expander.py to
%  be on the user's path somwehere AND a fully installed
%  version of pypenv on the machine you're running on.
%
%  INPUT
%    pypefile = string containing name (full path) of original pype
%		data file. If pypefile contains wildcards, iterate
%               over the entire list of files (can't mix with oldpf!)
%
%    oldpf = previously extracted PF structure or name of p2m file.
%            data in pypefile will be converted, extracted and tacked
%            on at the end of oldpf and returned as pf
%
%  OUTPUT
%    pf = moderately complicated data structure containing all the data.
%      pf.rec contains entry for each trial
%      pf.extradata contains the "extradata" info
%      pf.src name of file data originated from
%
% Sun Feb 16 17:38:17 2003 mazer 
%
% Sat Mar  1 16:05:27 2003 mazer 
%   Removed the matfile option -- p2m no longer knows about writing
%   the resulting structure to disk.  The calling function (usually
%   p2mBatch) is responsible.
%
% Sun May 21 13:58:44 2006 mazer 
%   added support to appending new data to existing p2m structure. If you
%   pass in an old data struct, only the new data will be converted and
%   appended to the existing data.
%
% Fri Oct 22 12:54:54 2010 mazer 
%   added wildcard support -- pypefile can contain wildcards and each
%   file will get p2m'd
%  

if nargin == 0
  p2mHelp()
  return
end

files = p2m_dir(pypefile);
if length(files) > 1
  if exist('oldpf', 'var')
    error('Can''t mix wildcards with oldpf');
  end
  for n = 1:length(files)
    fprintf('converting: %s\n', files{n});
    p2m(files{n});
  end
  return;
end

if ~exist('oldpf', 'var')
  oldpf = [];
elseif ischar(oldpf)
  oldpf = p2mLoad(oldpf);
end

tmpf = [tempname '.m'];

if isempty(oldpf)
  n = 0;
else
  n = length(oldpf.rec);
end 

cmd = sprintf('pype_expander.py %s %s %d', pypefile, tmpf, n);
tic;
status = unix(cmd);
pet = toc;

if status ~= 0
  error('Can''t find pype_expander.py or datafile, check path');
  return
end

rec = [];
origdir = pwd;
et = [];
try
  cd(tempdir)
  try
    tic;
    eval(strrep(basename(tmpf),'.m',''));
    et = [et toc];
  catch
    err = lasterror;
    fprintf(2, '\n');
    fprintf(2, 'ERROR loading %s into matlab.\n', pypefile);
    fprintf(2, '%s\n', err.message);
    fprintf(2, '\n');
    rethrow(err);
  end
  for n = 1:length(rec)
    rec(n).ttl_times = rec(n).spike_times;
  end
  cd(origdir);
catch
  cd(origdir);
end
delete(tmpf);

if 0
  fprintf(2, 'python: %.2fs / trial\n', pet/length(et));
  fprintf(2, 'matlab: %.2fs / trial\n', mean(et));
end

if ~exist('extradata', 'var')
  extradata = [];
end


if isempty(oldpf)
  fprintf(2, 'Converted %d trials.\n', length(rec));
  pf.extradata = extradata;
  pf.src = cannonicalfname(pypefile);
  pf.rec = rec;
elseif isempty(rec)
  fprintf(2, 'No new data converted.\n');
  pf = oldpf;
else
  fprintf(2, 'Updated %d new trials (%d old).\n', ...
	  length(rec) - length(oldpf.rec), length(oldpf.rec));
  pf.extradata = extradata;
  pf.src = cannonicalfname(pypefile);
  pf.rec = rec;
  % merge in the old data for return 
  if ~isempty(oldpf)
    for n = 1:length(oldpf.rec)
      flist = fieldnames(oldpf.rec(n));
      for k = 1:length(flist)
        pf.rec(n).(flist{k}) = oldpf.rec(n).(flist{k});
      end
    end
  end
end

