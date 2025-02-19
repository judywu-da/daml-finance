#!/usr/bin/env python3
# Copyright (c) 2022 Digital Asset (Switzerland) GmbH and/or its affiliates. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# coding: utf8
#
## Idempotently add DA copyright headers to source files.
#
# To check that all files have required headers:
# $ dade-copyright-headers check
#
# To add/update the copyright headers:
# $ dade-copyright-headers update
#
# To ignore files under a certain directory and below:
# $ touch some/directory/NO_AUTO_COPYRIGHT
# $ git add some/directory/NO_AUTO_COPYRIGHT

import subprocess
import re
import os
import string
import sys


#########################
# File-type configuration
# start: The start marker of the block.
# line: The prefix for the notice text.
# end: The end marker of the block.
# skip: Optional prefix for lines to skip when adding header initially.

filetypes = \
  { 'bat'    : { 'start' : '::'     , 'line' : '::'   , 'end' : ''    , 'empty_line' : '' } ,
    'bats'   : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '', 'skip' : '#!' } ,
    'bazel'  : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '', 'skip': '#!' } ,
    'bzl'    : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '', 'skip': '#!' } ,
    'c'      : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'cc'     : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'chs'    : { 'start' : '-' * 80 , 'line' : '--'   , 'end' : ''    , 'empty_line' : '' } ,
    'cmd'    : { 'start' : '::'     , 'line' : '::'   , 'end' : ''    , 'empty_line' : '' } ,
    'cpp'    : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'css'    : { 'start' : '/*'     , 'line' : ''     , 'end' : ' */' } ,
    'daml'   : { 'start' : '-' * 80 , 'line' : '--'   , 'end' : ''    , 'empty_line' : '' } ,
    'groovy' : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'h'      : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'hh'     : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'hpp'    : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'hs'     : { 'start' : '-' * 80 , 'line' : '--'   , 'end' : ''    , 'empty_line' : '', 'skip' : '#!'  } ,
    'html'   : { 'start' : '<!--'   , 'line' : ''     , 'end' : '-->' , 'skip' : '<!' } ,
    'java'   : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'js'     : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'lf'     : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'lhs'    : { 'start' : '-' * 80 , 'line' : '--'   , 'end' : ''    , 'empty_line' : '' } ,
    'proto'  : { 'start' : '/*'     , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'py'     : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '', 'skip' : '#!' } ,
    'rb'     : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '' } ,
    'rst'    : { 'start' : ''       , 'line' : '..'   , 'end' : ''    , 'empty_line' : '' } ,
    'scala'  : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'scss'   : { 'start' : '/*'     , 'line' : ''     , 'end' : ' */' } ,
    'sh'     : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '', 'skip' : '#!' } ,
    'sql'    : { 'start' : '/*'     , 'line' : '--'   , 'end' : ''    , 'empty_line' : '' } ,
    'tex'    : { 'start' : '%' * 80 , 'line' : '%'    , 'end' : ''    , 'empty_line' : '' } ,
    'tf'     : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '' } ,
    'ts'     : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'tsx'    : { 'start' : ''       , 'line' : '//'   , 'end' : ''    , 'empty_line' : '' } ,
    'yaml'   : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '' } ,
    'yml'    : { 'start' : '#' * 80 , 'line' : '#'    , 'end' : ''    , 'empty_line' : '' } ,
  }

#########################

# Switch the current working directory to the root of the repository.
def chdir_to_toplevel():
  toplevel = subprocess                                    \
    .check_output(["git", "rev-parse", "--show-toplevel"], universal_newlines=True) \
    .strip()
  os.chdir(toplevel)

# Find all files from the provided directory (defaults to '.')
# using git ls-files, ignoring all prefixes specified in the root
# .copyright-ignore file.
def list_files(dir):
  if dir is None:
    dir = "."

  all_files = subprocess                       \
    .check_output(["git", "ls-files", dir], universal_newlines=True)    \
    .strip()                                   \
    .split("\n")

  # Find all 'NO_AUTO_COPYRIGHT' paths
  ignores = [ os.path.dirname(f) + "/" for f in all_files
              if os.path.basename(f) == 'NO_AUTO_COPYRIGHT' ]

  # Filter out files under directories that contained
  # NO_AUTO_COPYRIGHT.
  unignored = [ f for f in all_files
                if not any(map(lambda x: f.startswith(x), ignores))  ]

  # Filter out symlinks
  return [ f for f in unignored if not os.path.islink(f) ]

