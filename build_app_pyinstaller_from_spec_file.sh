#! /bin/bash
git rev-parse --short HEAD > git_commit_sha.txt
/home/mitjan/miniconda3/envs/39nov/bin/pyinstaller -y --clean Basic_GUI.spec
pause
