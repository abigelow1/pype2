#!/usr/bin/env python
#
# Copyright 2000 Doug Hellmann
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of Doug
# Hellmann not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# DOUG HELLMANN DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL DOUG HELLMANN BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

"""Base class for formatting info generated by parseinfo classes.

  This class can be subclassed for easily changing the output format,
  or more drastically a new class which supports a write() method with
  the same interface can completely replace this class.

"""

__rcs_info__ = {
    #
    #  Creation Information
    #
    'module_name'  : '$RCSfile: happyformatter.py,v $',
    'rcs_id'       : '$Id: happyformatter.py,v 1.5 2002/02/03 21:49:27 doughellmann Exp $',
    'creator'      : 'Doug Hellmann <doug@hellfly.net>',
    'project'      : 'HappyDoc',
    'created'      : 'Thu, 09-Mar-2000 13:41:44 EST',

    #
    #  Current Information
    #
    'author'       : '$Author: doughellmann $',
    'version'      : '$Revision: 1.5 $',
    'date'         : '$Date: 2002/02/03 21:49:27 $',
    'locker'       : '$Locker:  $',
}
try:
    __version__ = __rcs_info__['version'].split(' ')[1]
except:
    __version__ = '0.0'

#
# Import system modules
#
import os
import sys
import parser
import token, symbol
import types
import string
import time
import glob
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

#
# Local Modules
#
import happydoclib.path

#
# Module
#

class DevNull:
    '''Null output class.

    This class simulates the UNIX /dev/null device file
    by discarding its inputs.
    '''
    def write(self, str):
        "Value is discarded."
        return


#
# Find a list of system modules for creating reference
# links to them.
#

_sysdirs = []
version_dir='python%d.%d' % (sys.version_info[0], sys.version_info[1])
for path in sys.path:
    path_parts = string.split(path, os.sep)
    if (version_dir in path_parts) and ('site-packages' not in path_parts):
        # system directory
        _sysdirs.append(path)
_sys_modules = []
for path in _sysdirs:
    module_list = glob.glob( happydoclib.path.join( path, '*.py' ) )
    module_file_names = map(happydoclib.path.basename, module_list)
    for name in module_file_names:
        name = name[:-3]
        if name:
            #print 'System module %s/%s.py' % (path, name)
            _sys_modules.append(name)
    shared_lib_list = glob.glob( happydoclib.path.join( path, '*.so' ) )
    shared_lib_file_names = map(happydoclib.path.basename, shared_lib_list)
    for name in shared_lib_file_names:
        #print 'Shared library %s/%s' % (path, name)
        name = name[:-3]
        #print '  name="%s"' % name
        if name:
            _sys_modules.append(name)

_well_known_names = ( 'regex', 'sys', 'thread', 'threading', 'new' )
for _name in _well_known_names:
    _sys_modules.append(_name)
#print _sys_modules
#sys.exit(1)