def process_file(filename, check_only):
  (_, ext) = os.path.splitext(filename)
  ext = ext[1:]
  if ext not in filetypes:
    #print "skipping %s" % filename
    return True

  start_mark = filetypes[ext]['start'] + "\n"
  line_mark = filetypes[ext]['line']
  # filetypes[ext]['start'] + ' ' + line + ' ' + filetypes[ext]['end']
  empty_line_mark = filetypes[ext].get('empty_line', line_mark)
  end_mark = filetypes[ext]['end'] + "\n"

  def comment(line):
    if line == '':
      return empty_line_mark
    else:
      if line_mark == '':
          return filetypes[ext]['start'] + ' ' + line + ' ' + filetypes[ext]['end']
      else:
          return line_mark + ' ' + line

  notice_lines = list(map(comment, LEGAL_NOTICES))
  suffix="\n"
  header = suffix.join(notice_lines) + "\n"

  # Read all lines from the file
  with open(filename, 'r', encoding="UTF-8") as fp:
    lines = fp.readlines()
  # Pretend that the file has extra empty line at the end to handle files,
  # which consist only of the copyright notice and nothing else.
  # label: ADD_BLANK_LINE
  lines.append('\n')

  # Process the file:
  # If we find an existing copyright header with the same starting line
  # compare against it. If no copyright header exists or it's different
  # remove the existing one and prepend the new header to the file.
  state='start'
  index=0      # Current index to copyright notice text when comparing
  before_header=[] # Lines in the file before possible copyright header
  after_header=[]  # Lines in the file after the header
  for line in lines:
    # looking for start comment block
    if state == 'start':
      if (line.strip(filetypes[ext]['line']).strip(filetypes[ext]['start'])[1:14] == "Copyright (c)"):
        state='notice'

        if line != notice_lines[0]+"\n":
            print("{0}: notice text mismatch:\n  actual  : {1}\n  expected: {2}" \
                  .format(filename, line.strip(), notice_lines[index].strip()))
            state='find_end_and_fail'
        else:
            index += 1

      else:
        before_header.append(line)

    # looking for notice start
    elif state == 'notice':
      if (line != notice_lines[1] + "\n"):
        # not a copyright block, switch back to looking for start
        state='start'
        before_header.append(start_mark)
        before_header.append(line)

      else:
        # match, found the copyright block, start comparing.
        index += 1
        state='compare'

    # comparing notice texts
    elif state == 'compare':
      if index == len(notice_lines):
        if line != end_mark and not line.endswith(end_mark) and line != empty_line_mark + "\n":
          print(f"end marker invalid: {line} vs {end_mark}")
          state='fail'
        else:
          state='ok'

      elif line != notice_lines[index]+"\n":
        print("{0}: notice text mismatch:\n  actual  : {1}\n  expected: {2}" \
          .format(filename, line.strip(), notice_lines[index].strip()))
        state='find_end_and_fail'

      else:
        index += 1

    # skip comment lines until end mark and fail
    elif state == 'find_end_and_fail':
      if not line.startswith(line_mark) \
              and not line.startswith(' *') \
              and not line.startswith('    ') \
              or line == end_mark\
              or line.endswith(end_mark)\
              or line == empty_line_mark + "\n":
        state = 'fail'

    elif state == 'fail' or state == 'ok':
      after_header.append(line)

    else:
      sys.exit("abort: unknown state %s" % state)

  if state == 'ok':
    #print "%s: ok." % filename
    return True
  else:
    if not check_only:
      print(f"{filename}: copyright header missing or out-of-date, updating.")
      with open(filename, 'w') as fp:
        if state == 'fail':
           # copyright header existed, but was out of date, replace it.
          fp.write("".join(before_header))
          fp.write(header)
          # remove additional blank line added at ADD_BLANK_LINE
          fp.write("".join(after_header[:-1]))
        elif 'skip' in filetypes[ext]:
          # no copyright header, but file type requires skipping lines
          skip_prefix = filetypes[ext]['skip']
          # skip lines matching the given prefix
          index=0
          while index < len(before_header):
            line = before_header[index]
            if line.startswith(skip_prefix):
              fp.write(line)
              index += 1
            else:
              break
          fp.write(header + "\n")
          # write the rest of the file.
          while index < len(before_header):
            fp.write(before_header[index])
            index += 1
        else:
          # no copyright header, prepend it.
          fp.write(header + "\n")
          fp.write("".join(before_header))
      return True
    else:
      if state == 'fail':
        print(f"{filename}s: copyright header out-of-date")
      else:
        print(f"{filename}: copyright header missing")
      return False

#########################
# Main

def usage():
  print("usage: dade-copyright-headers <check|update> [DIRECTORY]")
  print("  If DIRECTORY is provided, checks only in that directory")
  print("  Otherwise, checks in 'pkgs'.")
  print("  Note that the provided directory must be relative to the")
  print("  root of the git repository.")
  sys.exit(1)

chdir_to_toplevel()
with open('COPY', 'r') as f:
  LEGAL_NOTICES = list(map(lambda x: x.strip(), f.readlines()))

if len(sys.argv) != 2 and len(sys.argv) != 3:
  usage()

if sys.argv[1] == "update":
  check_only = False
elif sys.argv[1] == "check":
  check_only = True
else:
  usage()

dir = None
if len(sys.argv) > 2:
  dir = sys.argv[2]

failed=False
for file in list_files(dir):
  if not process_file(file, check_only):
    failed=True

if failed and check_only:
  print("\nCopyright header check failed.\nPlease update copyright headers by running 'dade-copyright-headers update'")

sys.exit(failed)


