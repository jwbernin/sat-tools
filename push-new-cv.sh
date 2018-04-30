#!/bin/bash

CVs=$(hammer --csv content-view list | grep -v 'Default Organization View' | grep -v 'Name' | awk -F, '{print $2}')

for f in $CVs
do
  echo Working on Content View $f...
  hammer content-view publish --name $f 
  echo Content View $f published
  hammer content-view version promote --content-view $f --from-lifecycle-environment Library --to-lifecycle-environment Testing
  echo Content View $f promoted to Testing
  hammer content-view version promote --content-view $f --from-lifecycle-environment Library --to-lifecycle-environment Homelab
  echo Content View $f promoted to Homelab
done
