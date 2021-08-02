#!/bin/sh
QUERY="$(cat)"
echo "Content-type: application/json"
echo
START="@$(echo "$QUERY" | sed -n 's|.start.:\([0-9]*\).|\1|p')"
END="@$(echo "$QUERY"   | sed -n 's|.end.:\([0-9]*\).|\1|p')"
[ "$END" = "@" ] && END="now"
exec pakon-show -j -s "$START" -e "$END"
