#!/usr/bin/env bash
pkill -f "python3.*googletasks-widget/main.py" 2>/dev/null
sleep 0.5
GDK_BACKEND=x11 python3 ~/src/googletasks-widget/main.py &
echo "googletasks-widget reiniciado (PID $!)"
