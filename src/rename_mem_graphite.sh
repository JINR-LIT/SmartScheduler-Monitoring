#!/bin/env bash

for i in `ls /var/lib/carbon/whisper/icinga2`; do

	cd /var/lib/carbon/whisper/icinga2/$i/services/openvz_perf/check_openvz_vm_perf/perfdata
	for f in `ls | grep _kb_`; do
		n=`echo "$f" | sed -e 's/_kb_/_b_/'`
		{
	        whisper-merge "$f/value.wsp" "$n/value.wsp" ||
	        {
	            mkdir "$n"
	            cp "$f/value.wsp" "$n/value.wsp"
	        }
	    } && rm "$f/value.wsp"
	    rmdir "$f"
	done
done