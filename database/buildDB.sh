#!/bin/bash

rm ncaa.db3
sqlite3 < script.txt
python input_games_stats_to_db.py