class HappyFormatterBase:
    'Base class for HappyDoc formatters.'

    sys_modules = _sys_modules
        

    def __init__(self,
                 docSet,
                 pythonLibDoc='http://www.python.org/doc/current/lib',
                 **extraNamedParameters):
        """Initialize the output formatter.

        Parameters:

            'docSet' -- documentation set controlling this formatter

            'pythonLibDoc' -- Base of URL for Python library
            documentation.  Defaults to
            'http://www.python.org/doc/current/lib'.
            
            'extraNamedParameters' -- Parameters specified by name
            which were not interpreted by a subclass initialization.

        """
        self._docset = docSet
        self._python_lib_doc = pythonLibDoc
        #
        # Initialize some instance members
        #
        self._update_time = time.ctime(time.time())
        self.list_context = None
        self.current_list_context = None
        #
        # Warn about extra named parameters
        #
        for extra_param, extra_value in extraNamedParameters.items():
            docSet.statusMessage(
                'WARNING: Parameter "%s" (%s) unrecognized by formatter %s.' % \
                (extra_param, extra_value, self.__class__.__name__)
                )
        return

    def supportedOptions(self):
        "Returns a dictionary of option names and descriptions."
        self._requiredOfSubclass('supportedOptions')
        return

    def _requiredOfSubclass(self, name):
        "Convenient way to raise a consistent exception."
        raise AttributeError('%s is not implemented for this class.' % name,
                             self.__class__.__name__)
        

    ##
    ## OUTPUT HANDLING
    ##
    
    def openOutput(self, name, title1, title2=None):
        "Open the named output destination and give a title and subtitle."
        self._requiredOfSubclass('openOutput')
        return

    def fileHeader(self, title1, title2=None, output=None):
        """Write the title and subtitle header to an open file."""
        self._requiredOfSubclass('fileHeader')
        return

    def closeOutput(self, output):
        "Close the output handle."
        self._requiredOfSubclass('closeOutput')
        return

    def fileFooter(self, output):
        """Write the file footer to the output stream."""
        self._requiredOfSubclass('fileFooter')
        return

        
    ##
    ## STRING HANDLING
    ##
    
    def _unquoteString(self, str):
        "Remove surrounding quotes from a string."
        str = string.strip(str)
        while ( str
                and
                (str[0] == str[-1])
                and
                str[0] in ('"', "'")
                ):
            str = str[1:-1]
        return str

    def writeText(self, text, output, textFormat, quote=1):
        """Write the text to the output destination.

        Arguments

            'text' -- text to output

            'output' -- output file object

            'textFormat' -- String identifying the format of 'text' so
            the formatter can use a docstring converter to convert the
            body of 'text' to the appropriate output format.

            'quote=1' -- Boolean option to control whether the text
            should be quoted to escape special characters.
        """
        text = self._unquoteString(text)
        self.writeRaw(text, output)
        return

    def writeRaw(self, text, output):
        "Write the unaltered text to the output destination."
        output.write(text)
        return

    def formatCode(self, text, textFormat):
        "Format 'text' as source code and return the new string."
        self._requiredOfSubclass('formatCode')
        return 

    def formatKeyword(self, text):
        "Format 'text' as a keyword and return the new string."
        self._requiredOfSubclass('formatKeyword')
        return 
    
    def writeCode(self, text, textFormat, output):
        "Write the text to the output formatted as source code."
        try:
            formatted_text = self.formatCode(text, textFormat)
        except:
            print 'FAILURE: %s' % self.__class__.__name__
            raise
        self.writeRaw(formatted_text, output)
        return

    ##
    ## STRUCTURED OUTPUT METHODS
    ##

    def _pushListContext(self, resetCurrentContext):
        "Add to the list context for nested lists."
        self.list_context = ( [], self.list_context )
        if resetCurrentContext:
            self.current_list_context = self.list_context[0]
        else:
            self.current_list_context = None
        return

    def _popListContext(self):
        "Remove context from the list context stack."
        self.list_context = self.list_context[1]
        if self.list_context:
            self.list_current_context = self.list_context[0]
        else:
            self.list_current_context = None
        return
    
    def listHeader(self, output, title, allowMultiColumn=1):
        self._requiredOfSubclass('listHeader')
        return

    def listItem(self, output, text):
        self._requiredOfSubclass('listItem')
        return

    def listFooter(self, output):
        self._requiredOfSubclass('listFooter')
        return

    def descriptiveListHeader(self, output, title):
        self._requiredOfSubclass('descriptiveListHeader')
        return

    def descriptiveListItem(self, output, item, description):
        self._requiredOfSubclass('descriptiveListItem')
        return

    def descriptiveListFooter(self, output):
        self._requiredOfSubclass('descriptiveListFooter')
        return

    def sectionHeader(self, output, title):
        self._requiredOfSubclass('sectionHeader')
        return

    def sectionFooter(self, output):
        self._requiredOfSubclass('sectionFooter')
        return

    def itemHeader(self, output, title):
        self._requiredOfSubclass('itemHeader')
        return

    def itemFooter(self, output):
        self._requiredOfSubclass('itemFooter')
        return

    def pushSectionLevel(self, output):
        self._requiredOfSubclass('pushSectionLevel')
        return

    def popSectionLevel(self, output):
        self._requiredOfSubclass('popSectionLevel')
        return
 
    def dividingLine(self, output, fill='-', span=80):
        '''Output a sectional dividing line.

        Parameters:

            output -- destination for written output

            fill="-" -- character to use to draw the line

            span=80 -- horizontal width of line to draw
            
        '''
        self._requiredOfSubclass('dividingLine')
        return

    def comment(self, text, output):
        """Output text as a comment, if the output format supports comments."""
        self._requiredOfSubclass('comment')
        return
    
    ##
    ## INFO OBJECT NAMING
    ##

    def getNameForInfoSource(self, infoSource):
        """Return the name for an infoSource."""
        if type(infoSource) == types.FileType:
            name = happydoclib.path.basename(infoSource.name)
        elif type(infoSource) == types.StringType:
            name = happydoclib.path.basename(infoSource)
        else:
            name = infoSource.getReferenceTargetName()
        return name

    def getOutputNameForObject(self, infoObject):
        """
        Return the base name of the thing to which output should be written
        for an info source.  This is usually a file name, but could
        be anything understood by the formatter as a name.  If
        infoObject is None, return the name for a root node for this
        formatter.
        """
        self._requiredOfSubclass('getOutputNameForObject')
        return

    def fixUpOutputFilename(self, filename):
        """Tweak the filename to meet formatter-specific requirements.

        The default behavior is to return the same value."""
        return filename
    
    def getOutputNameForFile(self, filename):
        """
        Return the base name of the thing to which output should be
        written for a file.  This is usually a file name, but could be
        anything understood by the formatter as a name.  If infoObject
        is None, return the name for a root node for this formatter.
        """
        self._requiredOfSubclass('getOutputNameForFile')
        return

    def getFullOutputNameForObject(self, infoObject):
        "Get the full name, including path, to the object being output."
        self._requiredOfSubclass('getFullOutputNameForObject')
        return


    def getReference(self, infoSource, relativeSource, name=None):
        """Return a reference from relativeSource to infoSource.

        Return a string containing a reference which points to the
        documentation for an object from the node located at
        relativeSource.  The relativeSource parameter is a string
        naming a node from which the reference should work.

        Parameters

          infoSource -- Documentation, target of reference.

          relativeSource -- Start point of reference

          name=None -- Name to use in the reference, if supported and
                       supplied.
          
        """
        self._requiredOfSubclass('getReference')
        return

    def getNamedReference(self, infoSource, name, relativeSource):
        """Return a reference from relativeSource to name within infoSource.

        Return a string containing a reference which points to the
        documentation for 'name' from the node located at
        'relativeSource'.  The 'relativeSource' parameter is a string
        naming a node from which the reference should work.
        """
        self._requiredOfSubclass('getNamedReference')
        return

    def getInternalReference(self, infoSource):
        """Return a reference to infoSource within an open documentation node.

        Return a string containing a reference which points to the
        documentation for an object from the current node.
        """
        self._requiredOfSubclass('getInternalReference')
        return
    
    def getPythonReference(self, moduleName):
        """Return a reference pointing to Python.org.

        Return a reference to the standard documentation for a
        standard Python library module on http://www.python.org.
        """
        self._requiredOfSubclass('getPythonReference')
        return



        
        

    