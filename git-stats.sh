#!/usr/bin/env bash
for author in Soizic dominique matthieu; do echo -en "$author  \t"; git log  --author="$author" --numstat --pretty=tformat: | gawk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "added lines: %s, removed lines: %s, total lines: %s\n", add, subs, loc}'; done

sprint_number=7
let sprint_number_minus_one=$sprint_number-1
for n in $(seq 0 $sprint_number_minus_one); do if [ "$n" -eq "$sprint_number_minus_one" ]; then tag2=HEAD; else let nplusone=$n+1; tag2="s$nplusone"; fi; tag1="s$n"; commits=$(git describe  --match $tag1 $tag2 | cut -d '-' -f 2); echo -e "$tag1-$tag2:  \t$commits commits"; done
